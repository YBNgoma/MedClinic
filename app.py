from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
import os
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'clinic_management_secret_key'

# Database setup
DB_PATH = './clinic.db'

def init_db():
    """Initialize the database with required tables"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Users table (Staff/Admin)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        name TEXT NOT NULL,
        role TEXT NOT NULL,
        email TEXT UNIQUE,
        phone TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Patients table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS patients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        dob TEXT NOT NULL,
        gender TEXT NOT NULL,
        address TEXT,
        phone TEXT,
        email TEXT,
        emergency_contact TEXT,
        blood_type TEXT,
        allergies TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Appointments table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS appointments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER NOT NULL,
        doctor_id INTEGER NOT NULL,
        appointment_date TEXT NOT NULL,
        appointment_time TEXT NOT NULL,
        status TEXT NOT NULL,
        reason TEXT,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (patient_id) REFERENCES patients (id),
        FOREIGN KEY (doctor_id) REFERENCES users (id)
    )
    ''')
    
    # Medical records table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS medical_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER NOT NULL,
        doctor_id INTEGER NOT NULL,
        visit_date TEXT NOT NULL,
        symptoms TEXT,
        diagnosis TEXT,
        treatment TEXT,
        prescription TEXT,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (patient_id) REFERENCES patients (id),
        FOREIGN KEY (doctor_id) REFERENCES users (id)
    )
    ''')
    
    # Create admin user if not exists
    cursor.execute("SELECT * FROM users WHERE username = 'admin'")
    if not cursor.fetchone():
        admin_password = generate_password_hash('admin123')
        cursor.execute('''
        INSERT INTO users (username, password, name, role, email) 
        VALUES (?, ?, ?, ?, ?)
        ''', ('admin', admin_password, 'Administrator', 'admin', 'admin@clinic.com'))
    
    conn.commit()
    conn.close()

# Initialize database on startup
if not os.path.exists(DB_PATH):
    init_db()

# Authentication decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Role-based access control decorator
def role_required(roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_role' not in session or session['user_role'] not in roles:
                flash('You do not have permission to access this page', 'danger')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.template_filter('strptime')
def _jinja2_filter_strptime(date_string, format_string):
    return datetime.strptime(date_string, format_string)

# Routes
@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session['user_role'] = user['role']
            conn.close()
            flash(f'Welcome back, {user["name"]}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'danger')
        
        conn.close()
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('home'))

@app.route('/dashboard')
@login_required
def dashboard():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get counts for dashboard
    cursor.execute("SELECT COUNT(*) as patient_count FROM patients")
    patient_count = cursor.fetchone()['patient_count']
    
    cursor.execute("SELECT COUNT(*) as appointment_count FROM appointments WHERE appointment_date = date('now')")
    today_appointments = cursor.fetchone()['appointment_count']
    
    cursor.execute("""
    SELECT a.id, p.name as patient_name, u.name as doctor_name, 
           a.appointment_date, a.appointment_time, a.status, a.reason
    FROM appointments a
    JOIN patients p ON a.patient_id = p.id
    JOIN users u ON a.doctor_id = u.id
    WHERE a.appointment_date = date('now')
    ORDER BY a.appointment_time
    """)
    appointments = cursor.fetchall()
    
    conn.close()
    
    return render_template('dashboard.html',
                          patient_count=patient_count,
                          today_appointments=today_appointments,
                          appointments=appointments)

# Patient Routes
@app.route('/patients')
@login_required
def patients():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    search = request.args.get('search', '')
    if search:
        cursor.execute("""
        SELECT * FROM patients 
        WHERE name LIKE ? OR phone LIKE ? OR email LIKE ?
        ORDER BY name
        """, (f'%{search}%', f'%{search}%', f'%{search}%'))
    else:
        cursor.execute("SELECT * FROM patients ORDER BY name")
    
    patients = cursor.fetchall()
    conn.close()
    
    return render_template('patients.html', patients=patients, search=search)

@app.route('/patients/add', methods=['GET', 'POST'])
@login_required
def add_patient():
    if request.method == 'POST':
        name = request.form['name']
        dob = request.form['dob']
        gender = request.form['gender']
        address = request.form['address']
        phone = request.form['phone']
        email = request.form['email']
        emergency_contact = request.form['emergency_contact']
        blood_type = request.form['blood_type']
        allergies = request.form['allergies']
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO patients (name, dob, gender, address, phone, email, emergency_contact, blood_type, allergies)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, dob, gender, address, phone, email, emergency_contact, blood_type, allergies))
        
        conn.commit()
        conn.close()
        
        flash('Patient added successfully', 'success')
        return redirect(url_for('patients'))
    
    return render_template('add_patient.html')

@app.route('/patients/<int:id>')
@login_required
def view_patient(id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM patients WHERE id = ?", (id,))
    patient = cursor.fetchone()
    
    if not patient:
        conn.close()
        flash('Patient not found', 'danger')
        return redirect(url_for('patients'))
    
    # Get patient's appointments
    cursor.execute("""
    SELECT a.*, u.name as doctor_name
    FROM appointments a
    JOIN users u ON a.doctor_id = u.id
    WHERE a.patient_id = ?
    ORDER BY a.appointment_date DESC, a.appointment_time DESC
    """, (id,))
    appointments = cursor.fetchall()
    
    # Get patient's medical records
    cursor.execute("""
    SELECT m.*, u.name as doctor_name
    FROM medical_records m
    JOIN users u ON m.doctor_id = u.id
    WHERE m.patient_id = ?
    ORDER BY m.visit_date DESC
    """, (id,))
    records = cursor.fetchall()
    
    conn.close()
    
    return render_template('view_patient.html', 
                           patient=patient, 
                           appointments=appointments, 
                           records=records)

@app.route('/patients/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_patient(id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM patients WHERE id = ?", (id,))
    patient = cursor.fetchone()
    
    if not patient:
        conn.close()
        flash('Patient not found', 'danger')
        return redirect(url_for('patients'))
    
    if request.method == 'POST':
        name = request.form['name']
        dob = request.form['dob']
        gender = request.form['gender']
        address = request.form['address']
        phone = request.form['phone']
        email = request.form['email']
        emergency_contact = request.form['emergency_contact']
        blood_type = request.form['blood_type']
        allergies = request.form['allergies']
        
        cursor.execute('''
        UPDATE patients 
        SET name = ?, dob = ?, gender = ?, address = ?, phone = ?, 
            email = ?, emergency_contact = ?, blood_type = ?, allergies = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        ''', (name, dob, gender, address, phone, email, emergency_contact, 
              blood_type, allergies, id))
        
        conn.commit()
        flash('Patient updated successfully', 'success')
        
        return redirect(url_for('view_patient', id=id))
    
    conn.close()
    return render_template('edit_patient.html', patient=patient)

# Appointment Routes
@app.route('/appointments')
@login_required
def appointments():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    date_filter = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    status_filter = request.args.get('status', 'all')
    doctor_filter = request.args.get('doctor', 'all')
    
    query = """
    SELECT a.*, p.name as patient_name, u.name as doctor_name
    FROM appointments a
    JOIN patients p ON a.patient_id = p.id
    JOIN users u ON a.doctor_id = u.id
    WHERE 1=1
    """
    params = []
    
    if date_filter:
        query += " AND a.appointment_date = ?"
        params.append(date_filter)
    
    if status_filter != 'all':
        query += " AND a.status = ?"
        params.append(status_filter)
    
    if doctor_filter != 'all':
        query += " AND a.doctor_id = ?"
        params.append(doctor_filter)
    
    query += " ORDER BY a.appointment_time"
    
    cursor.execute(query, params)
    appointments = cursor.fetchall()
    
    # Get doctors for filter
    cursor.execute("SELECT id, name FROM users WHERE role = 'doctor' OR role = 'admin'")
    doctors = cursor.fetchall()
    
    conn.close()
    
    return render_template('appointments.html', 
                           appointments=appointments,
                           date_filter=date_filter,
                           status_filter=status_filter,
                           doctor_filter=doctor_filter,
                           doctors=doctors)

@app.route('/appointments/schedule', methods=['GET', 'POST'])
@login_required
def schedule_appointment():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get all patients and doctors
    cursor.execute("SELECT id, name FROM patients ORDER BY name")
    patients = cursor.fetchall()
    
    cursor.execute("SELECT id, name FROM users WHERE role = 'doctor' OR role = 'admin' ORDER BY name")
    doctors = cursor.fetchall()
    
    if request.method == 'POST':
        patient_id = request.form['patient_id']
        doctor_id = request.form['doctor_id']
        appointment_date = request.form['appointment_date']
        appointment_time = request.form['appointment_time']
        status = request.form['status']
        reason = request.form['reason']
        notes = request.form['notes']
        
        cursor.execute('''
        INSERT INTO appointments 
        (patient_id, doctor_id, appointment_date, appointment_time, status, reason, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (patient_id, doctor_id, appointment_date, appointment_time, status, reason, notes))
        
        conn.commit()
        conn.close()
        
        flash('Appointment scheduled successfully', 'success')
        return redirect(url_for('appointments'))
    
    conn.close()
    return render_template('schedule_appointment.html', patients=patients, doctors=doctors)

@app.route('/appointments/<int:id>')
@login_required
def view_appointment(id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
    SELECT a.*, p.name as patient_name, p.phone as patient_phone, u.name as doctor_name
    FROM appointments a
    JOIN patients p ON a.patient_id = p.id
    JOIN users u ON a.doctor_id = u.id
    WHERE a.id = ?
    """, (id,))
    
    appointment = cursor.fetchone()
    
    if not appointment:
        conn.close()
        flash('Appointment not found', 'danger')
        return redirect(url_for('appointments'))
    
    conn.close()
    return render_template('view_appointment.html', appointment=appointment)

