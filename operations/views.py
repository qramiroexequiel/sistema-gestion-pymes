"""Vistas del módulo operations con protección multi-tenant completa."""

from django.views.generic import ListView, CreateView, DetailView, View
from django.urls import reverse_lazy, reverse
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.db import models, transaction
from django.core.exceptions import ValidationError
from core.mixins import (
    CompanyRequiredMixin, 
    CompanyContextMixin, 
    CompanyFilterMixin,
    CompanyObjectMixin,
    RoleRequiredMixin,
    HTMXResponseMixin,
)
from core.constants import ROLE_ADMIN, ROLE_MANAGER, ROLE_OPERATOR
from core.utils.csv_export import export_csv_response
from core.utils import log_audit
from core.utils.request import get_client_ip
from operations.services import (
    create_operation,
    recalculate_operation_totals,
    confirm_operation,
    cancel_operation,
    add_item_to_operation,
    remove_item_from_operation,
    update_operation_item,
    validate_operation_can_be_modified,
)
from .models import Operation, OperationItem
from .forms import OperationForm, OperationItemFormSet


class OperationListView(
    CompanyRequiredMixin, 
    CompanyContextMixin, 
    CompanyFilterMixin,
    HTMXResponseMixin,
    ListView
):
    """
    Lista de operaciones.
    Protegido por tenant y filtrado automático por empresa.
    Soporta HTMX para actualizaciones parciales.
    """
    template_name = 'operations/list.html'
    partial_template_name = 'operations/_operations_list.html'
    model = Operation
    context_object_name = 'operations'
    paginate_by = 25
    
    def get_queryset(self):
        """Filtra operaciones por empresa actual."""
        queryset = super().get_queryset()
        company = self.get_company()
        
        if company is None:
            return queryset.none()
        
        # Aplicar filtro de tipo si existe
        type_filter = self.request.GET.get('type', '')
        if type_filter in ['sale', 'purchase']:
            queryset = queryset.filter(type=type_filter)
        
        # Aplicar filtro de estado si existe
        status_filter = self.request.GET.get('status', '')
        if status_filter in ['draft', 'confirmed', 'cancelled']:
            queryset = queryset.filter(status=status_filter)
        
        # Aplicar búsqueda si existe
        search = self.request.GET.get('search', '').strip()
        if search:
            queryset = queryset.filter(
                models.Q(number__icontains=search) |
                models.Q(customer__name__icontains=search) |
                models.Q(supplier__name__icontains=search)
            )
        
        return queryset.order_by('-date', '-number')
    
    def get_context_data(self, **kwargs):
        """Añade datos adicionales al contexto."""
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['type_filter'] = self.request.GET.get('type', '')
        context['status_filter'] = self.request.GET.get('status', '')
        return context


class OperationCreateView(
    CompanyRequiredMixin,
    CompanyContextMixin,
    RoleRequiredMixin,
    CreateView
):
    """
    Crear nueva operación.
    Protegido por tenant y roles (admin, manager, operator).
    """
    template_name = 'operations/create.html'
    form_class = OperationForm
    model = Operation
    required_roles = [ROLE_ADMIN, ROLE_MANAGER, ROLE_OPERATOR]
    
    def get_form_kwargs(self):
        """Pasa la empresa y usuario al formulario."""
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.get_company()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_context_data(self, **kwargs):
        """Añade el formset de items al contexto."""
        context = super().get_context_data(**kwargs)
        company = self.get_company()
        
        if self.request.POST:
            context['item_formset'] = OperationItemFormSet(
                self.request.POST,
                instance=self.object if self.object else None,
                prefix='items'
            )
        else:
            context['item_formset'] = OperationItemFormSet(
                instance=self.object if self.object else None,
                prefix='items'
            )
        
        # Pasar company a cada form del formset usando form_kwargs
        # Crear una función helper para inicializar forms con company
        def formset_form_kwargs(form, index):
            return {'company': company}
        
        # Asignar company a cada form del formset
        for form in context['item_formset']:
            if form:
                form.company = company
                # Re-inicializar el queryset de productos
                if company:
                    form.fields['product'].queryset = Product.objects.for_company(company).filter(active=True)
                else:
                    form.fields['product'].queryset = Product.objects.none()
        
        return context
    
    def form_valid(self, form):
        """Guarda la operación y sus items. Atómico: si falla cualquier paso, no se persiste nada."""
        context = self.get_context_data()
        item_formset = context['item_formset']

        if not item_formset.is_valid():
            return self.form_invalid(form)

        company = self.get_company()
        try:
            with transaction.atomic():
                operation = create_operation(
                    company=company,
                    type=form.cleaned_data['type'],
                    date=form.cleaned_data['date'],
                    customer=form.cleaned_data.get('customer'),
                    supplier=form.cleaned_data.get('supplier'),
                    notes=form.cleaned_data.get('notes'),
                    created_by=self.request.user
                )

                item_formset.instance = operation
                items = item_formset.save(commit=False)

                for item in items:
                    if item.product.company != company:
                        raise ValidationError(
                            f'El producto {item.product.name} no pertenece a esta empresa.'
                        )
                    add_item_to_operation(
                        operation=operation,
                        product=item.product,
                        quantity=item.quantity,
                        unit_price=item.unit_price
                    )

                for item in item_formset.deleted_objects:
                    remove_item_from_operation(operation, item.id)

                if not operation.items.exists():
                    raise ValidationError('La operación debe tener al menos un item.')

                log_audit(
                    company=company,
                    user=self.request.user,
                    action='create',
                    model_name='Operation',
                    object_id=operation.pk,
                    changes={
                        'type': operation.type,
                        'number': operation.number,
                        'date': str(operation.date)
                    },
                    ip_address=get_client_ip(self.request)
                )
        except ValidationError as e:
            messages.error(self.request, str(e))
            return self.form_invalid(form)

        messages.success(self.request, f'Operación "{operation.number}" creada correctamente.')
        return redirect('operations:detail', pk=operation.pk)
    
    def get_success_url(self):
        """URL después de crear exitosamente."""
        return reverse_lazy('operations:detail', kwargs={'pk': self.object.pk})


