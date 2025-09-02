import requests
import json
from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt


def get_auth_headers(request):
    """Get authorization headers from session"""
    token = request.session.get('access_token')
    if token:
        return {'Authorization': f'Bearer {token}'}
    return {}


def is_authenticated(request):
    """Check if user is authenticated"""
    return 'access_token' in request.session and 'user_data' in request.session


def require_auth(view_func):
    """Decorator to require authentication"""
    def wrapper(request, *args, **kwargs):
        if not is_authenticated(request):
            messages.error(request, 'Debe iniciar sesión para acceder a esta página')
            return redirect('hospital:login')
        return view_func(request, *args, **kwargs)
    return wrapper


def require_role(roles):
    """Decorator to require specific roles"""
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if not is_authenticated(request):
                return redirect('hospital:login')
            
            user_roles = request.session.get('user_data', {}).get('roles', [])
            if not any(role in user_roles for role in roles):
                messages.error(request, 'No tiene permisos para acceder a esta página')
                return redirect('hospital:home')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


# PUBLIC VIEWS
def home(request):
    """Home page"""
    return render(request, 'hospital/home.html')


def about(request):
    """About page"""
    return render(request, 'hospital/about.html')


# AUTHENTICATION VIEWS
def register(request):
    """User registration"""
    if is_authenticated(request):
        return redirect('hospital:home')
    
    if request.method == 'POST':
        data = {
            'dni': request.POST.get('dni'),
            'nombre': request.POST.get('nombre'),
            'apellidos': request.POST.get('apellidos'),
            'email': request.POST.get('email'),
            'telefono': request.POST.get('telefono'),
            'direccion': request.POST.get('direccion'),
            'fecha_nacimiento': request.POST.get('fecha_nacimiento'),
            'password': request.POST.get('password'),
        }
        
        try:
            response = requests.post(f'{settings.FASTAPI_BASE_URL}/register', json=data)
            if response.status_code == 201:
                result = response.json()
                # Auto-login after registration
                request.session['access_token'] = result['access_token']
                request.session['user_data'] = result['user']
                messages.success(request, 'Registro exitoso')
                return redirect('hospital:home')
            else:
                error_detail = response.json().get('detail', 'Error en el registro')
                messages.error(request, f'Error: {error_detail}')
        except requests.exceptions.RequestException as e:
            messages.error(request, f'Error de conexión: {str(e)}')
    
    return render(request, 'hospital/register.html')


def login_view(request):
    """User login"""
    if is_authenticated(request):
        return redirect('hospital:home')
    
    if request.method == 'POST':
        data = {
            'email': request.POST.get('email'),  # FastAPI expects email, not username
            'password': request.POST.get('password'),
        }
        
        try:
            response = requests.post(f'{settings.FASTAPI_BASE_URL}/login', json=data)  # Use json=data instead of data=data
            if response.status_code == 200:
                result = response.json()
                request.session['access_token'] = result['access_token']
                request.session['user_data'] = result['user']
                messages.success(request, 'Inicio de sesión exitoso')
                return redirect('hospital:home')
            else:
                messages.error(request, 'Credenciales incorrectas')
        except requests.exceptions.RequestException as e:
            messages.error(request, f'Error de conexión: {str(e)}')
    
    return render(request, 'hospital/login.html')


def logout_view(request):
    """User logout"""
    request.session.flush()
    messages.success(request, 'Sesión cerrada exitosamente')
    return redirect('hospital:home')


# PROTECTED USER VIEWS
@require_auth
def profile(request):
    """User profile"""
    return render(request, 'hospital/profile.html')


@require_auth
def appointments(request):
    """User appointments"""
    headers = get_auth_headers(request)
    try:
        response = requests.get(f'{settings.FASTAPI_BASE_URL}/appointments', headers=headers)
        if response.status_code == 200:
            appointments_data = response.json()
        else:
            appointments_data = {'appointments': [], 'total': 0}
            messages.error(request, 'Error al cargar las citas')
    except requests.exceptions.RequestException:
        appointments_data = {'appointments': [], 'total': 0}
        messages.error(request, 'Error de conexión')
    
    return render(request, 'hospital/appointments.html', {'appointments_data': appointments_data})


