"""Vistas del módulo customers con protección multi-tenant completa."""

from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView, View
from django.urls import reverse_lazy
from django.contrib import messages
from django.db import models
from core.mixins import (
    CompanyRequiredMixin, 
    CompanyContextMixin, 
    CompanyFilterMixin,
    CompanyObjectMixin,
    RoleRequiredMixin,
    HTMXResponseMixin,
)
from core.constants import ROLE_ADMIN, ROLE_MANAGER, ROLE_OPERATOR
from core.utils import log_audit
from core.utils.request import get_client_ip
from core.utils.security_services import check_anomalous_behavior
from core.utils.csv_export import export_csv_response
from .models import Customer
from .forms import CustomerForm


class CustomerListView(
    CompanyRequiredMixin, 
    CompanyContextMixin, 
    CompanyFilterMixin,
    HTMXResponseMixin,
    ListView
):
    """
    Lista de clientes.
    Protegido por tenant y filtrado automático por empresa.
    Soporta HTMX para actualizaciones parciales.
    """
    template_name = 'customers/list.html'
    partial_template_name = 'customers/_customers_list.html'
    model = Customer
    context_object_name = 'customers'
    paginate_by = 25
    
    def get_queryset(self):
        """Filtra clientes por empresa actual. El filtrado por empresa es automático por CompanyFilterMixin."""
        # Obtener queryset ya filtrado por empresa (gracias a CompanyFilterMixin)
        queryset = super().get_queryset()
        company = self.get_company()
        
        if company is None:
            return queryset.none()
        
        # Aplicar búsqueda si existe
        search = self.request.GET.get('search', '').strip()
        if search:
            queryset = queryset.filter(
                models.Q(name__icontains=search) |
                models.Q(code__icontains=search) |
                models.Q(email__icontains=search) |
                models.Q(tax_id__icontains=search)
            )
        
        # Aplicar filtro de activos si existe
        active_filter = self.request.GET.get('active', '')
        if active_filter == '1':
            queryset = queryset.filter(active=True)
        elif active_filter == '0':
            queryset = queryset.filter(active=False)
        
        return queryset.order_by('name')
    
    def get_context_data(self, **kwargs):
        """Añade datos adicionales al contexto."""
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['active_filter'] = self.request.GET.get('active', '')
        return context


class CustomerCreateView(
    CompanyRequiredMixin,
    CompanyContextMixin,
    RoleRequiredMixin,
    CreateView
):
    """
    Crear nuevo cliente.
    Protegido por tenant y roles (admin, manager, operator).
    """
    template_name = 'customers/create.html'
    form_class = CustomerForm
    model = Customer
    required_roles = [ROLE_ADMIN, ROLE_MANAGER, ROLE_OPERATOR]
    
    def get_form_kwargs(self):
        """Pasa la empresa y usuario al formulario."""
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.get_company()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        """Mensaje de éxito después de crear."""
        response = super().form_valid(form)
        
        # Auditoría: registrar creación
        log_audit(
            company=self.get_company(),
            user=self.request.user,
            action='create',
            model_name='Customer',
            object_id=self.object.pk,
            changes={'name': form.cleaned_data.get('name'), 'code': form.cleaned_data.get('code')},
            ip_address=get_client_ip(self.request)
        )
        
        messages.success(self.request, f'Cliente "{form.cleaned_data["name"]}" creado correctamente.')
        return response
    
    def get_success_url(self):
        """URL después de crear exitosamente."""
        return reverse_lazy('customers:detail', kwargs={'pk': self.object.pk})


class CustomerDetailView(
    CompanyRequiredMixin,
    CompanyContextMixin,
    CompanyObjectMixin,
    DetailView
):
    """
    Detalle de cliente.
    Protegido por tenant - verifica que pertenezca a la empresa actual.
    """
    template_name = 'customers/detail.html'
    model = Customer
    context_object_name = 'customer'


