# Generated migration for refactoring to bid system
# This migration creates new models and updates existing ones

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('umoja', '0002_product_booking_product'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Add admin to UserProfile user_type choices (no migration needed, just model change)
        
        # Create FarmerProduct model
        migrations.CreateModel(
            name='FarmerProduct',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('produce_type', models.CharField(choices=[('maize', 'Maize'), ('beans', 'Beans'), ('tomatoes', 'Tomatoes'), ('potatoes', 'Potatoes'), ('cabbage', 'Cabbage'), ('onions', 'Onions'), ('carrots', 'Carrots'), ('wheat', 'Wheat'), ('rice', 'Rice'), ('other', 'Other')], max_length=50)),
                ('quantity_available', models.DecimalField(decimal_places=2, max_digits=10)),
                ('unit', models.CharField(choices=[('kg', 'Kilograms (kg)'), ('ton', 'Tons'), ('bag', 'Bags')], default='kg', max_length=10)),
                ('quality', models.CharField(choices=[('premium', 'Premium'), ('standard', 'Standard'), ('organic', 'Organic'), ('grade_a', 'Grade A'), ('grade_b', 'Grade B')], default='standard', max_length=20)),
                ('price_expected', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('origin_text', models.CharField(max_length=255)),
                ('origin_lat', models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ('origin_lng', models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ('available_from', models.DateField()),
                ('notes', models.TextField(blank=True)),
                ('status', models.CharField(choices=[('active', 'Active'), ('sold', 'Sold'), ('expired', 'Expired')], default='active', max_length=20)),
                ('image', models.ImageField(blank=True, null=True, upload_to='products/')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('farmer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='farmer_products', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
                'verbose_name': 'Farmer Product',
                'verbose_name_plural': 'Farmer Products',
            },
        ),
        
        # Create Bid model
        migrations.CreateModel(
            name='Bid',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity_requested', models.DecimalField(decimal_places=2, max_digits=10)),
                ('price_per_unit', models.DecimalField(decimal_places=2, max_digits=10)),
                ('total_price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('accepted', 'Accepted'), ('rejected', 'Rejected'), ('cancelled', 'Cancelled'), ('collected', 'Collected'), ('completed', 'Completed')], default='pending', max_length=20)),
                ('notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('broker', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bids', to=settings.AUTH_USER_MODEL)),
                ('listing', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bids', to='umoja.farmerproduct')),
                ('route', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='bids', to='umoja.route')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        
        # Create Contract model
        migrations.CreateModel(
            name='Contract',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('terms', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('bid', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='contract', to='umoja.bid')),
            ],
        ),
        
        # Update Payment model - change from Booking to Bid
        # First, delete old Payment records that reference Booking (since we're refactoring)
        migrations.RunPython(
            lambda apps, schema_editor: apps.get_model('umoja', 'Payment').objects.all().delete(),
            reverse_code=migrations.RunPython.noop
        ),
        # Remove old foreign key to Booking
        migrations.RemoveField(
            model_name='payment',
            name='booking',
        ),
        # Add new foreign key to Bid (non-nullable since we deleted old records)
        migrations.AddField(
            model_name='payment',
            name='bid',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payments', to='umoja.bid'),
        ),
        # Update payment fields
        migrations.AddField(
            model_name='payment',
            name='currency',
            field=models.CharField(default='KES', max_length=3),
        ),
        migrations.RenameField(
            model_name='payment',
            old_name='created_at',
            new_name='timestamp',
        ),
        migrations.AddField(
            model_name='payment',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='payment',
            name='payment_method',
            field=models.CharField(choices=[('stripe', 'Stripe'), ('mpesa', 'M-Pesa'), ('manual', 'Manual')], default='mpesa', max_length=20),
        ),
        migrations.AlterField(
            model_name='payment',
            name='status',
            field=models.CharField(choices=[('pending', 'Pending'), ('paid', 'Paid'), ('released', 'Released'), ('refunded', 'Refunded'), ('failed', 'Failed')], default='pending', max_length=20),
        ),
        migrations.AlterField(
            model_name='payment',
            name='transaction_id',
            field=models.CharField(blank=True, max_length=100, null=True, unique=True),
        ),
        
        # Update Review model - change from Booking to Bid
        # First, delete old Review records that reference Booking
        migrations.RunPython(
            lambda apps, schema_editor: apps.get_model('umoja', 'Review').objects.all().delete(),
            reverse_code=migrations.RunPython.noop
        ),
        # Remove old foreign key to Booking
        migrations.RemoveField(
            model_name='review',
            name='booking',
        ),
        # Add new foreign key to Bid (non-nullable since we deleted old records)
        migrations.AddField(
            model_name='review',
            name='bid',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='review', to='umoja.bid'),
        ),
    ]

