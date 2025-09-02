-- Hospital Management System Database Setup Script
-- This script creates all tables and inserts realistic test data

-- Drop existing tables if they exist (in correct order to handle foreign keys)
DROP TABLE IF EXISTS appointment_history;
DROP TABLE IF EXISTS appointments;
DROP TABLE IF EXISTS doctor_availability;
DROP TABLE IF EXISTS doctor_profiles;
DROP TABLE IF EXISTS doctors_deprecated;
DROP TABLE IF EXISTS users;

-- Create Users table
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    dni VARCHAR(9) UNIQUE NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    apellidos VARCHAR(200) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    telefono VARCHAR(15) NOT NULL,
    direccion VARCHAR(500) NOT NULL,
    fecha_nacimiento VARCHAR(10) NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    roles VARCHAR(500) NOT NULL DEFAULT '["patient"]',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_users_dni (dni),
    INDEX idx_users_email (email)
);

-- Create Doctor Profiles table
CREATE TABLE doctor_profiles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT UNIQUE NOT NULL,
    numero_colegiado VARCHAR(20) UNIQUE NOT NULL,
    colegio_medico VARCHAR(200) NOT NULL,
    especialidad ENUM(
        'Medicina General', 'Cardiología', 'Pediatría', 
        'Ginecología y Obstetricia', 'Traumatología y Cirugía Ortopédica',
        'Neurología', 'Dermatología', 'Oftalmología', 
        'Otorrinolaringología', 'Urología', 'Psiquiatría',
        'Radiodiagnóstico', 'Anestesiología y Reanimación',
        'Medicina Interna', 'Cirugía General y del Aparato Digestivo',
        'Endocrinología y Nutrición', 'Neumología', 
        'Aparato Digestivo', 'Hematología y Hemoterapia', 'Oncología Médica'
    ) NOT NULL,
    subespecialidad VARCHAR(200),
    universidad VARCHAR(300) NOT NULL,
    ano_graduacion INT NOT NULL,
    titulo_especialista VARCHAR(300),
    hospital_centro VARCHAR(300) NOT NULL,
    departamento_servicio VARCHAR(200) NOT NULL,
    consulta_numero VARCHAR(20),
    horario_consulta TEXT,
    idiomas TEXT,
    biografia TEXT,
    foto_url VARCHAR(500),
    is_active BOOLEAN DEFAULT TRUE,
    fecha_alta_sistema TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by_admin INT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by_admin) REFERENCES users(id),
    INDEX idx_doctor_profiles_user_id (user_id),
    INDEX idx_doctor_profiles_numero_colegiado (numero_colegiado)
);

-- Create Doctor Availability table
CREATE TABLE doctor_availability (
    id INT AUTO_INCREMENT PRIMARY KEY,
    doctor_profile_id INT NOT NULL,
    day_of_week INT NOT NULL CHECK (day_of_week >= 0 AND day_of_week <= 6),
    start_time VARCHAR(5) NOT NULL,
    end_time VARCHAR(5) NOT NULL,
    slot_duration_minutes INT DEFAULT 30 NOT NULL,
    buffer_minutes INT DEFAULT 5 NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    effective_from TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    effective_until TIMESTAMP NULL,
    FOREIGN KEY (doctor_profile_id) REFERENCES doctor_profiles(id) ON DELETE CASCADE,
    INDEX idx_doctor_availability_profile_day (doctor_profile_id, day_of_week)
);

-- Create Appointments table
CREATE TABLE appointments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    doctor_profile_id INT NOT NULL,
    appointment_date TIMESTAMP NOT NULL,
    duration_minutes INT DEFAULT 30 NOT NULL,
    appointment_type ENUM('consultation', 'follow_up', 'emergency', 'check_up', 'procedure', 'vaccination') DEFAULT 'consultation',
    priority ENUM('low', 'normal', 'high', 'urgent') DEFAULT 'normal',
    status ENUM('scheduled', 'confirmed', 'in_progress', 'completed', 'cancelled', 'no_show', 'rescheduled') DEFAULT 'scheduled',
    reason TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by_user_id INT NOT NULL,
    cancelled_at TIMESTAMP NULL,
    cancelled_by_user_id INT NULL,
    cancellation_reason TEXT,
    FOREIGN KEY (patient_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (doctor_profile_id) REFERENCES doctor_profiles(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by_user_id) REFERENCES users(id),
    FOREIGN KEY (cancelled_by_user_id) REFERENCES users(id),
    INDEX idx_appointments_patient (patient_id),
    INDEX idx_appointments_doctor (doctor_profile_id),
    INDEX idx_appointments_date (appointment_date),
    INDEX idx_appointments_status (status)
);

