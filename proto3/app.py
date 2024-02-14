from flask import *
from flask_sqlalchemy import *
from flask_login import *
from flask import flash
from flask import render_template, redirect, url_for
from sqlalchemy import func


app = Flask(__name__, static_url_path='/static')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.sqlite'
app.config['SECRET_KEY'] = 'theSecretKey'
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.init_app(app)

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.Integer, nullable=True)
    email = db.Column(db.String(50), nullable=True)
    school_id = db.Column(db.Integer, db.ForeignKey('school.id'), unique=True, nullable=True)
    school = db.relationship('School', back_populates='student', uselist=False)
    application = db.relationship('Application', backref='student', lazy=True)
    comments = db.relationship('Comment', backref='student', lazy=True)
    degree = db.Column(db.String(50), nullable=True)
    graduation_year = db.Column(db.Integer, nullable=True)

class School(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    typeof = db.Column(db.String(50), nullable=False)
    student = db.relationship('Student', back_populates='school', uselist=False)

class Application(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    yearapplied = db.Column(db.Integer, nullable=False)
    accepted = db.Column(db.Boolean, nullable=True)
    reapp_accepted_same_field = db.Column(db.Boolean, nullable=True)
    reapp_accepted_diff_field = db.Column(db.Boolean, nullable=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    school_id = db.Column(db.Integer, db.ForeignKey('school.id'), nullable=False)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)

class User(UserMixin, db.Model): # for authentication, only authenticated users can manage the database
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)

@login_manager.user_loader
def load_user(uid):
    user = User.query.get(uid)
    return user

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/createuser', methods=['GET', 'POST'])
def createuser():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if User.query.filter_by(username=username).first():
            return render_template('createuser.html', error='Username already taken. Please choose another one.')

        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)
        return redirect('/')

    return render_template('createuser.html', error=error)

