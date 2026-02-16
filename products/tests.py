"""
Tests del módulo products.
Verifica la seguridad multi-tenant y prevención de fugas de datos.
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from core.models import Company, Membership
from products.models import Product


class ProductMultiTenantTestCase(TestCase):
    """Tests para verificar seguridad multi-tenant en el módulo products."""
    
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
        
        # Crear productos
        self.product1_company1 = Product.objects.create(
            company=self.company1,
            code='PR001',
            name='Producto 1 Empresa 1',
            type='product',
            price=100.00,
            active=True,
            created_by=self.user1
        )
        self.product2_company1 = Product.objects.create(
            company=self.company1,
            code='SR001',
            name='Servicio 1 Empresa 1',
            type='service',
            price=200.00,
            active=True,
            created_by=self.user1
        )
        self.product1_company2 = Product.objects.create(
            company=self.company2,
            code='PR001',
            name='Producto 1 Empresa 2',
            type='product',
            price=150.00,
            active=True,
            created_by=self.user2
        )
        
        # Configurar cliente de prueba
        self.client = Client()
    
    def test_user_cannot_see_other_company_products_in_list(self):
        """Un usuario solo ve productos de su empresa activa."""
        # Login como user1
        self.client.login(username='user1', password='testpass123')
        
        # Seleccionar empresa1
        session = self.client.session
        session['current_company_id'] = self.company1.id
        session.save()
        
        # Listar productos
        url = reverse('products:list')
        response = self.client.get(url)
        
        # Verificar que solo se muestran productos de company1
        self.assertEqual(response.status_code, 200)
        products = response.context['products']
        self.assertEqual(products.count(), 2)
        self.assertIn(self.product1_company1, products)
        self.assertIn(self.product2_company1, products)
        self.assertNotIn(self.product1_company2, products)
    
    def test_user_cannot_access_other_company_product_by_id(self):
        """Un usuario no puede acceder a productos de otra empresa por ID."""
        # Login como user1
        self.client.login(username='user1', password='testpass123')
        
        # Seleccionar empresa1
        session = self.client.session
        session['current_company_id'] = self.company1.id
        session.save()
        
        # Intentar acceder a producto de company2
        url = reverse('products:detail', kwargs={'pk': self.product1_company2.pk})
        response = self.client.get(url)
        
        # Debe retornar 404
        self.assertEqual(response.status_code, 404)
    
    def test_manager_for_company_filters_correctly(self):
        """El manager for_company filtra correctamente por empresa."""
        # Obtener productos de company1
        products_company1 = Product.objects.for_company(self.company1)
        self.assertEqual(products_company1.count(), 2)
        self.assertIn(self.product1_company1, products_company1)
        self.assertIn(self.product2_company1, products_company1)
        
        # Obtener productos de company2
        products_company2 = Product.objects.for_company(self.company2)
        self.assertEqual(products_company2.count(), 1)
        self.assertIn(self.product1_company2, products_company2)
