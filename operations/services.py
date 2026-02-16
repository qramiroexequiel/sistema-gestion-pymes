"""
Servicios del módulo operations.
Toda la lógica de negocio debe estar aquí, no en las views.
"""

from decimal import Decimal, ROUND_HALF_UP
from django.db import transaction
from django.db.models import Sum, F
from django.core.exceptions import ValidationError
from operations.models import Operation, OperationItem
from customers.models import Customer
from suppliers.models import Supplier
from products.models import Product

# Constante para cuantización contable (2 decimales)
TWOPLACES = Decimal("0.01")


def create_operation(company, type, date, customer=None, supplier=None, notes=None, created_by=None):
    """
    Crea una nueva operación (venta o compra).
    
    Args:
        company: Instancia de Company
        type: 'sale' o 'purchase'
        date: Fecha de la operación
        customer: Cliente (requerido si type='sale')
        supplier: Proveedor (requerido si type='purchase')
        notes: Notas opcionales
        created_by: Usuario que crea la operación
    
    Returns:
        Operation: Instancia creada
    
    Raises:
        ValidationError: Si las validaciones fallan
    """
    # Validar tipo
    if type not in ['sale', 'purchase']:
        raise ValidationError('El tipo debe ser "sale" o "purchase".')
    
    # Validar cliente/proveedor según tipo
    if type == 'sale' and not customer:
        raise ValidationError('Una venta debe tener un cliente asociado.')
    if type == 'purchase' and not supplier:
        raise ValidationError('Una compra debe tener un proveedor asociado.')
    
    # Validar que pertenezcan a la misma empresa
    if customer and customer.company != company:
        raise ValidationError('El cliente debe pertenecer a la empresa actual.')
    if supplier and supplier.company != company:
        raise ValidationError('El proveedor debe pertenecer a la empresa actual.')
    
    # Generar número de operación
    last_operation = Operation.objects.filter(
        company=company,
        type=type
    ).order_by('-number').first()
    
    if last_operation and last_operation.number:
        try:
            last_number = int(last_operation.number)
            new_number = str(last_number + 1).zfill(6)
        except ValueError:
            new_number = '000001'
    else:
        new_number = '000001'
    
    # Crear operación
    operation = Operation(
        company=company,
        type=type,
        number=new_number,
        date=date,
        customer=customer,
        supplier=supplier,
        notes=notes,
        status='draft',
        created_by=created_by
    )
    operation.full_clean()
    operation.save()
    
    return operation


def add_item_to_operation(operation, product, quantity, unit_price):
    """
    Añade un item a una operación.
    
    Args:
        operation: Instancia de Operation
        product: Instancia de Product
        quantity: Cantidad
        unit_price: Precio unitario
    
    Returns:
        OperationItem: Item creado
    
    Raises:
        ValidationError: Si las validaciones fallan
    """
    # Validar que la operación sea borrador
    if operation.status != 'draft':
        raise ValidationError('Solo se pueden añadir items a operaciones en estado borrador.')
    
    # Validar que el producto pertenezca a la misma empresa
    if product.company != operation.company:
        raise ValidationError('El producto debe pertenecer a la empresa actual.')
    
    # Validar cantidad y precio
    if quantity <= 0:
        raise ValidationError('La cantidad debe ser mayor a cero.')
    if unit_price < 0:
        raise ValidationError('El precio unitario no puede ser negativo.')
    
    # Calcular subtotal del item (asegurar que sean Decimal)
    if not isinstance(quantity, Decimal):
        quantity = Decimal(str(quantity))
    if not isinstance(unit_price, Decimal):
        unit_price = Decimal(str(unit_price))
    subtotal = quantity * unit_price
    
    # Crear item con subtotal calculado
    item = OperationItem(
        operation=operation,
        product=product,
        quantity=quantity,
        unit_price=unit_price,
        subtotal=subtotal
    )
    item.save()
    
    # Recalcular totales de la operación (OBLIGATORIO después de agregar item)
    recalculate_operation_totals(operation)
    
    return item


def remove_item_from_operation(operation, item_id):
    """
    Elimina un item de una operación.
    
    Args:
        operation: Instancia de Operation
        item_id: ID del item a eliminar
    
    Returns:
        bool: True si se eliminó correctamente
    
    Raises:
        ValidationError: Si la operación no puede ser modificada
    """
    # Validar que la operación pueda ser modificada
    validate_operation_can_be_modified(operation)
    
    try:
        item = OperationItem.objects.get(id=item_id, operation=operation)
        item.delete()
        # Recalcular totales de la operación (OBLIGATORIO después de eliminar item)
        recalculate_operation_totals(operation)
        return True
    except OperationItem.DoesNotExist:
        return False


