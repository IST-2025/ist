import os
import smtplib
import uuid
import requests
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Blueprint, render_template, request, flash, redirect, url_for, send_file, jsonify
from werkzeug.utils import secure_filename
from sqlalchemy import inspect, text
from fpdf import FPDF
from .models import Contact, ProjectRequest, JobApplication, InternshipApplication, CertificateRecord
from . import db
import tempfile

public_pages = Blueprint('public_pages', __name__, template_folder='templates', static_folder='static')

def send_admin_notification(subject, body):
    sender_email = os.environ.get('MAIL_USERNAME')
    sender_password = os.environ.get('MAIL_APP_PASSWORD')
    recipient_email = "inovatesolutiontechnology@gmail.com"

    if not sender_email or not sender_password:
        return

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
    except Exception:
        pass

def upload_to_vercel_blob(file_obj):
    token = os.getenv('BLOB_READ_WRITE_TOKEN')
    if not token:
        raise Exception("Vercel Blob Token is missing from Environment Variables.")
        
    clean_filename = secure_filename(file_obj.filename)
    unique_filename = f"{str(uuid.uuid4())[:8]}_{clean_filename}"
    
    url = f"https://blob.vercel-storage.com/{unique_filename}"
    headers = {
        "authorization": f"Bearer {token}",
        "x-api-version": "7"
    }
    
    response = requests.put(url, data=file_obj.read(), headers=headers)
    if response.status_code != 200:
        raise Exception(f"Vercel API Error {response.status_code}: {response.text}")
    return response.json().get('url')


# ==========================================
# PUBLIC ROUTES & SEO
# ==========================================
@public_pages.route('/')
def index():
    return render_template('index.html', 
                           page_title="Inovate Solution Technology | Madurai IT Experts",
                           page_desc="Leading IT firm in Madurai providing custom software, Cloud, and DevOps solutions.",
                           page_keywords="IT company Madurai, software development, DevOps services, cloud solutions")

@public_pages.route('/about')
def about():
    return render_template('about.html', 
                           page_title="About Us | Inovate Solution Technology",
                           page_desc="Learn more about our mission to deliver cutting-edge digital solutions.",
                           page_keywords="about IST, tech company Madurai, IT experts India")

@public_pages.route('/journey')
def journey():
    return render_template('journey.html', 
                           page_title="Our Journey | Inovate Solution Technology",
                           page_desc="Discover the story of our growth and achievements.",
                           page_keywords="IST journey, tech company history, Madurai IT firm")

@public_pages.route('/services')
def services():
    return render_template('services.html', 
                           page_title="Cloud & DevOps Services | IST",
                           page_desc="Explore our specialized services in cloud infrastructure and DevOps automation.",
                           page_keywords="cloud infrastructure, DevOps automation, IT consulting Madurai")

@public_pages.route('/products')
def products():
    return render_template('products.html')

@public_pages.route('/privacy-policy')
def privacy_policy():
    return render_template('privacy-policy.html')

@public_pages.route('/terms')
def terms():
    return render_template('terms.html')


# ==========================================
# FORM SUBMISSION ROUTES
# ==========================================
@public_pages.route('/interns', methods=['GET', 'POST'])
def interns():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        domain = request.form.get('domain')
        college = request.form.get('college')
        
        resume_file = request.files.get('resume')
        resume_url = ""

        if not name or not email or not phone or not domain or not college:
            flash("Please fill out all required fields.", "error")
            return redirect(url_for('public_pages.interns') + '#apply-internship')

        if resume_file and resume_file.filename != '':
            try:
                resume_url = upload_to_vercel_blob(resume_file)
            except Exception as e:
                flash(f"Cloud Upload Failed: {str(e)}", "error")
                return redirect(url_for('public_pages.interns') + '#apply-internship')
        else:
            flash("Please upload a valid resume (PDF or DOC).", "error")
            return redirect(url_for('public_pages.interns') + '#apply-internship')

        new_intern = InternshipApplication(name=name, email=email, phone=phone, domain=domain, college=college, resume_filename=resume_url)
        
        try:
            db.session.add(new_intern)
            db.session.commit()
            email_body = f"New Internship Application:\nName: {name}\nEmail: {email}\nPhone: {phone}\nDomain: {domain}\nCollege: {college}\nResume: {resume_url}"
            send_admin_notification("New Internship Application - IST", email_body)
            flash("Your internship application has been submitted successfully!", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"System Error (Database): {str(e)}", "error")
            
        return redirect(url_for('public_pages.interns') + '#apply-internship')
    return render_template('interns.html')