@require_auth
def create_appointment(request):
    """Create new appointment"""
    if request.method == 'POST':
        # Convert datetime-local format to ISO format
        appointment_date_str = request.POST.get('appointment_date')
        if appointment_date_str:
            # Convert "2024-12-15T14:30" to "2024-12-15T14:30:00"
            if len(appointment_date_str) == 16:  # YYYY-MM-DDTHH:MM
                appointment_date_str += ":00"  # Add seconds
        
        data = {
            'doctor_profile_id': int(request.POST.get('doctor_profile_id')),
            'appointment_date': appointment_date_str,
            'duration_minutes': int(request.POST.get('duration_minutes', 30)),
            'appointment_type': request.POST.get('appointment_type', 'consultation'),
            'priority': request.POST.get('priority', 'normal'),
            'reason': request.POST.get('reason'),
            'notes': request.POST.get('notes'),
        }
        
        headers = get_auth_headers(request)
        
        # Debug: Print the data being sent (remove in production)
        print(f"DEBUG: Appointment data being sent: {data}")
        print(f"DEBUG: Headers: {headers}")
        
        try:
            response = requests.post(f'{settings.FASTAPI_BASE_URL}/appointments', json=data, headers=headers)
            if response.status_code == 200 or response.status_code == 201:
                messages.success(request, 'Cita creada exitosamente')
                return redirect('hospital:appointments')
            else:
                # Debug: Show status code and raw response
                try:
                    error_detail = response.json().get('detail', 'Error al crear la cita')
                except:
                    error_detail = f'Error HTTP {response.status_code}: {response.text[:200]}'
                messages.error(request, f'Error: {error_detail}')
        except requests.exceptions.RequestException as e:
            messages.error(request, f'Error de conexión: {str(e)}')
    
    # Get doctors list for the form
    try:
        response = requests.get(f'{settings.FASTAPI_BASE_URL}/doctors')
        doctors = response.json() if response.status_code == 200 else []
    except requests.exceptions.RequestException:
        doctors = []
    
    # Handle pre-selected doctor from URL parameter (e.g., ?doctor=8)
    selected_doctor_id = None
    doctor_user_id = request.GET.get('doctor')
    if doctor_user_id:
        try:
            doctor_user_id = int(doctor_user_id)
            # Find the doctor with matching user ID and get their profile ID
            for doctor in doctors:
                if doctor['id'] == doctor_user_id:  # doctor.id is user ID
                    selected_doctor_id = doctor['profile_id']  # we need profile ID
                    break
        except (ValueError, TypeError):
            pass  # Invalid doctor parameter, ignore
    
    return render(request, 'hospital/create_appointment.html', {
        'doctors': doctors,
        'selected_doctor_id': selected_doctor_id
    })


@require_auth
def appointment_detail(request, appointment_id):
    """Appointment detail"""
    headers = get_auth_headers(request)
    try:
        response = requests.get(f'{settings.FASTAPI_BASE_URL}/appointments/{appointment_id}', headers=headers)
        if response.status_code == 200:
            appointment = response.json()
        else:
            appointment = None
            messages.error(request, 'Cita no encontrada')
    except requests.exceptions.RequestException:
        appointment = None
        messages.error(request, 'Error de conexión')
    
    return render(request, 'hospital/appointment_detail.html', {'appointment': appointment})


@require_auth
def cancel_appointment(request, appointment_id):
    """Cancel appointment"""
    if request.method == 'POST':
        headers = get_auth_headers(request)
        cancellation_reason = request.POST.get('cancellation_reason', '')
        
        try:
            params = {'cancellation_reason': cancellation_reason} if cancellation_reason else {}
            response = requests.delete(f'{settings.FASTAPI_BASE_URL}/appointments/{appointment_id}', headers=headers, params=params)
            if response.status_code == 200:
                messages.success(request, 'Cita cancelada exitosamente')
            else:
                error_detail = response.json().get('detail', 'Error al cancelar la cita')
                messages.error(request, f'Error: {error_detail}')
        except requests.exceptions.RequestException as e:
            messages.error(request, f'Error de conexión: {str(e)}')
    
    return redirect('hospital:appointments')


@require_auth
def doctors_list(request):
    """Doctors list"""
    try:
        response = requests.get(f'{settings.FASTAPI_BASE_URL}/doctors')
        doctors = response.json() if response.status_code == 200 else []
    except requests.exceptions.RequestException:
        doctors = []
        messages.error(request, 'Error al cargar la lista de médicos')
    
    return render(request, 'hospital/doctors_list.html', {'doctors': doctors})


@require_auth
def doctor_detail(request, doctor_id):
    """Doctor detail"""
    try:
        response = requests.get(f'{settings.FASTAPI_BASE_URL}/doctors/{doctor_id}')
        doctor = response.json() if response.status_code == 200 else None
    except requests.exceptions.RequestException:
        doctor = None
        messages.error(request, 'Error al cargar información del médico')
    
    return render(request, 'hospital/doctor_detail.html', {'doctor': doctor})


