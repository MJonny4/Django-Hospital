from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import test_database_connection, get_db, engine
from app.models.models import (
    Base, User, Doctor, DoctorProfile, UserRole,
    Appointment, DoctorAvailability, AppointmentHistory,
    AppointmentStatus, AppointmentType, AppointmentPriority
)
from app.schemas.schemas import (
    UserRegister, UserLogin, UserResponse, Token, HomePageResponse,
    DoctorRegister, DoctorResponse, DoctorProfileResponse, AdminCreateUser, BackofficeStats,
    # Appointment schemas
    DoctorAvailabilityCreate, DoctorAvailabilityResponse,
    AppointmentCreate, AppointmentUpdate, AppointmentResponse,
    AppointmentDetailedResponse, AppointmentListResponse,
    AppointmentAvailabilityRequest, AppointmentTimeSlot, AppointmentAvailabilityResponse
)
from app.core.auth import get_password_hash, verify_password, create_access_token, require_admin, get_current_user
from datetime import timedelta, datetime
from typing import List

app = FastAPI(
    title="Hospital Appointment System",
    description="A FastAPI application for managing doctor appointments",
    version="1.0.0"
)

# Create database tables
Base.metadata.create_all(bind=engine)

# Add CORS middleware to allow frontend connections
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# HOME PAGE
@app.get("/", response_model=HomePageResponse)
async def home_page():
    return HomePageResponse(
        mensaje="¡Bienvenido al Sistema de Citas Médicas!",
        descripcion="Sistema de gestión de citas médicas para hospitales. Regístrate o inicia sesión para continuar.",
        acciones=["Registrarse", "Iniciar Sesión", "Ver Información"]
    )

# HEALTH CHECK
@app.get("/health")
async def health_check():
    db_status = await test_database_connection()
    return {"status": "healthy", "database": db_status}

# USER REGISTRATION
@app.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserRegister, db: Session = Depends(get_db)):
    # Check if user already exists (by email or DNI)
    existing_user = db.query(User).filter(
        (User.email == user_data.email) | (User.dni == user_data.dni)
    ).first()
    
    if existing_user:
        if existing_user.email == user_data.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Este email ya está registrado"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Este DNI ya está registrado"
            )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        dni=user_data.dni,
        nombre=user_data.nombre,
        apellidos=user_data.apellidos,
        email=user_data.email,
        telefono=user_data.telefono,
        direccion=user_data.direccion,
        fecha_nacimiento=user_data.fecha_nacimiento,
        hashed_password=hashed_password
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Create access token
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": db_user.email}, expires_delta=access_token_expires
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(db_user)
    )

# USER LOGIN
@app.post("/login", response_model=Token)
async def login_user(user_credentials: UserLogin, db: Session = Depends(get_db)):
    # Find user by email
    user = db.query(User).filter(User.email == user_credentials.email).first()
    
    if not user or not verify_password(user_credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuario inactivo"
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )

# USER LOGOUT (placeholder for now)
@app.post("/logout")
async def logout_user():
    return {"message": "Logout exitoso", "detail": "Token invalidado correctamente"}

# ADMIN ENDPOINTS
@app.post("/admin/create-user", response_model=UserResponse)
async def admin_create_user(
    user_data: AdminCreateUser, 
    db: Session = Depends(get_db),
    admin_user = Depends(require_admin)
):
    """Admin endpoint to create new admin users"""
    # Check if user already exists
    existing_user = db.query(User).filter(
        (User.email == user_data.email) | (User.dni == user_data.dni)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuario ya existe con este email o DNI"
        )
    
    # Create new admin user
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        dni=user_data.dni,
        nombre=user_data.nombre,
        apellidos=user_data.apellidos,
        email=user_data.email,
        telefono=user_data.telefono,
        direccion=user_data.direccion,
        fecha_nacimiento=user_data.fecha_nacimiento,
        hashed_password=hashed_password
    )
    db_user.set_roles(user_data.roles)
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return UserResponse.model_validate(db_user)

