# Generated by Django 5.2.1 on 2025-05-14 19:29

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='User_com',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100, unique=True)),
                ('password', models.CharField(max_length=128)),
                ('bloqueado', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='Requisicion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('codigo', models.CharField(max_length=20, unique=True)),
                ('archivo', models.FileField(upload_to='requisiciones/')),
                ('fecha_registro', models.DateTimeField(auto_now_add=True)),
                ('fecha_requerida', models.DateField()),
                ('estado', models.CharField(choices=[('P', 'Pendiente'), ('A', 'Aprobada'), ('R', 'Rechazada')], default='P', max_length=1)),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='compras.user_com')),
            ],
            options={
                'verbose_name_plural': 'Requisiciones',
                'ordering': ['-fecha_registro'],
            },
        ),
    ]
