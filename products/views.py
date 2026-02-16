"""Vistas del módulo products con protección multi-tenant completa."""

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
from .models import Product
from .forms import ProductForm


class ProductListView(
    CompanyRequiredMixin, 
    CompanyContextMixin, 
    CompanyFilterMixin,
    HTMXResponseMixin,
    ListView
):
    """
    Lista de productos/servicios.
    Protegido por tenant y filtrado automático por empresa.
    Soporta HTMX para actualizaciones parciales.
    """
    template_name = 'products/list.html'
    partial_template_name = 'products/_products_list.html'
    model = Product
    context_object_name = 'products'
    paginate_by = 25
    
    def get_queryset(self):
        """Filtra productos por empresa actual. El filtrado por empresa es automático por CompanyFilterMixin."""
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
                models.Q(description__icontains=search)
            )
        
        # Aplicar filtro de tipo si existe
        type_filter = self.request.GET.get('type', '')
        if type_filter in ['product', 'service']:
            queryset = queryset.filter(type=type_filter)
        
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
        context['type_filter'] = self.request.GET.get('type', '')
        context['active_filter'] = self.request.GET.get('active', '')
        return context


class ProductCreateView(
    CompanyRequiredMixin,
    CompanyContextMixin,
    RoleRequiredMixin,
    CreateView
):
    """
    Crear nuevo producto/servicio.
    Protegido por tenant y roles (admin, manager, operator).
    """
    template_name = 'products/create.html'
    form_class = ProductForm
    model = Product
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
            model_name='Product',
            object_id=self.object.pk,
            changes={'name': form.cleaned_data.get('name'), 'code': form.cleaned_data.get('code'), 'type': form.cleaned_data.get('type')},
            ip_address=get_client_ip(self.request)
        )
        
        messages.success(self.request, f'Producto/Servicio "{form.cleaned_data["name"]}" creado correctamente.')
        return response
    
    def get_success_url(self):
        """URL después de crear exitosamente."""
        return reverse_lazy('products:detail', kwargs={'pk': self.object.pk})


class ProductDetailView(
    CompanyRequiredMixin,
    CompanyContextMixin,
    CompanyObjectMixin,
    DetailView
):
    """
    Detalle de producto/servicio.
    Protegido por tenant - verifica que pertenezca a la empresa actual.
    """
    template_name = 'products/detail.html'
    model = Product
    context_object_name = 'product'


class ProductUpdateView(
    CompanyRequiredMixin,
    CompanyContextMixin,
    CompanyObjectMixin,
    RoleRequiredMixin,
    UpdateView
):
    """
    Actualizar producto/servicio.
    Protegido por tenant y roles (admin, manager, operator).
    """
    template_name = 'products/update.html'
    form_class = ProductForm
    model = Product
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
            'type': self.object.type,
            'price': self.object.price,
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
            model_name='Product',
            object_id=self.object.pk,
            changes=changes,
            ip_address=get_client_ip(self.request)
        )
        
        messages.success(self.request, f'Producto/Servicio "{form.cleaned_data["name"]}" actualizado correctamente.')
        return response
    
    def get_success_url(self):
        """URL después de actualizar exitosamente."""
        return reverse_lazy('products:detail', kwargs={'pk': self.object.pk})


class ProductDeleteView(
    CompanyRequiredMixin,
    CompanyContextMixin,
    CompanyObjectMixin,
    RoleRequiredMixin,
    DeleteView
):
    """
    Eliminar producto/servicio.
    Protegido por tenant y roles (solo admin y manager).
    """
    template_name = 'products/delete.html'
    model = Product
    success_url = reverse_lazy('products:list')
    context_object_name = 'product'
    required_roles = [ROLE_ADMIN, ROLE_MANAGER]
    
    def delete(self, request, *args, **kwargs):
        """Mensaje de éxito después de eliminar."""
        product = self.get_object()
        product_name = product.name
        product_pk = product.pk
        
        # Auditoría: registrar eliminación (antes de eliminar)
        log_audit(
            company=self.get_company(),
            user=request.user,
            action='delete',
            model_name='Product',
            object_id=product_pk,
            changes={'name': product_name, 'code': product.code},
            ip_address=get_client_ip(request)
        )
        
        response = super().delete(request, *args, **kwargs)
        messages.success(request, f'Producto/Servicio "{product_name}" eliminado correctamente.')
        return response


class ProductExportCSVView(
    CompanyRequiredMixin,
    CompanyContextMixin,
    RoleRequiredMixin,
    View
):
    """Exporta productos/servicios a CSV."""
    required_roles = [ROLE_ADMIN, ROLE_MANAGER, ROLE_OPERATOR]
    
    def get(self, request):
        """Genera CSV de productos/servicios con los filtros activos."""
        company = request.current_company
        
        # Obtener queryset con los mismos filtros que el listado
        queryset = Product.objects.for_company(company)
        
        # Aplicar búsqueda
        search = request.GET.get('search', '').strip()
        if search:
            queryset = queryset.filter(
                models.Q(name__icontains=search) |
                models.Q(code__icontains=search) |
                models.Q(description__icontains=search)
            )
        
        # Aplicar filtro de tipo
        type_filter = request.GET.get('type', '')
        if type_filter in ['product', 'service']:
            queryset = queryset.filter(type=type_filter)
        
        # Aplicar filtro de activos
        active_filter = request.GET.get('active', '')
        if active_filter == '1':
            queryset = queryset.filter(active=True)
        elif active_filter == '0':
            queryset = queryset.filter(active=False)
        
        products = queryset.order_by('name')
        
        # Preparar datos para CSV
        headers = ['Código', 'Nombre', 'Tipo', 'Precio', 'Unidad de Medida', 'Descripción', 'Estado']
        rows = []
        
        for product in products:
            rows.append([
                product.code,
                product.name,
                product.get_type_display(),
                f'{product.price:.2f}',
                product.unit_of_measure,
                product.description or '',
                'Activo' if product.active else 'Inactivo',
            ])
        
        filename = f'productos_servicios_{company.name.replace(" ", "_")}'
        return export_csv_response(filename, headers, rows)
