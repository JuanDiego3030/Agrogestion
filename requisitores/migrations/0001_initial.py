# Generated by Django 5.0.14 on 2025-05-27 18:33

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='User_req',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100, unique=True)),
                ('password', models.CharField(max_length=128)),
                ('bloqueado', models.BooleanField(default=False)),
            ],
        ),
    ]