@app.post("/admin/register-doctor", response_model=DoctorResponse)
async def admin_register_doctor(
    doctor_data: DoctorRegister,
    db: Session = Depends(get_db),
    admin_user = Depends(require_admin)
):
    """Admin endpoint to register new doctors"""
    # Check if user already exists
    existing_user = db.query(User).filter(
        (User.email == doctor_data.email) | (User.dni == doctor_data.dni)
    ).first()
    
    # Check if medical license already exists
    existing_profile = db.query(DoctorProfile).filter(
        DoctorProfile.numero_colegiado == doctor_data.numero_colegiado
    ).first()
    
    if existing_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un médico con este número de colegiado"
        )
    
    # If user exists, add doctor role and create profile
    if existing_user:
        # Check if user already has doctor role
        if existing_user.has_role("doctor"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Este usuario ya es médico"
            )
        
        # Add doctor role to existing user
        existing_user.add_role("doctor")
        db_user = existing_user
    else:
        # Create new user with patient and doctor roles
        from ..core.auth import get_password_hash
        import secrets
        temp_password = secrets.token_urlsafe(12)  # Generate temporary password
        hashed_password = get_password_hash(temp_password)
        
        db_user = User(
            dni=doctor_data.dni,
            nombre=doctor_data.nombre,
            apellidos=doctor_data.apellidos,
            email=doctor_data.email,
            telefono=doctor_data.telefono,
            direccion="Por completar",  # Default value
            fecha_nacimiento=doctor_data.fecha_nacimiento,
            hashed_password=hashed_password
        )
        db_user.set_roles(["patient", "doctor"])  # Both patient and doctor
        db.add(db_user)
        db.flush()  # Get the user ID
    
    # Create doctor profile
    db_doctor_profile = DoctorProfile(
        user_id=db_user.id,
        numero_colegiado=doctor_data.numero_colegiado,
        colegio_medico=doctor_data.colegio_medico,
        especialidad=doctor_data.especialidad,
        subespecialidad=doctor_data.subespecialidad,
        universidad=doctor_data.universidad,
        ano_graduacion=doctor_data.ano_graduacion,
        titulo_especialista=doctor_data.titulo_especialista,
        hospital_centro=doctor_data.hospital_centro,
        departamento_servicio=doctor_data.departamento_servicio,
        consulta_numero=doctor_data.consulta_numero,
        horario_consulta=doctor_data.horario_consulta,
        idiomas=doctor_data.idiomas,
        biografia=doctor_data.biografia,
        foto_url=doctor_data.foto_url,
        created_by_admin=admin_user.id
    )
    
    db.add(db_doctor_profile)
    db.commit()
    db.refresh(db_user)
    db.refresh(db_doctor_profile)
    
    # Create combined response
    doctor_response_data = {
        # User data
        "id": db_user.id,
        "profile_id": db_doctor_profile.id,  # Add doctor profile ID
        "dni": db_user.dni,
        "nombre": db_user.nombre,
        "apellidos": db_user.apellidos,
        "email": db_user.email,
        "telefono": db_user.telefono,
        "roles": db_user.get_roles(),
        "is_active": db_user.is_active,
        # Doctor profile data
        "numero_colegiado": db_doctor_profile.numero_colegiado,
        "colegio_medico": db_doctor_profile.colegio_medico,
        "especialidad": db_doctor_profile.especialidad,
        "subespecialidad": db_doctor_profile.subespecialidad,
        "universidad": db_doctor_profile.universidad,
        "ano_graduacion": db_doctor_profile.ano_graduacion,
        "titulo_especialista": db_doctor_profile.titulo_especialista,
        "hospital_centro": db_doctor_profile.hospital_centro,
        "departamento_servicio": db_doctor_profile.departamento_servicio,
        "consulta_numero": db_doctor_profile.consulta_numero,
        "horario_consulta": db_doctor_profile.horario_consulta,
        "idiomas": db_doctor_profile.idiomas,
        "biografia": db_doctor_profile.biografia,
        "foto_url": db_doctor_profile.foto_url,
        "fecha_alta_sistema": db_doctor_profile.fecha_alta_sistema,
    }
    
    return DoctorResponse(**doctor_response_data)

@app.get("/admin/backoffice", response_model=BackofficeStats)
async def get_backoffice_stats(
    db: Session = Depends(get_db),
    admin_user = Depends(require_admin)
):
    """Get backoffice statistics"""
    # Get counts using new role system
    all_users = db.query(User).all()
    total_patients = sum(1 for user in all_users if user.has_role("patient"))
    total_doctors = db.query(DoctorProfile).count()  # Count doctor profiles
    total_admins = sum(1 for user in all_users if user.has_role("admin"))
    
    # Recent registrations (last 7 days)
    seven_days_ago = datetime.now() - timedelta(days=7)
    recent_registrations = db.query(User).filter(User.created_at >= seven_days_ago).count()
    
    return BackofficeStats(
        total_patients=total_patients,
        total_doctors=total_doctors,
        total_admins=total_admins,
        recent_registrations=recent_registrations
    )

@app.get("/admin/doctors", response_model=list[DoctorResponse])
async def get_all_doctors(
    db: Session = Depends(get_db),
    admin_user = Depends(require_admin),
    skip: int = 0,
    limit: int = 100
):
    """Get all doctors (admin only)"""
    # Join User and DoctorProfile tables
    doctor_profiles = db.query(DoctorProfile).join(User, DoctorProfile.user_id == User.id).filter(
        DoctorProfile.is_active == True
    ).offset(skip).limit(limit).all()
    
    doctors = []
    for profile in doctor_profiles:
        user = profile.user
        doctor_data = {
            # User data
            "id": user.id,
            "profile_id": profile.id,  # Add doctor profile ID for forms that need it
            "dni": user.dni,
            "nombre": user.nombre,
            "apellidos": user.apellidos,
            "email": user.email,
            "telefono": user.telefono,
            "roles": user.get_roles(),
            "is_active": user.is_active,
            # Doctor profile data
            "numero_colegiado": profile.numero_colegiado,
            "colegio_medico": profile.colegio_medico,
            "especialidad": profile.especialidad,
            "subespecialidad": profile.subespecialidad,
            "universidad": profile.universidad,
            "ano_graduacion": profile.ano_graduacion,
            "titulo_especialista": profile.titulo_especialista,
            "hospital_centro": profile.hospital_centro,
            "departamento_servicio": profile.departamento_servicio,
            "consulta_numero": profile.consulta_numero,
            "horario_consulta": profile.horario_consulta,
            "idiomas": profile.idiomas,
            "biografia": profile.biografia,
            "foto_url": profile.foto_url,
            "fecha_alta_sistema": profile.fecha_alta_sistema,
        }
        doctors.append(DoctorResponse(**doctor_data))
    
    return doctors

