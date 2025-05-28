from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from django.dispatch import receiver
from django.db.models.signals import pre_delete

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
        ('N', 'Negada'),
    )
    
    codigo = models.CharField(max_length=20, unique=True)
    archivo = models.FileField(upload_to='requisiciones/')
    archivo_aprobacion = models.FileField(upload_to='aprobaciones/', null=True, blank=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    fecha_requerida = models.DateField()
    descripcion = models.TextField(max_length=500, blank=True, null=True)
    estado = models.CharField(max_length=1, choices=ESTADOS, default='P')
    usuario = models.ForeignKey(User_com, on_delete=models.CASCADE)
    creador_req = models.CharField(max_length=100, blank=True, null=True)  # Nuevo campo
    
    class Meta:
        ordering = ['-fecha_registro']
    
    def delete(self, *args, **kwargs):
        """Eliminar archivos físicos al borrar la requisición"""
        if self.archivo:
            self.archivo.delete()
        if self.archivo_aprobacion:
            self.archivo_aprobacion.delete()
        super().delete(*args, **kwargs)

@receiver(pre_delete, sender=Requisicion)
def requisicion_pre_delete(sender, instance, **kwargs):
    """Señal para eliminar archivos cuando se borra una requisición"""
    if instance.archivo:
        instance.archivo.delete()
    if instance.archivo_aprobacion:
        instance.archivo_aprobacion.delete()

class OrdenCompra(models.Model):
    ESTADOS = (
        ('P', 'Pendiente'),
        ('A', 'Aprobada'),
        ('N', 'Negada'),
    )
    
    requisicion = models.ForeignKey(Requisicion, on_delete=models.CASCADE, related_name='ordenes_compra')
    codigo = models.CharField(max_length=20, unique=True)
    archivo = models.FileField(upload_to='ordenes_compra/')
    archivo_aprobacion = models.FileField(upload_to='ordenes_aprobacion/', null=True, blank=True)
    archivo_cuadro_comparativo = models.FileField(upload_to='cuadros_comparativos/', null=True, blank=True)  # Nuevo campo
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_entrega_esperada = models.DateField()
    proveedor = models.CharField(max_length=100)
    descripcion = models.TextField(max_length=500, blank=True, null=True)
    estado = models.CharField(max_length=1, choices=ESTADOS, default='P')
    creador = models.ForeignKey(User_com, on_delete=models.CASCADE)
    
    class Meta:
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"{self.codigo} - {self.get_estado_display()}"
    
    def delete(self, *args, **kwargs):
        if self.archivo:
            self.archivo.delete()
        if self.archivo_aprobacion:
            self.archivo_aprobacion.delete()
        if self.archivo_cuadro_comparativo:
            self.archivo_cuadro_comparativo.delete()
        super().delete(*args, **kwargs)

class Proveedor(models.Model):
    co_prov = models.CharField(max_length=10, primary_key=True)  # Código del proveedor
    prov_des = models.CharField(max_length=60)  # Nombre/descripción del proveedor
    # Agrega otros campos que necesites de la tabla prov

    class Meta:
        managed = False  # Para tablas existentes
        db_table = 'prov'  # Nombre exacto de la tabla en SQL Server
        verbose_name_plural = 'Proveedores'

    def __str__(self):
        return f"{self.co_prov} - {self.prov_des}"