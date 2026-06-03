import os
from flask import Blueprint, render_template, request, flash, redirect, url_for
from werkzeug.utils import secure_filename
import uuid
import requests

# Import your models
from .models import Contact, ProjectRequest, JobApplication, InternshipApplication
from . import db

# Define the Blueprint
public_pages = Blueprint('public_pages', __name__, template_folder='templates', static_folder='static')

# -----------------------------------------------------------
# VERCEL BLOB UPLOAD HELPER
# -----------------------------------------------------------
def upload_to_vercel_blob(file_obj):
    token = os.getenv('BLOB_READ_WRITE_TOKEN')
    if not token:
        raise Exception("Vercel Blob Token is missing.")
        
    clean_filename = secure_filename(file_obj.filename)
    unique_filename = f"{str(uuid.uuid4())[:8]}_{clean_filename}"
    
    # Vercel Blob REST API endpoint
    url = f"https://blob.vercel-storage.com/{unique_filename}"
    headers = {
        "authorization": f"Bearer {token}",
    }
    
    # Push the file to Vercel Storage
    response = requests.put(url, data=file_obj.read(), headers=headers)
    response.raise_for_status() # Will trigger an error if the upload fails
    
    # Return the public URL of the uploaded resume
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
        resume_url = "" # Will hold the Vercel URL

        # Validate inputs
        if not name or not email or not phone or not domain or not college:
            flash("Please fill out all required fields.", "error")
            return redirect(url_for('public_pages.interns') + '#apply-internship')

        # Handle File Upload to Vercel Blob
        if resume_file and resume_file.filename != '':
            try:
                resume_url = upload_to_vercel_blob(resume_file)
            except Exception as e:
                flash("Error uploading resume to cloud storage.", "error")
                print("Vercel Blob Upload Error:", e)
                return redirect(url_for('public_pages.interns') + '#apply-internship')
        else:
            flash("Please upload a valid resume (PDF or DOC).", "error")
            return redirect(url_for('public_pages.interns') + '#apply-internship')

        # Save to database using the Vercel URL
        new_intern = InternshipApplication(
            name=name, email=email, phone=phone, 
            domain=domain, college=college, resume_filename=resume_url
        )
        
        try:
            db.session.add(new_intern)
            db.session.commit()
            flash("Your internship application has been submitted successfully!", "success")
        except Exception as e:
            db.session.rollback()
            flash("There was an error submitting your application. Please try again.", "error")
            print(f"Database error: {e}")
            
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
        resume_url = "" # Will hold the Vercel URL

        # Validate inputs
        if not name or not email or not phone or not position:
            flash("Please fill out all required fields.", "error")
            return redirect(url_for('public_pages.join_us') + '#apply-form')

        # Handle File Upload securely to Vercel Blob
        if resume_file and resume_file.filename != '':
            try:
                resume_url = upload_to_vercel_blob(resume_file)
            except Exception as e:
                flash("Error uploading resume to cloud storage.", "error")
                print("Vercel Blob Upload Error:", e)
                return redirect(url_for('public_pages.join_us') + '#apply-form')
        else:
            flash("Please upload a valid resume (PDF or DOC).", "error")
            return redirect(url_for('public_pages.join_us') + '#apply-form')

        # Save to database using the Vercel URL
        new_app = JobApplication(
            name=name, email=email, phone=phone, 
            position=position, resume_filename=resume_url, message=message
        )
        
        try:
            db.session.add(new_app)
            db.session.commit()
            flash("Your application has been submitted successfully! We will review it shortly.", "success")
        except Exception as e:
            db.session.rollback()
            flash("There was an error submitting your application. Please try again.", "error")
            print(f"Database error: {e}")
            
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
            flash("Your project request has been submitted successfully! Our mentors will contact you soon.", "success")
        except Exception as e:
            db.session.rollback()
            flash("There was an error submitting your request. Please try again.", "error")
            print(f"Database error: {e}")
            
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
            flash("Your message has been sent successfully!", "success")
        except Exception as e:
            db.session.rollback()
            flash("There was an error sending your message. Please try again.", "error")
            print(f"Database error: {e}") 
            
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