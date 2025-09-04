from typing import List, Dict, Optional, Any
from datetime import datetime, date
from pydantic import BaseModel, Field, validator
from enum import Enum

# Enums matching the database models
class MedicalRecordSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class PrescriptionStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    DISCONTINUED = "discontinued"
    ON_HOLD = "on_hold"

class ConsultationType(str, Enum):
    IN_PERSON = "in_person"
    TELEMEDICINE = "telemedicine"
    PHONE = "phone"

class DocumentType(str, Enum):
    LAB_REPORT = "lab_report"
    IMAGING = "imaging"
    PRESCRIPTION = "prescription"
    DISCHARGE_SUMMARY = "discharge_summary"
    CONSULTATION_NOTES = "consultation_notes"
    REFERRAL = "referral"

# Base schemas
class MedicalRecordBase(BaseModel):
    patient_id: int
    doctor_id: int
    appointment_id: Optional[int] = None
    diagnosis: Optional[str] = None
    treatment_plan: Optional[str] = None
    medications: Optional[List[Dict[str, Any]]] = None
    lab_results: Optional[Dict[str, Any]] = None
    vital_signs: Optional[Dict[str, Any]] = None
    attachments: Optional[List[Dict[str, Any]]] = None
    follow_up_notes: Optional[str] = None
    severity: MedicalRecordSeverity = MedicalRecordSeverity.MEDIUM
    is_confidential: bool = False

class MedicalRecordCreate(MedicalRecordBase):
    record_date: Optional[datetime] = None

class MedicalRecordUpdate(BaseModel):
    diagnosis: Optional[str] = None
    treatment_plan: Optional[str] = None
    medications: Optional[List[Dict[str, Any]]] = None
    lab_results: Optional[Dict[str, Any]] = None
    vital_signs: Optional[Dict[str, Any]] = None
    attachments: Optional[List[Dict[str, Any]]] = None
    follow_up_notes: Optional[str] = None
    severity: Optional[MedicalRecordSeverity] = None
    is_confidential: Optional[bool] = None

class MedicalRecordResponse(MedicalRecordBase):
    id: int
    record_date: datetime
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Related data
    patient_name: Optional[str] = None
    doctor_name: Optional[str] = None
    doctor_specialidad: Optional[str] = None

    class Config:
        from_attributes = True

# Prescription schemas
class PrescriptionBase(BaseModel):
    medication_name: str = Field(..., max_length=200)
    generic_name: Optional[str] = Field(None, max_length=200)
    dosage: str = Field(..., max_length=100)
    frequency: str = Field(..., max_length=100)
    duration_days: Optional[int] = None
    start_date: datetime
    end_date: Optional[datetime] = None
    instructions: Optional[str] = None
    warnings: Optional[str] = None
    refills_remaining: int = 0
    total_refills_authorized: int = 0
    pharmacy_notes: Optional[str] = None

class PrescriptionCreate(PrescriptionBase):
    medical_record_id: int
    patient_id: int
    doctor_id: int
    status: PrescriptionStatus = PrescriptionStatus.ACTIVE

class PrescriptionUpdate(BaseModel):
    medication_name: Optional[str] = None
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    duration_days: Optional[int] = None
    end_date: Optional[datetime] = None
    instructions: Optional[str] = None
    warnings: Optional[str] = None
    status: Optional[PrescriptionStatus] = None
    refills_remaining: Optional[int] = None
    pharmacy_notes: Optional[str] = None

    @validator('refills_remaining')
    def refills_not_negative(cls, v):
        if v is not None and v < 0:
            raise ValueError('Refills remaining cannot be negative')
        return v

class PrescriptionResponse(PrescriptionBase):
    id: int
    medical_record_id: int
    patient_id: int
    doctor_id: int
    status: PrescriptionStatus
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Calculated fields
    is_active: Optional[bool] = None
    is_expired: Optional[bool] = None
    days_remaining: Optional[int] = None
    can_refill: Optional[bool] = None
    
    # Related data
    patient_name: Optional[str] = None
    doctor_name: Optional[str] = None
    medical_record_diagnosis: Optional[str] = None

    class Config:
        from_attributes = True

# Enhanced User schemas (for medical information)
class UserMedicalInfoUpdate(BaseModel):
    medical_history_summary: Optional[str] = None
    emergency_contact_name: Optional[str] = Field(None, max_length=200)
    emergency_contact_phone: Optional[str] = Field(None, max_length=15)
    emergency_contact_relationship: Optional[str] = Field(None, max_length=50)
    insurance_provider: Optional[str] = Field(None, max_length=200)
    insurance_policy_number: Optional[str] = Field(None, max_length=100)
    insurance_group_number: Optional[str] = Field(None, max_length=100)
    blood_type: Optional[str] = None
    allergies: Optional[str] = None
    chronic_conditions: Optional[str] = None
    preferred_language: Optional[str] = Field("Spanish", max_length=50)

    @validator('blood_type')
    def valid_blood_type(cls, v):
        if v is not None:
            valid_types = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-', 'Unknown']
            if v not in valid_types:
                raise ValueError('Invalid blood type')
        return v

# Medical document schemas
class MedicalDocumentBase(BaseModel):
    patient_id: int
    doctor_id: int
    medical_record_id: Optional[int] = None
    document_type: DocumentType
    title: str = Field(..., max_length=200)
    file_path: Optional[str] = Field(None, max_length=500)
    file_size: Optional[int] = None
    mime_type: Optional[str] = Field(None, max_length=100)
    is_patient_visible: bool = True
    expiry_date: Optional[date] = None
    tags: Optional[List[str]] = None

class MedicalDocumentCreate(MedicalDocumentBase):
    pass

