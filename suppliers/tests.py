"""
Tests del módulo suppliers.
Verifica la seguridad multi-tenant y prevención de fugas de datos.
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from core.models import Company, Membership
from suppliers.models import Supplier


class SupplierMultiTenantTestCase(TestCase):
    """Tests para verificar seguridad multi-tenant en el módulo suppliers."""
    
    def setUp(self):
        """Configurar datos de prueba."""
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
            user=self.user1,
            company=self.company2,
            role='admin',
            active=True
        )
        self.membership3 = Membership.objects.create(
            user=self.user2,
            company=self.company2,
            role='admin',
            active=True
        )
        
        # Crear proveedores
        self.supplier1_company1 = Supplier.objects.create(
            company=self.company1,
            code='P001',
            name='Proveedor 1 Empresa 1',
            email='p1e1@test.com',
            active=True,
            created_by=self.user1
        )
        self.supplier2_company1 = Supplier.objects.create(
            company=self.company1,
            code='P002',
            name='Proveedor 2 Empresa 1',
            email='p2e1@test.com',
            active=True,
            created_by=self.user1
        )
        self.supplier1_company2 = Supplier.objects.create(
            company=self.company2,
            code='P001',
            name='Proveedor 1 Empresa 2',
            email='p1e2@test.com',
            active=True,
            created_by=self.user2
        )
        
        # Configurar cliente de prueba
        self.client = Client()
    
    def test_user_cannot_see_other_company_suppliers_in_list(self):
        """Un usuario solo ve proveedores de su empresa activa."""
        # Login como user1
        self.client.login(username='user1', password='testpass123')
        
        # Seleccionar empresa1
        session = self.client.session
        session['current_company_id'] = self.company1.id
        session.save()
        
        # Listar proveedores
        url = reverse('suppliers:list')
        response = self.client.get(url)
        
        # Verificar que solo se muestran proveedores de company1
        self.assertEqual(response.status_code, 200)
        suppliers = response.context['suppliers']
        self.assertEqual(suppliers.count(), 2)
        self.assertIn(self.supplier1_company1, suppliers)
        self.assertIn(self.supplier2_company1, suppliers)
        self.assertNotIn(self.supplier1_company2, suppliers)
    
    def test_user_cannot_access_other_company_supplier_by_id(self):
        """Un usuario no puede acceder a proveedores de otra empresa por ID."""
        # Login como user1
        self.client.login(username='user1', password='testpass123')
        
        # Seleccionar empresa1
        session = self.client.session
        session['current_company_id'] = self.company1.id
        session.save()
        
        # Intentar acceder a proveedor de company2
        url = reverse('suppliers:detail', kwargs={'pk': self.supplier1_company2.pk})
        response = self.client.get(url)
        
        # Debe retornar 404
        self.assertEqual(response.status_code, 404)
    
    def test_manager_for_company_filters_correctly(self):
        """El manager for_company filtra correctamente por empresa."""
        # Obtener proveedores de company1
        suppliers_company1 = Supplier.objects.for_company(self.company1)
        self.assertEqual(suppliers_company1.count(), 2)
        self.assertIn(self.supplier1_company1, suppliers_company1)
        self.assertIn(self.supplier2_company1, suppliers_company1)
        
        # Obtener proveedores de company2
        suppliers_company2 = Supplier.objects.for_company(self.company2)
        self.assertEqual(suppliers_company2.count(), 1)
        self.assertIn(self.supplier1_company2, suppliers_company2)
