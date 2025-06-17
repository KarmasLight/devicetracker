from flask import Flask, render_template, request, redirect, url_for, flash, send_file, make_response, session
import sqlite3
from datetime import datetime
import pytz
import os
import csv
from io import StringIO
from datetime import datetime as dt
from functools import wraps
from country_codes import COUNTRIES

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this to a secure random key in production

# Ensure session cookies work over HTTPS
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

from werkzeug.middleware.proxy_fix import ProxyFix
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# ---- Authentication ----

# Hardcoded user for demo
USERS = {
    'convention2025': 'Event2025!',
    'admin': 'Kangen2025!'
}

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        if USERS.get(username) == password:
            session['logged_in'] = True
            session['username'] = username
            flash('Login successful!', 'success')
            return redirect(url_for('devices'))
        else:
            flash('Invalid username or password.', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('login'))

# Custom template filters
@app.template_filter('format_datetime')
@app.template_filter('format_phone_display')
def format_phone_display(phone):
    """
    Format phone number for display using phonenumbers library for country-aware formatting.
    Fallback to old logic if parsing fails or phonenumbers is not available.
    """
    if not isinstance(phone, str):
        return phone
    if not phone:
        return ""
    try:
        import phonenumbers
        # Try to parse as E.164, fallback to US if no country code
        try:
            parsed = phonenumbers.parse(phone, None)
        except Exception:
            parsed = phonenumbers.parse(phone, "US")
        if phonenumbers.is_possible_number(parsed) or phonenumbers.is_valid_number(parsed):
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
    except Exception:
        pass
    # Fallback to previous logic
    digits = ''.join(c for c in phone if c.isdigit())
    if phone.startswith('+'):
        if len(digits) > 11:
            country_len = len(digits) - 10
            country = digits[:country_len]
            rest = digits[country_len:]
            if len(rest) == 10:
                return f'+{country}-{rest[0:3]}-{rest[3:6]}-{rest[6:10]}'
            else:
                return f'+{country}-{rest}'
        elif len(digits) == 11:
            return f'+{digits[0]}-{digits[1:4]}-{digits[4:7]}-{digits[7:11]}'
        elif len(digits) == 10:
            return f'+1-{digits[0:3]}-{digits[3:6]}-{digits[6:10]}'
        else:
            return phone
    elif len(digits) == 10:
        return f'+1-{digits[0:3]}-{digits[3:6]}-{digits[6:10]}'
    else:
        return phone



def format_datetime_filter(value, format='%Y-%m-%d %I:%M %p'):
    """
    Format a UTC datetime string or timestamp to local time (US Pacific) as 'YYYY-MM-DD HH:MM AM/PM'.
    Handles ISO strings with microseconds and timezone offsets.
    """
    if not value:
        return ""
    try:
        utc = pytz.utc
        local_tz = pytz.timezone('US/Pacific')
        dt_obj = None
        if isinstance(value, dt):
            if value.tzinfo is None:
                dt_obj = value.replace(tzinfo=utc)
            else:
                dt_obj = value
        elif isinstance(value, str):
            try:
                # Handle ISO 8601 with microseconds and offset
                import re
                iso_match = re.match(r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?)([+-]\d{2}:\d{2}|Z)?", value)
                if iso_match:
                    from dateutil import parser
                    dt_obj = parser.isoparse(value)
                else:
                    # Try common formats
                    for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d'):
                        try:
                            dt_obj = dt.strptime(value, fmt)
                            dt_obj = dt_obj.replace(tzinfo=utc)
                            break
                        except ValueError:
                            continue
            except Exception:
                pass
        if dt_obj is not None:
            if dt_obj.tzinfo is None:
                dt_obj = dt_obj.replace(tzinfo=utc)
            local_dt = dt_obj.astimezone(local_tz)
            return local_dt.strftime(format)
        return str(value)
    except Exception:
        return str(value)

# Register filter for Jinja as 'format_datetime'
app.jinja_env.filters['format_datetime'] = format_datetime_filter




# Database configuration
DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'headset_tracking.db')

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with app.app_context():
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Create devices table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            barcode TEXT UNIQUE NOT NULL,
            attendee_name TEXT,
            email TEXT,
            phone TEXT,
            check_out_time TEXT,
            check_in_time TEXT,
            notes TEXT
        )
        ''')
        
        # Create audit_log table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            action TEXT NOT NULL,
            barcode TEXT NOT NULL,
            details TEXT
        )
        ''')
        
        conn.commit()
        conn.close()

def format_phone_display(phone):
    """Format phone number for display as +XX-XXX-XXX-XXXX"""
    if not phone:
        return ""
    
    # Remove all non-digit characters
    digits = ''.join(c for c in phone if c.isdigit())
    
    # Format as +XX-XXX-XXX-XXXX
    if len(digits) >= 11:
        return f"+{digits[0]}{digits[1]}-{digits[2:5]}-{digits[5:8]}-{digits[8:12]}"
    elif len(digits) >= 10:
        return f"+1-{digits[0:3]}-{digits[3:6]}-{digits[6:10]}"
    else:
        return phone  # Return as is if not standard length