class CustomerUpdateView(
    CompanyRequiredMixin,
    CompanyContextMixin,
    CompanyObjectMixin,
    RoleRequiredMixin,
    UpdateView
):
    """
    Actualizar cliente.
    Protegido por tenant y roles (admin, manager, operator).
    """
    template_name = 'customers/update.html'
    form_class = CustomerForm
    model = Customer
    required_roles = [ROLE_ADMIN, ROLE_MANAGER, ROLE_OPERATOR]
    
    def get_form_kwargs(self):
        """Pasa la empresa y usuario al formulario."""
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.get_company()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        """Mensaje de éxito después de actualizar."""
        # Guardar cambios para auditoría
        old_data = {
            'name': self.object.name,
            'code': self.object.code,
            'email': self.object.email,
            'active': self.object.active,
        }
        
        response = super().form_valid(form)
        
        # Calcular cambios
        changes = {}
        for field, old_value in old_data.items():
            new_value = form.cleaned_data.get(field)
            if old_value != new_value:
                changes[field] = {'old': old_value, 'new': new_value}
        
        # Auditoría: registrar actualización
        log_audit(
            company=self.get_company(),
            user=self.request.user,
            action='update',
            model_name='Customer',
            object_id=self.object.pk,
            changes=changes,
            ip_address=get_client_ip(self.request)
        )
        
        messages.success(self.request, f'Cliente "{form.cleaned_data["name"]}" actualizado correctamente.')
        return response
    
    def get_success_url(self):
        """URL después de actualizar exitosamente."""
        return reverse_lazy('customers:detail', kwargs={'pk': self.object.pk})


class CustomerDeleteView(
    CompanyRequiredMixin,
    CompanyContextMixin,
    CompanyObjectMixin,
    RoleRequiredMixin,
    DeleteView
):
    """
    Eliminar cliente.
    Protegido por tenant y roles (solo admin y manager).
    """
    template_name = 'customers/delete.html'
    model = Customer
    success_url = reverse_lazy('customers:list')
    context_object_name = 'customer'
    required_roles = [ROLE_ADMIN, ROLE_MANAGER]
    
    def delete(self, request, *args, **kwargs):
        """Mensaje de éxito después de eliminar."""
        customer = self.get_object()
        customer_name = customer.name
        customer_pk = customer.pk
        
        # Auditoría: registrar eliminación (antes de eliminar)
        log_audit(
            company=self.get_company(),
            user=request.user,
            action='delete',
            model_name='Customer',
            object_id=customer_pk,
            changes={'name': customer_name, 'code': customer.code},
            ip_address=get_client_ip(request)
        )
        
        response = super().delete(request, *args, **kwargs)
        check_anomalous_behavior(request.user, self.get_company())
        messages.success(request, f'Cliente "{customer_name}" eliminado correctamente.')
        return response


class CustomerExportCSVView(
    CompanyRequiredMixin,
    CompanyContextMixin,
    RoleRequiredMixin,
    View
):
    """Exporta clientes a CSV."""
    required_roles = [ROLE_ADMIN, ROLE_MANAGER, ROLE_OPERATOR]
    
    def get(self, request):
        """Genera CSV de clientes con los filtros activos."""
        company = request.current_company
        
        # Obtener queryset con los mismos filtros que el listado
        queryset = Customer.objects.for_company(company)
        
        # Aplicar búsqueda
        search = request.GET.get('search', '').strip()
        if search:
            queryset = queryset.filter(
                models.Q(name__icontains=search) |
                models.Q(code__icontains=search) |
                models.Q(email__icontains=search) |
                models.Q(tax_id__icontains=search)
            )
        
        # Aplicar filtro de activos
        active_filter = request.GET.get('active', '')
        if active_filter == '1':
            queryset = queryset.filter(active=True)
        elif active_filter == '0':
            queryset = queryset.filter(active=False)
        
        customers = queryset.order_by('name')
        
        # Preparar datos para CSV
        headers = ['Código', 'Nombre', 'CUIT/RUT/NIT', 'Email', 'Teléfono', 'Dirección', 'Estado']
        rows = []
        
        for customer in customers:
            rows.append([
                customer.code,
                customer.name,
                customer.tax_id or '',
                customer.email or '',
                customer.phone or '',
                customer.address or '',
                'Activo' if customer.active else 'Inactivo',
            ])
        
        filename = f'clientes_{company.name.replace(" ", "_")}'
        return export_csv_response(filename, headers, rows)
