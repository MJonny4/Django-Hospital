#!/usr/bin/env python3
"""
Script to create an admin user for the hospital system.
"""
import sys
import os

# Add the parent directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.models.models import User, Base
from app.core.auth import get_password_hash

def create_admin_user():
    """Create an admin user for the system"""
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Check if admin already exists
        existing_admin = db.query(User).filter(User.email == "admin@hospital.com").first()
        if existing_admin:
            print("Admin user already exists!")
            print(f"   Email: {existing_admin.email}")
            return
        
        # Create admin user
        admin_user = User(
            dni="00000000T",
            nombre="Administrador",
            apellidos="del Sistema",
            email="admin@hospital.com",
            telefono="600000000",
            direccion="Hospital Central",
            fecha_nacimiento="1980-01-01",
            hashed_password=get_password_hash("admin123456")
        )
        admin_user.set_roles(["admin", "patient"])  # Admin can also be a patient
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        print("Admin user created successfully!")
        print(f"   Email: admin@hospital.com")
        print(f"   Password: admin123456")
        print(f"   DNI: 00000000T")
        print(f"   Roles: {admin_user.get_roles()}")
        
    except Exception as e:
        print(f"Error creating admin user: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_admin_user()