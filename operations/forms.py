"""
Formularios del módulo operations.
"""

from django import forms
from django.forms import inlineformset_factory
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit
from .models import Operation, OperationItem
from customers.models import Customer
from suppliers.models import Supplier
from products.models import Product


class OperationForm(forms.ModelForm):
    """Formulario para crear/editar operaciones."""
    
    class Meta:
        model = Operation
        fields = ['type', 'date', 'customer', 'supplier', 'notes']
        widgets = {
            'type': forms.Select(attrs={'class': 'form-select', 'required': True}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'required': True}),
            'customer': forms.Select(attrs={'class': 'form-select'}),
            'supplier': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        labels = {
            'type': 'Tipo de Operación',
            'date': 'Fecha',
            'customer': 'Cliente',
            'supplier': 'Proveedor',
            'notes': 'Notas',
        }
    
    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filtrar clientes y proveedores por empresa
        if self.company:
            self.fields['customer'].queryset = Customer.objects.for_company(self.company).filter(active=True)
            self.fields['supplier'].queryset = Supplier.objects.for_company(self.company).filter(active=True)
        else:
            self.fields['customer'].queryset = Customer.objects.none()
            self.fields['supplier'].queryset = Supplier.objects.none()
        
        # Si es edición, mostrar tipo como solo lectura
        if self.instance and self.instance.pk:
            self.fields['type'].widget.attrs['readonly'] = True
            self.fields['type'].widget.attrs['disabled'] = True
        
        # Configurar crispy forms
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Row(
                Column('type', css_class='col-md-6'),
                Column('date', css_class='col-md-6'),
            ),
            Row(
                Column('customer', css_class='col-md-6'),
                Column('supplier', css_class='col-md-6'),
            ),
            'notes',
            Submit('submit', 'Guardar Operación', css_class='btn btn-primary'),
        )
    
    def clean(self):
        """Validar que se seleccione cliente o proveedor según el tipo."""
        cleaned_data = super().clean()
        type = cleaned_data.get('type')
        customer = cleaned_data.get('customer')
        supplier = cleaned_data.get('supplier')
        
        if type == 'sale' and not customer:
            raise forms.ValidationError({'customer': 'Una venta debe tener un cliente asociado.'})
        
        if type == 'purchase' and not supplier:
            raise forms.ValidationError({'supplier': 'Una compra debe tener un proveedor asociado.'})
        
        if type == 'sale' and supplier:
            raise forms.ValidationError({'supplier': 'Una venta no puede tener un proveedor asociado.'})
        
        if type == 'purchase' and customer:
            raise forms.ValidationError({'customer': 'Una compra no puede tener un cliente asociado.'})
        
        return cleaned_data
    
    def save(self, commit=True):
        """Guardar la operación asociándola a la empresa actual."""
        operation = super().save(commit=False)
        
        if self.company:
            operation.company = self.company
        
        if self.user:
            operation.created_by = self.user
        
        if commit:
            operation.save()
        
        return operation


class OperationItemForm(forms.ModelForm):
    """Formulario para items de operación."""
    
    class Meta:
        model = OperationItem
        fields = ['product', 'quantity', 'unit_price']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
        }
        labels = {
            'product': 'Producto/Servicio',
            'quantity': 'Cantidad',
            'unit_price': 'Precio Unitario',
        }
    
    def __init__(self, *args, **kwargs):
        # Intentar obtener company del formset
        self.company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        
        # Filtrar productos por empresa
        if self.company:
            self.fields['product'].queryset = Product.objects.for_company(self.company).filter(active=True)
        else:
            self.fields['product'].queryset = Product.objects.none()
        
        # Hacer campos obligatorios
        self.fields['product'].required = True
        self.fields['quantity'].required = True
        self.fields['unit_price'].required = True


# Formset para items de operación
OperationItemFormSet = inlineformset_factory(
    Operation,
    OperationItem,
    form=OperationItemForm,
    extra=3,
    can_delete=True,
    fields=['product', 'quantity', 'unit_price'],
    min_num=1,
    validate_min=True
)

