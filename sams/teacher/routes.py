import logging
from datetime import datetime

from flask import Blueprint, render_template
from flask import redirect, url_for, flash, jsonify, request
from flask_login import login_required, current_user
from sqlalchemy import func

from sams import db
from sams.models import Student, Class, ClassArm, Attendance

teacher = Blueprint('teacher', __name__, template_folder='templates', url_prefix='/teacher')


@teacher.route('/')
def teacherDashboard():
    if not current_user or not current_user.teacher:
        flash('Access denied. Please log in with a teacher account.', 'warning')
        return redirect(url_for('main.login'))

    teacher = current_user.teacher
    if not teacher:
        flash('Teacher profile not found.', 'error')
        return redirect(url_for('main.login'))

    # Fetch the count of students in the same class (and class arm if applicable)
    if teacher.class_id and teacher.class_arm_id:
        student_count = Student.query.filter_by(class_id=teacher.class_id, class_arm_id=teacher.class_arm_id).count()
    elif teacher.class_id:
        student_count = Student.query.filter_by(class_id=teacher.class_id).count()
    else:
        student_count = 0  # Default to 0 if no specific class or class arm is assigned

    # Initialize variables to hold class and class arm names
    class_name = "Not assigned"
    class_arm_name = "Not assigned"

    # Fetch class name if class_id is set
    if teacher.class_id:
        cls = Class.query.get(teacher.class_id)
        if cls:
            class_name = cls.name

    # Fetch class arm name if class_arm_id is set
    if teacher.class_arm_id:
        class_arm = ClassArm.query.get(teacher.class_arm_id)
        if class_arm:
            class_arm_name = class_arm.name

    class_id = teacher.class_id
    if not class_id:
        flash('No class assigned to this teacher.', 'info')
        return redirect(url_for('main.login'))
    attendance_count = Attendance.query.filter_by(class_id=class_id).count()

    return render_template('teacherDashboard.html', student_count=student_count, class_name=class_name,
                           class_arm_name=class_arm_name, attendance_count=attendance_count)


@teacher.route("/view_students")
def viewStudents():
    if not current_user or not hasattr(current_user, 'teacher'):
        flash('Access denied. Please log in with a teacher account.', 'warning')
        return redirect(url_for('main.login'))

    teacher = current_user.teacher
    if not teacher:
        flash('Teacher profile not found. Please contact support.', 'error')
        return redirect(url_for('teacher.teacherDashboard'))

    if not teacher.class_id:
        flash('You are not assigned to any class. Please contact the admin.', 'error')
        return redirect(url_for('teacher.teacherDashboard'))  # Redirect to a safe landing page

    # Fetch students assigned to the same class as the teacher
    students = Student.query.filter_by(class_id=teacher.class_id, class_arm_id=teacher.class_arm_id).all()
    return render_template('viewStudents.html', title='View Students', students=students)


@teacher.route("/take_attendance", methods=['GET', 'POST'])
@login_required
def takeAttendance():
    if not current_user or not hasattr(current_user, 'teacher'):
        flash('Access denied. Please log in with a teacher account.', 'warning')
        return redirect(url_for('main.login'))

    teacher = current_user.teacher
    if not teacher:
        flash('Teacher profile not found. Please contact support.', 'error')
        return redirect(url_for('teacher.teacherDashboard'))

    if not teacher.class_id:
        flash('You are not assigned to any class. Please contact the admin.', 'error')
        return redirect(url_for('teacher.teacherDashboard'))  # Redirect to a safe landing page
    students = Student.query.filter_by(class_id=teacher.class_id, class_arm_id=teacher.class_arm_id).all()

    return render_template('takeAttendance.html', title='Take Attendance', students=students)