@public_pages.route('/join-us', methods=['GET', 'POST'])
def join_us():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        position = request.form.get('position')
        message = request.form.get('message')
        
        resume_file = request.files.get('resume')
        resume_url = ""

        if not name or not email or not phone or not position:
            flash("Please fill out all required fields.", "error")
            return redirect(url_for('public_pages.join_us') + '#apply-form')

        if resume_file and resume_file.filename != '':
            try:
                resume_url = upload_to_vercel_blob(resume_file)
            except Exception as e:
                flash(f"Cloud Upload Failed: {str(e)}", "error")
                return redirect(url_for('public_pages.join_us') + '#apply-form')
        else:
            flash("Please upload a valid resume.", "error")
            return redirect(url_for('public_pages.join_us') + '#apply-form')

        new_app = JobApplication(name=name, email=email, phone=phone, position=position, resume_filename=resume_url, message=message)
        
        try:
            db.session.add(new_app)
            db.session.commit()
            email_body = f"New Job Application:\nName: {name}\nEmail: {email}\nPhone: {phone}\nPosition: {position}\nMessage: {message}\nResume: {resume_url}"
            send_admin_notification("New Job Application - IST", email_body)
            flash("Your application has been submitted successfully!", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"System Error (Database): {str(e)}", "error")
            
        return redirect(url_for('public_pages.join_us') + '#apply-form')
    return render_template('join-us.html')

@public_pages.route('/projects', methods=['GET', 'POST'])
def projects():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        college = request.form.get('college')
        domain = request.form.get('domain')
        description = request.form.get('description')
        
        if not name or not email or not phone or not college or not domain or not description:
            flash("Please fill out all fields.", "error")
            return redirect(url_for('public_pages.projects') + '#request-project')

        new_project = ProjectRequest(name=name, email=email, phone=phone, college=college, domain=domain, description=description)
        
        try:
            db.session.add(new_project)
            db.session.commit()
            email_body = f"New Project Request:\nName: {name}\nEmail: {email}\nPhone: {phone}\nCollege: {college}\nDomain: {domain}\nDescription: {description}"
            send_admin_notification("New Project Request - IST", email_body)
            flash("Your project request has been submitted successfully!", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"System Error (Database): {str(e)}", "error")
            
        return redirect(url_for('public_pages.projects') + '#request-project')
    return render_template('clg-projects.html')

@public_pages.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')
        
        if not name or not email or not phone or not message:
            flash("Please fill out all fields.", "error")
            return redirect(url_for('public_pages.contact'))

        new_contact = Contact(name=name, email=email, phone=phone, message=message)
        
        try:
            db.session.add(new_contact)
            db.session.commit()
            email_body = f"New Contact Message:\nName: {name}\nEmail: {email}\nPhone: {phone}\nMessage: {message}"
            send_admin_notification("New Contact Message - IST", email_body)
            flash("Your message has been sent successfully!", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"System Error (Database): {str(e)}", "error")
            
        return redirect(url_for('public_pages.contact'))
    return render_template('contact.html', 
                           page_title="Contact Us | Inovate Solution Technology",
                           page_desc="Get in touch with our team to start your next big tech project.",
                           page_keywords="contact IT company, software agency contact")

