# Generated migration for Product.stock_minimo

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0002_product_products_pr_company_28b2e6_idx'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='stock_minimo',
            field=models.DecimalField(
                decimal_places=2,
                default=0.0,
                help_text='Alerta cuando el stock cae por debajo de este valor.',
                max_digits=12,
                verbose_name='Stock mínimo'
            ),
        ),
    ]
