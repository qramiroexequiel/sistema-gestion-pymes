"""
Tests del módulo reports.
Verifica que los reportes solo incluyan datos de la empresa activa.
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from decimal import Decimal
from datetime import datetime, timedelta
from core.models import Company, Membership
from customers.models import Customer
from suppliers.models import Supplier
from products.models import Product
from operations.models import Operation, OperationItem
from operations.services import create_operation, recalculate_operation_totals


class ReportsMultiTenantTestCase(TestCase):
    """Tests para verificar seguridad multi-tenant en reports."""
    
    def setUp(self):
        """Configurar datos de prueba."""
        # Crear usuario
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@test.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@test.com',
            password='testpass123'
        )
        
        # Crear empresas
        self.company1 = Company.objects.create(
            name='Empresa 1',
            email='empresa1@test.com',
            active=True
        )
        self.company2 = Company.objects.create(
            name='Empresa 2',
            email='empresa2@test.com',
            active=True
        )
        
        # Crear membresías
        self.membership1 = Membership.objects.create(
            user=self.user1,
            company=self.company1,
            role='admin',
            active=True
        )
        self.membership2 = Membership.objects.create(
            user=self.user2,
            company=self.company2,
            role='admin',
            active=True
        )
        
        # Crear cliente para company1
        self.customer1 = Customer.objects.create(
            company=self.company1,
            code='C001',
            name='Cliente 1',
            active=True,
            created_by=self.user1
        )
        
        # Crear producto para company1
        self.product1 = Product.objects.create(
            company=self.company1,
            code='P001',
            name='Producto 1',
            type='product',
            price=Decimal('100.00'),
            active=True,
            created_by=self.user1
        )
        
        # Crear operación en company1
        self.operation1 = create_operation(
            company=self.company1,
            type='sale',
            date=datetime.now().date(),
            customer=self.customer1,
            created_by=self.user1
        )
        
        # Agregar item
        OperationItem.objects.create(
            operation=self.operation1,
            product=self.product1,
            quantity=Decimal('2.00'),
            unit_price=Decimal('100.00'),
            subtotal=Decimal('200.00')
        )
        
        recalculate_operation_totals(self.operation1)
        
        # Crear cliente para company2
        self.customer2 = Customer.objects.create(
            company=self.company2,
            code='C001',
            name='Cliente 2',
            active=True,
            created_by=self.user2
        )
        
        # Crear producto para company2
        self.product2 = Product.objects.create(
            company=self.company2,
            code='P001',
            name='Producto 2',
            type='product',
            price=Decimal('200.00'),
            active=True,
            created_by=self.user2
        )
        
        # Crear operación en company2
        self.operation2 = create_operation(
            company=self.company2,
            type='sale',
            date=datetime.now().date(),
            customer=self.customer2,
            created_by=self.user2
        )
        
        # Agregar item
        OperationItem.objects.create(
            operation=self.operation2,
            product=self.product2,
            quantity=Decimal('3.00'),
            unit_price=Decimal('200.00'),
            subtotal=Decimal('600.00')
        )
        
        recalculate_operation_totals(self.operation2)
        
        self.client = Client()
    
    def test_sales_report_only_includes_company_data(self):
        """El reporte de ventas solo incluye datos de la empresa activa."""
        # Login como user1
        self.client.login(username='user1', password='testpass123')
        
        # Seleccionar company1
        session = self.client.session
        session['current_company_id'] = self.company1.id
        session.save()
        
        # Generar reporte CSV
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        end_date = datetime.now().strftime('%Y-%m-%d')
        
        url = reverse('reports:sales_by_period')
        response = self.client.get(f'{url}?start_date={start_date}&end_date={end_date}&format=csv')
        
        # Verificar que solo incluye operación de company1
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Cliente 1', response.content or b'')
        self.assertNotIn(b'Cliente 2', response.content or b'')
        # Verificar que contiene el número de operación de company1
        self.assertIn(self.operation1.number.encode('utf-8'), response.content or b'')
    
    def test_summary_by_customer_only_includes_company_data(self):
        """El resumen por cliente solo incluye datos de la empresa activa."""
        # Login como user1
        self.client.login(username='user1', password='testpass123')
        
        # Seleccionar company1
        session = self.client.session
        session['current_company_id'] = self.company1.id
        session.save()
        
        # Generar reporte CSV
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        end_date = datetime.now().strftime('%Y-%m-%d')
        
        url = reverse('reports:summary_by_customer')
        response = self.client.get(f'{url}?start_date={start_date}&end_date={end_date}&format=csv')
        
        # Verificar que solo incluye cliente de company1
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Cliente 1', response.content or b'')
        self.assertNotIn(b'Cliente 2', response.content or b'')
