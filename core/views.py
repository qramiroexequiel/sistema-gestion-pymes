"""
Vistas del módulo core.
"""

from django.shortcuts import render, redirect
from django.views.generic import TemplateView, UpdateView
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.db.models import Count
from django.http import Http404
from .mixins import CompanyRequiredMixin, CompanyContextMixin
from .models import Membership, Company
from django.contrib.auth.models import User


class DashboardView(CompanyRequiredMixin, CompanyContextMixin, TemplateView):
    """
    Vista del dashboard principal con KPIs operativos.
    Todos los cálculos se realizan en backend usando services.
    """
    template_name = 'core/dashboard.html'
    
    def get_context_data(self, **kwargs):
        """Calcula KPIs operativos para el dashboard."""
        context = super().get_context_data(**kwargs)
        company = self.get_company()
        
        if company:
            from datetime import datetime, timedelta
            from django.db.models import Sum, Q
            from operations.models import Operation
            from customers.models import Customer
            from products.models import Product
            
            # Fecha actual y primer día del mes
            today = datetime.now().date()
            first_day_month = today.replace(day=1)
            
            # Ventas del mes (solo confirmadas)
            sales_month = Operation.objects.for_company(company).filter(
                type='sale',
                status='confirmed',
                date__gte=first_day_month,
                date__lte=today
            ).aggregate(
                total=Sum('total'),
                count=Count('id')
            )
            
            # Compras del mes (solo confirmadas)
            purchases_month = Operation.objects.for_company(company).filter(
                type='purchase',
                status='confirmed',
                date__gte=first_day_month,
                date__lte=today
            ).aggregate(
                total=Sum('total'),
                count=Count('id')
            )
            
            # Operaciones pendientes (borradores)
            pending_operations = Operation.objects.for_company(company).filter(
                status='draft'
            ).count()
            
            # Clientes activos
            active_customers = Customer.objects.for_company(company).filter(active=True).count()
            
            # Productos activos
            active_products = Product.objects.for_company(company).filter(active=True).count()
            
            # Totales generales (todas las operaciones confirmadas, sin importar fecha)
            total_sales = Operation.objects.for_company(company).filter(
                type='sale',
                status='confirmed'
            ).aggregate(total=Sum('total'))['total'] or 0
            
            total_purchases = Operation.objects.for_company(company).filter(
                type='purchase',
                status='confirmed'
            ).aggregate(total=Sum('total'))['total'] or 0
            
            total_operations = Operation.objects.for_company(company).filter(
                status='confirmed'
            ).count()
            
            context.update({
                'sales_month_total': sales_month['total'] or 0,
                'sales_month_count': sales_month['count'] or 0,
                'purchases_month_total': purchases_month['total'] or 0,
                'purchases_month_count': purchases_month['count'] or 0,
                'pending_operations': pending_operations,
                'active_customers': active_customers,
                'active_products': active_products,
                'total_sales': total_sales,
                'total_purchases': total_purchases,
                'total_operations': total_operations,
                'has_data': total_operations > 0 or active_customers > 0 or active_products > 0,
            })
        
        return context


@method_decorator(login_required, name='dispatch')
class ProfileView(CompanyContextMixin, UpdateView):
    """Vista de perfil del usuario."""
    model = User
    template_name = 'core/profile.html'
    fields = ['first_name', 'last_name', 'email']
    success_url = '/perfil/'
    
    def get_object(self):
        return self.request.user
    
    def form_valid(self, form):
        messages.success(self.request, 'Perfil actualizado correctamente.')
        return super().form_valid(form)


@method_decorator(login_required, name='dispatch')
class CompanySelectView(CompanyContextMixin, TemplateView):
    """Vista para seleccionar empresa."""
    template_name = 'core/company_select.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        memberships = Membership.objects.filter(
            user=self.request.user,
            active=True
        ).select_related('company')
        context['memberships'] = memberships
        return context
    
    def post(self, request, *args, **kwargs):
        """Procesa la selección de empresa."""
        company_id = request.POST.get('company_id')
        
        if company_id:
            try:
                membership = Membership.objects.get(
                    user=request.user,
                    company_id=company_id,
                    active=True
                )
                request.session['current_company_id'] = membership.company.id
                messages.success(request, f'Empresa {membership.company.name} seleccionada.')
                return redirect('core:dashboard')
            except Membership.DoesNotExist:
                messages.error(request, 'La empresa seleccionada no es válida.')
        
        return redirect('core:company_select')


def handler404(request, exception):
    """Maneja errores 404 con branding Suite Business."""
    return render(request, 'core/404.html', status=404)


def handler500(request):
    """Maneja errores 500 con branding Suite Business."""
    return render(request, 'core/500.html', status=500)
