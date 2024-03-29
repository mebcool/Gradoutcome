from flask import *
from flask_sqlalchemy import *
from flask_login import *
from flask import flash
from flask import render_template, redirect, url_for
from sqlalchemy import func
import mysql.connector
from mysql.connector import Error
import datetime

app = Flask(__name__, static_url_path='/static')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.sqlite'
app.config['SECRET_KEY'] = 'theSecretKey'
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.init_app(app)
today = datetime.date.today()
year = today.year
ten_years_ago = year - 10

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
        print(f"Executing query: {query} with params: {params}")
        cursor.execute(query, params)
        result = cursor.fetchall()
        print(result)
        print(f"Query returned {len(result)} rows")
        return result
    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        if cnx.is_connected():
            cursor.close()
            cnx.close()

def execute_insert(insert, params):
    try:
        cnx = mysql.connector.connect(**db_config)
        cursor = cnx.cursor()
        cursor.execute(insert, params)
        cnx.commit()
    except mysql.connector.Error as err:
        print("Error: ", err)
    finally:
        if 'cnx' in locals() and cnx.is_connected():
            cursor.close()
            cnx.close()

##code below is outdated, back when the DB was in flask and SQL alchemy, not MySQL...
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
##END outdated code do not use in Code Review

@app.route('/')
def index():
    return render_template('index.html')

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
        program = request.form.get('program')
        accepted = 'accepted' in request.form
        degree = request.form.get('degree')
        graduation_year = request.form.get('graduation_year')

        findStudent = ("SELECT stu_name FROM Student WHERE stu_name = %s")
        stuParams = (name)
        studentExists = execute_query(findStudent, stuParams)
        print("Student exists:", studentExists)

        if studentExists == None:
            insertStudentCMD = ("INSERT INTO student (stu_name, stu_phone, stu_email, stu_year_grad, stu_degree)"
                                "VALUES (%s, %s, %s, %s, %s)")
            studentData = (name, phone, email, graduation_year, degree)
            execute_insert(insertStudentCMD, studentData)

        findSchool = ("SELECT school_name FROM School WHERE school_name = %s")
        schoolParams = (school_name)
        schoolExists = execute_query(findSchool, schoolParams)

        if schoolExists == None:
            insertSchoolCMD = ("INSERT INTO SCHOOL "
                               "(school_name, school_type) "
                               "VALUES (%s, %s)")
            schoolData = (school_name, school_type)
            execute_insert(insertSchoolCMD, schoolData)

        findStuId = ("SELECT stu_id FROM Student WHERE stu_name = %s")
        stuId = execute_query(findStuId, stuParams)

        findSchoolId = ("SELECT school_id FROM School WHERE school_name = %s")
        schoolId = execute_query(findSchoolId, schoolParams)

        insertApplicationCMD = ("INSERT INTO Application (year_applied, program, accepted, stu_id, school_id"
                                "VALUES (%s, %s, %s, %s, %s")
        applicationData = (yearapplied, program, accepted, stuId, schoolId)
        execute_insert(insertApplicationCMD, applicationData)

        # Add print statements for debugging
        print(f"yearapplied: {yearapplied}")
        print(f"accepted: {accepted}")

        return redirect(url_for('view_db'))

    return render_template('createstudent.html')

@app.route('/view_db')
@login_required
def view_db():
    tab = request.args.get('tab', 'All')

    if tab == 'Healthcare':
        query = """
        SELECT a.year_applied, s.stu_name, sch.school_type, sch.school_name, a.program, a.accepted, s.stu_id, a.app_id
        FROM application AS a
        JOIN student AS s ON a.stu_id = s.stu_id
        JOIN school AS sch ON a.school_id = sch.school_id
        WHERE sch.school_type = 'healthcare' AND a.year_applied >= %s
        """
        applications = execute_query(query, (ten_years_ago,))
    elif tab == 'Postgrad':
        query = """
        SELECT a.year_applied, s.stu_name, sch.school_type, sch.school_name, a.program, a.accepted, s.stu_id, a.app_id
        FROM application AS a
        JOIN student AS s ON a.stu_id = s.stu_id
        JOIN school AS sch ON a.school_id = sch.school_id
        WHERE sch.school_type = 'postgrad' AND a.year_applied >= %s
        """
        applications = execute_query(query, (ten_years_ago,))
    else:  #'All'
        query = """
        SELECT a.year_applied, s.stu_name, sch.school_type, sch.school_name, a.program, a.accepted, s.stu_id, a.app_id
        FROM application AS a
        JOIN student AS s ON a.stu_id = s.stu_id
        JOIN school AS sch ON a.school_id = sch.school_id
        """
        applications = execute_query(query)

    return render_template('view_db.html', applications=applications, active_tab=tab)

