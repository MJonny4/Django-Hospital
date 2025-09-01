from pydantic import BaseModel, EmailStr, validator, ConfigDict
from typing import Optional, List
from datetime import datetime
from ..models.models import validate_spanish_dni, validate_numero_colegiado, EspecialidadMedica, UserRole
import re

class UserRegister(BaseModel):
    dni: str
    nombre: str
    apellidos: str
    email: EmailStr
    telefono: str
    direccion: str
    fecha_nacimiento: str  # YYYY-MM-DD
    password: str
    
    @validator('dni')
    def validate_dni(cls, v):
        if not validate_spanish_dni(v):
            raise ValueError('DNI español no válido. Formato: 8 dígitos + letra (ej: 12345678Z)')
        return v.upper()
    
    @validator('nombre')
    def validate_nombre(cls, v):
        if len(v.strip()) < 2:
            raise ValueError('El nombre debe tener al menos 2 caracteres')
        return v.strip().title()
    
    @validator('apellidos')
    def validate_apellidos(cls, v):
        if len(v.strip()) < 2:
            raise ValueError('Los apellidos deben tener al menos 2 caracteres')
        return v.strip().title()
    
    @validator('telefono')
    def validate_telefono(cls, v):
        # Spanish phone number validation (basic)
        if not re.match(r'^[679]\d{8}$', v.replace(' ', '')):
            raise ValueError('Teléfono no válido. Debe ser un número español válido')
        return v.replace(' ', '')
    
    @validator('fecha_nacimiento')
    def validate_fecha_nacimiento(cls, v):
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', v):
            raise ValueError('Fecha de nacimiento debe estar en formato YYYY-MM-DD')
        return v
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('La contraseña debe tener al menos 8 caracteres')
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    dni: str
    nombre: str
    apellidos: str
    email: str
    telefono: str
    roles: List[str]  # Now returns list of roles
    is_active: bool
    created_at: Optional[datetime] = None
    
    @validator('roles', pre=True)
    def parse_roles(cls, v):
        import json
        if isinstance(v, str):
            return json.loads(v)
        return v

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class HomePageResponse(BaseModel):
    mensaje: str
    descripcion: str
    acciones: list[str]

# Admin and Doctor schemas
class DoctorRegister(BaseModel):
    # Personal Information
    dni: str
    nombre: str
    apellidos: str
    email: EmailStr
    telefono: str
    fecha_nacimiento: str
    
    # Professional Information
    numero_colegiado: str
    colegio_medico: str
    especialidad: EspecialidadMedica
    subespecialidad: Optional[str] = None
    
    # Education
    universidad: str
    ano_graduacion: int
    titulo_especialista: Optional[str] = None
    
    # Work Information
    hospital_centro: str
    departamento_servicio: str
    consulta_numero: Optional[str] = None
    horario_consulta: Optional[str] = None
    
    # Additional Info
    idiomas: Optional[str] = None
    biografia: Optional[str] = None
    foto_url: Optional[str] = None
    
    @validator('dni')
    def validate_dni(cls, v):
        if not validate_spanish_dni(v):
            raise ValueError('DNI español no válido')
        return v.upper()
    
    @validator('numero_colegiado')
    def validate_colegiado(cls, v):
        if not validate_numero_colegiado(v):
            raise ValueError('Número de colegiado no válido')
        return v.upper()
    
    @validator('ano_graduacion')
    def validate_graduation_year(cls, v):
        current_year = datetime.now().year
        if v < 1950 or v > current_year:
            raise ValueError(f'Año de graduación debe estar entre 1950 y {current_year}')
        return v
    
    @validator('telefono')
    def validate_telefono(cls, v):
        if not re.match(r'^[679]\d{8}$', v.replace(' ', '')):
            raise ValueError('Teléfono no válido')
        return v.replace(' ', '')

class DoctorProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    numero_colegiado: str
    colegio_medico: str
    especialidad: EspecialidadMedica
    subespecialidad: Optional[str] = None
    universidad: str
    ano_graduacion: int
    titulo_especialista: Optional[str] = None
    hospital_centro: str
    departamento_servicio: str
    consulta_numero: Optional[str] = None
    horario_consulta: Optional[str] = None
    idiomas: Optional[str] = None
    biografia: Optional[str] = None
    foto_url: Optional[str] = None
    is_active: bool
    fecha_alta_sistema: Optional[datetime] = None

class DoctorResponse(BaseModel):
    """Combined doctor info (user + profile)"""
    model_config = ConfigDict(from_attributes=True)
    
    # User info
    id: int
    dni: str
    nombre: str
    apellidos: str
    email: str
    telefono: str
    roles: List[str]
    is_active: bool
    
    # Doctor profile info
    numero_colegiado: str
    colegio_medico: str
    especialidad: EspecialidadMedica
    subespecialidad: Optional[str] = None
    universidad: str
    ano_graduacion: int
    titulo_especialista: Optional[str] = None
    hospital_centro: str
    departamento_servicio: str
    consulta_numero: Optional[str] = None
    horario_consulta: Optional[str] = None
    idiomas: Optional[str] = None
    biografia: Optional[str] = None
    foto_url: Optional[str] = None
    fecha_alta_sistema: Optional[datetime] = None
    
    @validator('roles', pre=True)
    def parse_roles(cls, v):
        import json
        if isinstance(v, str):
            return json.loads(v)
        return v

class AdminCreateUser(BaseModel):
    dni: str
    nombre: str
    apellidos: str
    email: EmailStr
    telefono: str
    direccion: str
    fecha_nacimiento: str
    password: str
    roles: List[str] = ["admin"]  # Now supports multiple roles
    
    @validator('dni')
    def validate_dni(cls, v):
        if not validate_spanish_dni(v):
            raise ValueError('DNI español no válido')
        return v.upper()
    
    @validator('roles')
    def validate_roles(cls, v):
        valid_roles = ["patient", "doctor", "admin"]
        for role in v:
            if role not in valid_roles:
                raise ValueError(f'Rol no válido: {role}')
        return v

class BackofficeStats(BaseModel):
    total_patients: int
    total_doctors: int
    total_admins: int
    recent_registrations: int