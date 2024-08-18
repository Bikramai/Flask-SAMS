import os
from flask import Blueprint, render_template
from flask import redirect, url_for, flash, request, jsonify
from flask_login import login_required
from flask_bcrypt import Bcrypt
from sams import app, db, bcrypt
from sams.admin.forms import ClassArmForm, StudentForm
from sams.models import Class, ClassArm, User, Student, Teacher, Session, Attendance

admin = Blueprint('admin', __name__, template_folder='templates', url_prefix='/admin')


@admin.route('/')
@login_required
def adminDashboard():  # put application's code here
    students_count = Student.query.count()
    teachers_count = User.query.filter_by(role_id=3).count()
    classes_count = Class.query.count()
    class_arms_count = ClassArm.query.count()
    sessions = Session.query.distinct(Session.name).all()
    terms = Session.query.distinct(Session.term).all()
    total_attendance = Attendance.query.count()

    return render_template('adminDashboard.html',
                           students_count=students_count,
                           teachers_count=teachers_count,
                           classes_count=classes_count,
                           class_arms_count=class_arms_count,
                           sessions=sessions,
                           terms=terms,
                           total_attendance=total_attendance
                           )


@admin.route("/manage_classes", methods=['GET', 'POST'])
@login_required
def manageClasses():
    if request.method == 'POST':
        class_name = request.form['className']
        new_class = Class(name=class_name)
        db.session.add(new_class)
        db.session.commit()
        flash('Class added successfully.', 'success')
        return redirect(url_for('admin.manageClasses'))  # Redirect to the same page to show the updated list

    classes = Class.query.all()
    return render_template('manageClasses.html', title='Manage Classes', classes=classes)


@app.route('/delete_class/<int:class_id>')
@login_required
def delete_class(class_id):
    try:
        class_to_delete = Class.query.get(class_id)
        if class_to_delete:
            db.session.delete(class_to_delete)
            db.session.commit()
            flash('Class deleted successfully!', 'success')
        else:
            flash('Class not found.', 'error')
    except Exception as e:
        flash(f'Error deleting class: {str(e)}', 'error')
    return redirect(url_for('admin.manageClasses'))



@admin.route("/manage_class_arms", methods=['GET', 'POST'])
@login_required
def manageClassArms():
    form = ClassArmForm()
    classes = Class.query.all()  # Fetch all classes from the database
    form.classSelect.choices = [(cls.id, cls.name) for cls in classes]  # Populate choices for the select field

    if form.validate_on_submit():
        class_id = form.classSelect.data
        class_arm_name = form.classArmName.data
        new_class_arm = ClassArm(name=class_arm_name, class_id=class_id)
        db.session.add(new_class_arm)
        db.session.commit()
        flash('Class arm added successfully.', 'success')
        return redirect(url_for('admin.manageClassArms'))

    class_arms = db.session.query(ClassArm, Class.name).join(Class,
                                                             Class.id == ClassArm.class_id).all()  # Correct join condition
    return render_template('manageClassArms.html', form=form, classes=classes, class_arms=class_arms)


@app.route('/delete_class_arm/<int:class_arm_id>')
@login_required
def delete_class_arm(class_arm_id):
    class_arm = ClassArm.query.get_or_404(class_arm_id)
    try:
        db.session.delete(class_arm)
        db.session.commit()
        flash('Class arm deleted successfully.', 'success')
    except:
        db.session.rollback()
        flash('Error deleting class arm.', 'error')
    return redirect(url_for('admin.manageClassArms'))


@admin.route("/manage_teachers", methods=['GET', 'POST'])
@login_required
def manageTeachers():
    classes = Class.query.all()  # Load all classes for the form dropdown
    teachers = db.session.query(Teacher, User).join(User).all()

    if request.method == 'POST':
        # Extract data from form
        teacher_name = request.form['teacherName']
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        phone = request.form['phone']
        class_id = request.form['classSelect']
        class_arm_id = request.form['classArmSelect']
        role_id = 2

        # Create new User instance and save to database
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')  # Hash the password for security
        new_user = User(username=username, fullname=teacher_name, password=hashed_password, email=email, role_id=role_id)
        db.session.add(new_user)
        db.session.flush()  # Commit to retrieve the new user's ID

        # Create new Teacher instance and save to database
        new_teacher = Teacher(
            user_id=new_user.id,  # Use the new user's ID
            phone=phone,
            class_id=class_id,
            class_arm_id=class_arm_id
        )
        db.session.add(new_teacher)
        db.session.commit()

        flash('Teacher added successfully!', 'success')
        return redirect(url_for('admin.manageTeachers'))

    return render_template('manageTeachers.html', classes=classes, teachers=teachers)