@app.route('/')
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    # Get counts for the dashboard
    conn = get_db_connection()
    
    # Get total devices
    total_devices = conn.execute('SELECT COUNT(*) FROM devices').fetchone()[0]
    
    # Get checked out devices (checked out but not checked in)
    checked_out = conn.execute(
        'SELECT COUNT(*) FROM devices WHERE check_out_time IS NOT NULL AND check_in_time IS NULL'
    ).fetchone()[0]
    
    # Get checked in devices (either never checked out or checked back in)
    checked_in = total_devices - checked_out
    
    conn.close()
    
    return render_template('base.html', 
                         checked_in=checked_in,
                         checked_out=checked_out,
                         total=total_devices)

@app.route('/check_out', methods=['GET', 'POST'])
@login_required
def check_out():
    if request.method == 'GET':
        conn = get_db_connection()
        total_devices = conn.execute('SELECT COUNT(*) FROM devices').fetchone()[0]
        checked_out = conn.execute(
            'SELECT COUNT(*) FROM devices WHERE check_out_time IS NOT NULL AND check_in_time IS NULL'
        ).fetchone()[0]
        checked_in = total_devices - checked_out
        conn.close()
        return render_template('check_out.html', checked_in=checked_in, checked_out=checked_out, total=total_devices, barcode='', attendee_name='', email='', phone='', notes='', errors={}, countries=COUNTRIES, country_code='+1')
    if request.method == 'POST':
        barcode = request.form.get('barcode', '').strip()
        attendee_name = request.form.get('attendee_name', '').strip()
        email = request.form.get('email', '').strip()
        country_code = request.form.get('country_code', '').strip() or '+1'
        phone = request.form.get('phone', '').strip()
        notes = request.form.get('notes', '').strip()
        
        # Validate required fields (field-level)
        errors = {}
        if not barcode:
            errors['barcode'] = 'Barcode is required.'
        if not attendee_name:
            errors['attendee_name'] = 'Attendee name is required.'
        if not email:
            errors['email'] = 'Email is required.'
        # Basic email validation
        elif '@' not in email or '.' not in email.split('@')[1]:
            errors['email'] = 'Please enter a valid email address.'
        if not phone:
            errors['phone'] = 'Phone number is required.'
        if errors:
            conn = get_db_connection()
            total_devices = conn.execute('SELECT COUNT(*) FROM devices').fetchone()[0]
            checked_out = conn.execute(
                'SELECT COUNT(*) FROM devices WHERE check_out_time IS NOT NULL AND check_in_time IS NULL'
            ).fetchone()[0]
            checked_in = total_devices - checked_out
            conn.close()
            return render_template('check_out.html', checked_in=checked_in, checked_out=checked_out, total=total_devices, barcode=barcode, attendee_name=attendee_name, email=email, phone=phone, notes=notes, errors=errors, countries=COUNTRIES, country_code=country_code)
        
        # Format phone number for storage (E.164 format)
        if phone:
            # Remove all non-digit characters
            phone_digits = ''.join(c for c in phone if c.isdigit())
            if phone_digits:
                # Always prepend the selected country code (if not already present)
                if not phone_digits.startswith(country_code.replace('+','')):
                    phone = f"{country_code}{phone_digits}"
                else:
                    phone = f"+{phone_digits}"
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Clean the barcode (remove any whitespace or newlines that might be added by the scanner)
            barcode = barcode.strip()
            
            # Check if device exists
            device = cursor.execute('SELECT * FROM devices WHERE barcode = ?', (barcode,)).fetchone()
            current_time = datetime.now(pytz.utc).isoformat()
            
            if device and device['check_in_time'] is None:
                flash('This device is already checked out', 'error')
                conn.close()
                return redirect(url_for('check_out'))
                
            if device:
                # Update existing device
                cursor.execute('''
                    UPDATE devices 
                    SET attendee_name = ?, email = ?, phone = ?, 
                        check_out_time = ?, check_in_time = NULL, notes = ?
                    WHERE barcode = ?
                ''', (attendee_name, email, phone, current_time, request.form.get('notes', ''), barcode))
                action = 'updated'
            else:
                # Insert new device
                cursor.execute('''
                    INSERT INTO devices (barcode, attendee_name, email, phone, check_out_time, notes)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (barcode, attendee_name, email, phone, current_time, request.form.get('notes', '')))
                action = 'added'
            
            # Log the checkout
            cursor.execute('''
                INSERT INTO audit_log (timestamp, action, barcode, details)
                VALUES (?, ?, ?, ?)
            ''', (current_time, 'check_out', barcode, 
                 f'Checked out to {attendee_name} ({email})'))
            
            conn.commit()
            flash(f'Device {barcode} {action} and checked out successfully!', 'success')
            return redirect(url_for('check_out'))
            
        except sqlite3.IntegrityError:
            conn.rollback()
            flash('An error occurred. Please try again.', 'error')
            # Get counts for error render
            conn2 = get_db_connection()
            total_devices = conn2.execute('SELECT COUNT(*) FROM devices').fetchone()[0]
            checked_out = conn2.execute(
                'SELECT COUNT(*) FROM devices WHERE check_out_time IS NOT NULL AND check_in_time IS NULL'
            ).fetchone()[0]
            checked_in = total_devices - checked_out
            conn2.close()
            return render_template('check_out.html', checked_in=checked_in, checked_out=checked_out, total=total_devices, barcode=barcode, attendee_name=attendee_name, email=email, phone=phone, notes=notes, countries=COUNTRIES, country_code=country_code)
            
        finally:
            conn.close()
    
    # For GET request, show the check out form
    # Get counts
    conn = get_db_connection()
    total_devices = conn.execute('SELECT COUNT(*) FROM devices').fetchone()[0]
    checked_out = conn.execute(
        'SELECT COUNT(*) FROM devices WHERE check_out_time IS NOT NULL AND check_in_time IS NULL'
    ).fetchone()[0]
    checked_in = total_devices - checked_out
    conn.close()
    return render_template('check_out.html', checked_in=checked_in, checked_out=checked_out, total=total_devices, barcode=locals().get('barcode', ''), attendee_name=locals().get('attendee_name', ''), email=locals().get('email', ''), phone=locals().get('phone', ''), notes=locals().get('notes', ''), countries=COUNTRIES)

import logging

@app.route('/check_in', methods=['GET', 'POST'])
@login_required
def check_in():
    logging.info('Entered check_in route with method: %s', request.method)
    conn = get_db_connection()
    total_devices = conn.execute('SELECT COUNT(*) FROM devices').fetchone()[0]
    checked_out = conn.execute(
        'SELECT COUNT(*) FROM devices WHERE check_out_time IS NOT NULL AND check_in_time IS NULL'
    ).fetchone()[0]
    checked_in = total_devices - checked_out

    if request.method == 'POST':
        barcode = request.form.get('barcode', '').strip()
        logging.info('POST barcode: %s', barcode)

        if not barcode:
            flash('Please enter a barcode', 'error')
            conn.close()
            logging.warning('Barcode missing on POST')
            return redirect(url_for('check_in'))

        try:
            barcode = barcode.strip()
            device = conn.execute('''
                SELECT * FROM devices 
                WHERE barcode = ? AND check_out_time IS NOT NULL AND check_in_time IS NULL
            ''', (barcode,)).fetchone()
            if not device:
                flash('Device not found or already checked in', 'error')
                conn.close()
                logging.warning('Device not found or already checked in: %s', barcode)
                return redirect(url_for('check_in'))

            current_time = datetime.now(pytz.utc).isoformat()
            conn.execute('''
                UPDATE devices 
                SET check_in_time = ?
                WHERE barcode = ?
            ''', (current_time, barcode))

            conn.execute('''
                INSERT INTO audit_log (timestamp, action, barcode, details)
                VALUES (?, ?, ?, ?)
            ''', (current_time, 'check_in', barcode, 
                 f'Checked in by user: {request.remote_addr}'))

            conn.commit()

            device = conn.execute('SELECT * FROM devices WHERE barcode = ?', (barcode,)).fetchone()
            total_devices = conn.execute('SELECT COUNT(*) FROM devices').fetchone()[0]
            checked_out = conn.execute(
                'SELECT COUNT(*) FROM devices WHERE check_out_time IS NOT NULL AND check_in_time IS NULL'
            ).fetchone()[0]
            checked_in = total_devices - checked_out

            flash(
                f'Device {barcode} checked in successfully! '
                f'Checked out to {device["attendee_name"]} ({device["email"]})', 
                'success'
            )
            session['checked_in_barcode'] = barcode
            logging.info('Check-in success for barcode: %s', barcode)
            return redirect(url_for('check_in'))
        except Exception as e:
            conn.rollback()
            logging.exception('Error during check-in')
            flash(f'An error occurred: {str(e)}', 'error')
            return redirect(url_for('check_in'))

    checked_in_device = None
    barcode = ''
    if 'checked_in_barcode' in session:
        barcode = session.pop('checked_in_barcode')
        device = conn.execute('SELECT * FROM devices WHERE barcode = ?', (barcode,)).fetchone()
        if device:
            checked_in_device = dict(device)
            logging.info('Displaying checked-in device info for barcode: %s', barcode)
    conn.close()
    return render_template('check_in.html',
                         checked_in=checked_in,
                         checked_out=checked_out,
                         total=total_devices,
                         checked_in_device=checked_in_device)

@app.route('/clear_devices', methods=['POST'])
@login_required
def clear_devices():
    admin_password = request.form.get('admin_password', '')
    # TODO: Move this to config or env variable for production
    CORRECT_PASSWORD = 'admin123'
    if admin_password != CORRECT_PASSWORD:
        flash('Incorrect admin password. Device list was not cleared.', 'error')
        return redirect(url_for('devices'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM devices')
    conn.commit()
    conn.close()
    flash('Device list cleared successfully!', 'success')
    return redirect(url_for('devices'))


@app.route('/devices')
@login_required
def devices():
    search = request.args.get('search', '').strip()
    
    conn = get_db_connection()
    
    # Build the query based on search
    query = '''
        SELECT barcode, attendee_name, email, phone, 
               check_out_time, check_in_time, notes
        FROM devices
    '''
    
    params = []
    
    if search:
        query += ' WHERE barcode LIKE ? OR attendee_name LIKE ? OR email LIKE ?'
        search_term = f'%{search}%'
        params = [search_term, search_term, search_term]
    
    query += ' ORDER BY check_out_time DESC'
    
    # Execute the query
    devices = conn.execute(query, params).fetchall()
    
    # Format phone numbers and datetimes for display
    from dateutil import parser
    formatted_devices = []
    for device in devices:
        device_dict = dict(device)
        # Parse datetimes for Jinja filter compatibility first
        for field in ['check_out_time', 'check_in_time']:
            value = device_dict.get(field)
            if isinstance(value, str) and value:
                try:
                    device_dict[field] = parser.isoparse(value)
                except Exception:
                    device_dict[field] = value
            else:
                device_dict[field] = value if value else None
        # Now handle phone formatting (ensure phone is not a datetime)
        phone_val = device_dict.get('phone')
        if isinstance(phone_val, str):
            device_dict['phone'] = format_phone_display(phone_val) if phone_val else ''
        else:
            device_dict['phone'] = phone_val if phone_val else ''
        formatted_devices.append(device_dict)


    
    # Get counts for the header
    total_devices = conn.execute('SELECT COUNT(*) FROM devices').fetchone()[0]
    checked_out = conn.execute(
        'SELECT COUNT(*) FROM devices WHERE check_out_time IS NOT NULL AND check_in_time IS NULL'
    ).fetchone()[0]
    checked_in = total_devices - checked_out
    
    conn.close()
    
    return render_template('devices.html', 
                         devices=formatted_devices, 
                         search=search,
                         checked_in=checked_in,
                         checked_out=checked_out,
                         total=total_devices)

@app.route('/export')
@login_required
def export():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get all devices data
        cursor.execute('''
            SELECT 
                barcode,
                attendee_name,
                email,
                phone,
                check_out_time,
                check_in_time,
                notes
            FROM devices
            ORDER BY check_out_time DESC
        ''')
        
        # Create CSV in memory
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'Barcode', 'Attendee Name', 'Email', 'Phone', 
            'Check Out Time', 'Check In Time', 'Notes'
        ])
        
        # Write data rows
        def excel_safe(value):
            if value is None or value == "":
                return ""
            return f'="{value}"'

        for row in cursor.fetchall():
            # Format phone number for export
            phone = format_phone_display(row[3]) if row[3] else ''
            # Format check out/in times for export (US/Pacific, readable)
            check_out_time = format_datetime_filter(row[4]) if row[4] else ''
            check_in_time = format_datetime_filter(row[5]) if row[5] else ''
            writer.writerow([
                excel_safe(row[0]),  # barcode as text
                row[1],  # attendee_name
                row[2],  # email
                excel_safe(phone),   # phone as text
                check_out_time,  # formatted check_out_time
                check_in_time,   # formatted check_in_time
                row[6]   # notes
            ])
        
        # Prepare the response
        output.seek(0)
        response = make_response(output.getvalue())
        
        # Set the filename with timestamp
        filename = f'headset_tracker_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        
        # Set headers for file download
        response.headers['Content-Disposition'] = f'attachment; filename={filename}'
        response.headers['Content-type'] = 'text/csv'
        
        return response
        
    except Exception as e:
        flash(f"Error exporting data: {str(e)}", 'error')
        return redirect(url_for('devices'))
    finally:
        conn.close()

@app.route('/init_db')
def init_db_route():
    try:
        init_db()
        flash('Database initialized successfully!', 'success')
    except Exception as e:
        flash(f'Error initializing database: {str(e)}', 'error')
    
    return redirect(url_for('index'))

if __name__ == '__main__':
    # Create database and tables if they don't exist
    init_db()
    
    # Run the app
    app.run(debug=True, host='0.0.0.0', port=5000)
