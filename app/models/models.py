from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import re
import enum
import json
from datetime import datetime, timedelta

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

# Spanish Medical Specialties - Match database enum values exactly
class EspecialidadMedica(enum.Enum):
    MEDICINA_GENERAL = "Medicina General"
    CARDIOLOGIA = "Cardiologia"
    PEDIATRIA = "Pediatria"
    GINECOLOGIA = "Ginecologia y Obstetricia"
    TRAUMATOLOGIA = "Traumatologia y Cirugia Ortopedica"
    NEUROLOGIA = "Neurologia"
    DERMATOLOGIA = "Dermatologia"
    OFTALMOLOGIA = "Oftalmologia"
    OTORRINOLARINGOLOGIA = "Otorrinolaringologia"
    UROLOGIA = "Urologia"
    PSIQUIATRIA = "Psiquiatria"
    RADIOLOGIA = "Radiodiagnostico"
    ANESTESIOLOGIA = "Anestesiologia y Reanimacion"
    MEDICINA_INTERNA = "Medicina Interna"
    CIRUGIA_GENERAL = "Cirugia General y del Aparato Digestivo"
    ENDOCRINOLOGIA = "Endocrinologia y Nutricion"
    NEUMOLOGIA = "Neumologia"
    GASTROENTEROLOGIA = "Aparato Digestivo"
    HEMATOLOGIA = "Hematologia y Hemoterapia"
    ONCOLOGIA = "Oncologia Medica"

# Appointment Status
class AppointmentStatus(enum.Enum):
    SCHEDULED = "scheduled"      # Cita programada
    CONFIRMED = "confirmed"      # Cita confirmada
    IN_PROGRESS = "in_progress"  # En curso
    COMPLETED = "completed"      # Completada
    CANCELLED = "cancelled"      # Cancelada
    NO_SHOW = "no_show"         # No se presentó
    RESCHEDULED = "rescheduled"  # Reprogramada

# Appointment Type
class AppointmentType(enum.Enum):
    CONSULTATION = "consultation"      # Consulta general
    FOLLOW_UP = "follow_up"           # Seguimiento
    EMERGENCY = "emergency"           # Urgencia
    CHECK_UP = "check_up"             # Revisión
    PROCEDURE = "procedure"           # Procedimiento
    VACCINATION = "vaccination"       # Vacunación

# Appointment Priority
class AppointmentPriority(enum.Enum):
    LOW = "low"        # Baja
    NORMAL = "normal"  # Normal
    HIGH = "high"      # Alta
    URGENT = "urgent"  # Urgente

class DoctorProfile(Base):
    __tablename__ = "doctor_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), unique=True, nullable=False)
    
    # Professional Information
    numero_colegiado = Column(String(20), unique=True, index=True, nullable=False)  # Medical license number
    colegio_medico = Column(String(200), nullable=False)  # e.g., "Colegio de Médicos de Madrid"
    especialidad = Column(Enum(EspecialidadMedica, values_callable=lambda x: [e.value for e in x]), nullable=False)
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
    especialidad = Column(Enum(EspecialidadMedica, values_callable=lambda x: [e.value for e in x]), nullable=False)
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

# Appointment Management Models

class DoctorAvailability(Base):
    __tablename__ = "doctor_availability"
    
    id = Column(Integer, primary_key=True, index=True)
    doctor_profile_id = Column(Integer, ForeignKey('doctor_profiles.id'), nullable=False)
    
    # Availability details
    day_of_week = Column(Integer, nullable=False)  # 0=Monday, 6=Sunday
    start_time = Column(String(5), nullable=False)  # Format: "09:00"
    end_time = Column(String(5), nullable=False)    # Format: "17:00"
    
    # Slot configuration
    slot_duration_minutes = Column(Integer, default=30, nullable=False)  # 30 min slots
    buffer_minutes = Column(Integer, default=5, nullable=False)         # 5 min buffer
    
    # Status
    is_active = Column(Boolean, default=True)
    effective_from = Column(DateTime(timezone=True), server_default=func.now())
    effective_until = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    doctor_profile = relationship("DoctorProfile", foreign_keys=[doctor_profile_id])