@admin.route("/delete_teacher/<int:teacher_id>")
@login_required
def delete_teacher(teacher_id):
    try:
        teacher = Teacher.query.get_or_404(teacher_id)
        db.session.delete(teacher.user)
        db.session.delete(teacher)
        db.session.commit()
        flash('Teacher successfully deleted!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting teacher: {str(e)}', 'error')
    return redirect(url_for('admin.manageTeachers'))


@admin.route("/manage_students", methods=['GET', 'POST'])
@login_required
def manageStudents():
    classes = Class.query.all()  # Load all classes for the form dropdown
    students = db.session.query(Student, User).join(User).all()

    if request.method == 'POST':
        # Extract data from form
        student_name = request.form['studentName']
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        admission_no = request.form['admissionNo']
        class_id = request.form['classSelect']
        class_arm_id = request.form['classArmSelect']
        image = request.files['image']
        role_id = 3

        if not image or image.filename == '':
            flash("Invalid Image!")
            return redirect(url_for('admin.manageStudents'))
        
        filename = f"{admission_no}." + image.filename.split('.')[-1]
        image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        # Create new User instance and save to database
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')  # Hash the password for security
        try:
            new_user = User(
                username=username,
                fullname=student_name,
                password=hashed_password,
                email=email,
                role_id=role_id)
            db.session.add(new_user)
            db.session.flush()  # Commit to retrieve the new user's ID

            # Create new Student instance and save to database
            new_student = Student(
                user_id=new_user.id,
                admission_no=admission_no,
                class_id=class_id,
                class_arm_id=class_arm_id,
                image=filename
            )
        except Exception:
            flash('Email / Username / Admission Number Already Taken!', 'error')
            return redirect(url_for('admin.manageStudents'))

        db.session.add(new_student)
        db.session.commit()
        flash('Student added successfully!', 'success')
        return redirect(url_for('admin.manageStudents'))

    return render_template('manageStudents.html', classes=classes, students=students)



@admin.route("/delete_student/<int:student_id>")
@login_required
def delete_student(student_id):
    try:
        student = Student.query.get_or_404(student_id)
        db.session.delete(student.user)
        db.session.delete(student)
        db.session.commit()
        flash('Student successfully deleted!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting student: {str(e)}', 'error')
    return redirect(url_for('admin.manageStudents'))



@app.route('/get_class_arms/<int:class_id>')
def get_class_arms(class_id):
    class_arms = ClassArm.query.filter_by(class_id=class_id).all()
    return jsonify([{'id': ca.id, 'name': ca.name} for ca in class_arms])


@app.route('/manage_sessions_terms', methods=['GET', 'POST'])
@login_required
def manage_sessions_terms():
    if request.method == 'POST':
        session_name = request.form['sessionInput']
        term_name = request.form['termInput']
        new_session = Session(name=session_name, term=term_name)
        db.session.add(new_session)
        db.session.commit()
        flash('Session & Term added successfully.', 'success')
        return redirect(url_for('manage_sessions_terms'))  # Redirect to the same page to show the updated list

    sessions = Session.query.all()
    return render_template('manageSessionsTerms.html', title='Manage Sessions and Terms', sessions=sessions)


@app.route('/delete_session/<int:session_id>')
@login_required
def delete_session(session_id):
    try:
        session_to_delete = Session.query.get_or_404(session_id)
        if session_to_delete:
            db.session.delete(session_to_delete)
            db.session.commit()
            flash('Session deleted successfully.', 'success')
        else:
            flash('Error deleting session.', 'error')
    except Exception as e:
        flash(f'Error deleting class: {str(e)}', 'error')

    return redirect(url_for('manage_sessions_terms'))

def hash_and_update_admin_password():
    username = 'admin'  # Replace with your admin's username
    new_password = '123'  # Define the new password here

    with app.app_context():
        user = User.query.filter_by(username=username).first()
        if user:
            hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')
            user.password = hashed_password
            db.session.commit()
            print("Password updated successfully!")
        else:
            print("User not found!")

# Call the function to update the password
hash_and_update_admin_password()