@app.get("/admin/users", response_model=list[UserResponse])
async def get_all_users(
    db: Session = Depends(get_db),
    admin_user = Depends(require_admin),
    skip: int = 0,
    limit: int = 100
):
    """Get all users (admin only)"""
    users = db.query(User).offset(skip).limit(limit).all()
    return [UserResponse.model_validate(user) for user in users]

# PUBLIC DOCTOR ENDPOINTS (for patients)
@app.get("/doctors", response_model=list[DoctorResponse])
async def get_doctors_public(
    db: Session = Depends(get_db),
    especialidad: str = None,
    skip: int = 0,
    limit: int = 20
):
    """Get doctors list (public endpoint for patients)"""
    query = db.query(DoctorProfile).join(User, DoctorProfile.user_id == User.id).filter(
        DoctorProfile.is_active == True,
        User.is_active == True
    )
    
    if especialidad:
        try:
            from models import EspecialidadMedica
            especialidad_enum = EspecialidadMedica(especialidad)
            query = query.filter(DoctorProfile.especialidad == especialidad_enum)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Especialidad no válida"
            )
    
    doctor_profiles = query.offset(skip).limit(limit).all()
    
    doctors = []
    for profile in doctor_profiles:
        user = profile.user
        doctor_data = {
            # User data
            "id": user.id,
            "profile_id": profile.id,  # Add doctor profile ID
            "dni": user.dni,
            "nombre": user.nombre,
            "apellidos": user.apellidos,
            "email": user.email,
            "telefono": user.telefono,
            "roles": user.get_roles(),
            "is_active": user.is_active,
            # Doctor profile data
            "numero_colegiado": profile.numero_colegiado,
            "colegio_medico": profile.colegio_medico,
            "especialidad": profile.especialidad,
            "subespecialidad": profile.subespecialidad,
            "universidad": profile.universidad,
            "ano_graduacion": profile.ano_graduacion,
            "titulo_especialista": profile.titulo_especialista,
            "hospital_centro": profile.hospital_centro,
            "departamento_servicio": profile.departamento_servicio,
            "consulta_numero": profile.consulta_numero,
            "horario_consulta": profile.horario_consulta,
            "idiomas": profile.idiomas,
            "biografia": profile.biografia,
            "foto_url": profile.foto_url,
            "fecha_alta_sistema": profile.fecha_alta_sistema,
        }
        doctors.append(DoctorResponse(**doctor_data))
    
    return doctors

@app.get("/doctors/{doctor_id}", response_model=DoctorResponse)
async def get_doctor_by_id(doctor_id: int, db: Session = Depends(get_db)):
    """Get doctor details by ID"""
    # doctor_id now refers to user.id
    user = db.query(User).filter(User.id == doctor_id, User.is_active == True).first()
    if not user or not user.has_role("doctor"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Médico no encontrado"
        )
    
    profile = db.query(DoctorProfile).filter(
        DoctorProfile.user_id == doctor_id,
        DoctorProfile.is_active == True
    ).first()
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Perfil de médico no encontrado"
        )
    
    doctor_data = {
        # User data
        "id": user.id,
        "profile_id": profile.id,  # Add doctor profile ID
        "dni": user.dni,
        "nombre": user.nombre,
        "apellidos": user.apellidos,
        "email": user.email,
        "telefono": user.telefono,
        "roles": user.get_roles(),
        "is_active": user.is_active,
        # Doctor profile data
        "numero_colegiado": profile.numero_colegiado,
        "colegio_medico": profile.colegio_medico,
        "especialidad": profile.especialidad,
        "subespecialidad": profile.subespecialidad,
        "universidad": profile.universidad,
        "ano_graduacion": profile.ano_graduacion,
        "titulo_especialista": profile.titulo_especialista,
        "hospital_centro": profile.hospital_centro,
        "departamento_servicio": profile.departamento_servicio,
        "consulta_numero": profile.consulta_numero,
        "horario_consulta": profile.horario_consulta,
        "idiomas": profile.idiomas,
        "biografia": profile.biografia,
        "foto_url": profile.foto_url,
        "fecha_alta_sistema": profile.fecha_alta_sistema,
    }
    
    return DoctorResponse(**doctor_data)

# APPOINTMENT MANAGEMENT ENDPOINTS

