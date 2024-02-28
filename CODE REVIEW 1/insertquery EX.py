import mysql.connector
from mysql.connector import Error

try:
    cnx = mysql.connector.connect(user='meddy', password='student195',
                                  host='radyweb.wsc.western.edu',
                                  database='post_grad_outcome_bio')
    cursor = cnx.cursor()

    add_student = ("INSERT INTO STUDENT "
                   "(stu_name, stu_phone, stu_email, stu_year_grad, stu_degree) "
                   "VALUES (%s, %s, %s, %s, %s)")
    student_data = ('John Doe', '123-456-7890', 'john.doe@example.com', '2022', 'CS')
    cursor.execute(add_student, student_data)
    stu_id = cursor.lastrowid

    add_school = ("INSERT INTO SCHOOL "
                  "(school_name, school_type) "
                  "VALUES (%s, %s)")
    school_data = ('Western University', 'Postgrad')
    cursor.execute(add_school, school_data)
    school_id = cursor.lastrowid

    add_application = ("INSERT INTO APPLICATION "
                       "(year_applied, program, accepted, stu_id, school_id) "
                       "VALUES (%s, %s, %s, %s, %s)")
    application_data = ('2021', 'Computer Science', True, stu_id, school_id)
    cursor.execute(add_application, application_data)

    cnx.commit()

    cursor.execute("SELECT * FROM STUDENT")
    print("STUDENT table:")
    for row in cursor.fetchall():
        print(row)

    cursor.execute("SELECT * FROM APPLICATION")
    print("\nAPPLICATION table:")
    for row in cursor.fetchall():
        print(row)

    cursor.execute("SELECT * FROM SCHOOL")
    print("\nSCHOOL table:")
    for row in cursor.fetchall():
        print(row)

except Error as e:
    print("Error:", e)

finally:
    if 'cnx' in locals() and cnx.is_connected():
        cursor.close()
        cnx.close()
