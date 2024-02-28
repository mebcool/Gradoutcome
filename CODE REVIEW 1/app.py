from flask import *
from flask_sqlalchemy import *
from flask_login import *
from flask import flash
from flask import render_template, redirect, url_for
from sqlalchemy import func
import mysql.connector
from mysql.connector import Error

app = Flask(__name__, static_url_path='/static')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.sqlite'
app.config['SECRET_KEY'] = 'theSecretKey'
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.init_app(app)

db_config = {
    'user': 'meddy',
    'password': 'student195',
    'host': 'radyweb.wsc.western.edu',
    'database': 'post_grad_outcome_bio'
}
def execute_query(query, params=None):
    try:
        cnx = mysql.connector.connect(**db_config)
        cursor = cnx.cursor()
        cursor.execute(query, params)
        result = cursor.fetchall()
        return result
    except mysql.connector.Error as err:
        print("Error:", err)
    finally:
        if 'cnx' in locals() and cnx.is_connected():
            cursor.close()
            cnx.close()

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

@app.route('/queries')
def queries():
    query_total_accepted = "SELECT COUNT(*) FROM APPLICATION WHERE accepted = 1"
    query_total_applications = "SELECT COUNT(*) FROM APPLICATION"
    total_accepted = execute_query(query_total_accepted)[0][0]
    total_applications = execute_query(query_total_applications)[0][0]
    total_acceptance_rate = round((total_accepted / total_applications) * 100, 2) if total_applications > 0 else 0.0

    query_school_types = "SELECT DISTINCT school_type FROM SCHOOL"
    school_types = [row[0] for row in execute_query(query_school_types)]

    query_application_types = "SELECT DISTINCT program FROM APPLICATION"
    application_types = [row[0] for row in execute_query(query_application_types)]

    query_school_names = "SELECT DISTINCT school_name FROM SCHOOL"
    school_names = [row[0] for row in execute_query(query_school_names)]
    return render_template('queries.html',  total_acceptance_rate=total_acceptance_rate, school_types=school_types,application_types=application_types, school_names=school_names)

@app.route('/query_acceptance_by_year', methods=['POST'])
def query_acceptance_by_year():
    start_year = request.form['start_year']
    end_year = request.form['end_year']
    query_total = "SELECT COUNT(*) FROM APPLICATION WHERE year_applied BETWEEN %s AND %s"
    query_accepted = "SELECT COUNT(*) FROM APPLICATION WHERE year_applied BETWEEN %s AND %s AND accepted = 1"
    total = execute_query(query_total, (start_year, end_year))[0][0]
    accepted = execute_query(query_accepted, (start_year, end_year))[0][0]
    acceptance_rate = round((accepted / total) * 100, 2)if total > 0 else 0.0
    return render_template('queries.html', acceptance_rate_by_year=acceptance_rate)

@app.route('/query_acceptance_by_school_type', methods=['POST'])
def query_acceptance_by_school_type():
    school_type = request.form['school_type']
    query_total = "SELECT COUNT(*) FROM APPLICATION JOIN SCHOOL ON APPLICATION.school_id = SCHOOL.school_id WHERE SCHOOL.school_type = %s"
    query_accepted = "SELECT COUNT(*) FROM APPLICATION JOIN SCHOOL ON APPLICATION.school_id = SCHOOL.school_id WHERE SCHOOL.school_type = %s AND APPLICATION.accepted = 1"
    total = execute_query(query_total, (school_type,))[0][0]
    accepted = execute_query(query_accepted, (school_type,))[0][0]
    acceptance_rate = round((accepted / total) * 100, 2) if total > 0 else 0.0
    return render_template('queries.html', acceptance_rate_by_school_type=acceptance_rate)

@app.route('/query_acceptance_by_application_type', methods=['POST'])
def query_acceptance_by_application_type():
    application_type = request.form['application_type']
    query_total = "SELECT COUNT(*) FROM APPLICATION WHERE program = %s"
    query_accepted = "SELECT COUNT(*) FROM APPLICATION WHERE program = %s AND accepted = 1"
    total = execute_query(query_total, (application_type,))[0][0]
    accepted = execute_query(query_accepted, (application_type,))[0][0]
    acceptance_rate = round((accepted / total) * 100, 2) if total > 0 else 0.0
    return render_template('queries.html', acceptance_rate_by_application_type=acceptance_rate)

@app.route('/query_success_rate_reapplicants', methods=['POST'])
def query_success_rate_reapplicants():
    query_total_students = "SELECT COUNT(DISTINCT stu_id) FROM APPLICATION"
    query_reapplicants = "SELECT COUNT(*) FROM (SELECT stu_id FROM APPLICATION GROUP BY stu_id HAVING COUNT(*) > 1) AS reapplicants"
    total_students = execute_query(query_total_students)[0][0]
    reapplicants = execute_query(query_reapplicants)[0][0]
    success_rate_reapplicants = round((reapplicants / total_students) * 100, 2) if total_students > 0 else 0.0
    return render_template('queries.html', success_rate_reapplicants=success_rate_reapplicants)

@app.route('/query_acceptance_by_school_name', methods=['POST'])
def query_acceptance_by_school_name():
    school_name = request.form['school_name']
    query_total = "SELECT COUNT(*) FROM APPLICATION JOIN SCHOOL ON APPLICATION.school_id = SCHOOL.school_id WHERE SCHOOL.school_name = %s"
    query_accepted = "SELECT COUNT(*) FROM APPLICATION JOIN SCHOOL ON APPLICATION.school_id = SCHOOL.school_id WHERE SCHOOL.school_name = %s AND APPLICATION.accepted = 1"
    total = execute_query(query_total, (school_name,))[0][0]
    accepted = execute_query(query_accepted, (school_name,))[0][0]
    acceptance_rate = round((accepted / total) * 100, 2) if total > 0 else 0.0
    return render_template('queries.html', acceptance_rate_by_school_name=acceptance_rate)


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