def get_current_user_object(current_user_email: str = Depends(get_current_user), db: Session = Depends(get_db)):
    """Helper function to get full user object from email"""
    user = db.query(User).filter(User.email == current_user_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user

# DOCTOR AVAILABILITY MANAGEMENT
@app.post("/admin/doctor-availability", response_model=DoctorAvailabilityResponse)
async def create_doctor_availability(
    availability_data: DoctorAvailabilityCreate,
    db: Session = Depends(get_db),
    admin_user = Depends(require_admin)
):
    """Create doctor availability schedule (admin only)"""
    # Verify doctor profile exists
    doctor_profile = db.query(DoctorProfile).filter(
        DoctorProfile.id == availability_data.doctor_profile_id,
        DoctorProfile.is_active == True
    ).first()
    
    if not doctor_profile:
        raise HTTPException(status_code=404, detail="Perfil de médico no encontrado")
    
    # Check for existing availability on same day
    existing = db.query(DoctorAvailability).filter(
        DoctorAvailability.doctor_profile_id == availability_data.doctor_profile_id,
        DoctorAvailability.day_of_week == availability_data.day_of_week,
        DoctorAvailability.is_active == True
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400, 
            detail="Ya existe disponibilidad para este médico en este día de la semana"
        )
    
    availability = DoctorAvailability(**availability_data.model_dump())
    db.add(availability)
    db.commit()
    db.refresh(availability)
    
    return DoctorAvailabilityResponse.model_validate(availability)

@app.get("/doctor-availability/{doctor_profile_id}", response_model=List[DoctorAvailabilityResponse])
async def get_doctor_availability(
    doctor_profile_id: int,
    db: Session = Depends(get_db)
):
    """Get doctor availability schedule"""
    availabilities = db.query(DoctorAvailability).filter(
        DoctorAvailability.doctor_profile_id == doctor_profile_id,
        DoctorAvailability.is_active == True
    ).all()
    
    return [DoctorAvailabilityResponse.model_validate(avail) for avail in availabilities]

# APPOINTMENT BOOKING
@app.post("/appointments", response_model=AppointmentResponse)
async def create_appointment(
    appointment_data: AppointmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_object)
):
    """Create new appointment (patient only)"""
    # Verify user has patient role
    if not current_user.has_role("patient"):
        raise HTTPException(
            status_code=403,
            detail="Solo los pacientes pueden crear citas"
        )
    
    # Verify doctor profile exists and is active
    doctor_profile = db.query(DoctorProfile).filter(
        DoctorProfile.id == appointment_data.doctor_profile_id,
        DoctorProfile.is_active == True
    ).first()
    
    if not doctor_profile:
        raise HTTPException(status_code=404, detail="Médico no encontrado")
    
    # Prevent self-appointment (doctor booking appointment with themselves)
    if current_user.id == doctor_profile.user_id:
        raise HTTPException(
            status_code=400,
            detail="Los médicos no pueden programar citas consigo mismos"
        )
    
    # Check for appointment conflicts
    appointment_end = appointment_data.appointment_date + timedelta(minutes=appointment_data.duration_minutes)
    
    # Get all appointments for this doctor and check conflicts in Python
    existing_appointments = db.query(Appointment).filter(
        Appointment.doctor_profile_id == appointment_data.doctor_profile_id,
        Appointment.status.in_([AppointmentStatus.SCHEDULED, AppointmentStatus.CONFIRMED, AppointmentStatus.IN_PROGRESS]),
        Appointment.appointment_date >= appointment_data.appointment_date - timedelta(hours=6),  # Look 6 hours before
        Appointment.appointment_date <= appointment_end + timedelta(hours=6)  # Look 6 hours after
    ).all()
    
    # Check for time conflicts in Python
    conflicting_appointments = None
    for existing in existing_appointments:
        existing_end = existing.appointment_date + timedelta(minutes=existing.duration_minutes)
        if (existing.appointment_date < appointment_end and 
            existing_end > appointment_data.appointment_date):
            conflicting_appointments = existing
            break
    
    if conflicting_appointments:
        raise HTTPException(
            status_code=400,
            detail="El médico ya tiene una cita programada en ese horario"
        )
    
    # Create appointment
    appointment = Appointment(
        patient_id=current_user.id,
        doctor_profile_id=appointment_data.doctor_profile_id,
        appointment_date=appointment_data.appointment_date,
        duration_minutes=appointment_data.duration_minutes,
        appointment_type=appointment_data.appointment_type,
        priority=appointment_data.priority,
        reason=appointment_data.reason,
        notes=appointment_data.notes,
        created_by_user_id=current_user.id
    )
    
    db.add(appointment)
    db.flush()  # This assigns the ID without committing
    appointment_id = appointment.id  # Get ID before commit
    db.commit()
    
    # Return appointment data without refreshing from DB to avoid enum mismatch
    return AppointmentResponse(
        id=appointment_id,
        patient_id=current_user.id,
        doctor_profile_id=appointment_data.doctor_profile_id,
        appointment_date=appointment_data.appointment_date,
        duration_minutes=appointment_data.duration_minutes,
        appointment_type=appointment_data.appointment_type,
        priority=appointment_data.priority,
        status=AppointmentStatus.SCHEDULED,
        reason=appointment_data.reason,
        notes=appointment_data.notes,
        created_at=None  # We don't have this without reading from DB
    )