-- Create Appointment History table
CREATE TABLE appointment_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    appointment_id INT NOT NULL,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    changed_by_user_id INT NOT NULL,
    field_name VARCHAR(50) NOT NULL,
    old_value TEXT,
    new_value TEXT,
    change_reason TEXT,
    FOREIGN KEY (appointment_id) REFERENCES appointments(id) ON DELETE CASCADE,
    FOREIGN KEY (changed_by_user_id) REFERENCES users(id),
    INDEX idx_appointment_history_appointment (appointment_id),
    INDEX idx_appointment_history_date (changed_at)
);

-- Create deprecated doctors table for backward compatibility
CREATE TABLE doctors_deprecated (
    id INT AUTO_INCREMENT PRIMARY KEY,
    dni VARCHAR(9) UNIQUE NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    apellidos VARCHAR(200) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    telefono VARCHAR(15) NOT NULL,
    fecha_nacimiento VARCHAR(10) NOT NULL,
    numero_colegiado VARCHAR(20) UNIQUE NOT NULL,
    colegio_medico VARCHAR(200) NOT NULL,
    especialidad ENUM(
        'Medicina General', 'Cardiología', 'Pediatría', 
        'Ginecología y Obstetricia', 'Traumatología y Cirugía Ortopédica',
        'Neurología', 'Dermatología', 'Oftalmología', 
        'Otorrinolaringología', 'Urología', 'Psiquiatría',
        'Radiodiagnóstico', 'Anestesiología y Reanimación',
        'Medicina Interna', 'Cirugía General y del Aparato Digestivo',
        'Endocrinología y Nutrición', 'Neumología', 
        'Aparato Digestivo', 'Hematología y Hemoterapia', 'Oncología Médica'
    ) NOT NULL,
    subespecialidad VARCHAR(200),
    universidad VARCHAR(300) NOT NULL,
    ano_graduacion INT NOT NULL,
    titulo_especialista VARCHAR(300),
    hospital_centro VARCHAR(300) NOT NULL,
    departamento_servicio VARCHAR(200) NOT NULL,
    consulta_numero VARCHAR(20),
    horario_consulta TEXT,
    idiomas TEXT,
    biografia TEXT,
    foto_url VARCHAR(500),
    is_active BOOLEAN DEFAULT TRUE,
    fecha_alta_sistema TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by_admin INT NOT NULL,
    FOREIGN KEY (created_by_admin) REFERENCES users(id)
);

-- Insert test data
-- Note: Passwords are hashed versions of "password123" using bcrypt
SET @password_hash = '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBdXzrjUyQNOJS';

-- Insert Admin User
INSERT INTO users (dni, nombre, apellidos, email, telefono, direccion, fecha_nacimiento, hashed_password, roles, is_active) VALUES
('12345678A', 'Carlos', 'Administrador López', 'admin@hospital.com', '912345678', 'Calle Admin 1, Madrid', '1980-05-15', @password_hash, '["admin"]', TRUE);

-- Insert Patient Users
INSERT INTO users (dni, nombre, apellidos, email, telefono, direccion, fecha_nacimiento, hashed_password, roles, is_active) VALUES
('23456789B', 'María', 'García Fernández', 'maria.garcia@email.com', '612345678', 'Calle Mayor 15, Madrid', '1985-03-22', @password_hash, '["patient"]', TRUE),
('34567890C', 'José', 'Martín Ruiz', 'jose.martin@email.com', '623456789', 'Avenida Libertad 42, Madrid', '1978-11-08', @password_hash, '["patient"]', TRUE),
('45678901D', 'Ana', 'López Sánchez', 'ana.lopez@email.com', '634567890', 'Plaza España 7, Madrid', '1990-07-14', @password_hash, '["patient"]', TRUE),
('56789012E', 'Pedro', 'Rodríguez Moreno', 'pedro.rodriguez@email.com', '645678901', 'Calle Alcalá 123, Madrid', '1982-12-03', @password_hash, '["patient"]', TRUE),
('67890123F', 'Carmen', 'Jiménez Torres', 'carmen.jimenez@email.com', '656789012', 'Gran Vía 88, Madrid', '1975-09-19', @password_hash, '["patient"]', TRUE),
('78901234G', 'Francisco', 'Hernández Vega', 'francisco.hernandez@email.com', '667890123', 'Calle Serrano 56, Madrid', '1988-01-27', @password_hash, '["patient"]', TRUE);

