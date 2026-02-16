"""
Formularios del módulo products.
"""

from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit
from .models import Product


class ProductForm(forms.ModelForm):
    """Formulario para crear/editar productos/servicios."""
    
    class Meta:
        model = Product
        fields = ['code', 'name', 'type', 'description', 'price', 'unit_of_measure', 'active']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'type': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'unit_of_measure': forms.TextInput(attrs={'class': 'form-control'}),
            'active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'code': 'Código',
            'name': 'Nombre',
            'type': 'Tipo',
            'description': 'Descripción',
            'price': 'Precio',
            'unit_of_measure': 'Unidad de medida',
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
                Column('type', css_class='col-md-6'),
                Column('unit_of_measure', css_class='col-md-6'),
            ),
            Row(
                Column('price', css_class='col-md-6'),
            ),
            'description',
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
            queryset = Product.objects.filter(
                company=self.company,
                code=code
            )
            
            # Si es una edición, excluir el objeto actual
            if self.instance and self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            
            if queryset.exists():
                raise forms.ValidationError(f'Ya existe un producto/servicio con el código "{code}" en esta empresa.')
        
        return code
    
    def save(self, commit=True):
        """Guardar el producto asociándolo a la empresa actual."""
        product = super().save(commit=False)
        
        if self.company:
            product.company = self.company
        
        if self.user:
            product.created_by = self.user
        
        if commit:
            product.save()
        
        return product

