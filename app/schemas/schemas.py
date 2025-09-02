from pydantic import BaseModel, EmailStr, validator, ConfigDict
from typing import Optional, List
from datetime import datetime
from app.models.models import (
    validate_spanish_dni, validate_numero_colegiado, EspecialidadMedica, UserRole,
    AppointmentStatus, AppointmentType, AppointmentPriority
)
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
    profile_id: int  # Doctor profile ID for forms that need it
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

# Appointment Schemas
class DoctorAvailabilityCreate(BaseModel):
    doctor_profile_id: int
    day_of_week: int  # 0=Monday, 6=Sunday
    start_time: str   # Format: "09:00"
    end_time: str     # Format: "17:00"
    slot_duration_minutes: int = 30
    buffer_minutes: int = 5
    
    @validator('day_of_week')
    def validate_day_of_week(cls, v):
        if v < 0 or v > 6:
            raise ValueError('Día de la semana debe estar entre 0 (lunes) y 6 (domingo)')
        return v
    
    @validator('start_time', 'end_time')
    def validate_time_format(cls, v):
        if not re.match(r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$', v):
            raise ValueError('Formato de hora inválido. Use HH:MM (ej: 09:00)')
        return v
    
    @validator('end_time')
    def validate_end_after_start(cls, v, values):
        if 'start_time' in values:
            start_hour, start_min = map(int, values['start_time'].split(':'))
            end_hour, end_min = map(int, v.split(':'))
            start_total = start_hour * 60 + start_min
            end_total = end_hour * 60 + end_min
            if end_total <= start_total:
                raise ValueError('La hora de fin debe ser posterior a la hora de inicio')
        return v
    
    @validator('slot_duration_minutes')
    def validate_slot_duration(cls, v):
        if v < 15 or v > 120:
            raise ValueError('Duración de cita debe estar entre 15 y 120 minutos')
        return v

class DoctorAvailabilityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    doctor_profile_id: int
    day_of_week: int
    start_time: str
    end_time: str
    slot_duration_minutes: int
    buffer_minutes: int
    is_active: bool
    effective_from: Optional[datetime] = None
    effective_until: Optional[datetime] = None

class AppointmentCreate(BaseModel):
    doctor_profile_id: int
    appointment_date: datetime
    duration_minutes: int = 30
    appointment_type: AppointmentType = AppointmentType.CONSULTATION
    priority: AppointmentPriority = AppointmentPriority.NORMAL
    reason: Optional[str] = None
    notes: Optional[str] = None
    
    @validator('appointment_date')
    def validate_future_date(cls, v):
        if v <= datetime.now():
            raise ValueError('La fecha de la cita debe ser futura')
        return v
    
    @validator('duration_minutes')
    def validate_duration(cls, v):
        if v < 15 or v > 180:
            raise ValueError('Duración debe estar entre 15 y 180 minutos')
        return v
    
    @validator('reason')
    def validate_reason(cls, v):
        if v and len(v.strip()) < 5:
            raise ValueError('El motivo debe tener al menos 5 caracteres')
        return v.strip() if v else None

class AppointmentUpdate(BaseModel):
    appointment_date: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    appointment_type: Optional[AppointmentType] = None
    priority: Optional[AppointmentPriority] = None
    status: Optional[AppointmentStatus] = None
    reason: Optional[str] = None
    notes: Optional[str] = None
    cancellation_reason: Optional[str] = None
    
    @validator('appointment_date')
    def validate_future_date(cls, v):
        if v and v <= datetime.now():
            raise ValueError('La fecha de la cita debe ser futura')
        return v
    
    @validator('duration_minutes')
    def validate_duration(cls, v):
        if v and (v < 15 or v > 180):
            raise ValueError('Duración debe estar entre 15 y 180 minutos')
        return v

class AppointmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    patient_id: int
    doctor_profile_id: int
    appointment_date: datetime
    duration_minutes: int
    appointment_type: AppointmentType
    priority: AppointmentPriority
    status: AppointmentStatus
    reason: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    cancellation_reason: Optional[str] = None

class AppointmentDetailedResponse(BaseModel):
    """Appointment response with patient and doctor details"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    appointment_date: datetime
    duration_minutes: int
    appointment_type: AppointmentType
    priority: AppointmentPriority
    status: AppointmentStatus
    reason: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    
    # Patient info
    patient: UserResponse
    
    # Doctor info (nested from relationships)
    doctor_name: Optional[str] = None
    doctor_specialidad: Optional[EspecialidadMedica] = None
    doctor_hospital: Optional[str] = None
    
    cancellation_reason: Optional[str] = None

class AppointmentListResponse(BaseModel):
    appointments: List[AppointmentResponse]
    total: int
    page: int
    size: int

class AppointmentAvailabilityRequest(BaseModel):
    doctor_profile_id: int
    date: str  # YYYY-MM-DD format
    
    @validator('date')
    def validate_date_format(cls, v):
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', v):
            raise ValueError('Fecha debe estar en formato YYYY-MM-DD')
        try:
            datetime.strptime(v, '%Y-%m-%d')
        except ValueError:
            raise ValueError('Fecha no válida')
        return v

class AppointmentTimeSlot(BaseModel):
    time: str  # HH:MM format
    available: bool
    reason: Optional[str] = None  # Why it's not available

class AppointmentAvailabilityResponse(BaseModel):
    doctor_profile_id: int
    date: str
    available_slots: List[AppointmentTimeSlot]