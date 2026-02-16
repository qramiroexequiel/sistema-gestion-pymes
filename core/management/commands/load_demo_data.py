"""
Comando de gestión para cargar datos de demo comercial.

Uso:
    python manage.py load_demo_data

Crea:
    - Empresa "Fénix Tech - Soluciones Digitales" con CompanySettings (IVA 21%, ARS).
    - Vincula el primer superusuario como Administrador.
    - 3 clientes, 2 proveedores, 5 productos/servicios.
    - 10 ventas y 5 compras en los últimos 20 días (usando services para totales e impuestos).

El sistema queda listo para una demo con el Dashboard poblado.
"""

from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError

from core.models import Company, Membership
from config_app.models import CompanySettings
from customers.models import Customer
from suppliers.models import Supplier
from products.models import Product
from operations.services import (
    create_operation,
    add_item_to_operation,
    confirm_operation,
)


# Constantes para la demo
COMPANY_NAME = "Fénix Tech - Soluciones Digitales"
COMPANY_CUIT = "20-12345678-9"
TAX_RATE = Decimal("21.00")
CURRENCY = "ARS"
TIMEZONE = "America/Argentina/Buenos_Aires"

CUSTOMERS_DATA = [
    {"code": "CLI-DEMO-01", "name": "Estudio Contable Pérez", "tax_id": "20-20123456-7"},
    {"code": "CLI-DEMO-02", "name": "Logística Sur", "tax_id": "30-30123456-8"},
    {"code": "CLI-DEMO-03", "name": "Tienda de Ropa", "tax_id": "20-20987654-1"},
]

SUPPLIERS_DATA = [
    {"code": "PROV-DEMO-01", "name": "Mayorista Tech", "tax_id": "30-30567890-1"},
    {"code": "PROV-DEMO-02", "name": "Distribuidora Global", "tax_id": "30-30654321-9"},
]

PRODUCTS_DATA = [
    {"code": "PROD-001", "name": "Teclado inalámbrico", "type": "product", "price": Decimal("18500.00"), "unit": "unidad"},
    {"code": "PROD-002", "name": "Monitor 24\" LED", "type": "product", "price": Decimal("125000.00"), "unit": "unidad"},
    {"code": "SERV-001", "name": "Servicio de Consultoría", "type": "service", "price": Decimal("35000.00"), "unit": "hora"},
    {"code": "SERV-002", "name": "Soporte Técnico", "type": "service", "price": Decimal("22000.00"), "unit": "hora"},
    {"code": "PROD-003", "name": "Mouse ergonómico", "type": "product", "price": Decimal("8500.00"), "unit": "unidad"},
]