class OperationDetailView(
    CompanyRequiredMixin,
    CompanyContextMixin,
    CompanyObjectMixin,
    DetailView
):
    """
    Detalle de operación.
    Protegido por tenant - verifica que pertenezca a la empresa actual.
    """
    template_name = 'operations/detail.html'
    model = Operation
    context_object_name = 'operation'
    
    def get_context_data(self, **kwargs):
        """Añade los items de la operación al contexto."""
        context = super().get_context_data(**kwargs)
        operation = self.get_object()
        context['items'] = operation.items.all()
        return context


class OperationConfirmView(
    CompanyRequiredMixin,
    CompanyContextMixin,
    RoleRequiredMixin,
    View
):
    """
    Confirmar operación.
    Protegido por tenant y roles (admin, manager).
    """
    required_roles = [ROLE_ADMIN, ROLE_MANAGER]
    model = Operation
    
    def get_operation(self, pk):
        """Obtiene la operación filtrando por empresa."""
        company = self.get_company()
        if company is None:
            from django.http import Http404
            raise Http404('No tiene una empresa activa.')
        
        operation = get_object_or_404(
            Operation.objects.for_company(company),
            pk=pk
        )
        return operation
    
    def post(self, request, pk):
        """Confirma la operación."""
        operation = self.get_operation(pk)
        
        try:
            confirm_operation(operation, user=request.user)
            
            # Auditoría: registrar confirmación
            log_audit(
                company=self.get_company(),
                user=request.user,
                action='confirm',
                model_name='Operation',
                object_id=operation.pk,
                changes={'status': 'confirmed'},
                ip_address=get_client_ip(request)
            )
            
            messages.success(request, f'Operación "{operation.number}" confirmada correctamente.')
        except Exception as e:
            messages.error(request, f'Error al confirmar operación: {str(e)}')
        
        return redirect('operations:detail', pk=operation.pk)


class OperationCancelView(
    CompanyRequiredMixin,
    CompanyContextMixin,
    RoleRequiredMixin,
    View
):
    """
    Cancelar operación.
    Protegido por tenant y roles (admin, manager).
    """
    required_roles = [ROLE_ADMIN, ROLE_MANAGER]
    model = Operation
    
    def get_operation(self, pk):
        """Obtiene la operación filtrando por empresa."""
        company = self.get_company()
        if company is None:
            from django.http import Http404
            raise Http404('No tiene una empresa activa.')
        
        operation = get_object_or_404(
            Operation.objects.for_company(company),
            pk=pk
        )
        return operation
    
    def post(self, request, pk):
        """Cancela la operación."""
        operation = self.get_operation(pk)
        
        try:
            cancel_operation(operation, user=request.user)
            
            # Auditoría: registrar cancelación
            log_audit(
                company=self.get_company(),
                user=request.user,
                action='cancel',
                model_name='Operation',
                object_id=operation.pk,
                changes={'status': 'cancelled'},
                ip_address=get_client_ip(request)
            )
            
            messages.success(request, f'Operación "{operation.number}" cancelada correctamente.')
        except Exception as e:
            messages.error(request, f'Error al cancelar operación: {str(e)}')
        
        return redirect('operations:detail', pk=operation.pk)


class OperationExportCSVView(
    CompanyRequiredMixin,
    CompanyContextMixin,
    RoleRequiredMixin,
    View
):
    """Exporta operaciones a CSV."""
    required_roles = [ROLE_ADMIN, ROLE_MANAGER, ROLE_OPERATOR]
    
    def get(self, request):
        """Genera CSV de operaciones con los filtros activos."""
        company = request.current_company
        
        # Obtener queryset con los mismos filtros que el listado
        queryset = Operation.objects.for_company(company)
        
        # Aplicar filtros
        type_filter = request.GET.get('type', '')
        if type_filter in ['sale', 'purchase']:
            queryset = queryset.filter(type=type_filter)
        
        status_filter = request.GET.get('status', '')
        if status_filter in ['draft', 'confirmed', 'cancelled']:
            queryset = queryset.filter(status=status_filter)
        
        search = request.GET.get('search', '').strip()
        if search:
            queryset = queryset.filter(
                models.Q(number__icontains=search) |
                models.Q(customer__name__icontains=search) |
                models.Q(supplier__name__icontains=search)
            )
        
        operations = queryset.select_related('customer', 'supplier').order_by('-date', '-number')
        
        # Preparar datos para CSV
        headers = ['Fecha', 'Tipo', 'Número', 'Cliente/Proveedor', 'Subtotal', 'Impuesto', 'Total', 'Estado']
        rows = []
        
        for operation in operations:
            client_supplier = '-'
            if operation.customer:
                client_supplier = operation.customer.name
            elif operation.supplier:
                client_supplier = operation.supplier.name
            
            rows.append([
                operation.date.strftime('%d/%m/%Y'),
                operation.get_type_display(),
                operation.number,
                client_supplier,
                f'{operation.subtotal:.2f}',
                f'{operation.tax:.2f}',
                f'{operation.total:.2f}',
                operation.get_status_display(),
            ])
        
        filename = f'operaciones_{company.name.replace(" ", "_")}'
        return export_csv_response(filename, headers, rows)
