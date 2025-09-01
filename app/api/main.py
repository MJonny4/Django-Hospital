from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..core.database import test_database_connection, get_db, engine
from ..models.models import Base, User, Doctor, DoctorProfile, UserRole
from ..schemas.schemas import (
    UserRegister, UserLogin, UserResponse, Token, HomePageResponse,
    DoctorRegister, DoctorResponse, DoctorProfileResponse, AdminCreateUser, BackofficeStats
)
from ..core.auth import get_password_hash, verify_password, create_access_token, require_admin
from datetime import timedelta, datetime

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)