@app.route('/queries')
def queries():
    #total accepted and total applications in the last 10 years
    query_total_accepted = f"SELECT * FROM application WHERE accepted = 1 AND year_applied >= %s"
    query_total_applications = f"SELECT * FROM application WHERE year_applied >= %s"
    total_accepted = len(execute_query(query_total_accepted, (ten_years_ago,)))
    total_applications = len(execute_query(query_total_applications, (ten_years_ago,)))

    total_acceptance_rate = round((total_accepted / total_applications) * 100, 2) if total_applications > 0 else 0.0

    #total accepted and total applications in the last 10 years by school type
    query_healthcare_accepted = f"SELECT * FROM application AS a JOIN school AS s ON a.school_id = s.school_id WHERE a.accepted = 1 AND a.year_applied >= %s AND s.school_type = 'healthcare'"
    query_healthcare_applications = f"SELECT * FROM application AS a JOIN school AS s ON a.school_id = s.school_id WHERE a.year_applied >= %s AND s.school_type = 'healthcare'"
    healthcare_accepted = len(execute_query(query_healthcare_accepted, (ten_years_ago,)))
    healthcare_applications = len(execute_query(query_healthcare_applications, (ten_years_ago,)))
    healthcare_acceptance_rate = round((healthcare_accepted / healthcare_applications) * 100, 2) if healthcare_applications > 0 else 0.0

    query_postgrad_accepted = f"SELECT * FROM application AS a JOIN school AS s ON a.school_id = s.school_id WHERE a.accepted = 1 AND a.year_applied >= %s AND s.school_type = 'postgrad'"
    query_postgrad_applications = f"SELECT * FROM application AS a JOIN school AS s ON a.school_id = s.school_id WHERE a.year_applied >= %s AND s.school_type = 'postgrad'"
    postgrad_accepted = len(execute_query(query_postgrad_accepted, (ten_years_ago,)))
    postgrad_applications = len(execute_query(query_postgrad_applications, (ten_years_ago,)))
    postgrad_acceptance_rate = round((postgrad_accepted / postgrad_applications) * 100, 2) if postgrad_applications > 0 else 0.0



    #complete drop down menus
    query_school_types = "SELECT DISTINCT school_type FROM school"
    school_types = [row[0] for row in execute_query(query_school_types)]

    query_application_types = "SELECT DISTINCT program FROM application"
    application_types = [row[0] for row in execute_query(query_application_types)]

    query_school_names = "SELECT DISTINCT school_name FROM school"
    school_names = [row[0] for row in execute_query(query_school_names)]

    return render_template('queries.html',
                           total_acceptance_rate=total_acceptance_rate,
                           healthcare_acceptance_rate=healthcare_acceptance_rate,
                           postgrad_acceptance_rate=postgrad_acceptance_rate,
                           total_accepted=total_accepted,
                           total_applications=total_applications,
                           healthcare_accepted=healthcare_accepted,
                           healthcare_applications=healthcare_applications,
                           postgrad_accepted=postgrad_accepted,
                           postgrad_applications=postgrad_applications,
                           school_types=school_types,
                           application_types=application_types,
                           school_names=school_names)

@app.route('/query_acceptance_by_year', methods=['POST'])
def query_acceptance_by_year():
    start_year = request.form['start_year']
    end_year = request.form['end_year']
    query_total = "SELECT * FROM application WHERE year_applied BETWEEN %s AND %s"
    query_accepted = "SELECT * FROM application WHERE year_applied BETWEEN %s AND %s AND accepted = 1"
    total_result = len(execute_query(query_total, (start_year, end_year)))
    accepted_result = len(execute_query(query_accepted, (start_year, end_year)))
    acceptance_rate_by_year = round((accepted_result / total_result) * 100, 2) if total_result > 0 else 0.0
    return render_template('queries.html', acceptance_rate_by_year=acceptance_rate_by_year,
                           total_result=total_result,
                           accepted_result=accepted_result)

