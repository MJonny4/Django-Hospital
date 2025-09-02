# -*- coding: utf-8 -*-
import enum

# Spanish Medical Specialties - With proper UTF-8 encoding
class EspecialidadMedica(enum.Enum):
    MEDICINA_GENERAL = "Medicina General"
    CARDIOLOGIA = "Cardiología"
    PEDIATRIA = "Pediatría"
    GINECOLOGIA = "Ginecología y Obstetricia"
    TRAUMATOLOGIA = "Traumatología y Cirugía Ortopédica"
    NEUROLOGIA = "Neurología"
    DERMATOLOGIA = "Dermatología"
    OFTALMOLOGIA = "Oftalmología"
    OTORRINOLARINGOLOGIA = "Otorrinolaringología"
    UROLOGIA = "Urología"
    PSIQUIATRIA = "Psiquiatría"
    RADIOLOGIA = "Radiodiagnóstico"
    ANESTESIOLOGIA = "Anestesiología y Reanimación"
    MEDICINA_INTERNA = "Medicina Interna"
    CIRUGIA_GENERAL = "Cirugía General y del Aparato Digestivo"
    ENDOCRINOLOGIA = "Endocrinología y Nutrición"
    NEUMOLOGIA = "Neumología"
    GASTROENTEROLOGIA = "Aparato Digestivo"
    HEMATOLOGIA = "Hematología y Hemoterapia"
    ONCOLOGIA = "Oncología Médica"

if __name__ == "__main__":
    # Test the enum values
    for specialty in EspecialidadMedica:
        print(f"{specialty.name} = {repr(specialty.value)}")