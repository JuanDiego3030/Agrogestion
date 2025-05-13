from django.db import models
from django.contrib.auth.hashers import make_password, check_password

class User_com(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    password = models.CharField(max_length=128)
    bloqueado = models.BooleanField(default=False)

    def __str__(self):
        return self.nombre
    
    def set_password(self, raw_password):
        self.password = make_password(raw_password)
    
    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

from django.db import models
from django.contrib.auth.hashers import make_password, check_password

class User_com(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    password = models.CharField(max_length=128)
    bloqueado = models.BooleanField(default=False)

    def __str__(self):
        return self.nombre
    
    def set_password(self, raw_password):
        self.password = make_password(raw_password)
    
    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

class Requisicion(models.Model):
    ESTADOS = (
        ('P', 'Pendiente'),
        ('A', 'Aprobada'),
        ('R', 'Rechazada'),
    )
    
    codigo = models.CharField(max_length=20, unique=True, blank=True)
    archivo = models.FileField(upload_to='requisiciones/')
    fecha_registro = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=1, choices=ESTADOS, default='P')
    usuario = models.ForeignKey(User_com, on_delete=models.CASCADE)
    
    class Meta:
        ordering = ['-fecha_registro']
    
    def __str__(self):
        return f"{self.codigo}"
    
    def save(self, *args, **kwargs):
        if not self.codigo:
            # Generar código automático (ejemplo: REQ-0001)
            last_req = Requisicion.objects.order_by('-id').first()
            if last_req and last_req.codigo:
                try:
                    last_num = int(last_req.codigo.split('-')[-1])
                except (ValueError, IndexError):
                    last_num = 0
            else:
                last_num = 0
            self.codigo = f"REQ-{str(last_num + 1).zfill(4)}"
        super().save(*args, **kwargs)