@app.route('/query_acceptance_by_school_name', methods=['POST'])
def query_acceptance_by_school_name():
    school_name = request.form['school_name']
    query_total_name = "SELECT * FROM APPLICATION JOIN SCHOOL ON APPLICATION.school_id = SCHOOL.school_id WHERE SCHOOL.school_name = %s AND year_applied >= %s"
    query_accepted_name = "SELECT * FROM APPLICATION JOIN SCHOOL ON APPLICATION.school_id = SCHOOL.school_id WHERE SCHOOL.school_name = %s AND APPLICATION.accepted = 1 AND year_applied >= %s"
    total_result_name = len(execute_query(query_total_name, (school_name, ten_years_ago,)))
    accepted_result_name = len(execute_query(query_accepted_name, (school_name, ten_years_ago,)))
    acceptance_rate_by_school_name = round((accepted_result_name / total_result_name) * 100, 2)if total_result_name > 0 else 0.0
    return render_template('queries.html', acceptance_rate_by_school_name=acceptance_rate_by_school_name,
                           total_result_name=total_result_name,
                           accepted_result_name=accepted_result_name)

@app.route('/query_acceptance_by_program', methods=['POST'])
def query_acceptance_by_program():
    program = request.form['program']
    query_total = "SELECT * FROM APPLICATION WHERE program = %s AND year_applied >= %s"
    query_accepted = "SELECT * FROM APPLICATION WHERE program = %s AND accepted = 1 AND year_applied >= %s"
    total_program = len(execute_query(query_total, (program, ten_years_ago,)))
    accepted_program = len(execute_query(query_accepted, (program, ten_years_ago,)))
    acceptance_rate_by_program = round((accepted_program / total_program) * 100, 2)if total_program > 0 else 0.0
    return render_template('queries.html', acceptance_rate_by_program=acceptance_rate_by_program,
                           total_program=total_program,
                           accepted_program=accepted_program)

@app.route('/query_success_rate_reapplicants', methods=['POST'])
def query_success_rate_reapplicants():
    query_total_students = "SELECT DISTINCT stu_id FROM APPLICATION WHERE year_applied >= %s"
    query_reapplicants = """
        SELECT * FROM (
            SELECT a.stu_id, a.year_applied, s.school_type
            FROM APPLICATION a
            JOIN SCHOOL s ON a.school_id = s.school_id
            GROUP BY a.stu_id 
            HAVING COUNT(*) > 1
        ) AS reapplicants
        WHERE year_applied >= %s
        AND NOT EXISTS (
            SELECT 1 FROM APPLICATION a2
            JOIN SCHOOL s2 ON a2.school_id = s2.school_id
            WHERE a2.stu_id = reapplicants.stu_id
            AND s2.school_type = reapplicants.school_type
            AND a2.app_id <> (
                SELECT MIN(a3.app_id) FROM APPLICATION a3 
                WHERE a3.stu_id = reapplicants.stu_id
            )
        )
    """
    total_students = len(execute_query(query_total_students, (ten_years_ago,)))
    reapplicants = len(execute_query(query_reapplicants, (ten_years_ago,)))
    success_rate_reapplicants = round((reapplicants / total_students) * 100, 2) if total_students > 0 else 0.0
    return render_template('queries.html', success_rate_reapplicants=success_rate_reapplicants)


@app.route('/advanced_search', methods=['POST'])
@login_required
def advanced_search():
    name = request.form.get('name')
    program = request.form.get('program')
    school_type = request.form.get('school_type')

    query = """
        SELECT a.year_applied, s.stu_name, sch.school_type, sch.school_name, a.program, a.accepted, s.stu_id, a.app_id
        FROM application AS a
        JOIN student AS s ON a.stu_id = s.stu_id
        JOIN school AS sch ON a.school_id = sch.school_id
        WHERE 1=1
    """
    params = []

    if name:
        query += " AND s.stu_name LIKE %s"
        params.append(f'%{name}%')

    if program:
        query += " AND a.program LIKE %s"
        params.append(f'%{program}%')

    if school_type:
        query += " AND sch.school_type LIKE %s"
        params.append(f'%{school_type}%')

    applications = execute_query(query, params)

    return render_template('queries.html', search_results=applications)

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
