import os
import smtplib
import uuid
import requests
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Blueprint, render_template, request, flash, redirect, url_for, send_file
from werkzeug.utils import secure_filename
from sqlalchemy import inspect
from fpdf import FPDF
from .models import Contact, ProjectRequest, JobApplication, InternshipApplication, CertificateRecord
from . import db

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
@public_pages.route('/workshop-certificate', methods=['GET'])
def workshop_certificate():
    return render_template('certificate.html')

@public_pages.route('/generate-certificate', methods=['POST'])
def generate_certificate():
    student_name = request.form.get('student_name')
    email = request.form.get('email')
    
    if not student_name or not email:
        return "Missing details", 400

    inspector = inspect(db.engine)
    if not inspector.has_table('certificate_record'):
        CertificateRecord.__table__.create(db.engine)

    unique_id = f"IST-WS-2026-{str(uuid.uuid4().hex[:6]).upper()}"

    new_certificate = CertificateRecord(student_name=student_name, email=email, certificate_id=unique_id)
    try:
        db.session.add(new_certificate)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return f"Database Error: {str(e)}", 500

    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_fill_color(250, 252, 255) 
    pdf.rect(0, 0, 297, 210, 'F')
    pdf.set_draw_color(31, 78, 121) 
    pdf.set_line_width(3)
    pdf.rect(10, 10, 277, 190)
    pdf.set_draw_color(212, 175, 55)
    pdf.set_line_width(0.8)
    pdf.rect(14, 14, 269, 182)

    icon_path = os.path.join(os.path.dirname(__file__), 'static', 'assets', 'images', 'icon.png')
    watermark_size = 140
    watermark_x = (297 - watermark_size) / 2
    watermark_y = (210 - watermark_size) / 2
    try:
        with pdf.local_context(fill_opacity=0.08):
            pdf.image(icon_path, x=watermark_x, y=watermark_y, w=watermark_size)
    except Exception:
        pass

    pdf.set_font("Helvetica", style="B", size=10)
    pdf.set_text_color(100, 100, 100)
    pdf.set_xy(20, 18)
    pdf.cell(100, 6, f"Certificate No: {unique_id}", align='L')

    logo_url = "https://www.inovatesolutiontechnology.in/static/assets/images/logo.png"
    logo_width = 85
    logo_x = (297 - logo_width) / 2
    try:
        pdf.image(logo_url, x=logo_x, y=16, w=logo_width)
    except Exception:
        pass 

    pdf.set_y(54)
    pdf.set_font("Helvetica", style="I", size=11)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 5, "An MSME Registered Organization", align='C')

    pdf.set_y(70)
    pdf.set_font("Times", style="B", size=34)
    pdf.set_text_color(31, 78, 121) 
    pdf.cell(0, 15, "CERTIFICATE OF PARTICIPATION", align='C')
    
    pdf.set_y(90)
    pdf.set_font("Helvetica", style="I", size=15)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 10, "This is proudly presented to", align='C')
    
    pdf.set_y(106)
    pdf.set_font("Times", style="B", size=42)
    pdf.set_text_color(212, 175, 55) 
    pdf.cell(0, 15, student_name.title(), align='C')
    
    name_width = pdf.get_string_width(student_name.title()) + 20
    start_x = (297 - name_width) / 2
    pdf.set_line_width(0.5)
    pdf.set_draw_color(200, 200, 200)
    pdf.line(start_x, 124, start_x + name_width, 124)

    pdf.set_y(130)
    pdf.set_font("Helvetica", size=14)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 8, "For successfully completing the 2-Hour Workshop on", align='C')
    
    pdf.set_y(140)
    pdf.set_font("Helvetica", style="B", size=22)
    pdf.set_text_color(31, 78, 121)
    pdf.cell(0, 10, '"Build Your Own AI Agent"', align='C')
    
    pdf.set_y(152)
    pdf.set_font("Helvetica", size=12)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 8, "Organized and Conducted by Inovate Solution Technology", align='C')
    
    current_date = datetime.now().strftime("%B %d, %Y")
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", style="B", size=12)
    pdf.set_xy(40, 172)
    pdf.cell(50, 8, current_date, align='C')
    pdf.set_line_width(0.5)
    pdf.set_draw_color(0, 0, 0)
    pdf.line(40, 180, 90, 180)
    pdf.set_xy(40, 181)
    pdf.set_font("Helvetica", size=10)
    pdf.cell(50, 5, "Date", align='C')
    
    sig_path = os.path.join(os.path.dirname(__file__), 'static', 'assets', 'images', 'ist_sign.png')
    try:
        pdf.image(sig_path, x=212, y=148, w=40)
    except Exception:
        pass

    pdf.set_xy(207, 172)
    pdf.set_line_width(0.5)
    pdf.line(207, 180, 257, 180)
    pdf.set_xy(207, 181)
    pdf.set_font("Helvetica", size=10)
    pdf.cell(50, 5, "Authorized Signatory", align='C')

    safe_student_name = student_name.replace(' ', '_')
    pdf_filename = f"{safe_student_name}_Certificate.pdf"
    
    static_folder = os.path.join(os.path.dirname(__file__), 'static')
    if not os.path.exists(static_folder):
        os.makedirs(static_folder)
        
    file_path = os.path.join(static_folder, pdf_filename)
    pdf.output(file_path)

    return send_file(file_path, mimetype='application/pdf')