class Command(BaseCommand):
    help = "Carga datos de demo para presentación comercial (empresa, clientes, proveedores, productos, operaciones)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--skip-operations",
            action="store_true",
            help="Solo crear empresa, usuarios, catálogo; no crear ventas ni compras.",
        )

    def _success(self, msg):
        self.stdout.write(self.style.SUCCESS(f"  ✓ {msg}"))

    def _warning(self, msg):
        self.stdout.write(self.style.WARNING(f"  ⚠ {msg}"))

    def _error(self, msg):
        self.stdout.write(self.style.ERROR(f"  ✗ {msg}"))

    def _info(self, msg):
        self.stdout.write(f"  → {msg}")

    def handle(self, *args, **options):
        skip_operations = options.get("skip_operations", False)

        self.stdout.write("")
        self.stdout.write(self.style.HTTP_INFO("🚀 Carga de datos DEMO - Fénix Tech"))
        self.stdout.write("=" * 50)

        try:
            with transaction.atomic():
                company, user = self._ensure_company_and_membership()
                customers = self._ensure_customers(company)
                suppliers = self._ensure_suppliers(company)
                products = self._ensure_products(company)

                if not skip_operations:
                    self._create_operations(company, user, customers, suppliers, products)
                else:
                    self._warning("Operaciones omitidas (--skip-operations).")

            self.stdout.write("")
            self.stdout.write(self.style.SUCCESS("✅ Demo cargada correctamente. Listo para presentación."))
            self.stdout.write("")
        except Exception as e:
            self._error(str(e))
            raise

    def _ensure_company_and_membership(self):
        """Crea o obtiene la empresa demo y su CompanySettings; vincula superusuario como admin."""
        self.stdout.write("")
        self.stdout.write("📦 Empresa y configuración")

        company, created = Company.objects.get_or_create(
            name=COMPANY_NAME,
            defaults={
                "tax_id": COMPANY_CUIT,
                "email": "contacto@fenixtech.demo",
                "phone": "+54 11 1234-5678",
                "address": "Av. Demo 123, CABA",
                "active": True,
                "is_demo": True,
            },
        )
        if created:
            self._success(f"Empresa creada: {company.name}")
        else:
            self._info(f"Empresa existente: {company.name}")

        settings, set_created = CompanySettings.objects.get_or_create(
            company=company,
            defaults={
                "currency": CURRENCY,
                "tax_rate_default": TAX_RATE,
                "timezone": TIMEZONE,
                "date_format": "DD/MM/YYYY",
                "fiscal_year_start": "01-01",
            },
        )
        if set_created:
            self._success(f"CompanySettings: IVA {TAX_RATE}%, {CURRENCY}, {TIMEZONE}")
        else:
            # Actualizar por si se cambió algo
            settings.tax_rate_default = TAX_RATE
            settings.currency = CURRENCY
            settings.timezone = TIMEZONE
            settings.save(update_fields=["tax_rate_default", "currency", "timezone"])
            self._info("CompanySettings actualizados.")

        user = None
        from django.contrib.auth.models import User

        admin_user = User.objects.filter(is_superuser=True).order_by("pk").first()
        if not admin_user:
            self._warning("No hay superusuario. Crea uno con: python manage.py createsuperuser")
        else:
            user = admin_user
            membership, mem_created = Membership.objects.get_or_create(
                user=admin_user,
                company=company,
                defaults={"role": "admin", "active": True},
            )
            if mem_created:
                self._success(f"Usuario '{admin_user.username}' vinculado como Administrador.")
            else:
                self._info(f"Usuario '{admin_user.username}' ya tiene membresía en la empresa.")

        return company, user

    def _ensure_customers(self, company):
        """Crea los 3 clientes de demo si no existen."""
        self.stdout.write("")
        self.stdout.write("👥 Clientes")

        customers = []
        for data in CUSTOMERS_DATA:
            obj, created = Customer.objects.get_or_create(
                company=company,
                code=data["code"],
                defaults={
                    "name": data["name"],
                    "tax_id": data.get("tax_id", ""),
                    "email": f"{data['code'].lower()}@demo.local",
                    "phone": "+54 11 0000-0000",
                    "active": True,
                },
            )
            customers.append(obj)
            self._success(f"{obj.name}" + (" (nuevo)" if created else " (existente)"))

        return customers

    def _ensure_suppliers(self, company):
        """Crea los 2 proveedores de demo si no existen."""
        self.stdout.write("")
        self.stdout.write("🏭 Proveedores")

        suppliers = []
        for data in SUPPLIERS_DATA:
            obj, created = Supplier.objects.get_or_create(
                company=company,
                code=data["code"],
                defaults={
                    "name": data["name"],
                    "tax_id": data.get("tax_id", ""),
                    "email": f"{data['code'].lower()}@demo.local",
                    "phone": "+54 11 0000-0000",
                    "active": True,
                },
            )
            suppliers.append(obj)
            self._success(f"{obj.name}" + (" (nuevo)" if created else " (existente)"))

        return suppliers

    def _ensure_products(self, company):
        """Crea los 5 productos/servicios de demo si no existen."""
        self.stdout.write("")
        self.stdout.write("📋 Productos y servicios")

        products = []
        for data in PRODUCTS_DATA:
            obj, created = Product.objects.get_or_create(
                company=company,
                code=data["code"],
                defaults={
                    "name": data["name"],
                    "type": data["type"],
                    "price": data["price"],
                    "unit_of_measure": data.get("unit", "unidad"),
                    "active": True,
                },
            )
            products.append(obj)
            self._success(f"{obj.name} - ${obj.price}" + (" (nuevo)" if created else " (existente)"))

        return products

    def _create_operations(self, company, user, customers, suppliers, products):
        """
        Primero: compras para todos los productos físicos (generan stock).
        Después: ventas con cantidades <= stock disponible.
        ValidationError en una operación no detiene el resto.
        """
        import random

        self.stdout.write("")
        self.stdout.write("💼 Operaciones (compras primero → stock; luego ventas)")

        if not customers or not suppliers or not products:
            self._warning("Faltan clientes, proveedores o productos. No se crean operaciones.")
            return

        today = timezone.now().date()
        start = today - timedelta(days=20)
        date_list = [start + timedelta(days=i) for i in range(21)]

        physical_products = [p for p in products if p.type == "product"]
        stock_per_product = Decimal("50")  # stock inicial por producto físico

        # Paso 1: Compras para productos físicos (generar stock inicial)
        self._info("Paso 1: Compras a proveedores para generar stock.")
        for product in physical_products:
            try:
                op_date = random.choice(date_list)
                supplier = random.choice(suppliers)
                operation = create_operation(
                    company=company,
                    type="purchase",
                    date=op_date,
                    supplier=supplier,
                    created_by=user,
                )
                unit_price = product.price * Decimal(str(round(random.uniform(0.6, 0.85), 2)))
                add_item_to_operation(
                    operation=operation,
                    product=product,
                    quantity=stock_per_product,
                    unit_price=unit_price,
                )
                confirm_operation(operation, user=user)
                self._success(f"Compra #{operation.number} - {product.name} - stock +{stock_per_product}")
            except ValidationError as e:
                self._warning(f"Compra omitida ({product.name}): {e}")

        # Opcional: 1–2 compras adicionales aleatorias (mezcla de productos)
        for _ in range(2):
            try:
                op_date = random.choice(date_list)
                supplier = random.choice(suppliers)
                operation = create_operation(
                    company=company,
                    type="purchase",
                    date=op_date,
                    supplier=supplier,
                    created_by=user,
                )
                num_items = random.randint(1, min(3, len(products)))
                for product in random.sample(products, num_items):
                    qty = Decimal(str(round(random.uniform(1, 8), 2)))
                    unit_price = product.price * Decimal(str(round(random.uniform(0.6, 0.85), 2)))
                    add_item_to_operation(
                        operation=operation,
                        product=product,
                        quantity=qty,
                        unit_price=unit_price,
                    )
                confirm_operation(operation, user=user)
                self._success(f"Compra #{operation.number} - {supplier.name} - ${operation.total}")
            except ValidationError as e:
                self._warning(f"Compra omitida: {e}")

        # Paso 2: Ventas (cantidades <= stock disponible por producto)
        self._info("Paso 2: Ventas (cantidades respetando stock).")
        for i in range(10):
            try:
                # Refrescar productos para tener stock actualizado
                products = list(Product.objects.filter(company=company, active=True))
                # Productos vendibles: servicios siempre; productos con stock > 0
                sellable = [
                    p for p in products
                    if p.type == "service" or (Decimal(str(p.stock or 0)) > 0)
                ]
                if not sellable:
                    self._warning("Sin stock ni servicios para más ventas. Se omiten el resto.")
                    break

                op_date = random.choice(date_list)
                customer = random.choice(customers)
                operation = create_operation(
                    company=company,
                    type="sale",
                    date=op_date,
                    customer=customer,
                    created_by=user,
                )
                num_items = random.randint(1, min(3, len(sellable)))
                chosen = random.sample(sellable, num_items)
                for product in chosen:
                    if product.type == "service":
                        qty = Decimal(str(round(random.uniform(1, 5), 2)))
                    else:
                        available = Decimal(str(product.stock or 0)).quantize(Decimal("0.01"))
                        if available <= 0:
                            continue
                        # Cantidad deseada 1–5, nunca mayor al stock disponible
                        desired = Decimal(str(round(random.uniform(1, 5), 2)))
                        qty = min(desired, available)
                        if qty <= 0:
                            continue
                    unit_price = product.price * Decimal(str(round(random.uniform(0.95, 1.05), 2)))
                    add_item_to_operation(
                        operation=operation,
                        product=product,
                        quantity=qty,
                        unit_price=unit_price,
                    )
                if not operation.items.exists():
                    operation.delete()
                    self._warning("Venta sin ítems válidos omitida.")
                    continue
                confirm_operation(operation, user=user)
                self._success(f"Venta #{operation.number} - {customer.name} - ${operation.total}")
            except ValidationError as e:
                self._warning(f"Venta omitida: {e}")
