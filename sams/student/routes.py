import os
from datetime import datetime
from flask import Blueprint, render_template, request, current_app
from flask import redirect, url_for, flash
from flask_login import current_user, login_required

from sams import db
from sams.models import Attendance, Student

import cv2
import numpy as np
import face_recognition
from sams.videoCapture import VideoCapture

student = Blueprint('student', __name__, template_folder='templates', url_prefix='/student')


@student.route('/')
def studentDashboard():  # put application's code here
    if not current_user or not hasattr(current_user, 'student'):
        flash('Access denied. Please log in with a student account.', 'warning')
        return redirect(url_for('main.login'))

    student_id = current_user.student.id  # assuming current_user is linked to the Student model

    # Fetch all attendance records for the logged-in student
    attendance_records = Attendance.query.filter_by(student_id=student_id).all()

    # Calculate total, present, and absent days
    total_days = len(attendance_records)
    present_days = sum(1 for record in attendance_records if record.status)
    absent_days = total_days - present_days

    # Check today's attendance status
    todays_attendance = Attendance.query.filter_by(student_id=current_user.student.id, date=datetime.today().date()).first()

    return render_template("studentDashboard.html", total_days=total_days, present_days=present_days,
                           absent_days=absent_days, todays_attendance=todays_attendance)


# THIS IS FROM STUDENTS DASHBOARD
@student.route("/student_view_attendance", methods=['GET', 'POST'])
def studentViewAttendance():
    if not current_user or not hasattr(current_user, 'student'):
        flash('Access denied. Please log in with a student account.', 'warning')
        return redirect(url_for('main.login'))

    student_id = current_user.student.id
    filter_type = request.args.get('filter_type', 'all')
    attendances = Attendance.query.filter(Attendance.student_id == student_id)

    if filter_type == 'single_date':
        date = request.args.get('single_date')
        if date:
            attendances = attendances.filter(
                db.func.date(Attendance.date) == datetime.strptime(date, '%Y-%m-%d').date())
    elif filter_type == 'date_range':
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        if start_date and end_date:
            attendances = attendances.filter(Attendance.date >= datetime.strptime(start_date, '%Y-%m-%d').date(),
                                             Attendance.date <= datetime.strptime(end_date, '%Y-%m-%d').date())

    attendances = attendances.all()
    attendance_data = [{
        'index': i + 1,
        'full_name': current_user.student.user.fullname,
        'email': current_user.student.user.email,
        'admission_no': current_user.student.admission_no,
        'class': current_user.student.class_.name,
        'class_arm': current_user.student.class_arm.name,
        'status': 'Present' if att.status else 'Absent',
        'date': att.date.strftime('%Y-%m-%d')
    } for i, att in enumerate(attendances)]

    return render_template('studentViewAttendance.html', attendances=attendance_data)


@student.route("/mark-attendance")
@login_required
def mark_face_attendance():
    video_capture = VideoCapture(1)

    known_face_encodings = []
    known_face_names = []
    known_faces_filenames = []

    for (dirpath, dirnames, filenames) in os.walk(current_app.config['UPLOAD_FOLDER']):
        known_faces_filenames.extend(filenames)
        break

    for filename in known_faces_filenames:
        face = face_recognition.load_image_file(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
        known_face_names.append(filename[:-4])
        known_face_encodings.append(face_recognition.face_encodings(face)[0])

    face_locations = []
    face_encodings = []
    face_names = []
    process_this_frame = True

    flag = False

    while True:
        frame = video_capture.read()
        # Process every frame only one time
        if process_this_frame:
            # Find all the faces and face encodings in the current frame of video
            face_locations = face_recognition.face_locations(frame)
            face_encodings = face_recognition.face_encodings(
                frame, face_locations)

            # Initialize an array for the name of the detected users
            face_names = []
            # * ---------- Initialyse JSON to EXPORT --------- *
            json_to_export = {}
            for face_encoding in face_encodings:
                # See if the face is a match for the known face(s)
                matches = face_recognition.compare_faces(
                    known_face_encodings, face_encoding)
                roll_name = "Unknown"  # roll_name variables has roll no. and named saved. e.g. rahul-1666

                # Use the known face with the smallest distance to the new face
                face_distances = face_recognition.face_distance(
                    known_face_encodings, face_encoding)
                best_match_index = np.argmin(face_distances)
                if matches[best_match_index]:
                    admission_number = known_face_names[best_match_index].split('.')[0]

                    if current_user.student.admission_no == admission_number:
                        roll_name = current_user.student.user.fullname

                        attendance = Attendance.query.filter_by(
                            student_id=current_user.student.id,
                            date=datetime.today().date()
                        ).first()

                        if not attendance:
                            attendance = Attendance(student_id=current_user.student.id,
                                                    status=True,
                                                    teacher_id=current_user.student.class_.teachers[0].id,
                                                    class_id=current_user.student.class_id,
                                                    class_arm_id=current_user.student.class_arm_id,
                                                    )

                            db.session.add(attendance)
                            db.session.commit()

                            flag = True

                face_names.append(roll_name)

        process_this_frame = not process_this_frame

        for (top, right, bottom, left), roll_name in zip(face_locations, face_names):

            # Draw a box around the face
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)

            # Draw a label with a name below the face
            font = cv2.FONT_HERSHEY_DUPLEX
            if flag:
                cv2.putText(frame, "Marked! Press 'q' to quit.", (left + 6, bottom - 6),
                            font, 0.5, (255, 255, 255), 1)

            # Display the resulting image
        cv2.imshow('Marking attendance', frame)

        # Hit 'q' on the keyboard to quit!
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        # Release handle to the webcam
    video_capture.release()
    cv2.destroyAllWindows()

    if flag:
        flash('Attendance marked successfully', 'success')
    else:
        flash('Attendance already marked', 'warning')

    return redirect(url_for('student.studentDashboard'))