class Appointment(Base):
    __tablename__ = "appointments"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Core appointment info
    patient_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    doctor_profile_id = Column(Integer, ForeignKey('doctor_profiles.id'), nullable=False)
    
    # Scheduling details
    appointment_date = Column(DateTime(timezone=True), nullable=False)
    duration_minutes = Column(Integer, default=30, nullable=False)
    
    # Appointment metadata
    appointment_type = Column(Enum(AppointmentType, values_callable=lambda x: [e.value for e in x]), default=AppointmentType.CONSULTATION)
    priority = Column(Enum(AppointmentPriority, values_callable=lambda x: [e.value for e in x]), default=AppointmentPriority.NORMAL)
    status = Column(Enum(AppointmentStatus, values_callable=lambda x: [e.value for e in x]), default=AppointmentStatus.SCHEDULED)
    
    # Details
    reason = Column(Text, nullable=True)  # Motivo de la cita
    notes = Column(Text, nullable=True)   # Notas adicionales
    
    # System fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by_user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Cancellation info
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    cancelled_by_user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    cancellation_reason = Column(Text, nullable=True)
    
    # Relationships
    patient = relationship("User", foreign_keys=[patient_id])
    doctor_profile = relationship("DoctorProfile", foreign_keys=[doctor_profile_id])
    created_by = relationship("User", foreign_keys=[created_by_user_id])
    cancelled_by = relationship("User", foreign_keys=[cancelled_by_user_id])
    
    # Helper methods
    def get_end_time(self):
        """Calculate appointment end time"""
        return self.appointment_date + timedelta(minutes=self.duration_minutes)
    
    def is_past_due(self):
        """Check if appointment is past due"""
        return self.appointment_date < datetime.now()
    
    def can_be_cancelled(self, hours_before=24):
        """Check if appointment can be cancelled (24h before by default)"""
        if self.status in [AppointmentStatus.COMPLETED, AppointmentStatus.CANCELLED]:
            return False
        
        cancellation_deadline = self.appointment_date - timedelta(hours=hours_before)
        return datetime.now() < cancellation_deadline
    
    def get_duration_display(self):
        """Get human readable duration"""
        hours = self.duration_minutes // 60
        minutes = self.duration_minutes % 60
        
        if hours > 0:
            return f"{hours}h {minutes}min" if minutes > 0 else f"{hours}h"
        return f"{minutes}min"
    
    def validate_self_appointment(self):
        """Prevent doctors from booking appointments with themselves"""
        # Get the doctor's user ID
        doctor_user_id = self.doctor_profile.user_id
        
        # Check if patient is the same as the doctor
        if self.patient_id == doctor_user_id:
            return False, "Los doctores no pueden programar citas consigo mismos"
        
        return True, None
    
    @staticmethod
    def can_patient_book_with_doctor(patient_user_id, doctor_profile_id, db_session):
        """Check if a patient can book an appointment with a specific doctor"""
        from sqlalchemy.orm import Session
        
        # Get doctor's user ID
        doctor_profile = db_session.query(DoctorProfile).filter(
            DoctorProfile.id == doctor_profile_id
        ).first()
        
        if not doctor_profile:
            return False, "Médico no encontrado"
        
        # Check if patient is the same as doctor
        if patient_user_id == doctor_profile.user_id:
            return False, "Los doctores no pueden programar citas consigo mismos"
        
        return True, None

class AppointmentHistory(Base):
    __tablename__ = "appointment_history"
    
    id = Column(Integer, primary_key=True, index=True)
    appointment_id = Column(Integer, ForeignKey('appointments.id'), nullable=False)
    
    # Change tracking
    changed_at = Column(DateTime(timezone=True), server_default=func.now())
    changed_by_user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # What changed
    field_name = Column(String(50), nullable=False)  # 'status', 'appointment_date', etc.
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    change_reason = Column(Text, nullable=True)
    
    # Relationships
    appointment = relationship("Appointment", foreign_keys=[appointment_id])
    changed_by = relationship("User", foreign_keys=[changed_by_user_id])

# Medical Records System

