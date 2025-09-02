from .schemas import (
    UserRegister, UserLogin, UserResponse, Token, HomePageResponse,
    DoctorRegister, DoctorResponse, DoctorProfileResponse, 
    AdminCreateUser, BackofficeStats,
    # Appointment schemas
    DoctorAvailabilityCreate, DoctorAvailabilityResponse,
    AppointmentCreate, AppointmentUpdate, AppointmentResponse,
    AppointmentDetailedResponse, AppointmentListResponse,
    AppointmentAvailabilityRequest, AppointmentTimeSlot, AppointmentAvailabilityResponse
)

__all__ = [
    "UserRegister",
    "UserLogin", 
    "UserResponse",
    "Token",
    "HomePageResponse",
    "DoctorRegister",
    "DoctorResponse",
    "DoctorProfileResponse",
    "AdminCreateUser",
    "BackofficeStats",
    # Appointment schemas
    "DoctorAvailabilityCreate",
    "DoctorAvailabilityResponse",
    "AppointmentCreate",
    "AppointmentUpdate", 
    "AppointmentResponse",
    "AppointmentDetailedResponse",
    "AppointmentListResponse",
    "AppointmentAvailabilityRequest",
    "AppointmentTimeSlot",
    "AppointmentAvailabilityResponse"
]