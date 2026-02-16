"""
Tests del módulo customers.
Verifica multi-tenant y acceso por roles.
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.db import IntegrityError
from core.models import Company, Membership
from customers.models import Customer


class CustomerMultiTenantTestCase(TestCase):
    """Tests de multi-tenant para clientes."""
    
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
        
        # Crear clientes
        self.customer1 = Customer.objects.create(
            company=self.company1,
            code='C001',
            name='Cliente Empresa 1',
            created_by=self.user1
        )
        
        self.customer2 = Customer.objects.create(
            company=self.company2,
            code='C002',
            name='Cliente Empresa 2',
            created_by=self.user2
        )
    
    def test_manager_for_company_filters_correctly(self):
        """El manager for_company filtra correctamente por empresa."""
        customers_company1 = Customer.objects.for_company(self.company1).all()
        self.assertEqual(customers_company1.count(), 1)
        self.assertIn(self.customer1, customers_company1)
        self.assertNotIn(self.customer2, customers_company1)
    
    def test_user_cannot_see_other_company_customers_in_list(self):
        """Un usuario no puede ver clientes de otra empresa en el listado."""
        # Login como user1 (empresa 1)
        self.client.login(username='user1', password='testpass123')
        
        # Establecer empresa 1 en sesión
        session = self.client.session
        session['current_company_id'] = self.company1.id
        session.save()
        
        # Acceder al listado
        url = reverse('customers:list')
        response = self.client.get(url)
        
        # Debe incluir customer1 pero no customer2
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.customer1.name)
        self.assertNotContains(response, self.customer2.name)
    
    def test_user_cannot_access_other_company_customer_by_id(self):
        """Un usuario no puede acceder a un cliente de otra empresa por ID."""
        # Login como user1 (empresa 1)
        self.client.login(username='user1', password='testpass123')
        
        # Establecer empresa 1 en sesión
        session = self.client.session
        session['current_company_id'] = self.company1.id
        session.save()
        
        # Intentar acceder a cliente de empresa 2
        url = reverse('customers:detail', kwargs={'pk': self.customer2.pk})
        response = self.client.get(url)
        
        # Debe retornar 404
        self.assertEqual(response.status_code, 404)
    
    def test_user_cannot_update_other_company_customer(self):
        """Un usuario no puede actualizar un cliente de otra empresa."""
        # Login como user1 (empresa 1)
        self.client.login(username='user1', password='testpass123')
        
        # Establecer empresa 1 en sesión
        session = self.client.session
        session['current_company_id'] = self.company1.id
        session.save()
        
        # Intentar actualizar cliente de empresa 2
        url = reverse('customers:update', kwargs={'pk': self.customer2.pk})
        response = self.client.get(url)
        
        # Debe retornar 404
        self.assertEqual(response.status_code, 404)
    
    def test_user_cannot_delete_other_company_customer(self):
        """Un usuario no puede eliminar un cliente de otra empresa."""
        # Login como user1 (empresa 1)
        self.client.login(username='user1', password='testpass123')
        
        # Establecer empresa 1 en sesión
        session = self.client.session
        session['current_company_id'] = self.company1.id
        session.save()
        
        # Intentar eliminar cliente de empresa 2
        url = reverse('customers:delete', kwargs={'pk': self.customer2.pk})
        response = self.client.post(url)
        
        # Debe retornar 404
        self.assertEqual(response.status_code, 404)
    
    def test_customer_code_unique_per_company(self):
        """El código de cliente debe ser único por empresa."""
        from django.db import transaction
        
        # Crear cliente con código duplicado en misma empresa
        # El código C001 ya existe en customer1, así que debe fallar
        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                Customer.objects.create(
                    company=self.company1,
                    code='C001',  # Mismo código que customer1
                    name='Otro Cliente',
                    created_by=self.user1
                )
        
        # Pero puede haber mismo código en otra empresa
        # customer2 ya tiene código C002, así que usamos C001 en empresa 2
        customer3 = Customer.objects.create(
            company=self.company2,
            code='C001',  # Mismo código pero diferente empresa
            name='Cliente Empresa 2',
            created_by=self.user2
        )
        self.assertIsNotNone(customer3)
    
    def test_user_can_switch_companies_and_see_correct_customers(self):
        """Un usuario con múltiples empresas ve clientes correctos al cambiar empresa."""
        # Crear membresía adicional para user1 en empresa 2
        Membership.objects.create(
            user=self.user1,
            company=self.company2,
            role='admin',
            active=True
        )
        
        # Login como user1
        self.client.login(username='user1', password='testpass123')
        
        # Establecer empresa 1 en sesión
        session = self.client.session
        session['current_company_id'] = self.company1.id
        session.save()
        
        # Ver listado de empresa 1
        url = reverse('customers:list')
        response = self.client.get(url)
        self.assertContains(response, self.customer1.name)
        self.assertNotContains(response, self.customer2.name)
        
        # Cambiar a empresa 2
        session['current_company_id'] = self.company2.id
        session.save()
        
        # Ver listado de empresa 2
        response = self.client.get(url)
        self.assertNotContains(response, self.customer1.name)
        self.assertContains(response, self.customer2.name)
    
    def test_customers_list_responds_to_htmx_request(self):
        """La vista de listado responde correctamente a un request HTMX."""
        # Login como user1
        self.client.login(username='user1', password='testpass123')
        
        # Establecer empresa 1 en sesión
        session = self.client.session
        session['current_company_id'] = self.company1.id
        session.save()
        
        # Request HTMX
        url = reverse('customers:list')
        response = self.client.get(url, HTTP_HX_REQUEST='true')
        
        # Debe retornar 200
        self.assertEqual(response.status_code, 200)
        # Debe usar template parcial
        self.assertTemplateUsed(response, 'customers/_customers_list.html')
        # No debe usar template completo
        self.assertTemplateNotUsed(response, 'customers/list.html')
    
    def test_customers_list_works_without_htmx(self):
        """La vista de listado funciona correctamente sin HTMX."""
        # Login como user1
        self.client.login(username='user1', password='testpass123')
        
        # Establecer empresa 1 en sesión
        session = self.client.session
        session['current_company_id'] = self.company1.id
        session.save()
        
        # Request normal (sin HTMX)
        url = reverse('customers:list')
        response = self.client.get(url)
        
        # Debe retornar 200
        self.assertEqual(response.status_code, 200)
        # Debe usar template completo
        self.assertTemplateUsed(response, 'customers/list.html')
        # Debe contener el cliente
        self.assertContains(response, self.customer1.name)
    
    def test_customers_export_csv_only_current_company(self):
        """La exportación CSV solo incluye datos de la empresa activa."""
        self.client.login(username='user1', password='testpass123')
        session = self.client.session
        session['current_company_id'] = self.company1.id
        session.save()
        
        url = reverse('customers:export_csv')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv; charset=utf-8-sig')
        self.assertIn('attachment', response['Content-Disposition'])
        
        # Verificar que el CSV contiene solo datos de company1
        content = response.content.decode('utf-8-sig')
        self.assertIn(self.customer1.name, content)
        self.assertNotIn(self.customer2.name, content)
