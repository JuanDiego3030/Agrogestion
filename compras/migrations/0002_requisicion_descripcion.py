# Generated by Django 5.2.1 on 2025-05-15 11:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('compras', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='requisicion',
            name='descripcion',
            field=models.TextField(blank=True, max_length=500, null=True),
        ),
    ]
