from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import logout_user, login_user
from sams.main.forms import LoginForm
from sams.models import User

main = Blueprint('main', __name__, template_folder='templates')


@main.route("/")
@main.route("/login", methods=['GET', 'POST'])
def login():
    form = LoginForm()
    # if current_user.is_authenticated:
    #     return redirect(url_for('managerDashboard'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()
        if not user:
            flash('Please check your user details and try again.', 'danger')
            return redirect(url_for('main.login'))

        login_user(user, remember=True)
        return redirect_appropriate_dashboard(user.role_id)

    return render_template('login.html', title='Login', form=form)


def redirect_appropriate_dashboard(role_id):
    """Helper function to redirect user to appropriate dashboard based on role_id."""
    if role_id == 1:
        return redirect(url_for('admin.adminDashboard'))
    elif role_id == 2:
        return redirect(url_for('teacher.teacherDashboard'))
    elif role_id == 3:
        return redirect(url_for('student.studentDashboard'))
    else:
        flash('Your account does not have a valid role assigned. Please contact support.', 'warning')
        return redirect(url_for('main.login'))


@main.route("/logout")
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.login'))
