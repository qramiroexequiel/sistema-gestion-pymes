"""Vistas del módulo suppliers con protección multi-tenant completa."""

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
from core.utils.csv_export import export_csv_response
from .models import Supplier
from .forms import SupplierForm


class SupplierListView(
    CompanyRequiredMixin, 
    CompanyContextMixin, 
    CompanyFilterMixin,
    HTMXResponseMixin,
    ListView
):
    """
    Lista de proveedores.
    Protegido por tenant y filtrado automático por empresa.
    Soporta HTMX para actualizaciones parciales.
    """
    template_name = 'suppliers/list.html'
    partial_template_name = 'suppliers/_suppliers_list.html'
    model = Supplier
    context_object_name = 'suppliers'
    paginate_by = 25
    
    def get_queryset(self):
        """Filtra proveedores por empresa actual. El filtrado por empresa es automático por CompanyFilterMixin."""
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


class SupplierCreateView(
    CompanyRequiredMixin,
    CompanyContextMixin,
    RoleRequiredMixin,
    CreateView
):
    """
    Crear nuevo proveedor.
    Protegido por tenant y roles (admin, manager, operator).
    """
    template_name = 'suppliers/create.html'
    form_class = SupplierForm
    model = Supplier
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
            model_name='Supplier',
            object_id=self.object.pk,
            changes={'name': form.cleaned_data.get('name'), 'code': form.cleaned_data.get('code')},
            ip_address=get_client_ip(self.request)
        )
        
        messages.success(self.request, f'Proveedor "{form.cleaned_data["name"]}" creado correctamente.')
        return response
    
    def get_success_url(self):
        """URL después de crear exitosamente."""
        return reverse_lazy('suppliers:detail', kwargs={'pk': self.object.pk})


class SupplierDetailView(
    CompanyRequiredMixin,
    CompanyContextMixin,
    CompanyObjectMixin,
    DetailView
):
    """
    Detalle de proveedor.
    Protegido por tenant - verifica que pertenezca a la empresa actual.
    """
    template_name = 'suppliers/detail.html'
    model = Supplier
    context_object_name = 'supplier'


class SupplierUpdateView(
    CompanyRequiredMixin,
    CompanyContextMixin,
    CompanyObjectMixin,
    RoleRequiredMixin,
    UpdateView
):
    """
    Actualizar proveedor.
    Protegido por tenant y roles (admin, manager, operator).
    """
    template_name = 'suppliers/update.html'
    form_class = SupplierForm
    model = Supplier
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
            model_name='Supplier',
            object_id=self.object.pk,
            changes=changes,
            ip_address=get_client_ip(self.request)
        )
        
        messages.success(self.request, f'Proveedor "{form.cleaned_data["name"]}" actualizado correctamente.')
        return response
    
    def get_success_url(self):
        """URL después de actualizar exitosamente."""
        return reverse_lazy('suppliers:detail', kwargs={'pk': self.object.pk})


class SupplierDeleteView(
    CompanyRequiredMixin,
    CompanyContextMixin,
    CompanyObjectMixin,
    RoleRequiredMixin,
    DeleteView
):
    """
    Eliminar proveedor.
    Protegido por tenant y roles (solo admin y manager).
    """
    template_name = 'suppliers/delete.html'
    model = Supplier
    success_url = reverse_lazy('suppliers:list')
    context_object_name = 'supplier'
    required_roles = [ROLE_ADMIN, ROLE_MANAGER]
    
    def delete(self, request, *args, **kwargs):
        """Mensaje de éxito después de eliminar."""
        supplier = self.get_object()
        supplier_name = supplier.name
        supplier_pk = supplier.pk
        
        # Auditoría: registrar eliminación (antes de eliminar)
        log_audit(
            company=self.get_company(),
            user=request.user,
            action='delete',
            model_name='Supplier',
            object_id=supplier_pk,
            changes={'name': supplier_name, 'code': supplier.code},
            ip_address=get_client_ip(request)
        )
        
        response = super().delete(request, *args, **kwargs)
        messages.success(request, f'Proveedor "{supplier_name}" eliminado correctamente.')
        return response


class SupplierExportCSVView(
    CompanyRequiredMixin,
    CompanyContextMixin,
    RoleRequiredMixin,
    View
):
    """Exporta proveedores a CSV."""
    required_roles = [ROLE_ADMIN, ROLE_MANAGER, ROLE_OPERATOR]
    
    def get(self, request):
        """Genera CSV de proveedores con los filtros activos."""
        company = request.current_company
        
        # Obtener queryset con los mismos filtros que el listado
        queryset = Supplier.objects.for_company(company)
        
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
        
        suppliers = queryset.order_by('name')
        
        # Preparar datos para CSV
        headers = ['Código', 'Nombre', 'CUIT/RUT/NIT', 'Email', 'Teléfono', 'Dirección', 'Estado']
        rows = []
        
        for supplier in suppliers:
            rows.append([
                supplier.code,
                supplier.name,
                supplier.tax_id or '',
                supplier.email or '',
                supplier.phone or '',
                supplier.address or '',
                'Activo' if supplier.active else 'Inactivo',
            ])
        
        filename = f'proveedores_{company.name.replace(" ", "_")}'
        return export_csv_response(filename, headers, rows)
