"""
Formularios del módulo customers.
"""

from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit
from crispy_bootstrap5.bootstrap5 import FloatingField
from .models import Customer


class CustomerForm(forms.ModelForm):
    """Formulario para crear/editar clientes."""
    
    class Meta:
        model = Customer
        fields = ['code', 'name', 'tax_id', 'email', 'phone', 'address', 'notes', 'active']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'tax_id': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'code': 'Código',
            'name': 'Nombre',
            'tax_id': 'CUIT/RUT/NIT',
            'email': 'Email',
            'phone': 'Teléfono',
            'address': 'Dirección',
            'notes': 'Notas',
            'active': 'Activo',
        }
    
    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Configurar crispy forms
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Row(
                Column('code', css_class='col-md-6'),
                Column('name', css_class='col-md-6'),
            ),
            Row(
                Column('tax_id', css_class='col-md-4'),
                Column('email', css_class='col-md-4'),
                Column('phone', css_class='col-md-4'),
            ),
            'address',
            'notes',
            Row(
                Column('active', css_class='col-md-12'),
            ),
            Submit('submit', 'Guardar', css_class='btn btn-primary'),
        )
    
    def clean_code(self):
        """Validar que el código sea único por empresa."""
        code = self.cleaned_data.get('code')
        
        if not code:
            raise forms.ValidationError('El código es obligatorio.')
        
        if self.company:
            # Verificar unicidad por empresa
            queryset = Customer.objects.filter(
                company=self.company,
                code=code
            )
            
            # Si es una edición, excluir el objeto actual
            if self.instance and self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            
            if queryset.exists():
                raise forms.ValidationError(f'Ya existe un cliente con el código "{code}" en esta empresa.')
        
        return code
    
    def save(self, commit=True):
        """Guardar el cliente asociándolo a la empresa actual."""
        customer = super().save(commit=False)
        
        if self.company:
            customer.company = self.company
        
        if self.user:
            customer.created_by = self.user
        
        if commit:
            customer.save()
        
        return customer

