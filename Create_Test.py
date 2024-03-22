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