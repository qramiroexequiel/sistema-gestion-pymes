"""
Vistas del módulo core.
"""

from datetime import datetime, timedelta

from django.shortcuts import render, redirect
from django.views.generic import TemplateView, UpdateView
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.db.models import Count, Sum
from django.http import Http404
from .mixins import CompanyRequiredMixin, CompanyContextMixin
from .models import Membership, Company
from django.contrib.auth.models import User


class DashboardView(CompanyRequiredMixin, CompanyContextMixin, TemplateView):
    """
    Vista del dashboard principal con KPIs operativos y datos para Chart.js.
    Todos los cálculos respetan request.current_company.
    """
    template_name = 'core/dashboard.html'

    def get_context_data(self, **kwargs):
        """Calcula KPIs y datos para gráficos (Ventas vs Compras 30 días, Top 5 clientes)."""
        context = super().get_context_data(**kwargs)
        company = self.get_company()

        if company:
            from operations.models import Operation
            from customers.models import Customer
            from products.models import Product

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

            # Clientes y productos activos
            active_customers = Customer.objects.for_company(company).filter(active=True).count()
            active_products = Product.objects.for_company(company).filter(active=True).count()

            # Totales generales
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

            # --- Tendencia ventas: últimos 30 días vs 30 días previos ---
            ventas_tendencia = self._ventas_tendencia_30_dias(company, today)

            # --- Datos para Chart.js (siempre filtrados por company) ---
            chart_sales_vs_purchases = self._chart_sales_vs_purchases_30_days(company)
            chart_top_customers = self._chart_top_customers(company)

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
                'ventas_tendencia': ventas_tendencia,
                'chart_sales_vs_purchases': chart_sales_vs_purchases,
                'chart_top_customers': chart_top_customers,
                'show_charts': True,
            })

        return context

    def _ventas_tendencia_30_dias(self, company, today):
        """
        Variación porcentual de ventas confirmadas: últimos 30 días vs 30 días previos.
        Retorna un float (porcentaje) o None si no hay período anterior para comparar.
        """
        from operations.models import Operation

        end_last_30 = today
        start_last_30 = today - timedelta(days=29)
        start_prev_30 = today - timedelta(days=59)
        end_prev_30 = today - timedelta(days=30)

        sales_last_30 = (
            Operation.objects.for_company(company)
            .filter(
                type='sale',
                status='confirmed',
                date__gte=start_last_30,
                date__lte=end_last_30,
            )
            .aggregate(total=Sum('total'))['total']
            or 0
        )
        sales_prev_30 = (
            Operation.objects.for_company(company)
            .filter(
                type='sale',
                status='confirmed',
                date__gte=start_prev_30,
                date__lte=end_prev_30,
            )
            .aggregate(total=Sum('total'))['total']
            or 0
        )

        if sales_prev_30 == 0:
            if sales_last_30 > 0:
                return 100.0  # Todo el crecimiento es "nuevo"
            return 0.0
        diff = float(sales_last_30) - float(sales_prev_30)
        return round((diff / float(sales_prev_30)) * 100, 1)

    def _chart_sales_vs_purchases_30_days(self, company):
        """
        Últimos 30 días: para cada día, total de ventas y compras confirmadas.
        Retorna un JSON string listo para el template (lista de {date, sales, purchases}).
        """
        from operations.models import Operation

        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=29)
        days = [start_date + timedelta(days=i) for i in range(30)]

        # Una sola consulta agrupada por date y type
        qs = (
            Operation.objects.for_company(company)
            .filter(status='confirmed', date__gte=start_date, date__lte=end_date)
            .values('date', 'type')
            .annotate(total=Sum('total'))
        )
        by_date = {}
        for row in qs:
            d = row['date'].isoformat() if hasattr(row['date'], 'isoformat') else str(row['date'])
            if d not in by_date:
                by_date[d] = {'sales': 0.0, 'purchases': 0.0}
            if row['type'] == 'sale':
                by_date[d]['sales'] = float(row['total'] or 0)
            else:
                by_date[d]['purchases'] = float(row['total'] or 0)

        result = []
        for d in days:
            key = d.isoformat()
            result.append({
                'date': key,
                'date_label': d.strftime('%d/%m'),
                'sales': by_date.get(key, {}).get('sales', 0),
                'purchases': by_date.get(key, {}).get('purchases', 0),
            })
        return result

    def _chart_top_customers(self, company):
        """
        Top 5 clientes por volumen total de ventas (operaciones confirmadas).
        Retorna un JSON string (lista de {name, total}).
        """
        from operations.models import Operation
        from customers.models import Customer

        top = (
            Customer.objects.for_company(company)
            .filter(
                operations__type='sale',
                operations__status='confirmed',
                operations__company=company,
            )
            .annotate(total_sales=Sum('operations__total'))
            .order_by('-total_sales')[:5]
        )
        result = [
            {'name': c.name, 'total': float(c.total_sales or 0)}
            for c in top
        ]
        return result


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
