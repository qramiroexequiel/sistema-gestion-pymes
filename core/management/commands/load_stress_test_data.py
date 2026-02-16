"""
Management command para cargar datos masivos para stress test.

Uso:
    python manage.py load_stress_test_data --company-id=1

Carga:
    - 500 clientes
    - 100 proveedores
    - 5000 productos/servicios
    - 100 operaciones
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import random

from core.models import Company
from customers.models import Customer
from suppliers.models import Supplier
from products.models import Product
from operations.models import Operation, OperationItem
from operations.services import create_operation, add_item_to_operation, confirm_operation


class Command(BaseCommand):
    help = 'Carga datos masivos para stress test del sistema'

    def add_arguments(self, parser):
        parser.add_argument(
            '--company-id',
            type=int,
            required=True,
            help='ID de la empresa para la cual cargar los datos'
        )
        parser.add_argument(
            '--skip-operations',
            action='store_true',
            help='Saltar la carga de operaciones (solo cargar clientes, proveedores y productos)'
        )

    def handle(self, *args, **options):
        company_id = options['company_id']
        skip_operations = options.get('skip_operations', False)
        
        try:
            company = Company.objects.get(id=company_id)
        except Company.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Empresa con ID {company_id} no existe.'))
            return
        
        self.stdout.write(self.style.SUCCESS(f'Iniciando carga de datos para: {company.name}'))
        
        with transaction.atomic():
            # FASE 1: Clientes (500)
            self.stdout.write('Cargando 500 clientes...')
            customers = self._create_customers(company, 500)
            self.stdout.write(self.style.SUCCESS(f'✓ {len(customers)} clientes creados'))
            
            # FASE 2: Proveedores (100)
            self.stdout.write('Cargando 100 proveedores...')
            suppliers = self._create_suppliers(company, 100)
            self.stdout.write(self.style.SUCCESS(f'✓ {len(suppliers)} proveedores creados'))
            
            # FASE 3: Productos/Servicios (5000)
            self.stdout.write('Cargando 5000 productos/servicios...')
            products = self._create_products(company, 5000)
            self.stdout.write(self.style.SUCCESS(f'✓ {len(products)} productos/servicios creados'))
            
            # FASE 4: Operaciones (100)
            if not skip_operations:
                self.stdout.write('Cargando 100 operaciones...')
                operations = self._create_operations(company, customers, suppliers, products, 100)
                self.stdout.write(self.style.SUCCESS(f'✓ {len(operations)} operaciones creadas'))
            else:
                self.stdout.write(self.style.WARNING('Operaciones omitidas (--skip-operations)'))
        
        self.stdout.write(self.style.SUCCESS('\n✓ Carga de datos completada exitosamente'))

    def _create_customers(self, company, count):
        """Crea clientes con datos realistas de Argentina."""
        customers = []
        
        # Nombres y apellidos comunes en Argentina
        nombres = [
            'Juan', 'María', 'Carlos', 'Ana', 'Luis', 'Laura', 'Pedro', 'Sofía',
            'Diego', 'Valentina', 'Martín', 'Camila', 'Andrés', 'Lucía', 'Fernando',
            'Isabella', 'Roberto', 'Emma', 'Javier', 'Olivia', 'Miguel', 'Mía',
            'Ricardo', 'Sara', 'Gustavo', 'Elena', 'Daniel', 'Carmen', 'Alejandro', 'Rosa'
        ]
        
        apellidos = [
            'García', 'Rodríguez', 'González', 'Fernández', 'López', 'Martínez',
            'Sánchez', 'Pérez', 'Gómez', 'Martín', 'Jiménez', 'Ruiz', 'Hernández',
            'Díaz', 'Moreno', 'Muñoz', 'Álvarez', 'Romero', 'Alonso', 'Gutiérrez',
            'Navarro', 'Torres', 'Domínguez', 'Vázquez', 'Ramos', 'Gil', 'Ramírez',
            'Serrano', 'Blanco', 'Suárez'
        ]
        
        # Razones sociales comunes
        razones_sociales = [
            'Comercial', 'Distribuidora', 'Servicios', 'Industrias', 'Construcciones',
            'Inversiones', 'Importadora', 'Exportadora', 'Logística', 'Tecnología'
        ]
        
        # Localidades argentinas
        localidades = [
            'Buenos Aires', 'Córdoba', 'Rosario', 'Mendoza', 'Tucumán',
            'La Plata', 'Mar del Plata', 'Salta', 'Santa Fe', 'San Juan'
        ]
        
        # Distribución: 20% frecuentes, 60% normales, 20% ocasionales
        frecuentes_count = int(count * 0.2)
        normales_count = int(count * 0.6)
        ocasionales_count = count - frecuentes_count - normales_count
        
        customer_id = 1
        
        # Clientes frecuentes (personas físicas y empresas)
        for i in range(frecuentes_count):
            is_company = random.choice([True, False])
            
            if is_company:
                name = f"{random.choice(razones_sociales)} {random.choice(apellidos)} S.A."
                tax_id = f"30-{random.randint(10000000, 99999999)}-{random.randint(1, 9)}"
            else:
                name = f"{random.choice(nombres)} {random.choice(apellidos)}"
                tax_id = f"{random.randint(20000000, 49999999)}"
            
            customer = Customer.objects.create(
                company=company,
                code=f"CLI-{customer_id:06d}",
                name=name,
                tax_id=tax_id,
                email=f"cliente{customer_id}@example.com",
                phone=f"+54 11 {random.randint(1000, 9999)}-{random.randint(1000, 9999)}",
                address=f"{random.choice(['Av.', 'Calle', 'Bv.'])} {random.randint(100, 9999)} {random.choice(localidades)}, Buenos Aires",
                active=True
            )
            customers.append(customer)
            customer_id += 1
        
        # Clientes normales
        for i in range(normales_count):
            is_company = random.choice([True, False])
            
            if is_company:
                name = f"{random.choice(razones_sociales)} {random.choice(apellidos)} S.R.L."
                tax_id = f"30-{random.randint(10000000, 99999999)}-{random.randint(1, 9)}"
            else:
                name = f"{random.choice(nombres)} {random.choice(apellidos)}"
                tax_id = f"{random.randint(20000000, 49999999)}"
            
            customer = Customer.objects.create(
                company=company,
                code=f"CLI-{customer_id:06d}",
                name=name,
                tax_id=tax_id,
                email=f"cliente{customer_id}@example.com",
                phone=f"+54 11 {random.randint(1000, 9999)}-{random.randint(1000, 9999)}",
                address=f"{random.choice(['Av.', 'Calle', 'Bv.'])} {random.randint(100, 9999)} {random.choice(localidades)}, Buenos Aires",
                active=True
            )
            customers.append(customer)
            customer_id += 1
        
        # Clientes ocasionales
        for i in range(ocasionales_count):
            is_company = random.choice([True, False])
            
            if is_company:
                name = f"{random.choice(razones_sociales)} {random.choice(apellidos)}"
                tax_id = f"30-{random.randint(10000000, 99999999)}-{random.randint(1, 9)}"
            else:
                name = f"{random.choice(nombres)} {random.choice(apellidos)}"
                tax_id = f"{random.randint(20000000, 49999999)}"
            
            customer = Customer.objects.create(
                company=company,
                code=f"CLI-{customer_id:06d}",
                name=name,
                tax_id=tax_id,
                email=f"cliente{customer_id}@example.com",
                phone=f"+54 11 {random.randint(1000, 9999)}-{random.randint(1000, 9999)}",
                address=f"{random.choice(['Av.', 'Calle', 'Bv.'])} {random.randint(100, 9999)} {random.choice(localidades)}, Buenos Aires",
                active=True
            )
            customers.append(customer)
            customer_id += 1
        
        return customers

    def _create_suppliers(self, company, count):
        """Crea proveedores con datos realistas."""
        suppliers = []
        
        rubros = [
            'Insumos Industriales', 'Materiales de Construcción', 'Equipamiento',
            'Servicios Técnicos', 'Logística y Transporte', 'Tecnología',
            'Materias Primas', 'Herramientas', 'Repuestos', 'Suministros'
        ]
        
        razones_sociales = [
            'Distribuidora', 'Proveedora', 'Comercial', 'Industrias', 'Importadora',
            'Suministros', 'Servicios', 'Tecnología', 'Logística', 'Equipamientos'
        ]
        
        apellidos = [
            'García', 'Rodríguez', 'González', 'Fernández', 'López', 'Martínez',
            'Sánchez', 'Pérez', 'Gómez', 'Martín', 'Jiménez', 'Ruiz', 'Hernández',
            'Díaz', 'Moreno', 'Muñoz', 'Álvarez', 'Romero', 'Alonso', 'Gutiérrez'
        ]
        
        localidades = [
            'Buenos Aires', 'Córdoba', 'Rosario', 'Mendoza', 'Tucumán',
            'La Plata', 'Mar del Plata', 'Salta', 'Santa Fe', 'San Juan'
        ]
        
        for i in range(count):
            rubro = random.choice(rubros)
            razon = random.choice(razones_sociales)
            apellido = random.choice(apellidos)
            
            name = f"{razon} {rubro} {apellido} S.A."
            tax_id = f"30-{random.randint(10000000, 99999999)}-{random.randint(1, 9)}"
            
            supplier = Supplier.objects.create(
                company=company,
                code=f"PROV-{i+1:04d}",
                name=name,
                tax_id=tax_id,
                email=f"proveedor{i+1}@example.com",
                phone=f"+54 11 {random.randint(1000, 9999)}-{random.randint(1000, 9999)}",
                address=f"{random.choice(['Av.', 'Calle', 'Bv.'])} {random.randint(100, 9999)} {random.choice(localidades)}, Buenos Aires",
                active=True
            )
            suppliers.append(supplier)
        
        return suppliers

    def _create_products(self, company, count):
        """Crea productos y servicios con datos realistas."""
        products = []
        
        # 70% productos, 30% servicios
        productos_count = int(count * 0.7)
        servicios_count = count - productos_count
        
        # Categorías de productos
        categorias_productos = [
            'Tornillo', 'Tuerca', 'Arandela', 'Perno', 'Clavo', 'Remache',
            'Repuesto', 'Componente', 'Material', 'Insumo', 'Herramienta',
            'Equipo', 'Máquina', 'Dispositivo', 'Accesorio', 'Pieza',
            'Rodamiento', 'Válvula', 'Manguera', 'Cable', 'Filtro',
            'Bomba', 'Motor', 'Transmisión', 'Sistema', 'Módulo'
        ]
        
        tipos_productos = [
            'galvanizado', 'inoxidable', 'acerado', 'plástico', 'aluminio',
            'hierro', 'cobre', 'bronce', 'niquelado', 'cromado',
            'estándar', 'premium', 'industrial', 'comercial', 'residencial'
        ]
        
        medidas = ['3cm', '5cm', '10cm', '15cm', '20cm', '25cm', '30cm', '1/2"', '3/4"', '1"']
        
        # Categorías de servicios
        categorias_servicios = [
            'Mantenimiento', 'Reparación', 'Instalación', 'Consultoría',
            'Soporte', 'Capacitación', 'Auditoría', 'Diseño', 'Desarrollo',
            'Implementación', 'Configuración', 'Monitoreo', 'Optimización',
            'Análisis', 'Testing', 'Migración', 'Integración', 'Seguridad'
        ]
        
        tipos_servicios = [
            'mensual', 'trimestral', 'anual', 'por hora', 'por proyecto',
            'preventivo', 'correctivo', 'emergencia', 'programado', 'express'
        ]
        
        product_id = 1
        
        # Crear productos
        for i in range(productos_count):
            categoria = random.choice(categorias_productos)
            tipo = random.choice(tipos_productos)
            medida = random.choice(medidas)
            
            # Alta rotación: 20%, Media: 50%, Baja: 30%
            rotacion = random.choices(
                ['alta', 'media', 'baja'],
                weights=[20, 50, 30]
            )[0]
            
            if rotacion == 'alta':
                price = Decimal(random.uniform(100, 5000))
            elif rotacion == 'media':
                price = Decimal(random.uniform(5000, 50000))
            else:
                price = Decimal(random.uniform(50000, 500000))
            
            name = f"{categoria} {tipo} {medida}"
            code = f"PROD-{product_id:06d}"
            
            product = Product.objects.create(
                company=company,
                code=code,
                name=name,
                type='product',
                description=f"Producto {categoria.lower()} de calidad {tipo}",
                price=price,
                unit_of_measure=random.choice(['unidad', 'kg', 'm', 'm²', 'm³', 'litro']),
                stock=Decimal(random.uniform(0, 1000)) if random.random() > 0.3 else None,
                active=True
            )
            products.append(product)
            product_id += 1
        
        # Crear servicios
        for i in range(servicios_count):
            categoria = random.choice(categorias_servicios)
            tipo = random.choice(tipos_servicios)
            
            # Servicios con precios más altos
            price = Decimal(random.uniform(5000, 200000))
            
            name = f"Servicio de {categoria} {tipo}"
            code = f"SERV-{product_id:06d}"
            
            product = Product.objects.create(
                company=company,
                code=code,
                name=name,
                type='service',
                description=f"Servicio profesional de {categoria.lower()}",
                price=price,
                unit_of_measure='hora' if 'por hora' in tipo else 'unidad',
                active=True
            )
            products.append(product)
            product_id += 1
        
        return products

    def _create_operations(self, company, customers, suppliers, products, count):
        """Crea operaciones distribuidas en los últimos 6 meses."""
        operations = []
        
        # 70% ventas, 30% compras
        ventas_count = int(count * 0.7)
        compras_count = count - ventas_count
        
        # Fechas distribuidas en los últimos 6 meses
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=180)
        
        # Obtener usuario admin o crear uno temporal
        from django.contrib.auth.models import User
        try:
            user = User.objects.filter(is_superuser=True).first()
            if not user:
                user = User.objects.first()
        except:
            user = None
        
        # Crear ventas
        for i in range(ventas_count):
            # Fecha aleatoria en el rango
            days_offset = random.randint(0, 180)
            date = start_date + timedelta(days=days_offset)
            
            # Cliente aleatorio
            customer = random.choice(customers)
            
            # Crear operación
            operation = create_operation(
                company=company,
                type='sale',
                date=date,
                customer=customer,
                created_by=user
            )
            
            # Agregar items (1-5 items por operación)
            num_items = random.randint(1, 5)
            operation_products = random.sample(products, min(num_items, len(products)))
            
            for product in operation_products:
                quantity = Decimal(random.uniform(1, 100))
                unit_price = product.price * Decimal(random.uniform(0.8, 1.2))  # Variación de precio
                
                add_item_to_operation(
                    operation=operation,
                    product=product,
                    quantity=quantity,
                    unit_price=unit_price
                )
            
            # Confirmar algunas operaciones (80% confirmadas, 20% borrador)
            if random.random() < 0.8:
                try:
                    confirm_operation(operation, user=user)
                except:
                    pass  # Si falla, queda en borrador
            
            operations.append(operation)
        
        # Crear compras
        for i in range(compras_count):
            # Fecha aleatoria en el rango
            days_offset = random.randint(0, 180)
            date = start_date + timedelta(days=days_offset)
            
            # Proveedor aleatorio
            supplier = random.choice(suppliers)
            
            # Crear operación
            operation = create_operation(
                company=company,
                type='purchase',
                date=date,
                supplier=supplier,
                created_by=user
            )
            
            # Agregar items (1-5 items por operación)
            num_items = random.randint(1, 5)
            operation_products = random.sample(products, min(num_items, len(products)))
            
            for product in operation_products:
                quantity = Decimal(random.uniform(1, 100))
                unit_price = product.price * Decimal(random.uniform(0.7, 0.95))  # Precio de compra menor
                
                add_item_to_operation(
                    operation=operation,
                    product=product,
                    quantity=quantity,
                    unit_price=unit_price
                )
            
            # Confirmar algunas operaciones (80% confirmadas, 20% borrador)
            if random.random() < 0.8:
                try:
                    confirm_operation(operation, user=user)
                except:
                    pass  # Si falla, queda en borrador
            
            operations.append(operation)
        
        return operations

