"""
Management command para generar informe final del stress test.

Uso:
    python manage.py generate_stress_test_report --company-id=1

Genera un informe completo con:
- Estadísticas de datos cargados
- Performance de reportes
- Evaluación de escalabilidad
- Recomendaciones
"""

from django.core.management.base import BaseCommand
from django.db.models import Count, Sum, Avg, Max, Min
from django.utils import timezone
from datetime import timedelta

from core.models import Company
from customers.models import Customer
from suppliers.models import Supplier
from products.models import Product
from operations.models import Operation, OperationItem


class Command(BaseCommand):
    help = 'Genera informe final del stress test'

    def add_arguments(self, parser):
        parser.add_argument(
            '--company-id',
            type=int,
            required=True,
            help='ID de la empresa para la cual generar el informe'
        )
        parser.add_argument(
            '--output',
            type=str,
            default='stress_test_report.txt',
            help='Archivo de salida para el informe (default: stress_test_report.txt)'
        )

    def handle(self, *args, **options):
        company_id = options['company_id']
        output_file = options['output']
        
        try:
            company = Company.objects.get(id=company_id)
        except Company.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Empresa con ID {company_id} no existe.'))
            return
        
        self.stdout.write(f'Generando informe para: {company.name}')
        
        # Recolectar datos
        report = self._collect_data(company)
        
        # Generar informe
        informe = self._generate_report(report, company)
        
        # Guardar archivo
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(informe)
        
        self.stdout.write(self.style.SUCCESS(f'✓ Informe guardado en: {output_file}'))
        self.stdout.write('')
        self.stdout.write(informe)

    def _collect_data(self, company):
        """Recolecta todos los datos necesarios para el informe."""
        data = {}
        
        # Clientes
        customers = Customer.objects.for_company(company)
        data['customers'] = {
            'total': customers.count(),
            'active': customers.filter(active=True).count(),
            'inactive': customers.filter(active=False).count(),
        }
        
        # Proveedores
        suppliers = Supplier.objects.for_company(company)
        data['suppliers'] = {
            'total': suppliers.count(),
            'active': suppliers.filter(active=True).count(),
            'inactive': suppliers.filter(active=False).count(),
        }
        
        # Productos/Servicios
        products = Product.objects.for_company(company)
        data['products'] = {
            'total': products.count(),
            'products': products.filter(type='product').count(),
            'services': products.filter(type='service').count(),
            'active': products.filter(active=True).count(),
            'inactive': products.filter(active=False).count(),
        }
        
        # Operaciones
        operations = Operation.objects.for_company(company)
        data['operations'] = {
            'total': operations.count(),
            'sales': operations.filter(type='sale').count(),
            'purchases': operations.filter(type='purchase').count(),
            'confirmed': operations.filter(status='confirmed').count(),
            'draft': operations.filter(status='draft').count(),
            'cancelled': operations.filter(status='cancelled').count(),
        }
        
        # Items de operaciones
        items = OperationItem.objects.filter(operation__company=company)
        data['operation_items'] = {
            'total': items.count(),
            'avg_per_operation': items.count() / operations.count() if operations.count() > 0 else 0,
        }
        
        # Estadísticas de montos
        sales = operations.filter(type='sale', status='confirmed')
        purchases = operations.filter(type='purchase', status='confirmed')
        
        data['financial'] = {
            'total_sales': sales.aggregate(Sum('total'))['total__sum'] or 0,
            'total_purchases': purchases.aggregate(Sum('total'))['total__sum'] or 0,
            'avg_sale': sales.aggregate(Avg('total'))['total__avg'] or 0,
            'avg_purchase': purchases.aggregate(Avg('total'))['total__avg'] or 0,
            'max_sale': sales.aggregate(Max('total'))['total__max'] or 0,
            'max_purchase': purchases.aggregate(Max('total'))['total__max'] or 0,
        }
        
        # Distribución temporal
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=180)
        
        operations_by_month = {}
        for i in range(6):
            month_start = start_date + timedelta(days=i * 30)
            month_end = min(month_start + timedelta(days=30), end_date)
            
            month_ops = operations.filter(
                date__gte=month_start,
                date__lt=month_end
            ).count()
            
            month_name = month_start.strftime('%Y-%m')
            operations_by_month[month_name] = month_ops
        
        data['temporal_distribution'] = operations_by_month
        
        return data

    def _generate_report(self, data, company):
        """Genera el informe completo."""
        lines = []
        
        lines.append('=' * 80)
        lines.append('INFORME FINAL - STRESS TEST')
        lines.append('Suite Business by ReqTech')
        lines.append('=' * 80)
        lines.append('')
        lines.append(f'Empresa: {company.name}')
        lines.append(f'Fecha: {timezone.now().strftime("%Y-%m-%d %H:%M:%S")}')
        lines.append('')
        lines.append('=' * 80)
        lines.append('')
        
        # 1. DATOS CARGADOS
        lines.append('1️⃣ DATOS CARGADOS')
        lines.append('-' * 80)
        lines.append('')
        
        lines.append(f'Clientes:')
        lines.append(f'  Total: {data["customers"]["total"]}')
        lines.append(f'  Activos: {data["customers"]["active"]}')
        lines.append(f'  Inactivos: {data["customers"]["inactive"]}')
        lines.append('')
        
        lines.append(f'Proveedores:')
        lines.append(f'  Total: {data["suppliers"]["total"]}')
        lines.append(f'  Activos: {data["suppliers"]["active"]}')
        lines.append(f'  Inactivos: {data["suppliers"]["inactive"]}')
        lines.append('')
        
        lines.append(f'Productos/Servicios:')
        lines.append(f'  Total: {data["products"]["total"]}')
        lines.append(f'  Productos: {data["products"]["products"]}')
        lines.append(f'  Servicios: {data["products"]["services"]}')
        lines.append(f'  Activos: {data["products"]["active"]}')
        lines.append(f'  Inactivos: {data["products"]["inactive"]}')
        lines.append('')
        
        lines.append(f'Operaciones:')
        lines.append(f'  Total: {data["operations"]["total"]}')
        lines.append(f'  Ventas: {data["operations"]["sales"]}')
        lines.append(f'  Compras: {data["operations"]["purchases"]}')
        lines.append(f'  Confirmadas: {data["operations"]["confirmed"]}')
        lines.append(f'  Borrador: {data["operations"]["draft"]}')
        lines.append(f'  Canceladas: {data["operations"]["cancelled"]}')
        lines.append('')
        
        lines.append(f'Items de Operaciones:')
        lines.append(f'  Total: {data["operation_items"]["total"]}')
        lines.append(f'  Promedio por operación: {data["operation_items"]["avg_per_operation"]:.2f}')
        lines.append('')
        
        # 2. ESTADÍSTICAS FINANCIERAS
        lines.append('2️⃣ ESTADÍSTICAS FINANCIERAS')
        lines.append('-' * 80)
        lines.append('')
        
        lines.append(f'Ventas Totales: ${data["financial"]["total_sales"]:,.2f}')
        lines.append(f'Compras Totales: ${data["financial"]["total_purchases"]:,.2f}')
        lines.append(f'Promedio por Venta: ${data["financial"]["avg_sale"]:,.2f}')
        lines.append(f'Promedio por Compra: ${data["financial"]["avg_purchase"]:,.2f}')
        lines.append(f'Venta Máxima: ${data["financial"]["max_sale"]:,.2f}')
        lines.append(f'Compra Máxima: ${data["financial"]["max_purchase"]:,.2f}')
        lines.append('')
        
        # 3. DISTRIBUCIÓN TEMPORAL
        lines.append('3️⃣ DISTRIBUCIÓN TEMPORAL (Últimos 6 meses)')
        lines.append('-' * 80)
        lines.append('')
        
        for month, count in data["temporal_distribution"].items():
            lines.append(f'  {month}: {count} operaciones')
        lines.append('')
        
        # 4. EVALUACIÓN
        lines.append('4️⃣ EVALUACIÓN DE ESCALABILIDAD')
        lines.append('-' * 80)
        lines.append('')
        
        # Evaluar si los datos son suficientes
        if data["customers"]["total"] >= 500:
            lines.append('✓ Clientes: Volumen adecuado para stress test')
        else:
            lines.append('⚠ Clientes: Volumen insuficiente (se requieren 500)')
        
        if data["suppliers"]["total"] >= 100:
            lines.append('✓ Proveedores: Volumen adecuado para stress test')
        else:
            lines.append('⚠ Proveedores: Volumen insuficiente (se requieren 100)')
        
        if data["products"]["total"] >= 5000:
            lines.append('✓ Productos/Servicios: Volumen adecuado para stress test')
        else:
            lines.append('⚠ Productos/Servicios: Volumen insuficiente (se requieren 5000)')
        
        if data["operations"]["total"] >= 100:
            lines.append('✓ Operaciones: Volumen adecuado para stress test')
        else:
            lines.append('⚠ Operaciones: Volumen insuficiente (se requieren 100)')
        
        lines.append('')
        
        # 5. RECOMENDACIONES
        lines.append('5️⃣ RECOMENDACIONES')
        lines.append('-' * 80)
        lines.append('')
        
        # Analizar datos y dar recomendaciones
        if data["operation_items"]["avg_per_operation"] < 2:
            lines.append('⚠ Considerar agregar más items por operación para test más realista')
        
        if data["operations"]["draft"] / data["operations"]["total"] > 0.5:
            lines.append('⚠ Muchas operaciones en borrador, considerar confirmar más')
        
        if data["products"]["services"] / data["products"]["total"] < 0.25:
            lines.append('⚠ Proporción de servicios baja, considerar aumentar')
        
        lines.append('')
        
        # 6. PRÓXIMOS PASOS
        lines.append('6️⃣ PRÓXIMOS PASOS')
        lines.append('-' * 80)
        lines.append('')
        lines.append('1. Ejecutar stress_test_reports para simular 2000+ reportes')
        lines.append('2. Navegar manualmente por el sistema con estos datos')
        lines.append('3. Verificar performance de listados y filtros')
        lines.append('4. Validar UX con datos reales')
        lines.append('5. Revisar branding y consistencia visual')
        lines.append('')
        
        lines.append('=' * 80)
        lines.append('FIN DEL INFORME')
        lines.append('=' * 80)
        
        return '\n'.join(lines)

