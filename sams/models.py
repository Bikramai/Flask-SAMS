from flask_login import UserMixin
from datetime import datetime
from sams import db, login_manager
from datetime import date


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    fullname = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))
    role = db.relationship('Role', backref=db.backref('users', lazy=True))


class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    role_name = db.Column(db.String(50), unique=True, nullable=False)


class Teacher(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True)
    phone = db.Column(db.String(100), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'))
    class_arm_id = db.Column(db.Integer, db.ForeignKey('class_arm.id'))
    user = db.relationship('User', backref=db.backref('teacher', uselist=False))
    class_ = db.relationship('Class', backref='teachers')
    class_arm = db.relationship('ClassArm', backref='teachers')


class Class(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    class_arms = db.relationship('ClassArm', backref='class', lazy=True, cascade="all, delete-orphan")


class ClassArm(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'))


class Admin(db.Model):
    admin_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True)
    user = db.relationship('User', backref=db.backref('admin', uselist=False))


class Session(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(9), nullable=False)
    term = db.Column(db.String(50), nullable=False)


class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True)
    admission_no = db.Column(db.String(100), unique=True, nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'))
    class_arm_id = db.Column(db.Integer, db.ForeignKey('class_arm.id'))
    image= db.Column(db.String(150), nullable=False)
    user = db.relationship('User', backref=db.backref('student', uselist=False))
    class_ = db.relationship('Class', backref='students')
    class_arm = db.relationship('ClassArm', backref='students')


class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'))
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'))
    date = db.Column(db.Date, default=date.today)
    status = db.Column(db.Boolean, default=False)
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'))
    class_arm_id = db.Column(db.Integer, db.ForeignKey('class_arm.id'))
    session_id = db.Column(db.Integer, db.ForeignKey('session.id'))
    student = db.relationship('Student', backref='attendances')
    teacher = db.relationship('Teacher', backref='attendances')
    class_ = db.relationship('Class', backref='attendances')
    class_arm = db.relationship('ClassArm', backref='attendances')
    session = db.relationship('Session', backref='attendances')
