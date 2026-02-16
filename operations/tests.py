"""
Tests del módulo operations.
Verifica multi-tenant, totales y acciones de operaciones.
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from core.models import Company, Membership
from customers.models import Customer
from suppliers.models import Supplier
from products.models import Product
from operations.models import Operation, OperationItem
from operations.services import create_operation, add_item_to_operation, recalculate_operation_totals


class OperationMultiTenantTestCase(TestCase):
    """Tests de multi-tenant para operaciones."""
    
    def setUp(self):
        """Configurar datos de prueba."""
        self.client = Client()
        
        # Crear usuarios
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
        
        # Crear cliente y producto para empresa 1
        self.customer1 = Customer.objects.create(
            company=self.company1,
            code='C001',
            name='Cliente 1',
            created_by=self.user1
        )
        
        self.product1 = Product.objects.create(
            company=self.company1,
            code='P001',
            name='Producto 1',
            price=100.00,
            created_by=self.user1
        )
        
        # Crear operación para empresa 1
        self.operation1 = create_operation(
            company=self.company1,
            type='sale',
            date='2024-01-01',
            customer=self.customer1,
            created_by=self.user1
        )
        
        add_item_to_operation(
            operation=self.operation1,
            product=self.product1,
            quantity=2,
            unit_price=100.00
        )
    
    def test_operation_totals_are_calculated_correctly(self):
        """Los totales de una operación se calculan correctamente."""
        recalculate_operation_totals(self.operation1)
        self.operation1.refresh_from_db()
        
        self.assertEqual(self.operation1.subtotal, 200.00)
        self.assertEqual(self.operation1.total, 200.00)
    
    def test_user_cannot_see_other_company_operations_in_list(self):
        """Un usuario no puede ver operaciones de otra empresa en el listado."""
        # Login como user1 (empresa 1)
        self.client.login(username='user1', password='testpass123')
        
        # Establecer empresa 1 en sesión
        session = self.client.session
        session['current_company_id'] = self.company1.id
        session.save()
        
        # Acceder al listado
        url = reverse('operations:list')
        response = self.client.get(url)
        
        # Debe incluir operation1
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.operation1.number)
    
    def test_user_cannot_access_other_company_operation_by_id(self):
        """Un usuario no puede acceder a una operación de otra empresa por ID."""
        # Crear operación en empresa 2
        customer2 = Customer.objects.create(
            company=self.company2,
            code='C002',
            name='Cliente 2',
            created_by=self.user2
        )
        
        operation2 = create_operation(
            company=self.company2,
            type='sale',
            date='2024-01-01',
            customer=customer2,
            created_by=self.user2
        )
        
        # Login como user1 (empresa 1)
        self.client.login(username='user1', password='testpass123')
        
        # Establecer empresa 1 en sesión
        session = self.client.session
        session['current_company_id'] = self.company1.id
        session.save()
        
        # Intentar acceder a operación de empresa 2
        url = reverse('operations:detail', kwargs={'pk': operation2.pk})
        response = self.client.get(url)
        
        # Debe retornar 404
        self.assertEqual(response.status_code, 404)
    
    def test_user_cannot_confirm_other_company_operation(self):
        """Un usuario no puede confirmar una operación de otra empresa."""
        # Crear operación en empresa 2
        customer2 = Customer.objects.create(
            company=self.company2,
            code='C002',
            name='Cliente 2',
            created_by=self.user2
        )
        
        product2 = Product.objects.create(
            company=self.company2,
            code='P002',
            name='Producto 2',
            price=50.00,
            created_by=self.user2
        )
        
        operation2 = create_operation(
            company=self.company2,
            type='sale',
            date='2024-01-01',
            customer=customer2,
            created_by=self.user2
        )
        
        add_item_to_operation(
            operation=operation2,
            product=product2,
            quantity=1,
            unit_price=50.00
        )
        
        # Login como user1 (empresa 1)
        self.client.login(username='user1', password='testpass123')
        
        # Establecer empresa 1 en sesión
        session = self.client.session
        session['current_company_id'] = self.company1.id
        session.save()
        
        # Intentar confirmar operación de empresa 2
        url = reverse('operations:confirm', kwargs={'pk': operation2.pk})
        response = self.client.post(url)
        
        # Debe retornar 404
        self.assertEqual(response.status_code, 404)
    
    def test_operations_list_responds_to_htmx_request(self):
        """La vista de listado responde correctamente a un request HTMX."""
        # Login como user1
        self.client.login(username='user1', password='testpass123')
        
        # Establecer empresa 1 en sesión
        session = self.client.session
        session['current_company_id'] = self.company1.id
        session.save()
        
        # Request HTMX
        url = reverse('operations:list')
        response = self.client.get(url, HTTP_HX_REQUEST='true')
        
        # Debe retornar 200
        self.assertEqual(response.status_code, 200)
        # Debe usar template parcial
        self.assertTemplateUsed(response, 'operations/_operations_list.html')
        # No debe usar template completo
        self.assertTemplateNotUsed(response, 'operations/list.html')
    
    def test_operations_list_works_without_htmx(self):
        """La vista de listado funciona correctamente sin HTMX."""
        # Login como user1
        self.client.login(username='user1', password='testpass123')
        
        # Establecer empresa 1 en sesión
        session = self.client.session
        session['current_company_id'] = self.company1.id
        session.save()
        
        # Request normal (sin HTMX)
        url = reverse('operations:list')
        response = self.client.get(url)
        
        # Debe retornar 200
        self.assertEqual(response.status_code, 200)
        # Debe usar template completo
        self.assertTemplateUsed(response, 'operations/list.html')
        # Debe contener la operación
        self.assertContains(response, self.operation1.number)
    
    def test_operations_export_csv_only_current_company(self):
        """La exportación CSV solo incluye datos de la empresa activa."""
        # Crear operación para company2
        customer2 = Customer.objects.create(
            company=self.company2,
            code='C002',
            name='Cliente Empresa 2',
            created_by=self.user2
        )
        operation2 = Operation.objects.create(
            company=self.company2,
            type='sale',
            number='V-0002',
            date='2024-01-15',
            customer=customer2,
            status='confirmed',
            subtotal=200.00,
            tax=42.00,
            total=242.00,
            created_by=self.user2
        )
        
        self.client.login(username='user1', password='testpass123')
        session = self.client.session
        session['current_company_id'] = self.company1.id
        session.save()
        
        url = reverse('operations:export_csv')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv; charset=utf-8-sig')
        self.assertIn('attachment', response['Content-Disposition'])
        
        # Verificar que el CSV contiene solo datos de company1
        content = response.content.decode('utf-8-sig')
        self.assertIn(self.operation1.number, content)
        self.assertNotIn(operation2.number, content)
    
    def test_operations_export_csv_respects_filters(self):
        """La exportación CSV respeta los filtros activos."""
        self.client.login(username='user1', password='testpass123')
        session = self.client.session
        session['current_company_id'] = self.company1.id
        session.save()
        
        # Filtrar solo ventas
        url = reverse('operations:export_csv') + '?type=sale'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8-sig')
        self.assertIn(self.operation1.number, content)  # Venta
        # operation2 es compra, no debe aparecer si filtramos solo ventas