@app.get("/appointments", response_model=AppointmentListResponse)
async def get_user_appointments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_object),
    status_filter: AppointmentStatus = None,
    skip: int = 0,
    limit: int = 20
):
    """Get appointments for current user"""
    query = db.query(Appointment)
    
    if current_user.has_role("doctor"):
        # Get appointments where user is the doctor
        doctor_profile = db.query(DoctorProfile).filter(
            DoctorProfile.user_id == current_user.id,
            DoctorProfile.is_active == True
        ).first()
        
        if doctor_profile:
            query = query.filter(Appointment.doctor_profile_id == doctor_profile.id)
        else:
            # No doctor profile found, return empty
            return AppointmentListResponse(appointments=[], total=0, page=skip//limit + 1, size=limit)
    else:
        # Get appointments where user is the patient
        query = query.filter(Appointment.patient_id == current_user.id)
    
    if status_filter:
        query = query.filter(Appointment.status == status_filter)
    
    total = query.count()
    appointments = query.order_by(Appointment.appointment_date.desc()).offset(skip).limit(limit).all()
    
    return AppointmentListResponse(
        appointments=[AppointmentResponse.model_validate(apt) for apt in appointments],
        total=total,
        page=skip//limit + 1,
        size=limit
    )

@app.get("/appointments/{appointment_id}", response_model=AppointmentDetailedResponse)
async def get_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_object)
):
    """Get appointment details"""
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    
    if not appointment:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    
    # Check if user has permission to view this appointment
    can_view = False
    if current_user.has_role("admin"):
        can_view = True
    elif current_user.has_role("doctor"):
        doctor_profile = db.query(DoctorProfile).filter(
            DoctorProfile.user_id == current_user.id,
            DoctorProfile.is_active == True
        ).first()
        if doctor_profile and appointment.doctor_profile_id == doctor_profile.id:
            can_view = True
    elif appointment.patient_id == current_user.id:
        can_view = True
    
    if not can_view:
        raise HTTPException(status_code=403, detail="No tiene permisos para ver esta cita")
    
    # Get patient info
    patient = db.query(User).filter(User.id == appointment.patient_id).first()
    doctor_profile = db.query(DoctorProfile).filter(DoctorProfile.id == appointment.doctor_profile_id).first()
    
    response_data = {
        "id": appointment.id,
        "appointment_date": appointment.appointment_date,
        "duration_minutes": appointment.duration_minutes,
        "appointment_type": appointment.appointment_type,
        "priority": appointment.priority,
        "status": appointment.status,
        "reason": appointment.reason,
        "notes": appointment.notes,
        "created_at": appointment.created_at,
        "patient": UserResponse.model_validate(patient),
        "doctor_name": f"{doctor_profile.user.nombre} {doctor_profile.user.apellidos}" if doctor_profile else None,
        "doctor_specialidad": doctor_profile.especialidad if doctor_profile else None,
        "doctor_hospital": doctor_profile.hospital_centro if doctor_profile else None,
        "cancellation_reason": appointment.cancellation_reason
    }
    
    return AppointmentDetailedResponse(**response_data)

@app.put("/appointments/{appointment_id}", response_model=AppointmentResponse)
async def update_appointment(
    appointment_id: int,
    update_data: AppointmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_object)
):
    """Update appointment"""
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    
    if not appointment:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    
    # Check permissions
    can_update = False
    if current_user.has_role("admin"):
        can_update = True
    elif current_user.has_role("doctor"):
        doctor_profile = db.query(DoctorProfile).filter(
            DoctorProfile.user_id == current_user.id,
            DoctorProfile.is_active == True
        ).first()
        if doctor_profile and appointment.doctor_profile_id == doctor_profile.id:
            can_update = True
    elif appointment.patient_id == current_user.id:
        # Patients can only update certain fields and only if appointment can be cancelled
        if not appointment.can_be_cancelled():
            raise HTTPException(
                status_code=400,
                detail="No se puede modificar la cita (debe ser al menos 24h antes)"
            )
        can_update = True
    
    if not can_update:
        raise HTTPException(status_code=403, detail="No tiene permisos para modificar esta cita")
    
    # Update fields
    update_dict = update_data.model_dump(exclude_unset=True)
    
    for field, value in update_dict.items():
        if hasattr(appointment, field):
            setattr(appointment, field, value)
    
    # Handle status changes
    if update_data.status == AppointmentStatus.CANCELLED:
        appointment.cancelled_at = datetime.now()
        appointment.cancelled_by_user_id = current_user.id
        if update_data.cancellation_reason:
            appointment.cancellation_reason = update_data.cancellation_reason
    
    db.commit()
    db.refresh(appointment)
    
    return AppointmentResponse.model_validate(appointment)

@app.delete("/appointments/{appointment_id}")
async def cancel_appointment(
    appointment_id: int,
    cancellation_reason: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_object)
):
    """Cancel appointment"""
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    
    if not appointment:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    
    # Check permissions
    can_cancel = False
    if current_user.has_role("admin"):
        can_cancel = True
    elif appointment.patient_id == current_user.id:
        if not appointment.can_be_cancelled():
            raise HTTPException(
                status_code=400,
                detail="No se puede cancelar la cita (debe ser al menos 24h antes)"
            )
        can_cancel = True
    elif current_user.has_role("doctor"):
        doctor_profile = db.query(DoctorProfile).filter(
            DoctorProfile.user_id == current_user.id,
            DoctorProfile.is_active == True
        ).first()
        if doctor_profile and appointment.doctor_profile_id == doctor_profile.id:
            can_cancel = True
    
    if not can_cancel:
        raise HTTPException(status_code=403, detail="No tiene permisos para cancelar esta cita")
    
    # Update appointment status
    appointment.status = AppointmentStatus.CANCELLED
    appointment.cancelled_at = datetime.now()
    appointment.cancelled_by_user_id = current_user.id
    if cancellation_reason:
        appointment.cancellation_reason = cancellation_reason
    
    db.commit()
    
    return {"message": "Cita cancelada exitosamente"}

# ADMIN APPOINTMENT MANAGEMENT
@app.get("/admin/appointments", response_model=AppointmentListResponse)
async def get_all_appointments(
    db: Session = Depends(get_db),
    admin_user = Depends(require_admin),
    status_filter: AppointmentStatus = None,
    doctor_id: int = None,
    skip: int = 0,
    limit: int = 50
):
    """Get all appointments (admin only)"""
    query = db.query(Appointment)
    
    if status_filter:
        query = query.filter(Appointment.status == status_filter)
    
    if doctor_id:
        doctor_profile = db.query(DoctorProfile).filter(
            DoctorProfile.user_id == doctor_id,
            DoctorProfile.is_active == True
        ).first()
        if doctor_profile:
            query = query.filter(Appointment.doctor_profile_id == doctor_profile.id)
    
    total = query.count()
    appointments = query.order_by(Appointment.appointment_date.desc()).offset(skip).limit(limit).all()
    
    return AppointmentListResponse(
        appointments=[AppointmentResponse.model_validate(apt) for apt in appointments],
        total=total,
        page=skip//limit + 1,
        size=limit
    )