@require_auth
def check_availability(request, doctor_id):
    """Check doctor availability"""
    date = request.GET.get('date')
    if not date:
        return JsonResponse({'error': 'Fecha requerida'}, status=400)
    
    data = {
        'doctor_profile_id': doctor_id,
        'date': date
    }
    
    try:
        response = requests.post(f'{settings.FASTAPI_BASE_URL}/appointments/availability', json=data)
        if response.status_code == 200:
            return JsonResponse(response.json())
        else:
            return JsonResponse({'error': 'Error al obtener disponibilidad'}, status=400)
    except requests.exceptions.RequestException:
        return JsonResponse({'error': 'Error de conexión'}, status=500)


# ADMIN VIEWS
@require_role(['admin'])
def admin_panel(request):
    """Admin dashboard"""
    headers = get_auth_headers(request)
    try:
        response = requests.get(f'{settings.FASTAPI_BASE_URL}/admin/backoffice', headers=headers)
        stats = response.json() if response.status_code == 200 else {}
    except requests.exceptions.RequestException:
        stats = {}
        messages.error(request, 'Error al cargar estadísticas')
    
    return render(request, 'hospital/admin/panel.html', {'stats': stats})


@require_role(['admin'])
def admin_users(request):
    """Admin users management"""
    headers = get_auth_headers(request)
    try:
        response = requests.get(f'{settings.FASTAPI_BASE_URL}/admin/users', headers=headers)
        users = response.json() if response.status_code == 200 else []
    except requests.exceptions.RequestException:
        users = []
        messages.error(request, 'Error al cargar usuarios')
    
    return render(request, 'hospital/admin/users.html', {'users': users})


@require_role(['admin'])
def admin_doctors(request):
    """Admin doctors management"""
    headers = get_auth_headers(request)
    try:
        response = requests.get(f'{settings.FASTAPI_BASE_URL}/admin/doctors', headers=headers)
        doctors = response.json() if response.status_code == 200 else []
    except requests.exceptions.RequestException:
        doctors = []
        messages.error(request, 'Error al cargar médicos')
    
    return render(request, 'hospital/admin/doctors.html', {'doctors': doctors})


@require_role(['admin'])
def admin_register_doctor(request):
    """Admin register doctor"""
    if request.method == 'POST':
        data = {
            'dni': request.POST.get('dni'),
            'nombre': request.POST.get('nombre'),
            'apellidos': request.POST.get('apellidos'),
            'email': request.POST.get('email'),
            'telefono': request.POST.get('telefono'),
            'fecha_nacimiento': request.POST.get('fecha_nacimiento'),
            'numero_colegiado': request.POST.get('numero_colegiado'),
            'colegio_medico': request.POST.get('colegio_medico'),
            'especialidad': request.POST.get('especialidad'),
            'subespecialidad': request.POST.get('subespecialidad'),
            'universidad': request.POST.get('universidad'),
            'ano_graduacion': int(request.POST.get('ano_graduacion')),
            'titulo_especialista': request.POST.get('titulo_especialista'),
            'hospital_centro': request.POST.get('hospital_centro'),
            'departamento_servicio': request.POST.get('departamento_servicio'),
            'consulta_numero': request.POST.get('consulta_numero'),
            'horario_consulta': request.POST.get('horario_consulta'),
            'idiomas': request.POST.get('idiomas'),
            'biografia': request.POST.get('biografia'),
        }
        
        headers = get_auth_headers(request)
        try:
            response = requests.post(f'{settings.FASTAPI_BASE_URL}/admin/register-doctor', json=data, headers=headers)
            if response.status_code == 200:
                messages.success(request, 'Médico registrado exitosamente')
                return redirect('hospital:admin_doctors')
            else:
                error_detail = response.json().get('detail', 'Error al registrar médico')
                messages.error(request, f'Error: {error_detail}')
        except requests.exceptions.RequestException as e:
            messages.error(request, f'Error de conexión: {str(e)}')
    
    return render(request, 'hospital/admin/register_doctor.html')


@require_role(['admin'])
def admin_appointments(request):
    """Admin appointments management"""
    headers = get_auth_headers(request)
    try:
        response = requests.get(f'{settings.FASTAPI_BASE_URL}/admin/appointments', headers=headers)
        appointments_data = response.json() if response.status_code == 200 else {'appointments': [], 'total': 0}
    except requests.exceptions.RequestException:
        appointments_data = {'appointments': [], 'total': 0}
        messages.error(request, 'Error al cargar citas')
    
    return render(request, 'hospital/admin/appointments.html', {'appointments_data': appointments_data})


