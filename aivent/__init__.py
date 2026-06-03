import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    
    # Secret Key setup
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'pro_secret_key')

    # Vercel Database Logic (PostgreSQL in Production, SQLite in Development)
    raw_db_url = os.getenv('DATABASE_URL')
    if raw_db_url:
        # Vercel/Supabase URLs often start with postgres://, but SQLAlchemy requires postgresql://
        app.config['SQLALCHEMY_DATABASE_URI'] = raw_db_url.replace("postgres://", "postgresql://", 1)
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
        
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize extensions
    db.init_app(app)
    
    login_manager.init_app(app)
    login_manager.login_view = 'login'

    # Import models here to avoid circular imports
    from .models import User
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Safely create tables
    with app.app_context():
        db.create_all()

    # Import and register blueprints
    from .pages import public_pages
    app.register_blueprint(public_pages, url_prefix="/")

    return app