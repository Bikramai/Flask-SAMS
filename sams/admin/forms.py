from flask_wtf import FlaskForm
from sams.models import User, Class, ClassArm
from wtforms import StringField, SelectField, PasswordField, SubmitField, EmailField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from wtforms_sqlalchemy.fields import QuerySelectField

class ClassArmForm(FlaskForm):
    classSelect = SelectField('Select Class', coerce=int, validators=[DataRequired()])
    classArmName = StringField('Class Arm Name', validators=[DataRequired()])
    submit = SubmitField('Create')

def class_query():
    return Class.query.all()

def class_arm_query():
    # You can filter the class arms based on the selected class
    return ClassArm.query.all()


class TeacherForm(FlaskForm):
    teacherName = StringField('Full Name', validators=[DataRequired()])
    username = StringField('Username', validators=[DataRequired()])
    email = EmailField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    phone = StringField('Phone No', validators=[DataRequired()])
    classSelect = SelectField('Select Class', coerce=int, choices=[], validators=[DataRequired()])
    classArmSelect = SelectField('Class Arm', coerce=int, choices=[], validators=[DataRequired()])
    submit = SubmitField('Add Teacher')


class StudentForm(FlaskForm):
    studentName = StringField('Full Name', validators=[DataRequired()])
    username = StringField('Username', validators=[DataRequired()])
    email = EmailField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    admissionNo = StringField('Admission No', validators=[DataRequired()])
    classSelect = SelectField('Select Class', coerce=int, choices=[], validators=[DataRequired()])
    classArmSelect = SelectField('Class Arm', coerce=int, choices=[], validators=[DataRequired()])
    submit = SubmitField('Add')