-- Insert Doctor Users (with dual roles: patient + doctor)
INSERT INTO users (dni, nombre, apellidos, email, telefono, direccion, fecha_nacimiento, hashed_password, roles, is_active) VALUES
('87654321X', 'Dra. María', 'González Pérez', 'maria.gonzalez@hospital.com', '913456789', 'Calle Médicos 10, Madrid', '1975-08-12', @password_hash, '["patient", "doctor"]', TRUE),
('76543210Y', 'Dr. Antonio', 'Ruiz Morales', 'antonio.ruiz@hospital.com', '914567890', 'Avenida Sanitaria 25, Madrid', '1968-04-20', @password_hash, '["patient", "doctor"]', TRUE),
('65432109Z', 'Dra. Elena', 'Martínez Silva', 'elena.martinez@hospital.com', '915678901', 'Plaza Medicina 3, Madrid', '1980-10-05', @password_hash, '["patient", "doctor"]', TRUE),
('54321098W', 'Dr. Miguel', 'Torres Blanco', 'miguel.torres@hospital.com', '916789012', 'Calle Hospital 18, Madrid', '1973-06-30', @password_hash, '["patient", "doctor"]', TRUE),
('43210987V', 'Dra. Isabel', 'Fernández Costa', 'isabel.fernandez@hospital.com', '917890123', 'Avenida Clínica 12, Madrid', '1977-02-14', @password_hash, '["patient", "doctor"]', TRUE),
('32109876U', 'Dr. Rafael', 'Sánchez Vidal', 'rafael.sanchez@hospital.com', '918901234', 'Calle Consulta 44, Madrid', '1971-12-18', @password_hash, '["patient", "doctor"]', TRUE);

-- Insert Doctor Profiles
INSERT INTO doctor_profiles (user_id, numero_colegiado, colegio_medico, especialidad, subespecialidad, universidad, ano_graduacion, titulo_especialista, hospital_centro, departamento_servicio, consulta_numero, horario_consulta, idiomas, biografia, created_by_admin) VALUES
(8, '280812345', 'Colegio Oficial de Médicos de Madrid', 'Cardiología', 'Cardiología Intervencionista', 'Universidad Complutense de Madrid', 2001, 'Especialista en Cardiología', 'Hospital Universitario La Paz', 'Servicio de Cardiología', '201', 'Lunes a Viernes: 9:00-14:00', 'Español, Inglés, Francés', 'Cardióloga especialista en procedimientos intervencionistas con más de 20 años de experiencia.', 1),

(9, '280956789', 'Colegio Oficial de Médicos de Madrid', 'Traumatología y Cirugía Ortopédica', 'Cirugía de Columna', 'Universidad Autónoma de Madrid', 1995, 'Especialista en Traumatología', 'Hospital Universitario Ramón y Cajal', 'Servicio de Traumatología', '305', 'Lunes a Jueves: 8:00-15:00', 'Español, Inglés', 'Traumatólogo con amplia experiencia en cirugía de columna vertebral y artroscopia.', 1),

(10, '281067890', 'Colegio Oficial de Médicos de Madrid', 'Pediatría', NULL, 'Universidad de Salamanca', 2005, 'Especialista en Pediatría', 'Hospital Infantil Niño Jesús', 'Servicio de Pediatría General', '102', 'Martes a Sábado: 9:00-13:00', 'Español, Inglés, Italiano', 'Pediatra dedicada al cuidado integral de niños y adolescentes.', 1),

(11, '281178901', 'Colegio Oficial de Médicos de Madrid', 'Neurología', 'Neurología Vascular', 'Universidad de Valencia', 1998, 'Especialista en Neurología', 'Hospital Clínico San Carlos', 'Servicio de Neurología', '405', 'Lunes a Viernes: 10:00-16:00', 'Español, Inglés, Alemán', 'Neurólogo especializado en enfermedades cerebrovasculares y trastornos del movimiento.', 1),

