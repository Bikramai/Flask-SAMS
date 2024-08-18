from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_wtf import CSRFProtect

app = Flask(__name__)
app.config['SECRET_KEY'] = '5791628bb0b13ce0c676dfde280ba245'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sams.db'
app.config['UPLOAD_FOLDER'] = 'sams/static/uploads'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'main.login'
login_manager.login_message_category = 'info'
with app.app_context():
    import sams.models
    db.create_all()

from sams.main.routes import main
from sams.admin.routes import admin
from sams.teacher.routes import teacher
from sams.student.routes import student

app.register_blueprint(main)
app.register_blueprint(admin)
app.register_blueprint(teacher)
app.register_blueprint(student)




from sams.models import User, Role, Admin, Student, Class, ClassArm, Session, Teacher
