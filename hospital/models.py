from django.db import models

# Create your models here.
from django.db import models

# Create your models here.
class Usuari(models.Model):
    id = models.AutoField(primary_key=True)
    DNI = models.CharField(max_length=9)
    login = models.CharField(max_length=20)
    Sexe = models.CharField(max_length=1)
    Cognoms_i_Nom = models.CharField(max_length=50)
    Data_Naixement = models.CharField(max_length=50)
    Adreca = models.CharField(max_length=50)
    Poblacio = models.CharField(max_length=50)
    CP = models.CharField(max_length=5)
    Provincia = models.CharField(max_length=50)
    Pais = models.CharField(max_length=50)
    contrasenya = models.CharField(max_length=50)