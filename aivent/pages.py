import os
from flask import Blueprint, render_template, request, flash, redirect, url_for

# Define the Blueprint
public_pages = Blueprint('public_pages', __name__, template_folder='templates', static_folder='static')

# -----------------------------------------------------------
# Explicit Routes Definition
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

# --- Careers Dropdown Routes ---

@public_pages.route('/interns')
def interns():
    return render_template('interns.html')

@public_pages.route('/join-us')
def join_us():
    return render_template('join-us.html')

@public_pages.route('/projects')
def projects():
    return render_template('clg-projects.html')

# --- Legal Routes ---

@public_pages.route('/privacy-policy')
def privacy_policy():
    return render_template('privacy-policy.html')

@public_pages.route('/terms')
def terms():
    return render_template('terms.html')

# --- Contact Route (Handles GET and POST for the form) ---

@public_pages.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        # Here you will handle the form data later
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')
        
        # Add your email sending or database logic here
        # Example: send_email(name, email, phone, message)
        
        # After successful submission, you can redirect or flash a message
        # flash("Your message has been sent successfully!", "success")
        # return redirect(url_for('public_pages.contact'))

    return render_template('contact.html')