# Severity levels for medical records
class MedicalRecordSeverity(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class MedicalRecord(Base):
    __tablename__ = "medical_records"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Core relationships
    patient_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    doctor_id = Column(Integer, ForeignKey('doctor_profiles.id'), nullable=False)
    appointment_id = Column(Integer, ForeignKey('appointments.id'), nullable=True)
    
    # Record metadata
    record_date = Column(DateTime(timezone=True), server_default=func.now())
    
    # Medical information
    diagnosis = Column(Text, nullable=True)
    treatment_plan = Column(Text, nullable=True)
    medications = Column(Text, nullable=True)  # JSON string for medication list
    lab_results = Column(Text, nullable=True)  # JSON string for lab results
    vital_signs = Column(Text, nullable=True)  # JSON string for vital signs
    attachments = Column(Text, nullable=True)  # JSON string for file attachments
    follow_up_notes = Column(Text, nullable=True)
    
    # Classification
    severity = Column(Enum(MedicalRecordSeverity, values_callable=lambda x: [e.value for e in x]), default=MedicalRecordSeverity.MEDIUM)
    is_confidential = Column(Boolean, default=False)
    
    # System timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    patient = relationship("User", foreign_keys=[patient_id])
    doctor_profile = relationship("DoctorProfile", foreign_keys=[doctor_id])
    appointment = relationship("Appointment", foreign_keys=[appointment_id])
    
    # Helper methods
    def get_medications(self):
        """Parse medications from JSON"""
        if self.medications:
            try:
                return json.loads(self.medications)
            except (json.JSONDecodeError, TypeError):
                return []
        return []
    
    def set_medications(self, medications_list):
        """Set medications as JSON"""
        self.medications = json.dumps(medications_list) if medications_list else None
    
    def get_lab_results(self):
        """Parse lab results from JSON"""
        if self.lab_results:
            try:
                return json.loads(self.lab_results)
            except (json.JSONDecodeError, TypeError):
                return {}
        return {}
    
    def set_lab_results(self, lab_results_dict):
        """Set lab results as JSON"""
        self.lab_results = json.dumps(lab_results_dict) if lab_results_dict else None
    
    def get_vital_signs(self):
        """Parse vital signs from JSON"""
        if self.vital_signs:
            try:
                return json.loads(self.vital_signs)
            except (json.JSONDecodeError, TypeError):
                return {}
        return {}
    
    def set_vital_signs(self, vital_signs_dict):
        """Set vital signs as JSON"""
        self.vital_signs = json.dumps(vital_signs_dict) if vital_signs_dict else None

# Prescription Management System

# Prescription status enum
class PrescriptionStatus(enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    DISCONTINUED = "discontinued"
    ON_HOLD = "on_hold"

class Prescription(Base):
    __tablename__ = "prescriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Core relationships
    medical_record_id = Column(Integer, ForeignKey('medical_records.id'), nullable=False)
    patient_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    doctor_id = Column(Integer, ForeignKey('doctor_profiles.id'), nullable=False)
    
    # Medication details
    medication_name = Column(String(200), nullable=False)
    generic_name = Column(String(200), nullable=True)
    dosage = Column(String(100), nullable=False)  # e.g., "500mg", "10ml"
    frequency = Column(String(100), nullable=False)  # e.g., "Twice daily", "Every 8 hours"
    duration_days = Column(Integer, nullable=True)  # Treatment duration
    
    # Schedule
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=True)
    
    # Instructions and warnings
    instructions = Column(Text, nullable=True)  # How to take the medication
    warnings = Column(Text, nullable=True)      # Side effects, precautions
    
    # Status and refills
    status = Column(Enum(PrescriptionStatus, values_callable=lambda x: [e.value for e in x]), default=PrescriptionStatus.ACTIVE)
    refills_remaining = Column(Integer, default=0)
    total_refills_authorized = Column(Integer, default=0)
    
    # Pharmacy information
    pharmacy_notes = Column(Text, nullable=True)
    
    # System timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    medical_record = relationship("MedicalRecord", foreign_keys=[medical_record_id])
    patient = relationship("User", foreign_keys=[patient_id])
    doctor_profile = relationship("DoctorProfile", foreign_keys=[doctor_id])
    
    # Helper methods
    def is_active(self):
        """Check if prescription is currently active"""
        if self.status != PrescriptionStatus.ACTIVE:
            return False
        
        now = datetime.now()
        if self.end_date and now > self.end_date:
            return False
        
        return now >= self.start_date
    
    def is_expired(self):
        """Check if prescription has expired"""
        if not self.end_date:
            return False
        return datetime.now() > self.end_date
    
    def days_remaining(self):
        """Calculate days remaining for treatment"""
        if not self.end_date:
            return None
        
        now = datetime.now()
        if now > self.end_date:
            return 0
        
        return (self.end_date - now).days
    
    def can_refill(self):
        """Check if prescription can be refilled"""
        return self.refills_remaining > 0 and self.status == PrescriptionStatus.ACTIVE

# Enhanced User Model Extensions
def enhance_user_model():
    """Add medical information columns to existing users table"""
    # These would be added via database migration
    # Adding them here for reference
    
    # Emergency contact information
    # emergency_contact_name = Column(String(200), nullable=True)
    # emergency_contact_phone = Column(String(15), nullable=True)
    # emergency_contact_relationship = Column(String(50), nullable=True)
    
    # Insurance information
    # insurance_provider = Column(String(200), nullable=True)
    # insurance_policy_number = Column(String(100), nullable=True)
    # insurance_group_number = Column(String(100), nullable=True)
    
    # Medical information
    # blood_type = Column(Enum(['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-', 'Unknown']), nullable=True)
    # allergies = Column(Text, nullable=True)
    # chronic_conditions = Column(Text, nullable=True)
    # medical_history_summary = Column(Text, nullable=True)
    # preferred_language = Column(String(50), default='Spanish')
    
    pass

# Enhanced Appointment Model Extensions  
def enhance_appointment_model():
    """Add financial and workflow columns to existing appointments table"""
    # These would be added via database migration
    # Adding them here for reference
    
    # Financial information
    # estimated_cost = Column(Decimal(10,2), nullable=True)
    # actual_cost = Column(Decimal(10,2), nullable=True)
    # insurance_covered = Column(Boolean, default=False)
    # copay_amount = Column(Decimal(10,2), nullable=True)
    
    # Follow-up workflow
    # follow_up_required = Column(Boolean, default=False)
    # follow_up_date = Column(DateTime(timezone=True), nullable=True)
    
    # Consultation details
    # consultation_type = Column(Enum(['in_person', 'telemedicine', 'phone']), default='in_person')
    # waiting_room_checkin = Column(DateTime(timezone=True), nullable=True)
    # consultation_start = Column(DateTime(timezone=True), nullable=True)
    # consultation_end = Column(DateTime(timezone=True), nullable=True)
    
    pass