def recalculate_operation_totals(operation):
    """
    Recalcula los totales de una operación desde sus items.
    
    Args:
        operation: Instancia de Operation
    
    Returns:
        Operation: Operación actualizada
    """
    # Calcular subtotal desde items
    items_total = OperationItem.objects.filter(operation=operation).aggregate(
        total=Sum(F('quantity') * F('unit_price'))
    )['total'] or Decimal('0.00')
    
    # Cuantizar subtotal a 2 decimales (rounding contable estándar)
    operation.subtotal = items_total.quantize(TWOPLACES, rounding=ROUND_HALF_UP)
    
    # Calcular impuesto (por ahora 0, puede venir de config por empresa)
    tax_value = Decimal('0.00')
    # Cuantizar impuesto a 2 decimales
    operation.tax = tax_value.quantize(TWOPLACES, rounding=ROUND_HALF_UP)
    
    # Calcular total
    total_value = operation.subtotal + operation.tax
    # Cuantizar total a 2 decimales
    operation.total = total_value.quantize(TWOPLACES, rounding=ROUND_HALF_UP)
    
    operation.save(update_fields=['subtotal', 'tax', 'total'])
    
    return operation


@transaction.atomic
def confirm_operation(operation, user=None):
    """
    Confirma una operación.
    
    Args:
        operation: Instancia de Operation
        user: Usuario que confirma
    
    Returns:
        Operation: Operación confirmada
    
    Raises:
        ValidationError: Si la operación no puede ser confirmada
    """
    # Validar que la operación sea borrador
    if operation.status != 'draft':
        raise ValidationError('Solo se pueden confirmar operaciones en estado borrador.')
    
    # Validar que tenga items
    if not operation.items.exists():
        raise ValidationError('La operación debe tener al menos un item para ser confirmada.')
    
    # Validar cliente/proveedor según tipo
    if operation.type == 'sale' and not operation.customer:
        raise ValidationError('Una venta debe tener un cliente asociado.')
    if operation.type == 'purchase' and not operation.supplier:
        raise ValidationError('Una compra debe tener un proveedor asociado.')
    
    # Confirmar operación
    operation.status = 'confirmed'
    operation.save(update_fields=['status'])
    
    return operation


@transaction.atomic
def cancel_operation(operation, user=None):
    """
    Cancela una operación.
    
    Args:
        operation: Instancia de Operation
        user: Usuario que cancela
    
    Returns:
        Operation: Operación cancelada
    
    Raises:
        ValidationError: Si la operación no puede ser cancelada
    """
    # Validar que la operación no esté ya cancelada
    if operation.status == 'cancelled':
        raise ValidationError('La operación ya está cancelada.')
    
    # Cancelar operación
    operation.status = 'cancelled'
    operation.save(update_fields=['status'])
    
    return operation


def update_operation_item(operation, item_id, quantity=None, unit_price=None):
    """
    Actualiza un item de una operación.
    
    Args:
        operation: Instancia de Operation
        item_id: ID del item a actualizar
        quantity: Nueva cantidad (opcional)
        unit_price: Nuevo precio unitario (opcional)
    
    Returns:
        OperationItem: Item actualizado
    
    Raises:
        ValidationError: Si las validaciones fallan
        OperationItem.DoesNotExist: Si el item no existe
    """
    # Validar que la operación sea borrador
    if operation.status != 'draft':
        raise ValidationError('Solo se pueden modificar items de operaciones en estado borrador.')
    
    # Obtener item y validar que pertenezca a la operación
    try:
        item = OperationItem.objects.get(id=item_id, operation=operation)
    except OperationItem.DoesNotExist:
        raise ValidationError('El item no existe o no pertenece a esta operación.')
    
    # Actualizar campos si se proporcionan
    if quantity is not None:
        if quantity <= 0:
            raise ValidationError('La cantidad debe ser mayor a cero.')
        item.quantity = quantity
    
    if unit_price is not None:
        if unit_price < 0:
            raise ValidationError('El precio unitario no puede ser negativo.')
        item.unit_price = unit_price
    
    # Recalcular subtotal del item
    item.subtotal = item.quantity * item.unit_price
    item.save()
    
    # Recalcular totales de la operación (OBLIGATORIO después de modificar item)
    recalculate_operation_totals(operation)
    
    return item


def validate_operation_can_be_modified(operation):
    """
    Valida que una operación pueda ser modificada.
    
    Args:
        operation: Instancia de Operation
    
    Raises:
        ValidationError: Si la operación no puede ser modificada
    """
    if operation.status == 'confirmed':
        raise ValidationError('No se pueden modificar operaciones confirmadas.')
    if operation.status == 'cancelled':
        raise ValidationError('No se pueden modificar operaciones canceladas.')
    if operation.status != 'draft':
        raise ValidationError(f'Estado de operación inválido: {operation.status}')

