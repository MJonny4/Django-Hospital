from .models import (
    User, DoctorProfile, Doctor, UserRole, EspecialidadMedica,
    validate_spanish_dni, validate_numero_colegiado,
    # Appointment models
    Appointment, DoctorAvailability, AppointmentHistory,
    AppointmentStatus, AppointmentType, AppointmentPriority
)

__all__ = [
    "User",
    "DoctorProfile", 
    "Doctor",
    "UserRole",
    "EspecialidadMedica",
    "validate_spanish_dni",
    "validate_numero_colegiado",
    # Appointment models
    "Appointment",
    "DoctorAvailability", 
    "AppointmentHistory",
    "AppointmentStatus",
    "AppointmentType",
    "AppointmentPriority"
]