#!/usr/bin/env python3
"""
Script to populate the database with sample data for testing.
"""
import sys
import os
from faker import Faker
import random
from datetime import datetime, timedelta

# Add the parent directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.models.models import User, DoctorProfile, Base, EspecialidadMedica
from app.core.auth import get_password_hash

fake = Faker('es_ES')

def create_sample_patients(db: Session, count: int = 20):
    """Create sample patients"""
    print(f"Creating {count} sample patients...")
    
    for i in range(count):
        # Generate fake Spanish DNI
        dni_number = fake.random_int(min=10000000, max=99999999)
        dni_letters = "TRWAGMYFPDXBNJZSQVHLCKE"
        dni_letter = dni_letters[dni_number % 23]
        dni = f"{dni_number}{dni_letter}"
        
        patient = User(
            dni=dni,
            nombre=fake.first_name(),
            apellidos=f"{fake.last_name()} {fake.last_name()}",
            email=fake.unique.email(),
            telefono=f"6{fake.random_int(min=10000000, max=99999999)}",
            direccion=fake.address(),
            fecha_nacimiento=fake.date_between(start_date='-80y', end_date='-18y').strftime('%Y-%m-%d'),
            hashed_password=get_password_hash("patient123")
        )
        patient.set_roles(["patient"])
        
        db.add(patient)
        
        if i % 10 == 0:
            db.commit()
    
    db.commit()
    print("✅ Sample patients created!")

def create_sample_doctors(db: Session):
    """Create sample doctors for each specialty"""
    print("Creating sample doctors for each medical specialty...")
    
    specialties = list(EspecialidadMedica)
    
    for specialty in specialties:
        # Generate fake Spanish DNI
        dni_number = fake.random_int(min=10000000, max=99999999)
        dni_letters = "TRWAGMYFPDXBNJZSQVHLCKE"
        dni_letter = dni_letters[dni_number % 23]
        dni = f"{dni_number}{dni_letter}"
        
        # Create user
        doctor_user = User(
            dni=dni,
            nombre=f"Dr. {fake.first_name()}",
            apellidos=f"{fake.last_name()} {fake.last_name()}",
            email=fake.unique.email(),
            telefono=f"6{fake.random_int(min=10000000, max=99999999)}",
            direccion=fake.address(),
            fecha_nacimiento=fake.date_between(start_date='-65y', end_date='-30y').strftime('%Y-%m-%d'),
            hashed_password=get_password_hash("doctor123")
        )
        doctor_user.set_roles(["patient", "doctor"])  # Doctors can also be patients
        
        db.add(doctor_user)
        db.flush()  # Get the ID
        
        # Generate medical license number
        numero_colegiado = f"28{fake.random_int(min=10000, max=99999)}"
        
        # Create doctor profile
        doctor_profile = DoctorProfile(
            user_id=doctor_user.id,
            numero_colegiado=numero_colegiado,
            colegio_medico="Colegio Oficial de Médicos de Madrid",
            especialidad=specialty,
            subespecialidad=fake.sentence(nb_words=2).strip('.') if random.choice([True, False]) else None,
            universidad=random.choice([
                "Universidad Complutense de Madrid",
                "Universidad Autónoma de Madrid", 
                "Universidad de Barcelona",
                "Universidad de Valencia",
                "Universidad de Sevilla"
            ]),
            ano_graduacion=fake.random_int(min=1990, max=2015),
            titulo_especialista=f"Especialista en {specialty.value}",
            hospital_centro=random.choice([
                "Hospital Universitario La Paz",
                "Hospital Clínico San Carlos",
                "Hospital Universitario 12 de Octubre",
                "Hospital Ramón y Cajal",
                "Hospital Gregorio Marañón"
            ]),
            departamento_servicio=f"Servicio de {specialty.value}",
            consulta_numero=fake.random_int(min=100, max=999),
            horario_consulta="Lunes a Viernes: 9:00-14:00",
            idiomas=random.choice([
                "Español, Inglés",
                "Español, Inglés, Francés", 
                "Español, Inglés, Alemán",
                "Español"
            ]),
            biografia=f"Médico especialista en {specialty.value} con amplia experiencia profesional.",
            created_by_admin=1  # Assuming admin user has ID 1
        )
        
        db.add(doctor_profile)
    
    db.commit()
    print("✅ Sample doctors created for all specialties!")

def populate_database():
    """Main function to populate the database"""
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Check if data already exists
        existing_users = db.query(User).count()
        if existing_users > 1:  # More than just the admin
            print("❌ Database already has data. Skipping population.")
            return
        
        print("🚀 Starting database population...")
        
        # Create sample data
        create_sample_patients(db, 25)
        create_sample_doctors(db)
        
        print("✅ Database population completed successfully!")
        print(f"   Total users: {db.query(User).count()}")
        print(f"   Total doctors: {db.query(DoctorProfile).count()}")
        
    except Exception as e:
        print(f"❌ Error populating database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    populate_database()