(12, '281289012', 'Colegio Oficial de Médicos de Madrid', 'Ginecología y Obstetricia', 'Medicina Materno-Fetal', 'Universidad de Barcelona', 2002, 'Especialista en Ginecología', 'Hospital Universitario 12 de Octubre', 'Servicio de Ginecología', '208', 'Lunes, Miércoles, Viernes: 8:30-14:30', 'Español, Inglés, Catalán', 'Ginecóloga especializada en medicina materno-fetal y ecografía obstétrica.', 1),

(13, '281390123', 'Colegio Oficial de Médicos de Madrid', 'Dermatología', 'Dermatología Oncológica', 'Universidad de Sevilla', 2000, 'Especialista en Dermatología', 'Hospital Universitario La Princesa', 'Servicio de Dermatología', '150', 'Martes a Viernes: 9:30-13:30', 'Español, Inglés, Portugués', 'Dermatólogo especializado en cáncer de piel y dermatoscopia avanzada.', 1);

-- Insert Doctor Availability (Monday = 0, Sunday = 6)
-- Dr. María González (Cardiología) - Lunes a Viernes
INSERT INTO doctor_availability (doctor_profile_id, day_of_week, start_time, end_time, slot_duration_minutes, buffer_minutes) VALUES
(1, 0, '09:00', '14:00', 30, 5),  -- Lunes
(1, 1, '09:00', '14:00', 30, 5),  -- Martes
(1, 2, '09:00', '14:00', 30, 5),  -- Miércoles
(1, 3, '09:00', '14:00', 30, 5),  -- Jueves
(1, 4, '09:00', '14:00', 30, 5);  -- Viernes

-- Dr. Antonio Ruiz (Traumatología) - Lunes a Jueves
INSERT INTO doctor_availability (doctor_profile_id, day_of_week, start_time, end_time, slot_duration_minutes, buffer_minutes) VALUES
(2, 0, '08:00', '15:00', 45, 10),  -- Lunes
(2, 1, '08:00', '15:00', 45, 10),  -- Martes
(2, 2, '08:00', '15:00', 45, 10),  -- Miércoles
(2, 3, '08:00', '15:00', 45, 10);  -- Jueves

-- Dra. Elena Martínez (Pediatría) - Martes a Sábado
INSERT INTO doctor_availability (doctor_profile_id, day_of_week, start_time, end_time, slot_duration_minutes, buffer_minutes) VALUES
(3, 1, '09:00', '13:00', 20, 5),  -- Martes
(3, 2, '09:00', '13:00', 20, 5),  -- Miércoles
(3, 3, '09:00', '13:00', 20, 5),  -- Jueves
(3, 4, '09:00', '13:00', 20, 5),  -- Viernes
(3, 5, '09:00', '13:00', 20, 5);  -- Sábado

-- Dr. Miguel Torres (Neurología) - Lunes a Viernes
INSERT INTO doctor_availability (doctor_profile_id, day_of_week, start_time, end_time, slot_duration_minutes, buffer_minutes) VALUES
(4, 0, '10:00', '16:00', 60, 15),  -- Lunes
(4, 1, '10:00', '16:00', 60, 15),  -- Martes
(4, 2, '10:00', '16:00', 60, 15),  -- Miércoles
(4, 3, '10:00', '16:00', 60, 15),  -- Jueves
(4, 4, '10:00', '16:00', 60, 15);  -- Viernes

-- Dra. Isabel Fernández (Ginecología) - Lunes, Miércoles, Viernes
INSERT INTO doctor_availability (doctor_profile_id, day_of_week, start_time, end_time, slot_duration_minutes, buffer_minutes) VALUES
(5, 0, '08:30', '14:30', 30, 5),  -- Lunes
(5, 2, '08:30', '14:30', 30, 5),  -- Miércoles
(5, 4, '08:30', '14:30', 30, 5);  -- Viernes

-- Dr. Rafael Sánchez (Dermatología) - Martes a Viernes
INSERT INTO doctor_availability (doctor_profile_id, day_of_week, start_time, end_time, slot_duration_minutes, buffer_minutes) VALUES
(6, 1, '09:30', '13:30', 25, 5),  -- Martes
(6, 2, '09:30', '13:30', 25, 5),  -- Miércoles
(6, 3, '09:30', '13:30', 25, 5),  -- Jueves
(6, 4, '09:30', '13:30', 25, 5);  -- Viernes