class MedicalDocumentResponse(MedicalDocumentBase):
    id: int
    upload_date: datetime
    
    # Related data
    patient_name: Optional[str] = None
    doctor_name: Optional[str] = None

    class Config:
        from_attributes = True

# Notification schemas
class NotificationType(str, Enum):
    APPOINTMENT_REMINDER = "appointment_reminder"
    APPOINTMENT_CHANGE = "appointment_change"
    PRESCRIPTION_READY = "prescription_ready"
    LAB_RESULTS = "lab_results"
    SYSTEM_ALERT = "system_alert"
    FOLLOW_UP_DUE = "follow_up_due"

class NotificationCreate(BaseModel):
    recipient_user_id: int
    sender_user_id: Optional[int] = None
    notification_type: NotificationType
    title: str = Field(..., max_length=200)
    message: str
    appointment_id: Optional[int] = None
    medical_record_id: Optional[int] = None
    prescription_id: Optional[int] = None
    send_via_email: bool = True
    send_via_sms: bool = False
    scheduled_send_time: Optional[datetime] = None

class NotificationResponse(NotificationCreate):
    id: int
    is_read: bool = False
    is_sent: bool = False
    created_at: datetime
    
    # Related data
    sender_name: Optional[str] = None

    class Config:
        from_attributes = True

# Enhanced Appointment schemas (with medical workflow)
class AppointmentMedicalUpdate(BaseModel):
    estimated_cost: Optional[float] = None
    actual_cost: Optional[float] = None
    insurance_covered: bool = False
    copay_amount: Optional[float] = None
    follow_up_required: bool = False
    follow_up_date: Optional[datetime] = None
    consultation_type: ConsultationType = ConsultationType.IN_PERSON
    waiting_room_checkin: Optional[datetime] = None
    consultation_start: Optional[datetime] = None
    consultation_end: Optional[datetime] = None

    @validator('actual_cost', 'estimated_cost', 'copay_amount')
    def non_negative_amounts(cls, v):
        if v is not None and v < 0:
            raise ValueError('Financial amounts cannot be negative')
        return v

    @validator('consultation_end')
    def end_after_start(cls, v, values):
        if v is not None and 'consultation_start' in values and values['consultation_start'] is not None:
            if v < values['consultation_start']:
                raise ValueError('Consultation end time must be after start time')
        return v

# Vital signs schema (for structured vital signs data)
class VitalSigns(BaseModel):
    blood_pressure_systolic: Optional[int] = None
    blood_pressure_diastolic: Optional[int] = None
    heart_rate: Optional[int] = None  # beats per minute
    temperature: Optional[float] = None  # Celsius
    respiratory_rate: Optional[int] = None  # breaths per minute
    oxygen_saturation: Optional[int] = None  # percentage
    weight: Optional[float] = None  # kg
    height: Optional[float] = None  # cm
    bmi: Optional[float] = None
    notes: Optional[str] = None

    @validator('blood_pressure_systolic', 'blood_pressure_diastolic')
    def valid_blood_pressure(cls, v):
        if v is not None and (v < 50 or v > 300):
            raise ValueError('Blood pressure values must be between 50 and 300')
        return v

    @validator('heart_rate')
    def valid_heart_rate(cls, v):
        if v is not None and (v < 30 or v > 200):
            raise ValueError('Heart rate must be between 30 and 200 bpm')
        return v

    @validator('temperature')
    def valid_temperature(cls, v):
        if v is not None and (v < 30.0 or v > 45.0):
            raise ValueError('Temperature must be between 30.0 and 45.0°C')
        return v

    @validator('oxygen_saturation')
    def valid_oxygen_saturation(cls, v):
        if v is not None and (v < 70 or v > 100):
            raise ValueError('Oxygen saturation must be between 70 and 100%')
        return v

# Lab results schema (for structured lab data)
class LabResult(BaseModel):
    test_name: str
    result_value: str
    unit: Optional[str] = None
    reference_range: Optional[str] = None
    status: Optional[str] = None  # "normal", "abnormal", "critical"
    notes: Optional[str] = None

class LabResults(BaseModel):
    test_date: datetime
    laboratory: Optional[str] = None
    technician: Optional[str] = None
    results: List[LabResult]
    overall_notes: Optional[str] = None

# Medication schema (for structured medication data)
class Medication(BaseModel):
    name: str
    generic_name: Optional[str] = None
    dosage: str
    frequency: str
    route: Optional[str] = None  # "oral", "injection", "topical", etc.
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    prescribing_doctor: Optional[str] = None
    notes: Optional[str] = None

# Summary schemas for dashboard
class PatientMedicalSummary(BaseModel):
    patient_id: int
    patient_name: str
    total_records: int
    active_prescriptions: int
    last_visit: Optional[datetime] = None
    next_appointment: Optional[datetime] = None
    critical_allergies: Optional[List[str]] = None
    chronic_conditions: Optional[List[str]] = None
    emergency_contact: Optional[str] = None

class DoctorMedicalStats(BaseModel):
    doctor_id: int
    doctor_name: str
    total_patients: int
    records_created_today: int
    active_prescriptions: int
    pending_follow_ups: int
    critical_patients: int

# Search and filter schemas
class MedicalRecordSearchParams(BaseModel):
    patient_id: Optional[int] = None
    doctor_id: Optional[int] = None
    severity: Optional[MedicalRecordSeverity] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    diagnosis_contains: Optional[str] = None
    page: int = 1
    size: int = 10

class PrescriptionSearchParams(BaseModel):
    patient_id: Optional[int] = None
    doctor_id: Optional[int] = None
    status: Optional[PrescriptionStatus] = None
    medication_name: Optional[str] = None
    active_only: bool = False
    expiring_soon: bool = False  # prescriptions ending within 7 days
    page: int = 1
    size: int = 10