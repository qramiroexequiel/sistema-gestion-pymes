"""
Management command para simular ejecución masiva de reportes.

Uso:
    python manage.py stress_test_reports --company-id=1 --count=2000

Simula la ejecución de reportes sin crear archivos físicos,
solo ejecutando las queries y midiendo performance.
"""

from django.core.management.base import BaseCommand
from django.db import connection, reset_queries
from django.utils import timezone
from datetime import datetime, timedelta
import time
import statistics

from core.models import Company
from operations.models import Operation
from customers.models import Customer
from suppliers.models import Supplier
import random


class Command(BaseCommand):
    help = 'Simula ejecución masiva de reportes para stress test'

    def add_arguments(self, parser):
        parser.add_argument(
            '--company-id',
            type=int,
            required=True,
            help='ID de la empresa para la cual ejecutar reportes'
        )
        parser.add_argument(
            '--count',
            type=int,
            default=2000,
            help='Número de reportes a simular (default: 2000)'
        )

    def handle(self, *args, **options):
        company_id = options['company_id']
        count = options['count']
        
        try:
            company = Company.objects.get(id=company_id)
        except Company.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Empresa con ID {company_id} no existe.'))
            return
        
        self.stdout.write(self.style.SUCCESS(f'Iniciando simulación de {count} reportes para: {company.name}'))
        self.stdout.write('')
        
        # Obtener datos para generar combinaciones
        customers = list(Customer.objects.for_company(company)[:50])  # Primeros 50 clientes
        suppliers = list(Supplier.objects.for_company(company)[:30])  # Primeros 30 proveedores
        
        # Fechas base
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=180)
        
        # Estadísticas
        times = []
        query_counts = []
        errors = []
        
        # Tipos de reportes
        report_types = [
            'sales_by_period',
            'purchases_by_period',
            'summary_by_customer',
            'summary_by_supplier'
        ]
        
        self.stdout.write('Ejecutando reportes...')
        
        for i in range(count):
            if (i + 1) % 100 == 0:
                self.stdout.write(f'  Procesados: {i + 1}/{count}')
            
            # Seleccionar tipo de reporte aleatorio
            report_type = random.choice(report_types)
            
            # Generar parámetros según tipo
            if report_type == 'sales_by_period':
                params = self._generate_sales_period_params(start_date, end_date)
            elif report_type == 'purchases_by_period':
                params = self._generate_purchases_period_params(start_date, end_date)
            elif report_type == 'summary_by_customer':
                params = self._generate_customer_summary_params(start_date, end_date, customers)
            else:  # summary_by_supplier
                params = self._generate_supplier_summary_params(start_date, end_date, suppliers)
            
            # Ejecutar reporte y medir
            try:
                reset_queries()
                start_time = time.time()
                
                result = self._execute_report(company, report_type, params)
                
                elapsed = time.time() - start_time
                query_count = len(connection.queries)
                
                times.append(elapsed)
                query_counts.append(query_count)
                
            except Exception as e:
                errors.append({
                    'report_type': report_type,
                    'params': params,
                    'error': str(e)
                })
        
        # Mostrar resultados
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('RESULTADOS DEL STRESS TEST'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write('')
        
        if times:
            self.stdout.write(f'Total de reportes ejecutados: {len(times)}')
            self.stdout.write(f'Reportes con error: {len(errors)}')
            self.stdout.write('')
            
            self.stdout.write('TIEMPOS DE EJECUCIÓN:')
            self.stdout.write(f'  Promedio: {statistics.mean(times):.4f}s')
            self.stdout.write(f'  Mediana: {statistics.median(times):.4f}s')
            self.stdout.write(f'  Mínimo: {min(times):.4f}s')
            self.stdout.write(f'  Máximo: {max(times):.4f}s')
            if len(times) > 1:
                self.stdout.write(f'  Desviación estándar: {statistics.stdev(times):.4f}s')
            self.stdout.write('')
            
            self.stdout.write('QUERIES POR REPORTE:')
            self.stdout.write(f'  Promedio: {statistics.mean(query_counts):.1f}')
            self.stdout.write(f'  Mediana: {statistics.median(query_counts):.1f}')
            self.stdout.write(f'  Mínimo: {min(query_counts)}')
            self.stdout.write(f'  Máximo: {max(query_counts)}')
            self.stdout.write('')
            
            # Percentiles
            sorted_times = sorted(times)
            p50 = sorted_times[int(len(sorted_times) * 0.5)]
            p75 = sorted_times[int(len(sorted_times) * 0.75)]
            p90 = sorted_times[int(len(sorted_times) * 0.90)]
            p95 = sorted_times[int(len(sorted_times) * 0.95)]
            p99 = sorted_times[int(len(sorted_times) * 0.99)]
            
            self.stdout.write('PERCENTILES DE TIEMPO:')
            self.stdout.write(f'  P50: {p50:.4f}s')
            self.stdout.write(f'  P75: {p75:.4f}s')
            self.stdout.write(f'  P90: {p90:.4f}s')
            self.stdout.write(f'  P95: {p95:.4f}s')
            self.stdout.write(f'  P99: {p99:.4f}s')
            self.stdout.write('')
        
        if errors:
            self.stdout.write(self.style.WARNING(f'ERRORES ENCONTRADOS: {len(errors)}'))
            for error in errors[:10]:  # Mostrar solo los primeros 10
                self.stdout.write(f'  - {error["report_type"]}: {error["error"]}')
            if len(errors) > 10:
                self.stdout.write(f'  ... y {len(errors) - 10} errores más')
            self.stdout.write('')
        
        # Evaluación
        self.stdout.write('EVALUACIÓN:')
        avg_time = statistics.mean(times) if times else 0
        max_time = max(times) if times else 0
        
        if avg_time < 0.5:
            self.stdout.write(self.style.SUCCESS('  ✓ Performance EXCELENTE (promedio < 0.5s)'))
        elif avg_time < 1.0:
            self.stdout.write(self.style.SUCCESS('  ✓ Performance BUENA (promedio < 1.0s)'))
        elif avg_time < 2.0:
            self.stdout.write(self.style.WARNING('  ⚠ Performance ACEPTABLE (promedio < 2.0s)'))
        else:
            self.stdout.write(self.style.ERROR('  ✗ Performance DEFICIENTE (promedio >= 2.0s)'))
        
        if max_time > 5.0:
            self.stdout.write(self.style.ERROR(f'  ✗ Algunos reportes son MUY LENTOS (máximo: {max_time:.2f}s)'))
        elif max_time > 3.0:
            self.stdout.write(self.style.WARNING(f'  ⚠ Algunos reportes son lentos (máximo: {max_time:.2f}s)'))
        else:
            self.stdout.write(self.style.SUCCESS(f'  ✓ Todos los reportes son rápidos (máximo: {max_time:.2f}s)'))
        
        self.stdout.write('')

    def _generate_sales_period_params(self, start_date, end_date):
        """Genera parámetros para reporte de ventas por período."""
        import random
        
        # Generar rango de fechas aleatorio dentro del período
        days_range = (end_date - start_date).days
        start_offset = random.randint(0, days_range - 30)
        end_offset = random.randint(start_offset + 1, min(start_offset + 90, days_range))
        
        return {
            'start_date': (start_date + timedelta(days=start_offset)).strftime('%Y-%m-%d'),
            'end_date': (start_date + timedelta(days=end_offset)).strftime('%Y-%m-%d'),
        }

    def _generate_purchases_period_params(self, start_date, end_date):
        """Genera parámetros para reporte de compras por período."""
        import random
        
        # Similar a ventas
        days_range = (end_date - start_date).days
        start_offset = random.randint(0, days_range - 30)
        end_offset = random.randint(start_offset + 1, min(start_offset + 90, days_range))
        
        return {
            'start_date': (start_date + timedelta(days=start_offset)).strftime('%Y-%m-%d'),
            'end_date': (start_date + timedelta(days=end_offset)).strftime('%Y-%m-%d'),
        }

    def _generate_customer_summary_params(self, start_date, end_date, customers):
        """Genera parámetros para resumen por cliente."""
        import random
        
        days_range = (end_date - start_date).days
        start_offset = random.randint(0, days_range - 30)
        end_offset = random.randint(start_offset + 1, min(start_offset + 90, days_range))
        
        return {
            'start_date': (start_date + timedelta(days=start_offset)).strftime('%Y-%m-%d'),
            'end_date': (start_date + timedelta(days=end_offset)).strftime('%Y-%m-%d'),
        }

    def _generate_supplier_summary_params(self, start_date, end_date, suppliers):
        """Genera parámetros para resumen por proveedor."""
        import random
        
        days_range = (end_date - start_date).days
        start_offset = random.randint(0, days_range - 30)
        end_offset = random.randint(start_offset + 1, min(start_offset + 90, days_range))
        
        return {
            'start_date': (start_date + timedelta(days=start_offset)).strftime('%Y-%m-%d'),
            'end_date': (start_date + timedelta(days=end_offset)).strftime('%Y-%m-%d'),
        }

    def _execute_report(self, company, report_type, params):
        """Ejecuta un reporte y retorna los resultados."""
        from django.db.models import Sum, Count
        
        if report_type == 'sales_by_period':
            start_date = datetime.strptime(params['start_date'], '%Y-%m-%d').date()
            end_date = datetime.strptime(params['end_date'], '%Y-%m-%d').date()
            
            operations = Operation.objects.for_company(company).filter(
                type='sale',
                date__gte=start_date,
                date__lte=end_date
            ).select_related('customer')
            
            totals = operations.aggregate(
                subtotal=Sum('subtotal'),
                tax=Sum('tax'),
                total=Sum('total')
            )
            
            return {
                'count': operations.count(),
                'totals': totals
            }
        
        elif report_type == 'purchases_by_period':
            start_date = datetime.strptime(params['start_date'], '%Y-%m-%d').date()
            end_date = datetime.strptime(params['end_date'], '%Y-%m-%d').date()
            
            operations = Operation.objects.for_company(company).filter(
                type='purchase',
                date__gte=start_date,
                date__lte=end_date
            ).select_related('supplier')
            
            totals = operations.aggregate(
                subtotal=Sum('subtotal'),
                tax=Sum('tax'),
                total=Sum('total')
            )
            
            return {
                'count': operations.count(),
                'totals': totals
            }
        
        elif report_type == 'summary_by_customer':
            start_date = datetime.strptime(params['start_date'], '%Y-%m-%d').date()
            end_date = datetime.strptime(params['end_date'], '%Y-%m-%d').date()
            
            customers = Customer.objects.for_company(company).filter(
                operations__type='sale',
                operations__date__gte=start_date,
                operations__date__lte=end_date,
                operations__company=company
            ).annotate(
                total_operations=Count('operations'),
                total_sales=Sum('operations__total')
            ).filter(total_operations__gt=0)
            
            return {
                'count': customers.count(),
                'total_general': sum(c.total_sales or 0 for c in customers)
            }
        
        else:  # summary_by_supplier
            start_date = datetime.strptime(params['start_date'], '%Y-%m-%d').date()
            end_date = datetime.strptime(params['end_date'], '%Y-%m-%d').date()
            
            suppliers = Supplier.objects.for_company(company).filter(
                operations__type='purchase',
                operations__date__gte=start_date,
                operations__date__lte=end_date,
                operations__company=company
            ).annotate(
                total_operations=Count('operations'),
                total_purchases=Sum('operations__total')
            ).filter(total_operations__gt=0)
            
            return {
                'count': suppliers.count(),
                'total_general': sum(s.total_purchases or 0 for s in suppliers)
            }