@app.route('/appointments/<int:id>/update', methods=['GET', 'POST'])
@login_required
def update_appointment(id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
    SELECT a.*, p.name as patient_name, u.name as doctor_name
    FROM appointments a
    JOIN patients p ON a.patient_id = p.id
    JOIN users u ON a.doctor_id = u.id
    WHERE a.id = ?
    """, (id,))
    
    appointment = cursor.fetchone()
    
    if not appointment:
        conn.close()
        flash('Appointment not found', 'danger')
        return redirect(url_for('appointments'))
    
    # Get all doctors
    cursor.execute("SELECT id, name FROM users WHERE role = 'doctor' OR role = 'admin' ORDER BY name")
    doctors = cursor.fetchall()
    
    if request.method == 'POST':
        doctor_id = request.form['doctor_id']
        appointment_date = request.form['appointment_date']
        appointment_time = request.form['appointment_time']
        status = request.form['status']
        reason = request.form['reason']
        notes = request.form['notes']
        
        cursor.execute('''
        UPDATE appointments 
        SET doctor_id = ?, appointment_date = ?, appointment_time = ?, 
            status = ?, reason = ?, notes = ?
        WHERE id = ?
        ''', (doctor_id, appointment_date, appointment_time, status, reason, notes, id))
        
        conn.commit()
        flash('Appointment updated successfully', 'success')
        
        return redirect(url_for('view_appointment', id=id))
    
    conn.close()
    return render_template('update_appointment.html', appointment=appointment, doctors=doctors)

# Medical Records Routes
@app.route('/records/add/<int:patient_id>', methods=['GET', 'POST'])
@login_required
@role_required(['admin', 'doctor'])
def add_medical_record(patient_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM patients WHERE id = ?", (patient_id,))
    patient = cursor.fetchone()
    
    if not patient:
        conn.close()
        flash('Patient not found', 'danger')
        return redirect(url_for('patients'))
    
    # Get doctors for selection
    cursor.execute("SELECT id, name FROM users WHERE role = 'doctor' OR role = 'admin' ORDER BY name")
    doctors = cursor.fetchall()
    
    if request.method == 'POST':
        doctor_id = request.form['doctor_id']
        visit_date = request.form['visit_date']
        symptoms = request.form['symptoms']
        diagnosis = request.form['diagnosis']
        treatment = request.form['treatment']
        prescription = request.form['prescription']
        notes = request.form['notes']
        
        cursor.execute('''
        INSERT INTO medical_records 
        (patient_id, doctor_id, visit_date, symptoms, diagnosis, 
         treatment, prescription, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (patient_id, doctor_id, visit_date, symptoms, diagnosis, 
              treatment, prescription, notes))
        
        conn.commit()
        conn.close()
        
        flash('Medical record added successfully', 'success')
        return redirect(url_for('view_patient', id=patient_id))
    
    conn.close()
    return render_template('add_medical_record.html', patient=patient, doctors=doctors)

@app.route('/records/<int:id>')
@login_required
def view_medical_record(id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
    SELECT m.*, p.name as patient_name, u.name as doctor_name
    FROM medical_records m
    JOIN patients p ON m.patient_id = p.id
    JOIN users u ON m.doctor_id = u.id
    WHERE m.id = ?
    """, (id,))
    
    record = cursor.fetchone()
    
    if not record:
        conn.close()
        flash('Medical record not found', 'danger')
        return redirect(url_for('patients'))
    
    conn.close()
    return render_template('view_medical_record.html', record=record)