@teacher.route('/mark_attendance', methods=['POST'])
@login_required
def mark_attendance():
    if not current_user or not hasattr(current_user, 'teacher'):
        return jsonify({'error': 'Unauthorized access'}), 403

        # Data contains student IDs and their attendance status
    attendance_data = request.get_json()
    today_date = datetime.utcnow().date()

    if not attendance_data:
        return jsonify({'error': 'No data provided'}), 400

    # Get all students in the teacher's class and class arm
    students = Student.query.filter_by(
        class_id=current_user.teacher.class_id,
        class_arm_id=current_user.teacher.class_arm_id
    ).all()

    # Create a set of student IDs from the input for quick lookup
    marked_students = {int(data['studentId']): data['status'] for data in attendance_data}

    for student in students:
        # Check if the student was marked present or not
        status = marked_students.get(student.id, False)  # Default to False if not marked

        # Find or create attendance record
        attendance = Attendance.query.filter_by(
            student_id=student.id,
            date=today_date
        ).first()

        if attendance:
            attendance.status = status
        else:
            # Create a new attendance record
            attendance = Attendance(
                student_id=student.id,
                teacher_id=current_user.teacher.id,
                status=status,
                date=today_date,
                class_id=current_user.teacher.class_id,
                class_arm_id=current_user.teacher.class_arm_id,
            )
            db.session.add(attendance)

    db.session.commit()
    return jsonify({'message': 'Attendance successfully updated'}), 200


@teacher.route("/view_students_for_attendance")
@login_required
def viewStudentsForAttendance():
    teacher = current_user.teacher
    if not teacher or not teacher.class_id:
        flash('You are not assigned to any class.', 'error')
        return redirect(url_for('teacher.teacherDashboard'))

    students = Student.query.filter_by(class_id=teacher.class_id, class_arm_id=teacher.class_arm_id).all()
    return render_template('takeAttendance.html', students=students)


@teacher.route("/view_class_attendance")
@login_required
def viewClassAttendance():
    if not current_user or not hasattr(current_user, 'teacher'):
        flash('Access denied. Please log in with a teacher account.', 'warning')
        return redirect(url_for('main.login'))

    teacher = current_user.teacher
    if not teacher:
        flash('Teacher profile not found. Please contact support.', 'error')
        return redirect(url_for('teacher.teacherDashboard'))

    if not teacher.class_id or not teacher.class_arm_id:
        flash('You are not assigned to any class or class arm. Please contact the admin.', 'error')
        return redirect(url_for('teacher.teacherDashboard'))

    today = datetime.utcnow().date()  # Adjust as needed for timezone considerations

    # Modify query to filter students by both class_id and class_arm_id
    results = db.session.query(
        Student,
        Attendance.status,
        Attendance.date
    ).outerjoin(
        Attendance, (Attendance.student_id == Student.id) & (func.date(Attendance.date) == today)
    ).filter(
        Student.class_id == teacher.class_id,
        Student.class_arm_id == teacher.class_arm_id
    ).all()

    student_data = [{
        'fullname': student.user.fullname,
        'email': student.user.email,
        'admission_no': student.admission_no,
        'class_name': student.class_.name,
        'class_arm_name': student.class_arm.name,
        'date': attendance_date.strftime('%Y-%m-%d') if attendance_date else 'No Data',
        'status': 'Present' if status else 'Absent'
    } for student, status, attendance_date in results]

    return render_template('viewClassAttendance.html', title='View Class Attendance', students=student_data)


