# Generated by Django 5.2.1 on 2025-05-15 16:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('compras', '0003_alter_requisicion_options'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='requisicion',
            options={'ordering': ['-fecha_registro']},
        ),
        migrations.AddField(
            model_name='requisicion',
            name='archivo_aprobacion',
            field=models.FileField(blank=True, null=True, upload_to='aprobaciones/'),
        ),
    ]
