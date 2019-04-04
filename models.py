import sqlite3 as sql

# the classes here are a vague analogue to an ORM. I thought it was probably
# more in the spirit of the class to write my own SQL rather than using a pre-made ORM.

connection = sql.connect('canvaspath.sqlite')


class User:
    # each user is identified by their email, and all their main info is stored in the User table
    user_entry = ()
    email = ""
    pw_hash = ""
    name = ""
    age = -1
    gender = ""
    # The type is "S" (student), "P" (professor), or "A" (administrator)
    user_type = ""
    # Fields specific to students:
    major = ""
    street = ""
    zipcode = ""
    # Fields specific to faculty:
    office_address= ""
    department = ""
    title = ""

    def __init__(self, email):
        cursor = connection.cursor()
        cursor.execute('SELECT * FROM User WHERE User.email = ?', email)
        user_entry = cursor.fetchone()
        email = user_entry[0]
        pw_hash = user_entry[1]
        name = user_entry[2]
        age = int(user_entry[3])
        gender = user_entry[4]
        user_type = user_entry[5]

        if user_type == "S":
            cursor.execute('SELECT * FROM Student WHERE Student.email = ?', email)
            student_entry = cursor.fetchone()
            major = student_entry[1]
            street = student_entry[2]
            zipcode = student_entry[3]

        if user_type == "P":
            cursor.execute('SELECT * FROM Professor WHERE Faculty.email = ?', email)
            prof_entry = cursor.fetchone()
            office_address = prof_entry[1]
            department = prof_entry[2]
            title = prof_entry[3]

    def get_enrollments(self):
        # sql to get sections a student is enrolled in
        return

    def get_sections(self):
        # sql to get sections a professor is teaching
        return

class Department:
    dept_id
    dept_name
    dept_head


class Course:
    course_id
    course_name
    course_description


class Section(Course):
    sec_no
    section_type
    limit
    prof_team_id

