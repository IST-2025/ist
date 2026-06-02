from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = b'_5#y2L"F4Q8z\n\xec]/'
    app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///db.sqllite"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    from .models import User
    with app.app_context():
        db.create_all()

    # Import the public_pages blueprint
    from .pages import public_pages  # Import the correct blueprint
    app.register_blueprint(public_pages, url_prefix="/")

    return app