@teacher.route("/search_by_date", methods=['GET'])
@login_required
def search_by_date():
    date_str = request.args.get('date')
    if not date_str:
        flash('No date selected', 'warning')
        return redirect(url_for('viewClassAttendance'))  # Adjust this to your appropriate 'view' function

    try:
        search_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        flash('Invalid date format', 'error')
        return redirect(url_for('viewClassAttendance'))

    teacher = current_user.teacher
    if not teacher:
        flash('Teacher profile not found. Please contact support.', 'error')
        return redirect(url_for('teacher.teacherDashboard'))

    if not teacher.class_id or not teacher.class_arm_id:
        flash('You are not assigned to any class or class arm.', 'error')
        return redirect(url_for('teacher.teacherDashboard'))

    # Check if there are any attendance records for the given date
    attendance_exists = db.session.query(Attendance.id).filter(
        Attendance.date == search_date,
        Attendance.class_id == teacher.class_id,
        Attendance.class_arm_id == teacher.class_arm_id  # Include class arm in the check
    ).first()

    if not attendance_exists:
        flash('No record found for this date in your class and class arm.', 'info')
        return redirect(url_for('teacher.viewClassAttendance'))  # Adjust redirect as necessary

    # Fetching detailed records for students
    results = db.session.query(
        Student,
        Attendance.status
    ).outerjoin(
        Attendance, (Attendance.student_id == Student.id) & (func.date(Attendance.date) == search_date)
    ).filter(
        Student.class_id == teacher.class_id,
        Student.class_arm_id == teacher.class_arm_id  # Filtering by class arm as well
    ).all()

    student_data = [{
        'fullname': student.user.fullname,
        'email': student.user.email,
        'admission_no': student.admission_no,
        'class_name': student.class_.name,
        'class_arm_name': student.class_arm.name,
        'status': 'Present' if status else 'Absent'
    } for student, status in results]

    return render_template('viewClassAttendance.html', title='View Class Attendance', students=student_data)


@teacher.route("/view_class_attendance_by_date")
@login_required
def viewClassAttendanceByDate():
    if not current_user or not hasattr(current_user, 'teacher'):
        flash('Access denied. Please log in with a teacher account.', 'warning')
        return redirect(url_for('main.login'))

    teacher = current_user.teacher
    if not teacher:
        flash('Teacher profile not found. Please contact support.', 'error')
        return redirect(url_for('teacher.teacherDashboard'))

    if not teacher.class_id or not teacher.class_arm_id:
        flash('You are not assigned to any class or class arm. Please contact the admin.', 'error')
        return redirect(url_for('teacher.teacherDashboard'))

    today = datetime.utcnow().date()  # Adjust as needed for timezone considerations

    # Modify query to use func.date to ignore the time part of the datetime and include class arm
    results = db.session.query(
        Student,
        Attendance.status
    ).outerjoin(
        Attendance, (Attendance.student_id == Student.id) & (func.date(Attendance.date) == today)
    ).filter(
        Student.class_id == teacher.class_id,
        Student.class_arm_id == teacher.class_arm_id  # Filter by class arm as well
    ).all()

    student_data = []
    for student, status in results:
        student_data.append({
            'fullname': "",
            'email': "",
            'admission_no': "",
            'class_name': "",
            'class_arm_name': "",
            'status': ""
        })

    return render_template('viewClassAttendance.html', title='View Class Attendance By Date', students=student_data)


# THIS IS FROM TEACHERS DASHBOARD
@teacher.route("/view_student_attendance", methods=['GET', 'POST'])
@login_required
def viewStudentAttendance():
    if not current_user or not hasattr(current_user, 'teacher'):
        flash('Access denied. Please log in with a teacher account.', 'warning')
        return redirect(url_for('main.login'))

    teacher = current_user.teacher
    if not teacher or not teacher.class_id or not teacher.class_arm_id:
        flash('No class or class arm assigned.', 'error')
        return redirect(url_for('teacher.teacherDashboard'))

    # Fetch students for dropdown - only those in the same class and class arm as the teacher
    students = Student.query.filter(
        Student.class_id == teacher.class_id,
        Student.class_arm_id == teacher.class_arm_id
    ).all()
    student_options = [(student.id, student.user.fullname) for student in students]

    student_records = []
    if request.method == 'POST':
        student_id = request.form.get('student_name')
        query = Attendance.query.filter(Attendance.student_id == student_id)
        student_records = query.all()

    return render_template('viewStudentAttendance.html', student_options=student_options,
                           student_records=student_records)


@teacher.route("/todays_report")
@login_required
def todaysReport():
    return render_template('todaysReport.html', title='Today\'s Report')