@require_role(['admin'])
def admin_availability(request):
    """Admin manage doctor availability"""
    if request.method == 'POST':
        data = {
            'doctor_profile_id': int(request.POST.get('doctor_profile_id')),
            'day_of_week': int(request.POST.get('day_of_week')),
            'start_time': request.POST.get('start_time'),
            'end_time': request.POST.get('end_time'),
            'slot_duration_minutes': int(request.POST.get('slot_duration_minutes', 30)),
            'buffer_minutes': int(request.POST.get('buffer_minutes', 5)),
        }
        
        headers = get_auth_headers(request)
        try:
            response = requests.post(f'{settings.FASTAPI_BASE_URL}/admin/doctor-availability', json=data, headers=headers)
            if response.status_code == 200:
                messages.success(request, 'Disponibilidad configurada exitosamente')
            else:
                error_detail = response.json().get('detail', 'Error al configurar disponibilidad')
                messages.error(request, f'Error: {error_detail}')
        except requests.exceptions.RequestException as e:
            messages.error(request, f'Error de conexión: {str(e)}')
    
    # Get doctors for the form
    headers = get_auth_headers(request)
    try:
        response = requests.get(f'{settings.FASTAPI_BASE_URL}/admin/doctors', headers=headers)
        doctors = response.json() if response.status_code == 200 else []
    except requests.exceptions.RequestException:
        doctors = []
    
    return render(request, 'hospital/admin/availability.html', {'doctors': doctors})

@require_role(['admin'])
def admin_create_patient(request):
    """Admin-only patient creation"""
    if request.method == 'POST':
        data = {
            'dni': request.POST.get('dni'),
            'nombre': request.POST.get('nombre'),
            'apellidos': request.POST.get('apellidos'),
            'email': request.POST.get('email'),
            'telefono': request.POST.get('telefono'),
            'direccion': request.POST.get('direccion'),
            'fecha_nacimiento': request.POST.get('fecha_nacimiento'),
            'password': request.POST.get('password'),
            'roles': ['patient']  # Admin is creating a patient
        }
        
        try:
            headers = get_auth_headers(request)
            response = requests.post(f'{settings.FASTAPI_BASE_URL}/admin/create-user', json=data, headers=headers)
            if response.status_code == 200:
                result = response.json()
                messages.success(request, f'Paciente {result["nombre"]} {result["apellidos"]} creado exitosamente')
                return redirect('hospital:admin_users')
            else:
                error_detail = response.json().get('detail', 'Error desconocido')
                messages.error(request, f'Error al crear paciente: {error_detail}')
        except requests.exceptions.RequestException:
            messages.error(request, 'Error de conexión con la API')
    
    return render(request, 'hospital/admin/create_patient.html')


# DOCTOR VIEWS
@require_role(['doctor'])
def doctor_panel(request):
    """Doctor dashboard"""
    return render(request, 'hospital/doctor/panel.html')


@require_role(['doctor'])
def doctor_appointments(request):
    """Doctor appointments"""
    headers = get_auth_headers(request)
    try:
        response = requests.get(f'{settings.FASTAPI_BASE_URL}/appointments', headers=headers)
        appointments_data = response.json() if response.status_code == 200 else {'appointments': [], 'total': 0}
    except requests.exceptions.RequestException:
        appointments_data = {'appointments': [], 'total': 0}
        messages.error(request, 'Error al cargar citas')
    
    return render(request, 'hospital/doctor/appointments.html', {'appointments_data': appointments_data})


@require_role(['doctor'])
def confirm_appointment(request, appointment_id):
    """Confirm appointment"""
    if request.method == 'POST':
        headers = get_auth_headers(request)
        try:
            response = requests.post(f'{settings.FASTAPI_BASE_URL}/appointments/{appointment_id}/confirm', headers=headers)
            if response.status_code == 200:
                messages.success(request, 'Cita confirmada exitosamente')
            else:
                error_detail = response.json().get('detail', 'Error al confirmar la cita')
                messages.error(request, f'Error: {error_detail}')
        except requests.exceptions.RequestException as e:
            messages.error(request, f'Error de conexión: {str(e)}')
    
    return redirect('hospital:doctor_appointments')


@require_role(['doctor'])
def complete_appointment(request, appointment_id):
    """Complete appointment"""
    if request.method == 'POST':
        headers = get_auth_headers(request)
        notes = request.POST.get('notes', '')
        
        try:
            params = {'notes': notes} if notes else {}
            response = requests.post(f'{settings.FASTAPI_BASE_URL}/appointments/{appointment_id}/complete', headers=headers, params=params)
            if response.status_code == 200:
                messages.success(request, 'Cita completada exitosamente')
            else:
                error_detail = response.json().get('detail', 'Error al completar la cita')
                messages.error(request, f'Error: {error_detail}')
        except requests.exceptions.RequestException as e:
            messages.error(request, f'Error de conexión: {str(e)}')
    
    return redirect('hospital:doctor_appointments')