@app.route('/createstudent', methods=['GET', 'POST'])
@login_required
def createstudent():
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        email = request.form.get('email')
        school_name = request.form.get('school_name')
        school_type = request.form.get('school_type')
        yearapplied = request.form.get('yearapplied')
        accepted = 'accepted' in request.form
        reapp_accepted_same_field = 'reapp_accepted_same_field' in request.form
        reapp_accepted_diff_field = 'reapp_accepted_diff_field' in request.form
        degree = request.form.get('degree')
        graduation_year = request.form.get('graduation_year')


        new_student = Student(name=name, phone=phone, email=email)
        new_student.degree = degree
        new_student.graduation_year = graduation_year
        db.session.add(new_student)
        db.session.commit()

        # Create a new school instance and associate it with the newly created student
        new_school = School(name=school_name, typeof=school_type, student=new_student)
        db.session.add(new_school)
        db.session.commit()

        # Create a new application instance and associate it with the newly created student and school
        new_application = Application(
            yearapplied=yearapplied,
            accepted=accepted,
            reapp_accepted_same_field=reapp_accepted_same_field,
            reapp_accepted_diff_field=reapp_accepted_diff_field,
            student=new_student,
            school_id=new_school.id
        )
        db.session.add(new_application)
        db.session.commit()

        # Add print statements for debugging
        print(f"yearapplied: {yearapplied}")
        print(f"accepted: {accepted}")
        print(f"reapp_accepted_same_field: {reapp_accepted_same_field}")
        print(f"reapp_accepted_diff_field: {reapp_accepted_diff_field}")

        return redirect(url_for('view_db'))

    return render_template('createstudent.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if not user or password != user.password:
            error = 'Invalid username or password. Please try again.'
        else:
            login_user(user)
            return redirect('/')

    return render_template('login.html', error=error)

@app.route('/view_users')
@login_required
def view_users():
    users = User.query.all()
    return render_template('view_users.html', users=users)

@app.route('/view_db')
@login_required
def view_db():
    students = Student.query.all()
    return render_template('view_db.html', students=students)

@app.route('/updateuser', methods=['GET', 'POST'])
@login_required
def updateuser():
    error = None
    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']

        if current_password != current_user.password:
            error = 'Current password is incorrect. Please try again.'
        else:
            current_user.password = new_password
            db.session.commit()
            return redirect('/')

    return render_template('updateuser.html', error=error)

@app.route('/deletestudent/<int:id>')
@login_required
def deletestudent(id):
    student = Student.query.get(id)

    # Delete associated applications first
    for application in student.application:
        db.session.delete(application)

    # Now delete the student
    db.session.delete(student)
    db.session.commit()

    return redirect('/view_db')

@app.route('/add_comment/<int:id>', methods=['POST'])
@login_required
def add_comment(id):
    student = Student.query.get(id)

    if not student:
        flash("Student not found", "error")
        return redirect('/view_db')

    comment_text = request.form.get('comment')

    new_comment = Comment(text=comment_text, student=student)
    db.session.add(new_comment)
    db.session.commit()

    return redirect(url_for('student_profile', id=id))


@app.route('/student_profile/<int:id>')
@login_required
def student_profile(id):
    student = Student.query.get(id)

    if not student:
        # Handle case when student is not found
        flash("Student not found", "error")
        return redirect('/view_db')

    return render_template('student_profile.html', student=student)


@app.route('/updatestudent/<int:id>', methods=['GET', 'POST'])
@login_required
def updatestudent(id):
    student = Student.query.get(id)

    if request.method == 'POST':
        student.name = request.form['name']
        student.phone = request.form['phone']
        student.email = request.form['email']

        # Update School Information
        if student.school:
            student.school.name = request.form['school_name']
            student.school.typeof = request.form['school_type']

        # Update Application Information
        if student.application:
            application = student.application[0]
            application.yearapplied = request.form['yearapplied']
            application.accepted = 'accepted' in request.form
            application.reapp_accepted_same_field = 'reapp_accepted_same_field' in request.form
            application.reapp_accepted_diff_field = 'reapp_accepted_diff_field' in request.form

        db.session.commit()

        return redirect('/view_db')

    return render_template('updatestudent.html', student=student)

@app.route('/queries', methods=['GET', 'POST'])
@login_required
def queries():
    total_acceptance_rate = calculate_total_acceptance_rate()

    acceptance_rate_by_year = None
    acceptance_rate_by_school_type = None
    acceptance_rate_by_application_type = None
    success_rate_for_reapplicants = None

    if request.method == 'POST':
        start_year = request.form.get('start_year')
        end_year = request.form.get('end_year')
        school_type = request.form.get('school_type')
        application_type = request.form.get('application_type')

        if start_year and end_year:
            acceptance_rate_by_year = calculate_acceptance_rate_by_year(start_year, end_year)

        if school_type:
            acceptance_rate_by_school_type = calculate_acceptance_rate_by_school_type(school_type)

        if application_type:
            acceptance_rate_by_application_type = calculate_acceptance_rate_by_application_type(application_type)

        success_rate_for_reapplicants = calculate_success_rate_for_reapplicants()

    return render_template('queries.html',
                           total_acceptance_rate=total_acceptance_rate,
                           acceptance_rate_by_year=acceptance_rate_by_year,
                           acceptance_rate_by_school_type=acceptance_rate_by_school_type,
                           acceptance_rate_by_application_type=acceptance_rate_by_application_type,
                           success_rate_for_reapplicants=success_rate_for_reapplicants)


def calculate_total_acceptance_rate():
    total_accepted = Application.query.filter_by(accepted=True).count()
    total_applications = Application.query.count()

    return calculate_percentage(total_accepted, total_applications)


def calculate_acceptance_rate_by_year(start_year, end_year):
    accepted_count = Application.query.filter(Application.yearapplied >= start_year,
                                              Application.yearapplied <= end_year,
                                              Application.accepted == True).count()
    total_applications = Application.query.filter(Application.yearapplied >= start_year,
                                                  Application.yearapplied <= end_year).count()

    return calculate_percentage(accepted_count, total_applications)


def calculate_acceptance_rate_by_school_type(school_type):
    accepted_count = Application.query.join(Student).join(School).filter(School.typeof == school_type,
                                                                         Application.accepted == True).count()
    total_applications = Application.query.join(Student).join(School).filter(School.typeof == school_type).count()

    acceptance_rate = calculate_percentage(accepted_count, total_applications)

    return f"{acceptance_rate}%"


def calculate_acceptance_rate_by_application_type(application_type):
    accepted_count = Application.query.filter(func.lower(Application.reapp_accepted_same_field) == func.lower(application_type),
                                              Application.accepted == True).count()
    total_applications = Application.query.filter(func.lower(Application.reapp_accepted_same_field) == func.lower(application_type)).count()

    return calculate_percentage(accepted_count, total_applications)


def calculate_success_rate_for_reapplicants():
    reapplicants = Application.query.filter(Application.reapp_accepted_same_field.isnot(None)).all()
    success_count = sum(1 for app in reapplicants if app.accepted)

    return calculate_percentage(success_count, len(reapplicants))


def calculate_percentage(numerator, denominator):
    if denominator == 0:
        return 0
    return int((numerator / denominator) * 100)

@app.route('/acceptance_rate_by_year', methods=['POST'])
@login_required
def acceptance_rate_by_year():
    start_year = request.form.get('start_year')
    end_year = request.form.get('end_year')

    if start_year and end_year:
        return calculate_acceptance_rate_by_year(start_year, end_year)

    return "Invalid input for year range"

@app.route('/advanced_search', methods=['POST'])
@login_required
def advanced_search():
    name = request.form.get('name')
    phone = request.form.get('phone')
    email = request.form.get('email')
    school_name = request.form.get('school_name')
    school_type = request.form.get('school_type')
    yearapplied = request.form.get('yearapplied')
    accepted = request.form.get('accepted')
    reapp_accepted_same_field = request.form.get('reapp_accepted_same_field')
    reapp_accepted_diff_field = request.form.get('reapp_accepted_diff_field')
    degree = request.form.get('degree')
    graduation_year = request.form.get('graduation_year')

    # Query the database based on the provided search criteria
    query = Student.query.join(Application)

    if name:
        query = query.filter(Student.name.ilike(f'%{name}%'))

    if phone:
        query = query.filter(Student.phone.ilike(f'%{phone}%'))

    if email:
        query = query.filter(Student.email.ilike(f'%{email}%'))

    if school_name:
        query = query.join(School).filter(School.name.ilike(f'%{school_name}%'))

    if school_type:
        query = query.join(School).filter(School.typeof.ilike(f'%{school_type}%'))

    if yearapplied:
        query = query.join(Application).filter(Application.yearapplied == int(yearapplied))

    if accepted is not None:
        query = query.join(Application).filter(Application.accepted == bool(int(accepted)))

    if reapp_accepted_same_field is not None:
        query = query.join(Application).filter(Application.reapp_accepted_same_field == bool(int(reapp_accepted_same_field)))

    if reapp_accepted_diff_field is not None:
        query = query.join(Application).filter(Application.reapp_accepted_diff_field == bool(int(reapp_accepted_diff_field)))

    if degree:
        query = query.filter(Student.degree.ilike(f'%{degree}%'))

    if graduation_year:
        query = query.filter(Student.graduation_year == int(graduation_year))

    search_results = query.all()

    return render_template('queries.html', total_acceptance_rate=calculate_total_acceptance_rate(),
                           acceptance_rate_by_year=None,
                           acceptance_rate_by_school_type=None,
                           acceptance_rate_by_application_type=None,
                           success_rate_for_reapplicants=None,
                           search_results=search_results)

@app.route('/acceptance_rate_by_school_type', methods=['POST'])
@login_required
def acceptance_rate_by_school_type():
    school_type = request.form.get('school_type')

    if school_type:
        return calculate_acceptance_rate_by_school_type(school_type)

    return "Invalid input for school type"


@app.route('/acceptance_rate_by_application_type', methods=['POST'])
@login_required
def acceptance_rate_by_application_type():
    application_type = request.form.get('application_type')

    if application_type:
        return calculate_acceptance_rate_by_application_type(application_type)

    return "Invalid input for application type"


@app.route('/success_rate_for_reapplicants', methods=['POST'])
@login_required
def success_rate_for_reapplicants():
    return calculate_success_rate_for_reapplicants()


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return render_template('logout.html')

@app.errorhandler(404)
def err404(err):
    return render_template('404.html', err=err)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run()