# ==========================================
# CERTIFICATE GENERATION ROUTES
# ==========================================

# Define workshop schedules
WORKSHOP_SCHEDULES = {
    'build_ai_agent': {
        'name': 'Build Your Own AI Agent',
        'date': datetime(2026, 7, 30, 10, 0, 0),
        'availability_start': datetime(2026, 7, 29, 10, 0, 0),
        'availability_end': datetime(2026, 7, 31, 10, 0, 0),
        'description': 'Learn to build, deploy, and manage intelligent AI agents from scratch',
        'order': 1
    },
    'visualizing_intelligence': {
        'name': 'Visualising the Intelligence Pipeline',
        'date': datetime(2026, 7, 24, 10, 0, 0),
        'availability_start': datetime(2026, 7, 23, 10, 0, 0),
        'availability_end': datetime(2026, 7, 25, 10, 0, 0),
        'description': 'Learn how raw data is collected, integrated, processed, and transformed into meaningful insights',
        'order': 2
    },
    'prompt_engineering': {
        'name': 'Mastering Prompt Engineering',
        'date': datetime(2026, 6, 12, 10, 0, 0),
        'availability_start': datetime(2026, 6, 12, 10, 0, 0),
        'availability_end': datetime(2026, 6, 13, 10, 0, 0),
        'description': 'Advanced techniques for communicating effectively with Large Language Models',
        'order': 3
    },
    'software_engineering': {
        'name': 'Building Software That Doesn\'t Break',
        'date': datetime(2026, 5, 25, 10, 0, 0),
        'availability_start': datetime(2026, 5, 25, 10, 0, 0),
        'availability_end': datetime(2026, 5, 26, 10, 0, 0),
        'description': 'Master the fundamentals of creating robust and maintainable software',
        'order': 4
    },
    'ai_workflows': {
        'name': 'Automating Workflows with AI',
        'date': datetime(2026, 4, 10, 10, 0, 0),
        'availability_start': datetime(2026, 4, 10, 10, 0, 0),
        'availability_end': datetime(2026, 4, 11, 10, 0, 0),
        'description': 'Streamlining business operations using intelligent AI automation',
        'order': 5
    },
    'fullstack_ai': {
        'name': 'Full Stack AI Development',
        'date': datetime(2026, 3, 18, 10, 0, 0),
        'availability_start': datetime(2026, 3, 18, 10, 0, 0),
        'availability_end': datetime(2026, 3, 19, 10, 0, 0),
        'description': 'Building end-to-end scalable web applications with machine learning',
        'order': 6
    },
    'ai_web_apps': {
        'name': 'AI-Powered Web Apps',
        'date': datetime(2026, 2, 5, 10, 0, 0),
        'availability_start': datetime(2026, 2, 5, 10, 0, 0),
        'availability_end': datetime(2026, 2, 6, 10, 0, 0),
        'description': 'Enhancing frontend frameworks with intelligent AI features and APIs',
        'order': 7
    }
}

@public_pages.route('/workshop-certificate', methods=['GET'])
def workshop_certificate():
    """Display the workshop certificate page with availability status"""
    workshops_status = {}
    current_time = datetime.now()
    
    for key, workshop in WORKSHOP_SCHEDULES.items():
        is_available = workshop['availability_start'] <= current_time <= workshop['availability_end']
        is_upcoming = current_time < workshop['availability_start']
        is_past = current_time > workshop['availability_end']
        
        if is_available:
            category = 'available'
            sort_order = 0
        elif is_upcoming:
            category = 'upcoming'
            sort_order = 1
        else:
            category = 'past'
            sort_order = 2
        
        workshops_status[key] = {
            **workshop,
            'is_available': is_available,
            'is_upcoming': is_upcoming,
            'is_past': is_past,
            'category': category,
            'sort_order': sort_order,
            'date_formatted': workshop['date'].strftime('%d/%m/%Y'),
            'time_remaining': None
        }
        
        if is_upcoming:
            time_diff = workshop['availability_start'] - current_time
            days = time_diff.days
            hours = time_diff.seconds // 3600
            workshops_status[key]['time_remaining'] = f"Opens in {days}d {hours}h"
        elif is_available:
            time_diff = workshop['availability_end'] - current_time
            hours = time_diff.seconds // 3600
            minutes = (time_diff.seconds % 3600) // 60
            workshops_status[key]['time_remaining'] = f"Closes in {hours}h {minutes}m"
    
    sorted_workshops = dict(sorted(
        workshops_status.items(),
        key=lambda x: (x[1]['sort_order'], -x[1]['date'].timestamp())
    ))
    
    return render_template('certificate.html', workshops=sorted_workshops)

