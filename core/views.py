"""
Vistas del módulo core.
"""

from datetime import datetime, timedelta

from django.shortcuts import render, redirect
from django.views.generic import TemplateView, UpdateView, View
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.db.models import Count, Sum
from django.http import Http404, HttpResponse
from django.template.loader import render_to_string
from .mixins import CompanyRequiredMixin, CompanyContextMixin
from .models import Membership, Company
from django.contrib.auth.models import User


def _get_period_dates(period):
    """Devuelve (start_date, end_date, period_label) para period in ('7d', 'this_month', 'last_month')."""
    today = datetime.now().date()
    if period == '7d':
        start = today - timedelta(days=6)
        return start, today, 'Últimos 7 días'
    if period == 'this_month':
        start = today.replace(day=1)
        return start, today, 'Este Mes'
    if period == 'last_month':
        first_this = today.replace(day=1)
        last_prev = first_this - timedelta(days=1)
        start = last_prev.replace(day=1)
        return start, last_prev, 'Mes Pasado'
    start = today.replace(day=1)
    return start, today, 'Este Mes'


def _chart_sales_vs_purchases_range(company, start_date, end_date):
    """Para cada día en [start_date, end_date], total ventas y compras confirmadas."""
    from operations.models import Operation

    days = []
    d = start_date
    while d <= end_date:
        days.append(d)
        d += timedelta(days=1)

    qs = (
        Operation.objects.for_company(company)
        .filter(status='confirmed', date__gte=start_date, date__lte=end_date)
        .values('date', 'type')
        .annotate(total=Sum('total'))
    )
    by_date = {}
    for row in qs:
        key = row['date'].isoformat() if hasattr(row['date'], 'isoformat') else str(row['date'])
        if key not in by_date:
            by_date[key] = {'sales': 0.0, 'purchases': 0.0}
        if row['type'] == 'sale':
            by_date[key]['sales'] = float(row['total'] or 0)
        else:
            by_date[key]['purchases'] = float(row['total'] or 0)

    return [
        {
            'date': d.isoformat(),
            'date_label': d.strftime('%d/%m'),
            'sales': by_date.get(d.isoformat(), {}).get('sales', 0),
            'purchases': by_date.get(d.isoformat(), {}).get('purchases', 0),
        }
        for d in days
    ]


def _chart_top_customers_range(company, start_date, end_date):
    """Top 5 clientes por ventas confirmadas en el rango de fechas."""
    from operations.models import Operation
    from customers.models import Customer

    top = (
        Customer.objects.for_company(company)
        .filter(
            operations__type='sale',
            operations__status='confirmed',
            operations__company=company,
            operations__date__gte=start_date,
            operations__date__lte=end_date,
        )
        .annotate(total_sales=Sum('operations__total'))
        .order_by('-total_sales')[:5]
    )
    return [{'name': c.name, 'total': float(c.total_sales or 0)} for c in top]


def get_dashboard_period_data(company, period):
    """
    Datos del dashboard para un período: ventas/compras del período y datos para gráficos.
    period: '7d' | 'this_month' | 'last_month'
    """
    from operations.models import Operation

    start_date, end_date, period_label = _get_period_dates(period)
    sales_agg = (
        Operation.objects.for_company(company)
        .filter(type='sale', status='confirmed', date__gte=start_date, date__lte=end_date)
        .aggregate(total=Sum('total'), count=Count('id'))
    )
    purchases_agg = (
        Operation.objects.for_company(company)
        .filter(type='purchase', status='confirmed', date__gte=start_date, date__lte=end_date)
        .aggregate(total=Sum('total'), count=Count('id'))
    )
    period_sales = sales_agg['total'] or 0
    period_purchases = purchases_agg['total'] or 0
    period_operations = (sales_agg['count'] or 0) + (purchases_agg['count'] or 0)
    chart_sales_vs_purchases = _chart_sales_vs_purchases_range(company, start_date, end_date)
    chart_top_customers = _chart_top_customers_range(company, start_date, end_date)
    return {
        'start_date': start_date,
        'end_date': end_date,
        'period_label': period_label,
        'period': period,
        'period_sales': period_sales,
        'period_purchases': period_purchases,
        'period_operations': period_operations,
        'chart_sales_vs_purchases': chart_sales_vs_purchases,
        'chart_top_customers': chart_top_customers,
    }


