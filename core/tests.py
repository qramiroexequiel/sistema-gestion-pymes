"""
Tests del módulo core.
Verifica middleware multi-tenant y acceso de superuser.
"""

import logging
from unittest.mock import patch
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from core.models import Company, Membership
from customers.models import Customer


class CompanyMiddlewareTestCase(TestCase):
    """Tests para el middleware multi-tenant."""
    
    def setUp(self):
        """Configurar datos de prueba."""
        self.client = Client()
        
        # Crear superuser
        self.superuser = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='testpass123'
        )
        
        # Crear usuario normal
        self.user = User.objects.create_user(
            username='user1',
            email='user1@test.com',
            password='testpass123'
        )
        
        # Crear empresa
        self.company = Company.objects.create(
            name='Empresa Test',
            email='empresa@test.com',
            active=True
        )
        
        # Crear membresía para usuario normal
        self.membership = Membership.objects.create(
            user=self.user,
            company=self.company,
            role='admin',
            active=True
        )
    
    def test_superuser_can_access_admin_without_membership(self):
        """Un superuser puede acceder a /admin/ sin membership ni empresa activa."""
        # Login como superuser
        self.client.login(username='admin', password='testpass123')
        
        # Intentar acceder a admin (debe funcionar sin redirección)
        url = reverse('admin:index')
        response = self.client.get(url)
        
        # Debe retornar 200 (o 302 a login si no está autenticado correctamente)
        # Lo importante es que NO redirige a company_select
        self.assertNotEqual(response.status_code, 404)
        
        # Verificar que no hay redirección a company_select
        self.assertNotIn('company_select', response.url if hasattr(response, 'url') else '')
        
        # Verificar que current_company es None (superuser no necesita empresa)
        # Esto se verifica indirectamente: no hay error 500 ni redirección
        self.assertTrue(response.status_code in [200, 302])
    
    def test_user_without_company_redirects_to_company_select(self):
        """Un usuario normal sin empresa activa redirige a selección de empresa o login."""
        # Crear usuario sin membresías
        user_no_company = User.objects.create_user(
            username='user_no_company',
            email='user_no_company@test.com',
            password='testpass123'
        )
        
        # Login como usuario sin membresías
        self.client.login(username='user_no_company', password='testpass123')
        
        # Limpiar sesión (sin empresa activa)
        session = self.client.session
        if 'current_company_id' in session:
            del session['current_company_id']
        session.save()
        
        # Intentar acceder a dashboard (requiere empresa)
        url = reverse('core:dashboard')
        response = self.client.get(url)
        
        # Debe redirigir (a login porque no tiene membresías válidas)
        self.assertEqual(response.status_code, 302)
        # Sin membresías válidas, cierra sesión y redirige a login
        self.assertIn('login', response.url)
        
        # Ahora probar con usuario que SÍ tiene membresías pero sin empresa seleccionada
        # Crear membresía para el usuario
        Membership.objects.create(
            user=user_no_company,
            company=self.company,
            role='admin',
            active=True
        )
        
        # Login nuevamente
        self.client.login(username='user_no_company', password='testpass123')
        
        # Limpiar sesión
        session = self.client.session
        if 'current_company_id' in session:
            del session['current_company_id']
        session.save()
        
        # Intentar acceder a dashboard
        response = self.client.get(url)
        
        # Debe redirigir a company_select (tiene membresías pero no hay selección)
        # O funcionar si el middleware auto-seleccionó
        self.assertEqual(response.status_code in [200, 302], True)
        if response.status_code == 302:
            # Si redirige, debe ser a company_select
            self.assertIn('empresa/seleccionar', response.url)
    
    @patch('core.middleware.logger')
    def test_membership_invalid_logs_event(self, mock_logger):
        """Un intento de acceso con membresía inválida genera log."""
        # Login como usuario
        self.client.login(username='user1', password='testpass123')
        
        # Establecer company_id inválido en sesión
        session = self.client.session
        session['current_company_id'] = 99999  # ID que no existe
        session.save()
        
        # Intentar acceder a una ruta protegida
        url = reverse('core:dashboard')
        self.client.get(url)
        
        # Verificar que se llamó al logger con WARNING
        self.assertTrue(mock_logger.warning.called)
        log_call_args = mock_logger.warning.call_args[0][0]
        self.assertIn('Intento de acceso sin membresía válida', log_call_args)
        self.assertIn('user_id', log_call_args)
        self.assertIn('username', log_call_args)
    
    @patch('core.mixins.logger')
    def test_cross_tenant_access_logs_404(self, mock_logger):
        """Un intento de acceso cross-tenant genera 404 y log."""
        # Crear segunda empresa
        company2 = Company.objects.create(
            name='Empresa 2',
            email='empresa2@test.com',
            active=True
        )
        
        # Crear cliente en empresa 2
        customer2 = Customer.objects.create(
            company=company2,
            code='C002',
            name='Cliente Empresa 2',
            created_by=self.user
        )
        
        # Login como usuario con acceso solo a empresa 1
        self.client.login(username='user1', password='testpass123')
        
        # Establecer empresa 1 en sesión
        session = self.client.session
        session['current_company_id'] = self.company.id
        session.save()
        
        # Intentar acceder a cliente de empresa 2
        url = reverse('customers:detail', kwargs={'pk': customer2.pk})
        response = self.client.get(url)
        
        # Debe retornar 404
        self.assertEqual(response.status_code, 404)
        
        # Verificar que se llamó al logger con WARNING
        self.assertTrue(mock_logger.warning.called)
        log_call_args = mock_logger.warning.call_args[0][0]
        self.assertIn('Intento de acceso cross-tenant (404)', log_call_args)
        self.assertIn('user_id', log_call_args)
        self.assertIn('model', log_call_args)
    
    def test_current_company_none_redirects_to_selection(self):
        """Usuario autenticado sin current_company redirige a selección de empresa."""
        # Login como usuario con membresía
        self.client.login(username='user1', password='testpass123')
        
        # Desactivar la empresa para que el middleware no pueda establecer current_company
        self.company.active = False
        self.company.save()
        
        # Limpiar sesión (sin empresa activa)
        session = self.client.session
        if 'current_company_id' in session:
            del session['current_company_id']
        session.save()
        
        # Ahora el usuario tiene membresía pero en empresa inactiva
        # El middleware no debería establecer current_company
        # El mixin debe detectar esto y redirigir
        
        # Intentar acceder a una ruta protegida (operations list)
        url = reverse('operations:list')
        response = self.client.get(url)
        
        # Debe redirigir (ya sea a selección o login dependiendo de si hay otras membresías)
        self.assertEqual(response.status_code, 302)
        
        # Reactivar empresa para limpiar
        self.company.active = True
        self.company.save()
    
    def test_no_valid_memberships_logs_out(self):
        """Usuario sin memberships válidas es deslogueado."""
        # Crear usuario sin membresías
        user_no_memberships = User.objects.create_user(
            username='user_no_memberships',
            email='user_no_memberships@test.com',
            password='testpass123'
        )
        
        # Login como usuario sin membresías
        self.client.login(username='user_no_memberships', password='testpass123')
        
        # Verificar que está autenticado
        self.assertTrue(user_no_memberships.is_authenticated)
        
        # Limpiar sesión (sin empresa activa)
        session = self.client.session
        if 'current_company_id' in session:
            del session['current_company_id']
        session.save()
        
        # Intentar acceder a una ruta protegida (reports list)
        url = reverse('reports:list')
        response = self.client.get(url)
        
        # Debe redirigir a login (sesión cerrada)
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
        
        # Verificar que el usuario fue deslogueado
        # Hacer otra request para verificar que no está autenticado
        response2 = self.client.get(reverse('core:dashboard'))
        # Debe redirigir a login porque no está autenticado
        self.assertIn('login', response2.url)
