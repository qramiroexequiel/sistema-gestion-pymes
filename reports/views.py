"""Vistas del módulo reports."""

import csv
from datetime import datetime, timedelta
from django.http import HttpResponse
from django.views.generic import ListView, View
from django.shortcuts import redirect, render
from django.contrib import messages
from django.db.models import Sum, Count
from core.mixins import (
    CompanyRequiredMixin, 
    CompanyContextMixin, 
    CompanyFilterMixin,
    RoleRequiredMixin,
)
from core.constants import ROLE_ADMIN, ROLE_MANAGER, ROLE_OPERATOR
from operations.models import Operation
from customers.models import Customer
from suppliers.models import Supplier


class ReportsListView(
    CompanyRequiredMixin,
    CompanyContextMixin,
    ListView
):
    """Lista de reportes disponibles."""
    template_name = 'reports/list.html'
    context_object_name = 'reports'
    
    def get_queryset(self):
        """Lista de reportes disponibles."""
        return [
            {
                'name': 'Ventas por Período',
                'description': 'Reporte de ventas filtrado por rango de fechas',
                'url': 'reports:sales_by_period',
            },
            {
                'name': 'Compras por Período',
                'description': 'Reporte de compras filtrado por rango de fechas',
                'url': 'reports:purchases_by_period',
            },
            {
                'name': 'Resumen por Cliente',
                'description': 'Resumen de ventas agrupadas por cliente',
                'url': 'reports:summary_by_customer',
            },
            {
                'name': 'Resumen por Proveedor',
                'description': 'Resumen de compras agrupadas por proveedor',
                'url': 'reports:summary_by_supplier',
            },
        ]


