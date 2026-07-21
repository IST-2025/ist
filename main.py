import os
from flask import send_from_directory, redirect, url_for, request, render_template, flash
from aivent import create_app, db
from aivent.models import User, Contact, ProjectRequest, JobApplication, InternshipApplication, CertificateRecord
from flask_admin import Admin, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from flask_login import LoginManager, current_user, login_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash

app = create_app()
app.secret_key = os.environ.get('SECRET_KEY', 'super_secret_key_change_this_later') 

# ==========================================
# 1. SET UP FLASK-LOGIN
# ==========================================
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ==========================================
# 2. SECURE THE FLASK-ADMIN VIEWS
# ==========================================
class SecureAdminIndexView(AdminIndexView):
    def is_accessible(self):
        return current_user.is_authenticated

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login', next=request.url))

class SecureModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login', next=request.url))

# ==========================================
# 3. INITIALIZE ADVANCED ADMIN PANEL UI
# ==========================================
app.config['FLASK_ADMIN_SWATCH'] = 'darkly' 

admin = Admin(app, name='IST Admin Panel', index_view=SecureAdminIndexView())
admin.add_view(SecureModelView(User, db))
admin.add_view(SecureModelView(Contact, db))
admin.add_view(SecureModelView(ProjectRequest, db))
admin.add_view(SecureModelView(JobApplication, db))
admin.add_view(SecureModelView(InternshipApplication, db))
admin.add_view(SecureModelView(CertificateRecord, db))

# ==========================================
# 4. AUTHENTICATION ROUTES
# ==========================================
@app.route('/login', methods=['GET', 'POST'])
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

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/setup-admin') 
def setup_admin():
    try:
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

# ==========================================
# 5. SITEMAP ROUTE
# ==========================================
@app.route('/sitemap.xml')
def sitemap():
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), 'sitemap.xml')

# ==========================================
# 6. START APP & CREATE TABLES
# ==========================================
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)