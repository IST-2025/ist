import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Blueprint, render_template, request, flash, redirect, url_for
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash  
from flask_login import login_user, logout_user, current_user              
import uuid
import requests
from sqlalchemy import text
# Import your models
from .models import Contact, ProjectRequest, JobApplication, InternshipApplication, User
from . import db

# Define the Blueprint
public_pages = Blueprint('public_pages', __name__, template_folder='templates', static_folder='static')

# -----------------------------------------------------------
# EMAIL NOTIFICATION HELPER
# -----------------------------------------------------------
def send_admin_notification(subject, body):
    sender_email = os.environ.get('MAIL_USERNAME')
    sender_password = os.environ.get('MAIL_APP_PASSWORD')
    recipient_email = "inovatesolutiontechnology@gmail.com"

    if not sender_email or not sender_password:
        print("Warning: Email credentials not found in environment variables.")
        return

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        # Connect to Gmail's SMTP server
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        print("Admin notification email sent successfully!")
    except Exception as e:
        print(f"Failed to send email notification: {str(e)}")

# -----------------------------------------------------------
# VERCEL BLOB UPLOAD HELPER
# -----------------------------------------------------------
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

# -----------------------------------------------------------
# Basic Page Routes
# -----------------------------------------------------------
@public_pages.route('/')
def index():
    return render_template('index.html')

@public_pages.route('/about')
def about():
    return render_template('about.html')

@public_pages.route('/services')
def services():
    return render_template('services.html')

@public_pages.route('/products')
def products():
    return render_template('products.html')

# -----------------------------------------------------------
# Careers & Internships Routes (File Uploads)
# -----------------------------------------------------------
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

        new_intern = InternshipApplication(
            name=name, email=email, phone=phone, 
            domain=domain, college=college, resume_filename=resume_url
        )
        
        try:
            db.session.add(new_intern)
            db.session.commit()
            
            # --- EMAIL TRIGGER ADDED HERE ---
            email_body = f"New Internship Application Received:\n\nName: {name}\nEmail: {email}\nPhone: {phone}\nDomain: {domain}\nCollege: {college}\nResume Link: {resume_url}"
            send_admin_notification("New Internship Application - IST", email_body)
            # --------------------------------
            
            flash("Your internship application has been submitted successfully!", "success")
        except Exception as e:
            db.session.rollback()
            error_msg = str(e)
            print(f"CRITICAL DB ERROR in /interns: {error_msg}")
            # EXPLICIT ERROR EXPOSED FOR DEBUGGING
            flash(f"System Error (Database): {error_msg}", "error")
            
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
            flash("Please upload a valid resume (PDF or DOC).", "error")
            return redirect(url_for('public_pages.join_us') + '#apply-form')

        new_app = JobApplication(
            name=name, email=email, phone=phone, 
            position=position, resume_filename=resume_url, message=message
        )
        
        try:
            db.session.add(new_app)
            db.session.commit()
            
            # --- EMAIL TRIGGER ADDED HERE ---
            email_body = f"New Job Application Received:\n\nName: {name}\nEmail: {email}\nPhone: {phone}\nPosition: {position}\nMessage: {message}\nResume Link: {resume_url}"
            send_admin_notification("New Job Application - IST", email_body)
            # --------------------------------
            
            flash("Your application has been submitted successfully! We will review it shortly.", "success")
        except Exception as e:
            db.session.rollback()
            error_msg = str(e)
            print(f"CRITICAL DB ERROR in /join-us: {error_msg}")
            # EXPLICIT ERROR EXPOSED FOR DEBUGGING
            flash(f"System Error (Database): {error_msg}", "error")
            
        return redirect(url_for('public_pages.join_us') + '#apply-form')

    return render_template('join-us.html')

# -----------------------------------------------------------
# Text-Only Forms (No Uploads)
# -----------------------------------------------------------
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
            flash("Please fill out all fields before submitting.", "error")
            return redirect(url_for('public_pages.projects') + '#request-project')

        new_project = ProjectRequest(
            name=name, email=email, phone=phone, 
            college=college, domain=domain, description=description
        )
        
        try:
            db.session.add(new_project)
            db.session.commit()
            
            # --- EMAIL TRIGGER ADDED HERE ---
            email_body = f"New Project Request:\n\nName: {name}\nEmail: {email}\nPhone: {phone}\nCollege: {college}\nDomain: {domain}\nDescription: {description}"
            send_admin_notification("New Project Request - IST", email_body)
            # --------------------------------
            
            flash("Your project request has been submitted successfully! Our mentors will contact you soon.", "success")
        except Exception as e:
            db.session.rollback()
            error_msg = str(e)
            print(f"CRITICAL DB ERROR in /projects: {error_msg}")
            # EXPLICIT ERROR EXPOSED FOR DEBUGGING
            flash(f"System Error (Database): {error_msg}", "error")
            
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
            flash("Please fill out all fields before submitting.", "error")
            return redirect(url_for('public_pages.contact'))

        new_contact = Contact(name=name, email=email, phone=phone, message=message)
        
        try:
            db.session.add(new_contact)
            db.session.commit()
            
            # --- EMAIL TRIGGER ADDED HERE ---
            email_body = f"New Contact Message Received:\n\nName: {name}\nEmail: {email}\nPhone: {phone}\nMessage: {message}"
            send_admin_notification("New Contact Message - IST", email_body)
            # --------------------------------
            
            flash("Your message has been sent successfully!", "success")
        except Exception as e:
            db.session.rollback()
            error_msg = str(e)
            print(f"CRITICAL DB ERROR in /contact: {error_msg}")
            # EXPLICIT ERROR EXPOSED FOR DEBUGGING
            flash(f"System Error (Database): {error_msg}", "error")
            
        return redirect(url_for('public_pages.contact'))

    return render_template('contact.html')


# -----------------------------------------------------------
# Legal Routes
# -----------------------------------------------------------
@public_pages.route('/privacy-policy')
def privacy_policy():
    return render_template('privacy-policy.html')

@public_pages.route('/terms')
def terms():
    return render_template('terms.html')

# -----------------------------------------------------------
# Admin & Authentication Routes
# -----------------------------------------------------------
@public_pages.route('/setup-admin')
def setup_admin():
    try:
        db.session.execute(text('ALTER TABLE "user" ALTER COLUMN password TYPE VARCHAR(255);'))
        db.session.commit()

        # FIXED: Check for 'ammu' since that is the user you are creating below
        admin_exists = User.query.filter_by(username='ammu').first()
        
        if not admin_exists:
            hashed_pw = generate_password_hash('Shalini0810*')
            new_admin = User(username='ammu', email='inovatesolutiontechnology@gmail.com', password=hashed_pw)
            db.session.add(new_admin)
            db.session.commit()
            return "<h3>Admin user created!</h3><p>Username: <b>ammu</b> | Password: <b>Shalini0810*</b></p><br><a href='/login'>Go to Login</a>"
        
        return "<h3>Admin already exists.</h3><a href='/login'>Go to Login</a>"
    
    except Exception as e:
        db.session.rollback()
        return f"<h3>Database Error:</h3><p>{str(e)}</p>"


@public_pages.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect('/admin')

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect('/admin')
        else:
            flash('Invalid username or password', 'error')
            
    return render_template('admin_login.html')

@public_pages.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('public_pages.login'))