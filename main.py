import os
from dotenv import load_dotenv

load_dotenv()
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

from flask import send_from_directory, redirect, url_for, request, render_template, flash, session
from aivent import create_app, db
from flask_migrate import Migrate 
from aivent.models import (
    User, Contact, ProjectRequest, JobApplication, 
    InternshipApplication, CertificateRecord, 
    SeminarRegistration, FeedbackRecord
)
from flask_admin import Admin, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from flask_admin.theme import Bootstrap4Theme 
from flask_login import LoginManager, current_user, login_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from authlib.integrations.flask_client import OAuth

app = create_app()
app.secret_key = os.environ.get('SECRET_KEY', 'super_secret_key_change_this_later') 

migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'public_pages.portal_login'

oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=os.environ.get('GOOGLE_CLIENT_ID'),
    client_secret=os.environ.get('GOOGLE_CLIENT_SECRET'),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class SecureAdminIndexView(AdminIndexView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.username == 'ammu'

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login', next=request.url))

class SecureModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.username == 'ammu'

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login', next=request.url))


# FIX: Changed swatch from 'darkly' to 'flatly' for a clean, modern white theme!
admin = Admin(
    app, 
    name='IST Admin Panel', 
    theme=Bootstrap4Theme(swatch='flatly'), 
    index_view=SecureAdminIndexView()
)

# Group 1: Accounts & Contacts 
admin.add_view(SecureModelView(User, db, category='Accounts & Info'))
admin.add_view(SecureModelView(Contact, db, category='Accounts & Info'))

# Group 2: Applications 
admin.add_view(SecureModelView(ProjectRequest, db, category='Applications'))
admin.add_view(SecureModelView(JobApplication, db, category='Applications'))
admin.add_view(SecureModelView(InternshipApplication, db, category='Applications'))

# Group 3: Records & Data 
admin.add_view(SecureModelView(SeminarRegistration, db, category='Records & Data'))
admin.add_view(SecureModelView(CertificateRecord, db, category='Records & Data'))
admin.add_view(SecureModelView(FeedbackRecord, db, category='Records & Data'))

@app.route('/google-login')
def google_login():
    redirect_uri = url_for('authorize', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/authorize')
def authorize():
    try:
        token = google.authorize_access_token()
        user_info = token.get('userinfo')
        if user_info:
            email = user_info['email']
            google_id = user_info['sub']
            username = user_info.get('name', email.split('@')[0])
            
            user = User.query.filter_by(email=email).first()
            if not user:
                user = User(email=email, username=username, google_id=google_id, role='unassigned')
                db.session.add(user)
                db.session.commit()
                
            login_user(user)
            # Make sure 'public_pages.portal' blueprint is correctly registered in create_app
            return redirect(url_for('public_pages.portal'))
    except Exception as e:
        print(f"OAUTH ERROR: {str(e)}")
        flash(f"Google login failed: {str(e)}", "error")
        
    return redirect(url_for('public_pages.portal_login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated and current_user.username == 'ammu':
        return redirect('/admin')

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.password and check_password_hash(user.password, password):
            login_user(user)
            if user.username == 'ammu':
                return redirect('/admin')
            return redirect(url_for('public_pages.portal'))
        else:
            flash('Invalid username or password', 'error')
            
    return render_template('admin_login.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('public_pages.portal_login'))

@app.route('/setup-admin') 
def setup_admin():
    try:
        admin_exists = User.query.filter_by(username='ammu').first()
        if not admin_exists:
            hashed_pw = generate_password_hash('Shalini0810*')
            new_admin = User(username='ammu', email='inovatesolutiontechnology@gmail.com', password=hashed_pw, role='admin')
            db.session.add(new_admin)
            db.session.commit()
            
            return "<h3>Admin user created!</h3><p>Username: <b>ammu</b> | Password: <b>Shalini0810*</b></p><br><a href='/login'>Go to Login</a>"
        
        return "<h3>Admin already exists.</h3><a href='/login'>Go to Login</a>"
        
    except Exception as e:
        db.session.rollback()
        return f"<h3>Database Error:</h3><p>{str(e)}</p>"

@app.route('/sitemap.xml')
def sitemap():
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), 'sitemap.xml')

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)