# Staff Management Routes
@app.route('/staff')
@login_required
@role_required(['admin'])
def staff():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users ORDER BY role, name")
    staff = cursor.fetchall()
    
    conn.close()
    return render_template('staff.html', staff=staff)

@app.route('/staff/add', methods=['GET', 'POST'])
@login_required
@role_required(['admin'])
def add_staff():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        name = request.form['name']
        role = request.form['role']
        email = request.form['email']
        phone = request.form['phone']
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
            INSERT INTO users (username, password, name, role, email, phone)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (username, password, name, role, email, phone))
            
            conn.commit()
            flash('Staff member added successfully', 'success')
            return redirect(url_for('staff'))
        
        except sqlite3.IntegrityError:
            flash('Username or email already exists', 'danger')
        
        finally:
            conn.close()
    
    return render_template('add_staff.html')

@app.route('/staff/<int:id>')
@login_required
@role_required(['admin'])
def view_staff(id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE id = ?", (id,))
    staff = cursor.fetchone()
    
    if not staff:
        conn.close()
        flash('Staff member not found', 'danger')
        return redirect(url_for('staff'))
    
    conn.close()
    return render_template('view_staff.html', staff=staff)

@app.route('/staff/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@role_required(['admin'])
def edit_staff(id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE id = ?", (id,))
    staff = cursor.fetchone()
    
    if not staff:
        conn.close()
        flash('Staff member not found', 'danger')
        return redirect(url_for('staff'))
    
    if request.method == 'POST':
        name = request.form['name']
        role = request.form['role']
        email = request.form['email']
        phone = request.form['phone']
        
        # Check if password needs to be updated
        password_update = ''
        password_param = []
        
        if request.form['password']:
            password_update = ', password = ?'
            password_param = [generate_password_hash(request.form['password'])]
        
        try:
            cursor.execute(f'''
            UPDATE users 
            SET name = ?, role = ?, email = ?, phone = ? {password_update}
            WHERE id = ?
            ''', [name, role, email, phone] + password_param + [id])
            
            conn.commit()
            flash('Staff member updated successfully', 'success')
            return redirect(url_for('view_staff', id=id))
        
        except sqlite3.IntegrityError:
            flash('Email already exists', 'danger')
        
        finally:
            conn.close()
    
    conn.close()
    return render_template('edit_staff.html', staff=staff)

# Reports Routes
@app.route('/reports')
@login_required
@role_required(['admin', 'doctor'])
def reports():
    return render_template('reports.html')

@app.route('/reports/appointments')
@login_required
@role_required(['admin', 'doctor'])
def appointment_reports():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    start_date = request.args.get('start_date', datetime.now().strftime('%Y-%m-01'))
    end_date = request.args.get('end_date', datetime.now().strftime('%Y-%m-%d'))
    status = request.args.get('status', 'all')
    doctor_id = request.args.get('doctor_id', 'all')
    
    query = """
    SELECT a.*, p.name as patient_name, u.name as doctor_name
    FROM appointments a
    JOIN patients p ON a.patient_id = p.id
    JOIN users u ON a.doctor_id = u.id
    WHERE a.appointment_date BETWEEN ? AND ?
    """
    params = [start_date, end_date]
    
    if status != 'all':
        query += " AND a.status = ?"
        params.append(status)
    
    if doctor_id != 'all':
        query += " AND a.doctor_id = ?"
        params.append(doctor_id)
    
    query += " ORDER BY a.appointment_date, a.appointment_time"
    
    cursor.execute(query, params)
    appointments = cursor.fetchall()
    
    # Get status counts
    cursor.execute("""
    SELECT status, COUNT(*) as count
    FROM appointments
    WHERE appointment_date BETWEEN ? AND ?
    GROUP BY status
    """, [start_date, end_date])
    status_counts = cursor.fetchall()
    
    # Get doctors for filter
    cursor.execute("SELECT id, name FROM users WHERE role = 'doctor' OR role = 'admin'")
    doctors = cursor.fetchall()
    
    conn.close()
    
    return render_template('appointment_reports.html',
                          appointments=appointments,
                          start_date=start_date,
                          end_date=end_date,
                          status=status,
                          doctor_id=doctor_id,
                          status_counts=status_counts,
                          doctors=doctors)

@app.route('/reports/patients')
@login_required
@role_required(['admin', 'doctor'])
def patient_reports():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get patient demographics
    cursor.execute("""
    SELECT gender, COUNT(*) as count
    FROM patients
    GROUP BY gender
    """)
    gender_counts = cursor.fetchall()
    
    # Get new patients by month (current year)
    cursor.execute("""
    SELECT strftime('%m', created_at) as month, COUNT(*) as count
    FROM patients
    WHERE strftime('%Y', created_at) = strftime('%Y', 'now')
    GROUP BY month
    ORDER BY month
    """)
    new_patients = cursor.fetchall()
    
    conn.close()
    
    return render_template('patient_reports.html',
                          gender_counts=gender_counts,
                          new_patients=new_patients)

# Profile Route
@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],))
    user = cursor.fetchone()
    
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        
        # Check if password needs to be updated
        password_update = ''
        password_param = []
        
        if request.form['new_password'] and check_password_hash(user['password'], request.form['current_password']):
            password_update = ', password = ?'
            password_param = [generate_password_hash(request.form['new_password'])]
        elif request.form['new_password']:
            flash('Current password is incorrect', 'danger')
            conn.close()
            return redirect(url_for('profile'))
        
        try:
            cursor.execute(f'''
            UPDATE users 
            SET name = ?, email = ?, phone = ? {password_update}
            WHERE id = ?
            ''', [name, email, phone] + password_param + [session['user_id']])
            
            conn.commit()
            session['user_name'] = name
            flash('Profile updated successfully', 'success')
        
        except sqlite3.IntegrityError:
            flash('Email already exists', 'danger')
        
        finally:
            conn.close()
            return redirect(url_for('profile'))
    
    conn.close()
    return render_template('profile.html', user=user)

# Error handlers
@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500

# Run the app
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port='3456')