-- Insert sample appointments (future dates - adjust as needed)
INSERT INTO appointments (patient_id, doctor_profile_id, appointment_date, duration_minutes, appointment_type, priority, status, reason, notes, created_by_user_id) VALUES
-- María García con Dra. González (Cardiología)
(2, 1, '2024-12-15 10:00:00', 30, 'consultation', 'normal', 'scheduled', 'Revisión rutinaria cardiológica', NULL, 2),

-- José Martín con Dr. Ruiz (Traumatología)
(3, 2, '2024-12-16 09:00:00', 45, 'follow_up', 'high', 'confirmed', 'Seguimiento post-cirugía de rodilla', 'Paciente refiere mejoría en el dolor', 3),

-- Ana López con Dra. Martínez (Pediatría)
(4, 3, '2024-12-17 10:30:00', 20, 'check_up', 'normal', 'scheduled', 'Revisión pediátrica rutinaria', NULL, 4),

-- Pedro Rodríguez con Dr. Torres (Neurología)
(5, 4, '2024-12-18 11:00:00', 60, 'consultation', 'urgent', 'confirmed', 'Cefaleas recurrentes', 'Historia de migrañas familiares', 5),

-- Carmen Jiménez con Dra. Fernández (Ginecología)
(6, 5, '2024-12-19 09:00:00', 30, 'procedure', 'normal', 'scheduled', 'Citología cervical', NULL, 6),

-- Francisco Hernández con Dr. Sánchez (Dermatología)
(7, 6, '2024-12-20 10:15:00', 25, 'consultation', 'high', 'scheduled', 'Revisión lunar sospechoso', 'Cambio reciente en lunar brazo izquierdo', 7),

-- More appointments for variety
(2, 3, '2024-12-21 11:20:00', 20, 'consultation', 'normal', 'completed', 'Consulta por dermatitis', 'Tratamiento prescrito exitosamente', 2),

(3, 1, '2024-12-22 12:00:00', 30, 'follow_up', 'normal', 'cancelled', 'Seguimiento hipertensión', NULL, 3);

-- Insert appointment history records
INSERT INTO appointment_history (appointment_id, changed_by_user_id, field_name, old_value, new_value, change_reason) VALUES
(2, 9, 'status', 'scheduled', 'confirmed', 'Cita confirmada por el médico'),
(4, 11, 'status', 'scheduled', 'confirmed', 'Cita confirmada por el médico'),
(7, 10, 'status', 'scheduled', 'completed', 'Cita completada exitosamente'),
(8, 3, 'status', 'scheduled', 'cancelled', 'Cancelada por el paciente por motivos personales');

-- Display summary of inserted data
SELECT 'DATA INSERTION SUMMARY' as Info;
SELECT 'Users created:' as Type, COUNT(*) as Count FROM users;
SELECT 'Admin users:' as Type, COUNT(*) as Count FROM users WHERE JSON_CONTAINS(roles, '"admin"');
SELECT 'Patient users:' as Type, COUNT(*) as Count FROM users WHERE JSON_CONTAINS(roles, '"patient"');
SELECT 'Doctor users:' as Type, COUNT(*) as Count FROM users WHERE JSON_CONTAINS(roles, '"doctor"');
SELECT 'Doctor profiles:' as Type, COUNT(*) as Count FROM doctor_profiles;
SELECT 'Doctor availability slots:' as Type, COUNT(*) as Count FROM doctor_availability;
SELECT 'Appointments:' as Type, COUNT(*) as Count FROM appointments;
SELECT 'Appointment history records:' as Type, COUNT(*) as Count FROM appointment_history;

-- Display test login credentials
SELECT 'TEST LOGIN CREDENTIALS' as Info;
SELECT 'Admin Login:' as Role, 'admin@hospital.com' as Email, 'password123' as Password;
SELECT 'Doctor Login:' as Role, 'maria.gonzalez@hospital.com' as Email, 'password123' as Password;
SELECT 'Patient Login:' as Role, 'maria.garcia@email.com' as Email, 'password123' as Password;