# APPOINTMENT SCHEDULING AND AVAILABILITY
@app.post("/appointments/availability", response_model=AppointmentAvailabilityResponse)
async def get_appointment_availability(
    availability_request: AppointmentAvailabilityRequest,
    db: Session = Depends(get_db)
):
    """Get available appointment slots for a doctor on a specific date"""
    from datetime import datetime, timedelta
    
    # Verify doctor profile exists
    doctor_profile = db.query(DoctorProfile).filter(
        DoctorProfile.id == availability_request.doctor_profile_id,
        DoctorProfile.is_active == True
    ).first()
    
    if not doctor_profile:
        raise HTTPException(status_code=404, detail="Médico no encontrado")
    
    # Parse the requested date
    try:
        requested_date = datetime.strptime(availability_request.date, '%Y-%m-%d').date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de fecha inválido")
    
    # Don't allow appointments in the past
    if requested_date <= datetime.now().date():
        return AppointmentAvailabilityResponse(
            doctor_profile_id=availability_request.doctor_profile_id,
            date=availability_request.date,
            available_slots=[]
        )
    
    # Get day of week (0=Monday, 6=Sunday)
    day_of_week = requested_date.weekday()
    
    # Get doctor's availability for this day of week
    availability = db.query(DoctorAvailability).filter(
        DoctorAvailability.doctor_profile_id == availability_request.doctor_profile_id,
        DoctorAvailability.day_of_week == day_of_week,
        DoctorAvailability.is_active == True
    ).first()
    
    if not availability:
        return AppointmentAvailabilityResponse(
            doctor_profile_id=availability_request.doctor_profile_id,
            date=availability_request.date,
            available_slots=[]
        )
    
    # Generate time slots based on availability
    start_hour, start_min = map(int, availability.start_time.split(':'))
    end_hour, end_min = map(int, availability.end_time.split(':'))
    
    start_time = datetime.combine(requested_date, datetime.min.time().replace(
        hour=start_hour, minute=start_min
    ))
    end_time = datetime.combine(requested_date, datetime.min.time().replace(
        hour=end_hour, minute=end_min
    ))
    
    # Get existing appointments for this doctor on this date
    existing_appointments = db.query(Appointment).filter(
        Appointment.doctor_profile_id == availability_request.doctor_profile_id,
        Appointment.status.in_([
            AppointmentStatus.SCHEDULED, 
            AppointmentStatus.CONFIRMED, 
            AppointmentStatus.IN_PROGRESS
        ]),
        func.date(Appointment.appointment_date) == requested_date
    ).all()
    
    # Generate all possible time slots
    available_slots = []
    current_time = start_time
    slot_duration = timedelta(minutes=availability.slot_duration_minutes)
    buffer_time = timedelta(minutes=availability.buffer_minutes)
    
    while current_time + slot_duration <= end_time:
        slot_end = current_time + slot_duration
        is_available = True
        reason = None
        
        # Check if this slot conflicts with existing appointments
        for appointment in existing_appointments:
            apt_start = appointment.appointment_date
            apt_end = apt_start + timedelta(minutes=appointment.duration_minutes)
            
            # Check for overlap (with buffer time)
            if (current_time < apt_end + buffer_time and 
                slot_end + buffer_time > apt_start):
                is_available = False
                reason = "Cita ya programada"
                break
        
        # Don't allow appointments too close to current time (2 hours minimum)
        min_advance_time = datetime.now() + timedelta(hours=2)
        if current_time < min_advance_time:
            is_available = False
            reason = "Debe programar con al menos 2 horas de anticipación"
        
        available_slots.append(AppointmentTimeSlot(
            time=current_time.strftime('%H:%M'),
            available=is_available,
            reason=reason
        ))
        
        current_time += slot_duration + buffer_time
    
    return AppointmentAvailabilityResponse(
        doctor_profile_id=availability_request.doctor_profile_id,
        date=availability_request.date,
        available_slots=available_slots
    )