class SalesByPeriodView(
    CompanyRequiredMixin,
    CompanyContextMixin,
    RoleRequiredMixin,
    View
):
    """Reporte de ventas por período."""
    required_roles = [ROLE_ADMIN, ROLE_MANAGER, ROLE_OPERATOR]
    
    def get(self, request):
        """Genera reporte de ventas por período."""
        company = request.current_company
        
        # Obtener fechas del request
        start_date = request.GET.get('start_date', (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
        end_date = request.GET.get('end_date', datetime.now().strftime('%Y-%m-%d'))
        
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            messages.error(request, 'Fechas inválidas.')
            return redirect('reports:list')
        
        # Filtrar operaciones por empresa, tipo y fechas
        operations = Operation.objects.for_company(company).filter(
            type='sale',
            date__gte=start_date,
            date__lte=end_date
        ).select_related('customer').order_by('-date', '-number')
        
        # Exportar CSV si se solicita
        if request.GET.get('format') == 'csv':
            response = HttpResponse(content_type='text/csv; charset=utf-8')
            response['Content-Disposition'] = f'attachment; filename="ventas_{start_date}_{end_date}.csv"'
            
            writer = csv.writer(response)
            writer.writerow(['Número', 'Fecha', 'Cliente', 'Subtotal', 'Impuesto', 'Total', 'Estado'])
            
            for operation in operations:
                writer.writerow([
                    operation.number,
                    operation.date.strftime('%d/%m/%Y'),
                    operation.customer.name if operation.customer else '-',
                    f'{operation.subtotal:.2f}',
                    f'{operation.tax:.2f}',
                    f'{operation.total:.2f}',
                    operation.get_status_display(),
                ])
            
            # Totales
            totals = operations.aggregate(
                subtotal=Sum('subtotal'),
                tax=Sum('tax'),
                total=Sum('total')
            )
            
            writer.writerow([])
            writer.writerow(['TOTALES', '', '', 
                           f"{totals['subtotal'] or 0:.2f}",
                           f"{totals['tax'] or 0:.2f}",
                           f"{totals['total'] or 0:.2f}",
                           ''])
            
            return response
        
        # Renderizar template
        context = {
            'operations': operations,
            'start_date': start_date,
            'end_date': end_date,
            'totals': operations.aggregate(
                subtotal=Sum('subtotal'),
                tax=Sum('tax'),
                total=Sum('total')
            ),
        }
        return render(request, 'reports/sales_by_period.html', context)


class PurchasesByPeriodView(
    CompanyRequiredMixin,
    CompanyContextMixin,
    RoleRequiredMixin,
    View
):
    """Reporte de compras por período."""
    required_roles = [ROLE_ADMIN, ROLE_MANAGER, ROLE_OPERATOR]
    
    def get(self, request):
        """Genera reporte de compras por período."""
        company = request.current_company
        
        # Obtener fechas del request
        start_date = request.GET.get('start_date', (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
        end_date = request.GET.get('end_date', datetime.now().strftime('%Y-%m-%d'))
        
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            messages.error(request, 'Fechas inválidas.')
            return redirect('reports:list')
        
        # Filtrar operaciones por empresa, tipo y fechas
        operations = Operation.objects.for_company(company).filter(
            type='purchase',
            date__gte=start_date,
            date__lte=end_date
        ).select_related('supplier').order_by('-date', '-number')
        
        # Exportar CSV si se solicita
        if request.GET.get('format') == 'csv':
            response = HttpResponse(content_type='text/csv; charset=utf-8')
            response['Content-Disposition'] = f'attachment; filename="compras_{start_date}_{end_date}.csv"'
            
            writer = csv.writer(response)
            writer.writerow(['Número', 'Fecha', 'Proveedor', 'Subtotal', 'Impuesto', 'Total', 'Estado'])
            
            for operation in operations:
                writer.writerow([
                    operation.number,
                    operation.date.strftime('%d/%m/%Y'),
                    operation.supplier.name if operation.supplier else '-',
                    f'{operation.subtotal:.2f}',
                    f'{operation.tax:.2f}',
                    f'{operation.total:.2f}',
                    operation.get_status_display(),
                ])
            
            # Totales
            totals = operations.aggregate(
                subtotal=Sum('subtotal'),
                tax=Sum('tax'),
                total=Sum('total')
            )
            
            writer.writerow([])
            writer.writerow(['TOTALES', '', '', 
                           f"{totals['subtotal'] or 0:.2f}",
                           f"{totals['tax'] or 0:.2f}",
                           f"{totals['total'] or 0:.2f}",
                           ''])
            
            return response
        
        # Renderizar template
        context = {
            'operations': operations,
            'start_date': start_date,
            'end_date': end_date,
            'totals': operations.aggregate(
                subtotal=Sum('subtotal'),
                tax=Sum('tax'),
                total=Sum('total')
            ),
        }
        return render(request, 'reports/purchases_by_period.html', context)


class SummaryByCustomerView(
    CompanyRequiredMixin,
    CompanyContextMixin,
    RoleRequiredMixin,
    View
):
    """Resumen de ventas por cliente."""
    required_roles = [ROLE_ADMIN, ROLE_MANAGER, ROLE_OPERATOR]
    
    def get(self, request):
        """Genera resumen de ventas por cliente."""
        company = request.current_company
        
        # Obtener fechas del request
        start_date = request.GET.get('start_date', (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
        end_date = request.GET.get('end_date', datetime.now().strftime('%Y-%m-%d'))
        
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            messages.error(request, 'Fechas inválidas.')
            return redirect('reports:list')
        
        # Agrupar ventas por cliente
        customers = Customer.objects.for_company(company).filter(
            operations__type='sale',
            operations__date__gte=start_date,
            operations__date__lte=end_date,
            operations__company=company
        ).annotate(
            total_operations=Count('operations'),
            total_sales=Sum('operations__total')
        ).filter(total_operations__gt=0).order_by('-total_sales')
        
        # Exportar CSV si se solicita
        if request.GET.get('format') == 'csv':
            response = HttpResponse(content_type='text/csv; charset=utf-8')
            response['Content-Disposition'] = f'attachment; filename="resumen_clientes_{start_date}_{end_date}.csv"'
            
            writer = csv.writer(response)
            writer.writerow(['Cliente', 'Código', 'Cantidad de Ventas', 'Total Ventas'])
            
            total_general = 0
            for customer in customers:
                total = customer.total_sales or 0
                total_general += total
                writer.writerow([
                    customer.name,
                    customer.code,
                    customer.total_operations,
                    f'{total:.2f}',
                ])
            
            writer.writerow([])
            writer.writerow(['TOTAL GENERAL', '', '', f'{total_general:.2f}'])
            
            return response
        
        # Renderizar template
        context = {
            'customers': customers,
            'start_date': start_date,
            'end_date': end_date,
            'total_general': sum(c.total_sales or 0 for c in customers),
        }
        return render(request, 'reports/summary_by_customer.html', context)


class SummaryBySupplierView(
    CompanyRequiredMixin,
    CompanyContextMixin,
    RoleRequiredMixin,
    View
):
    """Resumen de compras por proveedor."""
    required_roles = [ROLE_ADMIN, ROLE_MANAGER, ROLE_OPERATOR]
    
    def get(self, request):
        """Genera resumen de compras por proveedor."""
        company = request.current_company
        
        # Obtener fechas del request
        start_date = request.GET.get('start_date', (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
        end_date = request.GET.get('end_date', datetime.now().strftime('%Y-%m-%d'))
        
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            messages.error(request, 'Fechas inválidas.')
            return redirect('reports:list')
        
        # Agrupar compras por proveedor
        suppliers = Supplier.objects.for_company(company).filter(
            operations__type='purchase',
            operations__date__gte=start_date,
            operations__date__lte=end_date,
            operations__company=company
        ).annotate(
            total_operations=Count('operations'),
            total_purchases=Sum('operations__total')
        ).filter(total_operations__gt=0).order_by('-total_purchases')
        
        # Exportar CSV si se solicita
        if request.GET.get('format') == 'csv':
            response = HttpResponse(content_type='text/csv; charset=utf-8')
            response['Content-Disposition'] = f'attachment; filename="resumen_proveedores_{start_date}_{end_date}.csv"'
            
            writer = csv.writer(response)
            writer.writerow(['Proveedor', 'Código', 'Cantidad de Compras', 'Total Compras'])
            
            total_general = 0
            for supplier in suppliers:
                total = supplier.total_purchases or 0
                total_general += total
                writer.writerow([
                    supplier.name,
                    supplier.code,
                    supplier.total_operations,
                    f'{total:.2f}',
                ])
            
            writer.writerow([])
            writer.writerow(['TOTAL GENERAL', '', '', f'{total_general:.2f}'])
            
            return response
        
        # Renderizar template
        context = {
            'suppliers': suppliers,
            'start_date': start_date,
            'end_date': end_date,
            'total_general': sum(s.total_purchases or 0 for s in suppliers),
        }
        return render(request, 'reports/summary_by_supplier.html', context)