@public_pages.route('/api/check-workshop-availability/<workshop_id>', methods=['GET'])
def check_workshop_availability(workshop_id):
    """API endpoint to check if a workshop certificate is available"""
    if workshop_id not in WORKSHOP_SCHEDULES:
        return jsonify({'error': 'Workshop not found'}), 404
    
    workshop = WORKSHOP_SCHEDULES[workshop_id]
    current_time = datetime.now()
    
    is_available = workshop['availability_start'] <= current_time <= workshop['availability_end']
    is_upcoming = current_time < workshop['availability_start']
    
    time_remaining = None
    if is_upcoming:
        time_diff = workshop['availability_start'] - current_time
        time_remaining = f"{time_diff.days}d {time_diff.seconds // 3600}h {(time_diff.seconds % 3600) // 60}m"
    elif is_available:
        time_diff = workshop['availability_end'] - current_time
        time_remaining = f"{time_diff.seconds // 3600}h {(time_diff.seconds % 3600) // 60}m"
    
    return jsonify({
        'is_available': is_available,
        'is_upcoming': is_upcoming,
        'time_remaining': time_remaining,
        'workshop_name': workshop['name']
    })

@public_pages.route('/generate-certificate', methods=['POST'])
def generate_certificate():
    """Generate and download certificate for a workshop"""
    student_name = request.form.get('student_name')
    email = request.form.get('email')
    workshop_id = request.form.get('workshop_id', 'visualizing_intelligence')
    
    if not student_name or not email:
        return jsonify({'error': 'Missing details'}), 400
    
    if workshop_id not in WORKSHOP_SCHEDULES:
        return jsonify({'error': 'Invalid workshop'}), 400
    
    workshop = WORKSHOP_SCHEDULES[workshop_id]
    current_time = datetime.now()
    
    if current_time < workshop['availability_start']:
        return jsonify({
            'error': 'Certificate not yet available',
            'message': f"Certificates will be available on {workshop['date'].strftime('%B %d, %Y at %I:%M %p')}"
        }), 403
    
    if current_time > workshop['availability_end']:
        return jsonify({
            'error': 'Certificate generation closed',
            'message': 'The certificate generation window has closed for this workshop.'
        }), 403
    
    # Fix table if needed
    try:
        inspector = inspect(db.engine)
        if inspector.has_table('certificate_record'):
            columns = [col['name'] for col in inspector.get_columns('certificate_record')]
            if 'workshop_name' in columns or 'workshop_date' in columns:
                db.session.execute(text('DROP TABLE IF EXISTS certificate_record'))
                db.session.commit()
                db.create_all()
    except:
        pass
    
    unique_id = f"IST-WS-{workshop['date'].strftime('%Y')}-{str(uuid.uuid4().hex[:6]).upper()}"
    
    try:
        new_certificate = CertificateRecord(
            student_name=student_name,
            email=email,
            certificate_id=unique_id
        )
        db.session.add(new_certificate)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Database Error: {str(e)}'}), 500
    
    # =============================================
    # SINGLE PAGE A4 LANDSCAPE PDF CERTIFICATE
    # =============================================
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    
    # CRITICAL: Prevent auto page break - FORCE SINGLE PAGE
    pdf.set_auto_page_break(False)
    
    # Page dimensions: 297mm x 210mm (Landscape)
    page_w = 297
    page_h = 210
    
    # === BACKGROUND ===
    pdf.set_fill_color(248, 250, 252)
    pdf.rect(0, 0, page_w, page_h, 'F')
    
    # === OUTER BORDER - Navy Blue ===
    pdf.set_draw_color(25, 45, 80)
    pdf.set_line_width(3)
    pdf.rect(8, 8, 281, 194)
    
    # === INNER BORDER - Gold ===
    pdf.set_draw_color(200, 160, 50)
    pdf.set_line_width(0.6)
    pdf.rect(12, 12, 273, 186)
    
    # === WATERMARK LOGO ===
    icon_path = os.path.join(os.path.dirname(__file__), 'static', 'assets', 'images', 'icon.png')
    try:
        with pdf.local_context(fill_opacity=0.04):
            pdf.image(icon_path, x=78, y=35, w=140)
    except:
        pass
    
    # === CERTIFICATE NUMBER (Top Left) ===
    pdf.set_xy(18, 15)
    pdf.set_font("Helvetica", style="B", size=8)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(80, 4, f"Ref: {unique_id}", align='L')
    
    # === ISSUE DATE (Top Right) ===
    issue_date = datetime.now().strftime("%d %B %Y")
    pdf.set_xy(200, 15)
    pdf.set_font("Helvetica", style="B", size=8)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(80, 4, f"Issued: {issue_date}", align='R')
    
    # === LOGO (Center Top) ===
    logo_url = "https://www.inovatesolutiontechnology.in/static/assets/images/logo.png"
    try:
        pdf.image(logo_url, x=111, y=15, w=75)
    except:
        pass
    
    # === MSME REGISTRATION ===
    pdf.set_y(42)
    pdf.set_font("Helvetica", style="I", size=9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 4, "An MSME Registered Organization", align='C')
    
    pdf.set_y(47)
    pdf.set_font("Helvetica", style="", size=8)
    pdf.set_text_color(130, 130, 130)
    pdf.cell(0, 3, "UDYAM-TN-12-0147998", align='C')
    
    # === DECORATIVE DIVIDER ===
    pdf.set_y(55)
    pdf.set_draw_color(200, 160, 50)
    pdf.set_line_width(0.4)
    pdf.line(60, pdf.get_y(), 237, pdf.get_y())
    
    # === MAIN TITLE ===
    pdf.set_y(63)
    pdf.set_font("Times", style="B", size=32)
    pdf.set_text_color(25, 45, 80)
    pdf.cell(0, 12, "CERTIFICATE OF PARTICIPATION", align='C')
    
    # === TITLE UNDERLINE ===
    pdf.set_draw_color(200, 160, 50)
    pdf.set_line_width(1.5)
    pdf.line(95, 76, 202, 76)
    
    # === PRESENTED TO ===
    pdf.set_y(84)
    pdf.set_font("Helvetica", style="I", size=11)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 6, "This certificate is proudly presented to", align='C')
    
    # === STUDENT NAME ===
    pdf.set_y(96)
    pdf.set_font("Times", style="B", size=38)
    pdf.set_text_color(200, 160, 50)
    
    # Truncate name if too long
    display_name = student_name.title()
    if pdf.get_string_width(display_name) > 250:
        pdf.set_font("Times", style="B", size=30)
    pdf.cell(0, 14, display_name, align='C')
    
    # === NAME UNDERLINE ===
    name_w = pdf.get_string_width(display_name) + 30
    name_x = (page_w - name_w) / 2
    pdf.set_line_width(0.4)
    pdf.set_draw_color(180, 180, 180)
    pdf.line(name_x, 111, name_x + name_w, 111)
    
    # === WORKSHOP TEXT ===
    pdf.set_y(119)
    pdf.set_font("Helvetica", size=11)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 6, "for successfully participating in the Workshop on", align='C')
    
    # === WORKSHOP NAME ===
    pdf.set_y(128)
    pdf.set_font("Helvetica", style="B", size=18)
    pdf.set_text_color(25, 45, 80)
    
    workshop_title = f'"{workshop["name"]}"'
    if pdf.get_string_width(workshop_title) > 260:
        pdf.set_font("Helvetica", style="B", size=15)
    pdf.cell(0, 8, workshop_title, align='C')
    
    # === ORGANIZED BY ===
    pdf.set_y(140)
    pdf.set_font("Helvetica", size=10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 5, "organized and conducted by", align='C')
    
    pdf.set_y(147)
    pdf.set_font("Helvetica", style="B", size=13)
    pdf.set_text_color(25, 45, 80)
    pdf.cell(0, 6, "Inovate Solution Technology", align='C')
    
    pdf.set_y(154)
    pdf.set_font("Helvetica", size=9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 4, "Madurai, Tamil Nadu, India", align='C')
    
    # === DATE SECTION (Left) ===
    pdf.set_draw_color(25, 45, 80)
    pdf.set_line_width(0.4)
    
    cert_date = workshop['date'].strftime("%d %B %Y")
    pdf.set_xy(45, 172)
    pdf.set_font("Helvetica", style="B", size=10)
    pdf.set_text_color(40, 40, 40)
    pdf.cell(50, 5, cert_date, align='C')
    pdf.line(45, 179, 95, 179)
    pdf.set_xy(45, 180)
    pdf.set_font("Helvetica", size=8)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(50, 4, "Workshop Date", align='C')
    
    # === CERTIFICATE ID SECTION (Center) ===
    pdf.set_xy(123, 172)
    pdf.set_font("Helvetica", style="B", size=10)
    pdf.set_text_color(40, 40, 40)
    pdf.cell(50, 5, unique_id, align='C')
    pdf.line(123, 179, 173, 179)
    pdf.set_xy(123, 180)
    pdf.set_font("Helvetica", size=8)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(50, 4, "Certificate ID", align='C')
    
    # === SIGNATURE SECTION (Right) ===
    sig_path = os.path.join(os.path.dirname(__file__), 'static', 'assets', 'images', 'ist_sign.png')
    try:
        pdf.image(sig_path, x=215, y=152, w=35)
    except:
        pass
    
    pdf.set_xy(202, 172)
    pdf.set_font("Helvetica", style="B", size=10)
    pdf.set_text_color(40, 40, 40)
    pdf.cell(50, 5, "", align='C')
    pdf.line(202, 179, 252, 179)
    pdf.set_xy(202, 180)
    pdf.set_font("Helvetica", size=8)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(50, 4, "Authorized Signatory", align='C')
    
    # === BOTTOM DIVIDER ===
    pdf.set_draw_color(200, 160, 50)
    pdf.set_line_width(0.3)
    pdf.line(20, 190, 277, 190)
    
    # === VERIFICATION TEXT ===
    pdf.set_y(193)
    pdf.set_font("Helvetica", size=7)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(0, 3, "This certificate can be verified at: www.inovatesolutiontechnology.in/verify", align='C')
    
    pdf.set_y(197)
    pdf.set_font("Helvetica", size=7)
    pdf.set_text_color(150, 150, 150)
     
    # === SAVE PDF ===
    safe_student_name = student_name.replace(' ', '_')
    pdf_filename = f"{safe_student_name}_Certificate.pdf"
    
    tmp_dir = tempfile.gettempdir()
    file_path = os.path.join(tmp_dir, pdf_filename)
    
    pdf.output(file_path)
    
    return send_file(
        file_path,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f"{safe_student_name}_Certificate.pdf"
    )