@app.get("/appointments/conflicts/{doctor_profile_id}")
async def check_appointment_conflicts(
    doctor_profile_id: int,
    appointment_date: str,  # ISO format: 2024-01-15T10:30:00
    duration_minutes: int = 30,
    exclude_appointment_id: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_object)
):
    """Check for appointment conflicts before booking"""
    try:
        appointment_datetime = datetime.fromisoformat(appointment_date.replace('Z', '+00:00'))
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de fecha inválido. Use ISO format.")
    
    # Verify doctor profile exists
    doctor_profile = db.query(DoctorProfile).filter(
        DoctorProfile.id == doctor_profile_id,
        DoctorProfile.is_active == True
    ).first()
    
    if not doctor_profile:
        raise HTTPException(status_code=404, detail="Médico no encontrado")
    
    # Check for conflicts
    appointment_end = appointment_datetime + timedelta(minutes=duration_minutes)
    
    query = db.query(Appointment).filter(
        Appointment.doctor_profile_id == doctor_profile_id,
        Appointment.status.in_([
            AppointmentStatus.SCHEDULED, 
            AppointmentStatus.CONFIRMED, 
            AppointmentStatus.IN_PROGRESS
        ]),
        Appointment.appointment_date < appointment_end,
        func.date_add(
            Appointment.appointment_date, 
            func.interval(Appointment.duration_minutes, "MINUTE")
        ) > appointment_datetime
    )
    
    if exclude_appointment_id:
        query = query.filter(Appointment.id != exclude_appointment_id)
    
    conflicts = query.all()
    
    has_conflicts = len(conflicts) > 0
    conflict_details = []
    
    for conflict in conflicts:
        conflict_end = conflict.appointment_date + timedelta(minutes=conflict.duration_minutes)
        patient = db.query(User).filter(User.id == conflict.patient_id).first()
        
        conflict_details.append({
            "appointment_id": conflict.id,
            "patient_name": f"{patient.nombre} {patient.apellidos}" if patient else "Desconocido",
            "start_time": conflict.appointment_date.isoformat(),
            "end_time": conflict_end.isoformat(),
            "duration": conflict.duration_minutes,
            "status": conflict.status.value,
            "type": conflict.appointment_type.value
        })
    
    return {
        "has_conflicts": has_conflicts,
        "conflicts": conflict_details,
        "requested_appointment": {
            "start_time": appointment_datetime.isoformat(),
            "end_time": appointment_end.isoformat(),
            "duration": duration_minutes
        },
        "recommendation": "Conflicto detectado. Seleccione otro horario." if has_conflicts else "Sin conflictos. Puede proceder con la cita."
    }

# APPOINTMENT STATUS MANAGEMENT
@app.patch("/appointments/{appointment_id}/status")
async def update_appointment_status(
    appointment_id: int,
    new_status: AppointmentStatus,
    reason: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_object)
):
    """Update appointment status with proper validations"""
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    
    if not appointment:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    
    # Check permissions and validate status transitions
    old_status = appointment.status
    can_update = False
    
    if current_user.has_role("admin"):
        can_update = True
    elif current_user.has_role("doctor"):
        doctor_profile = db.query(DoctorProfile).filter(
            DoctorProfile.user_id == current_user.id,
            DoctorProfile.is_active == True
        ).first()
        if doctor_profile and appointment.doctor_profile_id == doctor_profile.id:
            can_update = True
    elif appointment.patient_id == current_user.id:
        # Patients can only cancel appointments
        if new_status == AppointmentStatus.CANCELLED:
            if not appointment.can_be_cancelled():
                raise HTTPException(
                    status_code=400,
                    detail="No se puede cancelar la cita (debe ser al menos 24h antes)"
                )
            can_update = True
    
    if not can_update:
        raise HTTPException(status_code=403, detail="No tiene permisos para cambiar el estado de esta cita")
    
    # Validate status transitions
    valid_transitions = {
        AppointmentStatus.SCHEDULED: [
            AppointmentStatus.CONFIRMED, 
            AppointmentStatus.CANCELLED, 
            AppointmentStatus.RESCHEDULED
        ],
        AppointmentStatus.CONFIRMED: [
            AppointmentStatus.IN_PROGRESS, 
            AppointmentStatus.CANCELLED, 
            AppointmentStatus.NO_SHOW,
            AppointmentStatus.RESCHEDULED
        ],
        AppointmentStatus.IN_PROGRESS: [
            AppointmentStatus.COMPLETED, 
            AppointmentStatus.CANCELLED
        ],
        AppointmentStatus.COMPLETED: [],  # Final status
        AppointmentStatus.CANCELLED: [],  # Final status
        AppointmentStatus.NO_SHOW: [],    # Final status
        AppointmentStatus.RESCHEDULED: [] # Final status
    }
    
    if old_status in valid_transitions and new_status not in valid_transitions[old_status]:
        raise HTTPException(
            status_code=400,
            detail=f"Transición de estado inválida: {old_status.value} -> {new_status.value}"
        )
    
    # Update appointment status
    appointment.status = new_status
    
    # Handle special status changes
    if new_status == AppointmentStatus.CANCELLED:
        appointment.cancelled_at = datetime.now()
        appointment.cancelled_by_user_id = current_user.id
        if reason:
            appointment.cancellation_reason = reason
    
    # Create history record
    history = AppointmentHistory(
        appointment_id=appointment_id,
        changed_by_user_id=current_user.id,
        field_name="status",
        old_value=old_status.value,
        new_value=new_status.value,
        change_reason=reason
    )
    
    db.add(history)
    db.commit()
    db.refresh(appointment)
    
    return {
        "message": f"Estado de cita actualizado a {new_status.value}",
        "appointment_id": appointment_id,
        "old_status": old_status.value,
        "new_status": new_status.value,
        "updated_at": datetime.now().isoformat()
    }

