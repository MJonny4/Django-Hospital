from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base
import re
import enum
import json

# User role enum
class UserRole(enum.Enum):
    PATIENT = "patient"
    DOCTOR = "doctor"
    ADMIN = "admin"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    dni = Column(String(9), unique=True, index=True, nullable=False)  # Spanish DNI
    nombre = Column(String(100), nullable=False)
    apellidos = Column(String(200), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    telefono = Column(String(15), nullable=False)
    direccion = Column(String(500), nullable=False)
    fecha_nacimiento = Column(String(10), nullable=False)  # YYYY-MM-DD format
    hashed_password = Column(String(255), nullable=False)
    roles = Column(Text, default='["patient"]', nullable=False)  # JSON array of roles
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    doctor_profile = relationship("DoctorProfile", back_populates="user", uselist=False, primaryjoin="User.id==DoctorProfile.user_id")
    
    def get_roles(self):
        """Get user roles as list"""
        return json.loads(self.roles)
    
    def set_roles(self, roles_list):
        """Set user roles from list"""
        self.roles = json.dumps(roles_list)
    
    def has_role(self, role):
        """Check if user has a specific role"""
        return role in self.get_roles()
    
    def add_role(self, role):
        """Add a role to user"""
        current_roles = self.get_roles()
        if role not in current_roles:
            current_roles.append(role)
            self.set_roles(current_roles)
    
    def remove_role(self, role):
        """Remove a role from user"""
        current_roles = self.get_roles()
        if role in current_roles:
            current_roles.remove(role)
            self.set_roles(current_roles)

# Spanish DNI validation function
def validate_spanish_dni(dni: str) -> bool:
    """
    Validates Spanish DNI format and check digit
    Format: 8 digits + 1 letter
    """
    if not dni or len(dni) != 9:
        return False
    
    # Check if first 8 characters are digits and last one is letter
    if not re.match(r'^\d{8}[A-Za-z]$', dni):
        return False
    
    # DNI letter validation
    numbers = dni[:8]
    letter = dni[8].upper()
    
    # Standard DNI letters
    dni_letters = "TRWAGMYFPDXBNJZSQVHLCKE"
    expected_letter = dni_letters[int(numbers) % 23]
    
    return letter == expected_letter

# Spanish Medical Specialties
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

class DoctorProfile(Base):
    __tablename__ = "doctor_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), unique=True, nullable=False)
    
    # Professional Information
    numero_colegiado = Column(String(20), unique=True, index=True, nullable=False)  # Medical license number
    colegio_medico = Column(String(200), nullable=False)  # e.g., "Colegio de Médicos de Madrid"
    especialidad = Column(Enum(EspecialidadMedica), nullable=False)
    subespecialidad = Column(String(200), nullable=True)  # Optional subspecialty
    
    # Education
    universidad = Column(String(300), nullable=False)  # Medical school
    ano_graduacion = Column(Integer, nullable=False)
    titulo_especialista = Column(String(300), nullable=True)  # Specialist degree
    
    # Work Information
    hospital_centro = Column(String(300), nullable=False)  # Hospital/clinic name
    departamento_servicio = Column(String(200), nullable=False)  # Department/service
    consulta_numero = Column(String(20), nullable=True)  # Office/room number
    horario_consulta = Column(Text, nullable=True)  # Working hours description
    
    # Additional Info
    idiomas = Column(Text, nullable=True)  # Languages spoken
    biografia = Column(Text, nullable=True)  # Professional biography
    foto_url = Column(String(500), nullable=True)  # Profile photo URL
    
    # Status
    is_active = Column(Boolean, default=True)
    fecha_alta_sistema = Column(DateTime(timezone=True), server_default=func.now())
    created_by_admin = Column(Integer, ForeignKey('users.id'), nullable=False)  # Admin who created the record
    
    # Relationships
    user = relationship("User", back_populates="doctor_profile", primaryjoin="User.id==DoctorProfile.user_id")
    created_by = relationship("User", foreign_keys=[created_by_admin])

# Keep Doctor class for backward compatibility (will be deprecated)
class Doctor(Base):
    __tablename__ = "doctors_deprecated" 
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Personal Information  
    dni = Column(String(9), unique=True, index=True, nullable=False)
    nombre = Column(String(100), nullable=False)
    apellidos = Column(String(200), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    telefono = Column(String(15), nullable=False)
    fecha_nacimiento = Column(String(10), nullable=False)
    
    # Professional Information
    numero_colegiado = Column(String(20), unique=True, index=True, nullable=False)
    colegio_medico = Column(String(200), nullable=False)
    especialidad = Column(Enum(EspecialidadMedica), nullable=False)
    subespecialidad = Column(String(200), nullable=True)
    
    # Education
    universidad = Column(String(300), nullable=False)
    ano_graduacion = Column(Integer, nullable=False)
    titulo_especialista = Column(String(300), nullable=True)
    
    # Work Information
    hospital_centro = Column(String(300), nullable=False)
    departamento_servicio = Column(String(200), nullable=False)
    consulta_numero = Column(String(20), nullable=True)
    horario_consulta = Column(Text, nullable=True)
    
    # Additional Info
    idiomas = Column(Text, nullable=True)
    biografia = Column(Text, nullable=True)
    foto_url = Column(String(500), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    fecha_alta_sistema = Column(DateTime(timezone=True), server_default=func.now())
    created_by_admin = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Relationships
    created_by = relationship("User", foreign_keys=[created_by_admin])

# Medical license number validation (basic format check)
def validate_numero_colegiado(numero: str, provincia: str = None) -> bool:
    """
    Validates Spanish medical license number format
    Format varies by province but generally: CCPPNNNN where:
    CC = Province code, PP = College code, NNNN = Sequential number
    """
    if not numero or len(numero) < 6 or len(numero) > 15:
        return False
    
    # Basic format check - should contain numbers and possibly letters
    import re
    if not re.match(r'^[A-Z0-9/\-]+$', numero.upper()):
        return False
    
    return True