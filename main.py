from aivent import create_app, db
# Add InternshipApplication to your imports
from aivent.models import User, Contact, ProjectRequest, JobApplication, InternshipApplication

from flask import redirect, url_for, request, render_template, flash
from flask_admin import Admin, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from flask_login import LoginManager, current_user, login_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash

app = create_app()
app.secret_key = 'super_secret_key_change_this_later' # Required for secure login sessions

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
# This protects the main /admin dashboard
class SecureAdminIndexView(AdminIndexView):
    def is_accessible(self):
        return current_user.is_authenticated

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login', next=request.url))

# This protects the individual database tables (User, Contact)
class SecureModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login', next=request.url))

# ==========================================
# 3. INITIALIZE ADVANCED ADMIN PANEL UI
# ==========================================
# Applies a sleek, modern dark theme called 'darkly' (you can also try 'cerulean' or 'flatly')
app.config['FLASK_ADMIN_SWATCH'] = 'darkly' 

admin = Admin(app, name='IST Admin Panel', index_view=SecureAdminIndexView())
admin.add_view(SecureModelView(User, db))
admin.add_view(SecureModelView(Contact, db))
# Add this right below your admin.add_view(SecureModelView(Contact, db)) line
admin.add_view(SecureModelView(ProjectRequest, db))
# Add this right below the ProjectRequest admin view
admin.add_view(SecureModelView(JobApplication, db))
# Add this right below the JobApplication admin view
admin.add_view(SecureModelView(InternshipApplication, db))

# ==========================================
# 4. AUTHENTICATION ROUTES
# ==========================================
@app.route('/login', methods=['GET', 'POST'])
def login():
    # If the user is already logged in, send them straight to the admin panel
    if current_user.is_authenticated:
        return redirect('/admin')

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Look for the user in the database
        user = User.query.filter_by(username=username).first()
        
        # Check if user exists and the password matches the hashed password
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

# --- TEMPORARY ROUTE TO CREATE YOUR FIRST PASSWORD ---
@app.route('/setup-admin')
def setup_admin():
    admin_exists = User.query.filter_by(username='admin').first()
    if not admin_exists:
        # Securely hash the password 'admin123'
        hashed_pw = generate_password_hash('admin123')
        new_admin = User(username='admin', email='admin@ist.com', password=hashed_pw)
        db.session.add(new_admin)
        db.session.commit()
        return "<h3>Admin user created!</h3><p>Username: <b>admin</b> | Password: <b>admin123</b></p><br><a href='/login'>Go to Login</a>"
    return "<h3>Admin already exists.</h3><a href='/login'>Go to Login</a>"

# ==========================================
# 5. START APP & CREATE TABLES
# ==========================================
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)