@app.post("/appointments/{appointment_id}/confirm")
async def confirm_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_object)
):
    """Confirm a scheduled appointment (doctor or admin only)"""
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    
    if not appointment:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    
    if appointment.status != AppointmentStatus.SCHEDULED:
        raise HTTPException(
            status_code=400,
            detail=f"Solo se pueden confirmar citas programadas. Estado actual: {appointment.status.value}"
        )
    
    # Check permissions
    can_confirm = False
    if current_user.has_role("admin"):
        can_confirm = True
    elif current_user.has_role("doctor"):
        doctor_profile = db.query(DoctorProfile).filter(
            DoctorProfile.user_id == current_user.id,
            DoctorProfile.is_active == True
        ).first()
        if doctor_profile and appointment.doctor_profile_id == doctor_profile.id:
            can_confirm = True
    
    if not can_confirm:
        raise HTTPException(status_code=403, detail="Solo el médico o administrador pueden confirmar citas")
    
    appointment.status = AppointmentStatus.CONFIRMED
    
    # Create history record
    history = AppointmentHistory(
        appointment_id=appointment_id,
        changed_by_user_id=current_user.id,
        field_name="status",
        old_value=AppointmentStatus.SCHEDULED.value,
        new_value=AppointmentStatus.CONFIRMED.value,
        change_reason="Cita confirmada por el médico"
    )
    
    db.add(history)
    db.commit()
    
    return {"message": "Cita confirmada exitosamente", "status": "confirmed"}

@app.post("/appointments/{appointment_id}/complete")
async def complete_appointment(
    appointment_id: int,
    notes: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_object)
):
    """Mark appointment as completed (doctor or admin only)"""
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    
    if not appointment:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    
    if appointment.status not in [AppointmentStatus.CONFIRMED, AppointmentStatus.IN_PROGRESS]:
        raise HTTPException(
            status_code=400,
            detail=f"Solo se pueden completar citas confirmadas o en curso. Estado actual: {appointment.status.value}"
        )
    
    # Check permissions
    can_complete = False
    if current_user.has_role("admin"):
        can_complete = True
    elif current_user.has_role("doctor"):
        doctor_profile = db.query(DoctorProfile).filter(
            DoctorProfile.user_id == current_user.id,
            DoctorProfile.is_active == True
        ).first()
        if doctor_profile and appointment.doctor_profile_id == doctor_profile.id:
            can_complete = True
    
    if not can_complete:
        raise HTTPException(status_code=403, detail="Solo el médico o administrador pueden completar citas")
    
    old_status = appointment.status
    appointment.status = AppointmentStatus.COMPLETED
    
    if notes:
        appointment.notes = notes
    
    # Create history record
    history = AppointmentHistory(
        appointment_id=appointment_id,
        changed_by_user_id=current_user.id,
        field_name="status",
        old_value=old_status.value,
        new_value=AppointmentStatus.COMPLETED.value,
        change_reason=f"Cita completada. {notes if notes else ''}"
    )
    
    db.add(history)
    db.commit()
    
    return {"message": "Cita completada exitosamente", "status": "completed"}

@app.post("/appointments/{appointment_id}/no-show")
async def mark_no_show(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_object)
):
    """Mark appointment as no-show (doctor or admin only)"""
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    
    if not appointment:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    
    if appointment.status != AppointmentStatus.CONFIRMED:
        raise HTTPException(
            status_code=400,
            detail=f"Solo se pueden marcar como 'no show' las citas confirmadas. Estado actual: {appointment.status.value}"
        )
    
    # Check permissions
    can_mark = False
    if current_user.has_role("admin"):
        can_mark = True
    elif current_user.has_role("doctor"):
        doctor_profile = db.query(DoctorProfile).filter(
            DoctorProfile.user_id == current_user.id,
            DoctorProfile.is_active == True
        ).first()
        if doctor_profile and appointment.doctor_profile_id == doctor_profile.id:
            can_mark = True
    
    if not can_mark:
        raise HTTPException(status_code=403, detail="Solo el médico o administrador pueden marcar como 'no show'")
    
    appointment.status = AppointmentStatus.NO_SHOW
    
    # Create history record
    history = AppointmentHistory(
        appointment_id=appointment_id,
        changed_by_user_id=current_user.id,
        field_name="status",
        old_value=AppointmentStatus.CONFIRMED.value,
        new_value=AppointmentStatus.NO_SHOW.value,
        change_reason="Paciente no se presentó a la cita"
    )
    
    db.add(history)
    db.commit()
    
    return {"message": "Cita marcada como 'no show' exitosamente", "status": "no_show"}

@app.get("/appointments/{appointment_id}/history")
async def get_appointment_history(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_object)
):
    """Get appointment change history"""
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    
    if not appointment:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    
    # Check permissions
    can_view = False
    if current_user.has_role("admin"):
        can_view = True
    elif current_user.has_role("doctor"):
        doctor_profile = db.query(DoctorProfile).filter(
            DoctorProfile.user_id == current_user.id,
            DoctorProfile.is_active == True
        ).first()
        if doctor_profile and appointment.doctor_profile_id == doctor_profile.id:
            can_view = True
    elif appointment.patient_id == current_user.id:
        can_view = True
    
    if not can_view:
        raise HTTPException(status_code=403, detail="No tiene permisos para ver el historial de esta cita")
    
    history = db.query(AppointmentHistory).filter(
        AppointmentHistory.appointment_id == appointment_id
    ).order_by(AppointmentHistory.changed_at.desc()).all()
    
    history_records = []
    for record in history:
        changed_by = db.query(User).filter(User.id == record.changed_by_user_id).first()
        history_records.append({
            "id": record.id,
            "changed_at": record.changed_at,
            "changed_by": f"{changed_by.nombre} {changed_by.apellidos}" if changed_by else "Desconocido",
            "field_name": record.field_name,
            "old_value": record.old_value,
            "new_value": record.new_value,
            "change_reason": record.change_reason
        })
    
    return {
        "appointment_id": appointment_id,
        "history": history_records
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)