class DashboardView(CompanyRequiredMixin, CompanyContextMixin, TemplateView):
    """
    Vista del dashboard principal con KPIs operativos y datos para Chart.js.
    Todos los cálculos respetan request.current_company.
    """
    template_name = 'core/dashboard.html'

    def get_context_data(self, **kwargs):
        """Calcula KPIs y datos para gráficos (Ventas vs Compras 30 días, Top 5 clientes)."""
        context = super().get_context_data(**kwargs)
        context.setdefault('security_alerts', [])
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

            # --- Período para KPIs y gráficos (filtro dinámico) ---
            period = self.request.GET.get('period', 'this_month')
            if period not in ('7d', 'this_month', 'last_month'):
                period = 'this_month'
            period_data = get_dashboard_period_data(company, period)

            # --- Tendencia ventas: últimos 30 días vs 30 días previos ---
            ventas_tendencia = self._ventas_tendencia_30_dias(company, today)

            # --- Alertas de seguridad (solo para rol ADMIN) ---
            security_alerts = []
            if getattr(self.request, 'current_membership', None) and self.request.current_membership.role == 'admin':
                from core.models import AuditLog
                security_alerts = list(
                    AuditLog.objects.filter(
                        company=company,
                        action='security_alert',
                    ).order_by('-timestamp')[:5]
                )

            context.update({
                'sales_month_total': sales_month['total'] or 0,
                'sales_month_count': sales_month['count'] or 0,
                'purchases_month_total': purchases_month['total'] or 0,
                'purchases_month_count': purchases_month['count'] or 0,
                'pending_operations': pending_operations,
                'active_customers': active_customers,
                'active_products': active_products,
                'period': period_data['period'],
                'period_label': period_data['period_label'],
                'period_sales': period_data['period_sales'],
                'period_purchases': period_data['period_purchases'],
                'period_operations': period_data['period_operations'],
                'has_data': period_data['period_operations'] > 0 or active_customers > 0 or active_products > 0,
                'ventas_tendencia': ventas_tendencia,
                'chart_sales_vs_purchases': period_data['chart_sales_vs_purchases'],
                'chart_top_customers': period_data['chart_top_customers'],
                'show_charts': True,
                'security_alerts': security_alerts,
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

@method_decorator(login_required, name='dispatch')
class DashboardDataView(CompanyRequiredMixin, CompanyContextMixin, View):
    """
    Vista HTMX: devuelve el fragmento de KPIs + gráficos para el período indicado.
    GET ?period=7d|this_month|last_month
    """
    def get(self, request, *args, **kwargs):
        company = self.get_company()
        if not company:
            from django.http import HttpResponse
            return HttpResponse(status=403)
        from django.shortcuts import render
        from customers.models import Customer
        from products.models import Product

        period = request.GET.get('period', 'this_month')
        if period not in ('7d', 'this_month', 'last_month'):
            period = 'this_month'
        data = get_dashboard_period_data(company, period)
        active_customers = Customer.objects.for_company(company).filter(active=True).count()
        active_products = Product.objects.for_company(company).filter(active=True).count()

        context = {
            'period': data['period'],
            'period_label': data['period_label'],
            'period_sales': data['period_sales'],
            'period_purchases': data['period_purchases'],
            'period_operations': data['period_operations'],
            'chart_sales_vs_purchases': data['chart_sales_vs_purchases'],
            'chart_top_customers': data['chart_top_customers'],
            'active_customers': active_customers,
            'active_products': active_products,
            'show_charts': True,
        }
        return render(request, 'core/dashboard_data_partial.html', context)


@method_decorator(login_required, name='dispatch')
class ExportDashboardPDFView(CompanyRequiredMixin, CompanyContextMixin, View):
    """
    Exporta el reporte del dashboard a PDF para el período indicado.
    GET ?period=7d|this_month|last_month
    Reutiliza get_dashboard_period_data y añade las últimas 20 operaciones del período.
    """
    def get(self, request, *args, **kwargs):
        from io import BytesIO
        from operations.models import Operation
        from customers.models import Customer
        from products.models import Product

        company = self.get_company()
        if not company:
            return HttpResponse('No hay empresa seleccionada.', status=403)

        period = request.GET.get('period', 'this_month')
        if period not in ('7d', 'this_month', 'last_month'):
            period = 'this_month'
        data = get_dashboard_period_data(company, period)
        start_date = data['start_date']
        end_date = data['end_date']

        operations = (
            Operation.objects.for_company(company)
            .filter(date__gte=start_date, date__lte=end_date, status='confirmed')
            .select_related('customer', 'supplier')
            .order_by('-date', '-id')[:20]
        )
        active_customers = Customer.objects.for_company(company).filter(active=True).count()
        active_products = Product.objects.for_company(company).filter(active=True).count()

        context = {
            'company_name': company.name,
            'period_label': data['period_label'],
            'period_sales': data['period_sales'],
            'period_purchases': data['period_purchases'],
            'period_operations': data['period_operations'],
            'active_customers': active_customers,
            'active_products': active_products,
            'operations': operations,
            'report_date': datetime.now(),
        }
        html = render_to_string('core/reports/dashboard_pdf.html', context)

        result = BytesIO()
        try:
            from xhtml2pdf import pisa
            src = BytesIO(html.encode('utf-8'))
            pisa_status = pisa.CreatePDF(src, dest=result, encoding='utf-8')
            if pisa_status.err:
                return HttpResponse('Error al generar el PDF.', status=500)
        except ImportError:
            return HttpResponse(
                'La librería xhtml2pdf no está instalada. Ejecutá: pip install xhtml2pdf',
                status=500,
            )

        result.seek(0)
        response = HttpResponse(result.getvalue(), content_type='application/pdf')
        filename = f'reporte-dashboard-{period}-{end_date}.pdf'
        response['Content-Disposition'] = f'inline; filename="{filename}"'
        return response


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
