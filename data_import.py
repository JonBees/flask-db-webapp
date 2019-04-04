import csv
import sqlite3 as sql
import werkzeug.security

import_conn = sql.connect('canvaspath.sqlite')


# This should import the data from the CSV files and create the necessary tables
def populate_all():
    prof_csv = open('./csv/Professors.csv', 'r')
    stud_csv = open('./csv/Students.csv', 'r')

    # populate_user(prof_csv, stud_csv)
    populate_student(stud_csv)
    populate_professor(prof_csv)
    populate_prof_teams(prof_csv)
    populate_prof_team_members(prof_csv)
    populate_zipcode(stud_csv)
    populate_department(prof_csv)
    populate_course(stud_csv)
    populate_sections(prof_csv, stud_csv)
    populate_enrolls(stud_csv)
    populate_homework(stud_csv)
    populate_homework_grades(stud_csv)
    populate_exams(stud_csv)
    populate_exam_grades(stud_csv)
    populate_capstone_section()
    populate_capstone_team()
    populate_capstone_team_members()
    populate_capstone_grades()

    print("data imported.")


# This should be populated using the Email, Password, Name, Age, Gender cols of both Students and Professors
# Password should be a hash generated from the value in the CSV using werkzeug.security.generate_password_hash
def populate_user(pcsv, scsv):
    print("populating User")

    cursor = import_conn.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS User(
                      email CHAR(22) NOT NULL,
                      password CHAR(95) NOT NULL,
                      name CHAR(50) NOT NULL,
                      age INTEGER NOT NULL,
                      gender CHAR(1) NOT NULL,
                      PRIMARY KEY (email))""")

    pdict = csv.DictReader(pcsv)
    sdict = csv.DictReader(scsv)

    # Collect the user info for both students and professors, then insert it to User all at once.
    user_insert = []
    print("\thashing professors' passwords")
    for prof in pdict:
        user_insert.append([prof["Email"], werkzeug.security.generate_password_hash(prof["Password"]), prof["Name"],
                            prof["Age"], prof["Gender"]])
    print("\thashing students' passwords")
    for stud in sdict:
        user_insert.append([stud["Email"], werkzeug.security.generate_password_hash(stud["Password"]), stud["Full Name"],
                            stud["Age"], stud["Gender"]])

    cursor.executemany("""INSERT INTO User (email, password, name, age, gender) VALUES (?, ?, ?, ?, ?)""", user_insert)
    import_conn.commit()

    pcsv.seek(0)
    scsv.seek(0)


# This should be populated using the Email, Major, Street, Zip cols of Students
def populate_student(scsv):
    print("populating Student")

    cursor = import_conn.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS Student(
                      email CHAR(22) NOT NULL,
                      major CHAR(5) NOT NULL,
                      street CHAR(50) NOT NULL,
                      zipcode INTEGER NOT NULL,
                      PRIMARY KEY (email),
                      FOREIGN KEY (email) REFERENCES User(email),
                      FOREIGN KEY (zipcode) REFERENCES Zipcode)""")

    sdict = csv.DictReader(scsv)

    # Collect the student-specific info from all students, then insert it to Student.
    stud_insert = []

    for stud in sdict:
        stud_insert.append([stud["Email"], stud["Major"], stud["Street"], stud["Zip"]])

    cursor.executemany("""INSERT INTO Student (email, major, street, zipcode) VALUES (?, ?, ?, ?)""", stud_insert)
    import_conn.commit()

    scsv.seek(0)

# This should be populated using the Email, Office, Department, Title cols of Professors
def populate_professor(pcsv):
    print("populating Professor")

    cursor = import_conn.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS Professor(
                      email CHAR(22) NOT NULL,
                      office_address CHAR(25) NOT NULL,
                      department CHAR(5) NOT NULL,
                      title CHAR(12) NOT NULL,
                      PRIMARY KEY (email),
                      FOREIGN KEY (email) REFERENCES User(email),
                      FOREIGN KEY (department) REFERENCES Department(dept_id))""")

    pdict = csv.DictReader(pcsv)

    # Collect the professor-specific info from all professors, then insert it to Professor.
    prof_insert = []

    for prof in pdict:
        prof_insert.append([prof["Email"], prof["Office"], prof["Department"], prof["Title"]])

    cursor.executemany("""INSERT INTO Professor (email, office_address, department, title) VALUES (?, ?, ?, ?)""",
                       prof_insert)
    import_conn.commit()

    pcsv.seek(0)


# This should be populated using the unique values of Team ID in Professors
def populate_prof_teams(pcsv):
    print("populating Prof_teams")

    cursor = import_conn.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS Prof_teams(
                      team_id INTEGER NOT NULL,
                      PRIMARY KEY (team_id))""")

    pdict = csv.DictReader(pcsv)

    # Collect all of the professor team numbers, then insert them to Prof_teams.
    teams_insert = []
    for prof in pdict:
        if prof["Team ID"] not in teams_insert:
            teams_insert.append([prof["Team ID"]])

    cursor.executemany("""INSERT INTO Prof_teams (team_id) VALUES (?)""", teams_insert)
    import_conn.commit()

    pcsv.seek(0)


# This should be populated using Email and Team ID cols of Professors
def populate_prof_team_members(pcsv):
    print("populating Prof_team_members")

    cursor = import_conn.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS Prof_team_members(
                      prof_email CHAR(22) NOT NULL,
                      team_id INTEGER NOT NULL,
                      PRIMARY KEY (prof_email, team_id),
                      FOREIGN KEY (prof_email) REFERENCES Professor(email),
                      FOREIGN KEY (team_id) REFERENCES Prof_teams(team_id))""")

    pdict = csv.DictReader(pcsv)

    # Collect all of the professors' emails, then connect them to their team number.
    members_insert = []

    for prof in pdict:
        members_insert.append([prof["Email"], prof["Team ID"]])

    cursor.executemany("""INSERT INTO Prof_team_members (prof_email, team_id) VALUES (?, ?)""", members_insert)
    import_conn.commit()

    pcsv.seek(0)


# This should be populated using the unique values from the Zip, City, and State cols of Students.
def populate_zipcode(scsv):
    print("populating Zipcode")

    cursor = import_conn.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS Zipcode(
                      zipcode INTEGER NOT NULL,
                      city CHAR(40) NOT NULL,
                      state CHAR(25) NOT NULL,
                      PRIMARY KEY (zipcode))""")

    sdict = csv.DictReader(scsv)

    # Collect all unique zip codes, then link them to their state and city.
    zips_insert = []
    for stud in sdict:
        if [stud["Zip"], stud["City"], stud["State"]] not in zips_insert:
            zips_insert.append([stud["Zip"], stud["City"], stud["State"]])

    cursor.executemany("""INSERT INTO Zipcode (zipcode, city, state) VALUES (?, ?, ?)""", zips_insert)
    import_conn.commit()

    scsv.seek(0)


# This should be populated using the Department, Department Name, and Title cols of Professors.
def populate_department(pcsv):
    print("populating Department")

    cursor = import_conn.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS Department(
                      dept_id CHAR(5) NOT NULL,
                      dept_name CHAR(50) NOT NULL,
                      dept_head CHAR(22) NOT NULL,
                      PRIMARY KEY (dept_id),
                      FOREIGN KEY (dept_head) REFERENCES Professor(email))""")

    pdict = csv.DictReader(pcsv)

    # Collect all unique departments, along with the professor in each department with the title "Head"
    depts = []
    for prof in pdict:
        if prof["Title"] == "Head" and [prof["Department"], prof["Department Name"], prof["Email"]] not in depts:
            depts.append([prof["Department"], prof["Department Name"], prof["Email"]])

    cursor.executemany("""INSERT INTO Department (dept_id, dept_name, dept_head) VALUES (?, ?, ?)""", depts)
    import_conn.commit()

    pcsv.seek(0)


# This should be populated using the unique values from
# Courses 1-3, Course 1-3 Name, Course 1-3 Details cols of Students
def populate_course(scsv):
    print("populating Course")

    cursor = import_conn.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS Course(
                      course_id CHAR(15) NOT NULL,
                      course_name CHAR(65) NOT NULL,
                      course_description VARCHAR(120) NOT NULL,
                      PRIMARY KEY (course_id))""")

    sdict = csv.DictReader(scsv)

    # Collect all unique courses students are taking, along with their name and details.
    courses = []
    for stud in sdict:
        if [stud["Courses 1"], stud["Course 1 Name"], stud["Course 1 Details"]] not in courses:
            courses.append([stud["Courses 1"], stud["Course 1 Name"], stud["Course 1 Details"]])
        if [stud["Courses 2"], stud["Course 2 Name"], stud["Course 2 Details"]] not in courses:
            courses.append([stud["Courses 2"], stud["Course 2 Name"], stud["Course 2 Details"]])
        if [stud["Courses 3"], stud["Course 3 Name"], stud["Course 3 Details"]] not in courses:
            courses.append([stud["Courses 3"], stud["Course 3 Name"], stud["Course 3 Details"]])

    cursor.executemany("""INSERT INTO Course (course_id, course_name, course_description) VALUES (?, ?, ?)""", courses)
    import_conn.commit()

    scsv.seek(0)


# This should be populated using the unique values from
# Courses 1-3, Course 1-3 Section, Course 1-3 Type, Course 1-3 Section Limit cols of Students
# Teaching, Team ID in Professors
def populate_sections(pcsv, scsv):
    print("populating Section")

    cursor = import_conn.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS Section(
                      course_id CHAR(15) NOT NULL,
                      sec_no INTEGER NOT NULL,
                      section_type CHAR(3) NOT NULL,
                      sec_limit INTEGER NOT NULL,
                      prof_team_id INTEGER NOT NULL,
                      PRIMARY KEY (course_id, sec_no),
                      FOREIGN KEY (course_id) REFERENCES Course(course_id),
                      FOREIGN KEY (prof_team_id) REFERENCES Prof_teams(team_id))""")

    pdict = csv.DictReader(pcsv)
    sdict = csv.DictReader(scsv)

    sections_insert = []

    # create a dict of all the fields necessary for sections with a key
    # consisting of the sec_no appended to the course_id
    sec_dict = {}

    # also create a list of all the valid section numbers for each course so
    # we can assign the proper prof_team_id to all sections of a course
    sec_nums = {}

    for stud in sdict:

        c1key = stud["Courses 1"] + ":" + stud["Course 1 Section"]
        c2key = stud["Courses 2"] + ":" + stud["Course 2 Section"]
        c3key = stud["Courses 3"] + ":" + stud["Course 3 Section"]

        if c1key not in sec_dict:
            sec_dict[c1key] = [stud["Courses 1"], stud["Course 1 Section"], stud["Course 1 Type"],
                               stud["Course 1 Section Limit"]]
            if stud["Courses 1"] not in sec_nums:
                sec_nums[stud["Courses 1"]] = [stud["Course 1 Section"]]
            else:
                sec_nums[stud["Courses 1"]].append(stud["Course 1 Section"])

        if c2key not in sec_dict:
            sec_dict[c2key] = [stud["Courses 2"], stud["Course 2 Section"], stud["Course 2 Type"],
                               stud["Course 2 Section Limit"]]
            if stud["Courses 2"] not in sec_nums:
                sec_nums[stud["Courses 2"]] = [stud["Course 2 Section"]]
            else:
                sec_nums[stud["Courses 2"]].append(stud["Course 2 Section"])

        if c3key not in sec_dict:
            sec_dict[c3key] = [stud["Courses 3"], stud["Course 3 Section"], stud["Course 3 Type"],
                               stud["Course 3 Section Limit"]]
            if stud["Courses 3"] not in sec_nums:
                sec_nums[stud["Courses 3"]] = [stud["Course 3 Section"]]
            else:
                sec_nums[stud["Courses 3"]].append(stud["Course 3 Section"])

    for prof in pdict:
        # If a sec_dict entry for a course section this professor teaches doesn't yet have a team id, assign it
        if prof["Teaching"] in sec_nums:
            for secnum in sec_nums[prof["Teaching"]]:
                dict_key = prof["Teaching"] + ":" + secnum
                if len(sec_dict[dict_key]) == 4:
                    sec_dict[dict_key].append(prof["Team ID"])

    # Add the info for all course sections to a plain old list so it's easy to do a SQL INSERT
    for sec in sec_nums:
        for num in sec_nums[sec]:
            dict_key = sec + ":" + num
            sections_insert.append(sec_dict[dict_key])

    cursor.executemany("""INSERT INTO Section (course_id, sec_no, section_type, sec_limit, prof_team_id) 
                          VALUES (?, ?, ?, ?, ?)""", sections_insert)

    import_conn.commit()

    pcsv.seek(0)
    scsv.seek(0)


# This should be populated using Email, Courses 1-3, Course 1-3 Section cols of Students
def populate_enrolls(scsv):
    print("populating Enrolls")
    cursor = import_conn.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS Enrolls(
                      student_email CHAR(22) NOT NULL,
                      course_id CHAR(15) NOT NULL,
                      section_no INTEGER NOT NULL,
                      PRIMARY KEY (student_email, course_id, section_no),
                      FOREIGN KEY (student_email) REFERENCES Student(email))""")

    sdict = csv.DictReader(scsv)

    enrol_insert = []

    # Collect all three course + section entries for each student
    for stud in sdict:
        enrol_insert.append([stud["Email"], stud["Courses 1"], stud["Course 1 Section"]])
        enrol_insert.append([stud["Email"], stud["Courses 2"], stud["Course 2 Section"]])
        enrol_insert.append([stud["Email"], stud["Courses 3"], stud["Course 3 Section"]])

    cursor.executemany("""INSERT INTO Enrolls (student_email, course_id, section_no) VALUES (?, ?, ?)""", enrol_insert)

    import_conn.commit()

    scsv.seek(0)


# This should be populated using
# Courses 1-3, Course 1-3 Section, Course 1-3 HW_No, Course 1-3 HW_Details cols of Students
def populate_homework(scsv):
    print("populating Homework")
    cursor = import_conn.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS Homework(
                      course_id CHAR(15) NOT NULL,
                      sec_no INTEGER NOT NULL,
                      hw_no INTEGER NOT NULL,
                      hw_details VARCHAR(120) NOT NULL,
                      PRIMARY KEY (course_id, sec_no, hw_no),
                      FOREIGN KEY (course_id, sec_no) REFERENCES Course(course_id, sec_no))""")

    sdict = csv.DictReader(scsv)

    hw_insert = []

    hw_dict = {}

    # Collect the unique values of all courses every student is enrolled in.
    for stud in sdict:
        hw1key = stud["Courses 1"] + ":" + stud["Course 1 Section"] + ":" + stud["Course 1 HW_No"]
        hw2key = stud["Courses 2"] + ":" + stud["Course 2 Section"] + ":" + stud["Course 2 HW_No"]
        hw3key = stud["Courses 3"] + ":" + stud["Course 3 Section"] + ":" + stud["Course 3 HW_No"]

        if hw1key not in hw_dict:
            hw_dict[hw1key] = [stud["Courses 1"], stud["Course 1 Section"], stud["Course 1 HW_No"],
                               stud["Course 1 HW_Details"]]

        if hw2key not in hw_dict:
            hw_dict[hw2key] = [stud["Courses 2"], stud["Course 2 Section"], stud["Course 2 HW_No"],
                               stud["Course 2 HW_Details"]]

        if hw3key not in hw_dict:
            hw_dict[hw3key] = [stud["Courses 3"], stud["Course 3 Section"], stud["Course 3 HW_No"],
                               stud["Course 3 HW_Details"]]

    for hw in hw_dict:
        hw_insert.append(hw_dict[hw])

    cursor.executemany("""INSERT INTO Homework (course_id, sec_no, hw_no, hw_details) VALUES (?, ?, ?, ?)""", hw_insert)

    import_conn.commit()

    scsv.seek(0)


# This should be populated using
# Email, Courses 1-3, Course 1-3 Section, Course 1-3 HW_No, Course 1-3 HW_Details, Course 1-3 HW_Grade cols of Students
def populate_homework_grades(scsv):
    print("populating Homework_grades")

    cursor = import_conn.cursor()
    cursor.execute(
        """CREATE TABLE IF NOT EXISTS Homework_grades(
           student_email CHAR(22) NOT NULL,
           course_id CHAR(15) NOT NULL,
           sec_no INTEGER NOT NULL,
           hw_no INTEGER NOT NULL,
           grade INTEGER NOT NULL,
           PRIMARY KEY (student_email, course_id, sec_no, hw_no),
           FOREIGN KEY (student_email, course_id, sec_no) REFERENCES Enrolls(student_email, course_id, sec_no),
           FOREIGN KEY (course_id, sec_no, hw_no) REFERENCES Homework(course_id, sec_no, hw_no))""")

    sdict = csv.DictReader(scsv)

    hw_insert = []

    # Collect all of each student's homework assignments and grades.
    for stud in sdict:
        hw_insert.append([stud["Email"], stud["Courses 1"], stud["Course 1 Section"], stud["Course 1 HW_No"],
                          stud["Course 1 HW_Grade"]])
        hw_insert.append([stud["Email"], stud["Courses 2"], stud["Course 2 Section"], stud["Course 2 HW_No"],
                          stud["Course 2 HW_Grade"]])
        hw_insert.append([stud["Email"], stud["Courses 3"], stud["Course 3 Section"], stud["Course 3 HW_No"],
                          stud["Course 3 HW_Grade"]])

    cursor.executemany(
        """INSERT INTO Homework_grades (student_email, course_id, sec_no, hw_no, grade) VALUES (?, ?, ?, ?, ?)""",
        hw_insert)

    import_conn.commit()

    scsv.seek(0)


# This should be populated using
# Courses 1-3, Course 1-3 Section, Course 1-3 EXAM_No, Course 1-3 EXAM_Details cols of Students
# KEEP IN MIND THAT CAPSTONE SECTIONS WILL HAVE THE EXAM COLUMNS BLANK
def populate_exams(scsv):
    print("populating Exams")

    cursor = import_conn.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS Exams(
                      course_id CHAR(15) NOT NULL,
                      sec_no INTEGER NOT NULL,
                      exam_no INTEGER NOT NULL,
                      exam_details VARCHAR(120) NOT NULL,
                      PRIMARY KEY (course_id, sec_no, exam_no),
                      FOREIGN KEY (course_id, sec_no) REFERENCES Section(course_id, sec_no))""")

    sdict = csv.DictReader(scsv)

    ex_insert = []

    ex_dict = {}

    # Collect the unique values of all courses every student is enrolled in.
    for stud in sdict:

        ex1key = stud["Courses 1"] + ":" + stud["Course 1 Section"] + ":" + stud["Course 1 EXAM_No"]
        ex2key = stud["Courses 2"] + ":" + stud["Course 2 Section"] + ":" + stud["Course 2 EXAM_No"]
        ex3key = stud["Courses 3"] + ":" + stud["Course 3 Section"] + ":" + stud["Course 3 EXAM_No"]

        if stud["Course 1 EXAM_No"] != "":
            if ex1key not in ex_dict:
                ex_dict[ex1key] = [stud["Courses 1"], stud["Course 1 Section"], stud["Course 1 EXAM_No"],
                                   stud["Course 1 Exam_Details"]]

        if stud["Course 2 EXAM_No"] != "":
            if ex2key not in ex_dict:
                ex_dict[ex2key] = [stud["Courses 2"], stud["Course 2 Section"], stud["Course 2 EXAM_No"],
                                   stud["Course 2 Exam_Details"]]

        if stud["Course 3 EXAM_No"] != "":
            if ex3key not in ex_dict:
                ex_dict[ex3key] = [stud["Courses 3"], stud["Course 3 Section"], stud["Course 3 EXAM_No"],
                                   stud["Course 3 Exam_Details"]]

    for ex in ex_dict:
        ex_insert.append(ex_dict[ex])

    cursor.executemany("""INSERT INTO Exams (course_id, sec_no, exam_no, exam_details) VALUES (?, ?, ?, ?)""",
                       ex_insert)

    import_conn.commit()

    scsv.seek(0)


# This should be populated using
# Email, Courses 1-3, Course 1-3 Section, Course 1-3 EXAM_No, Course 1-3 EXAM_Grade cols of Students
# KEEP IN MIND THAT CAPSTONE SECTIONS WILL HAVE THE EXAM COLUMNS BLANK
def populate_exam_grades(scsv):
    print("populating Exam_grades")

    cursor = import_conn.cursor()
    cursor.execute(
        """CREATE TABLE IF NOT EXISTS Exam_grades(
           student_email CHAR(22) NOT NULL,
           course_id CHAR(15) NOT NULL,
           sec_no INTEGER NOT NULL,
           exam_no INTEGER NOT NULL,
           grade INTEGER NOT NULL,
           PRIMARY KEY (student_email, course_id, sec_no, exam_no),
           FOREIGN KEY (student_email, course_id, sec_no) REFERENCES Enrolls(student_email, course_id, sec_no),
           FOREIGN KEY (course_id, sec_no, exam_no) REFERENCES Exams(course_id, sec_no, exam_no))""")

    sdict = csv.DictReader(scsv)

    ex_insert = []

    for stud in sdict:
        if stud["Course 1 EXAM_No"] != "":
            ex_insert.append([stud["Email"], stud["Courses 1"], stud["Course 1 Section"], stud["Course 1 EXAM_No"],
                              stud["Course 1 EXAM_Grade"]])
        if stud["Course 2 EXAM_No"] != "":
            ex_insert.append([stud["Email"], stud["Courses 2"], stud["Course 2 Section"], stud["Course 2 EXAM_No"],
                              stud["Course 2 EXAM_Grade"]])
        if stud["Course 3 EXAM_No"] != "":
            ex_insert.append([stud["Email"], stud["Courses 3"], stud["Course 3 Section"], stud["Course 3 EXAM_No"],
                              stud["Course 3 EXAM_Grade"]])

    cursor.executemany(
        """INSERT INTO Exam_grades (student_email, course_id, sec_no, exam_no, grade) VALUES (?, ?, ?, ?, ?)""",
        ex_insert)

    import_conn.commit()

    scsv.seek(0)


# The Capstone info, other than which sections are capstone sections, is not present in the csv files
# and will therefore have to be populated by faculty members. Because there's no project_no info, we can't
# actually create the rows properly.
def populate_capstone_section():
    print("populating Capstone_section")

    cursor = import_conn.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS Capstone_section(
                      course_id CHAR(15) NOT NULL,
                      sec_no INTEGER NOT NULL,
                      project_no INTEGER NOT NULL,
                      sponsor_id CHAR(22) NOT NULL,
                      PRIMARY KEY (course_id, sec_no, project_no),
                      FOREIGN KEY (course_id, sec_no) REFERENCES Section(course_id, sec_no),
                      FOREIGN KEY (sponsor_id) REFERENCES Professor(email))""")

    import_conn.commit()


def populate_capstone_team():
    print("populating Capstone_team")

    cursor = import_conn.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS Capstone_team(
                      course_id CHAR(15) NOT NULL,
                      sec_no INTEGER NOT NULL,
                      team_id INTEGER NOT NULL,
                      project_no INTEGER NOT NULL,
                      PRIMARY KEY (course_id, sec_no, team_id),
                      FOREIGN KEY (course_id, sec_no) REFERENCES Section(course_id, sec_no))""")

    import_conn.commit()


def populate_capstone_team_members():
    print("populating Capstone_team_members")

    cursor = import_conn.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS Capstone_team_members(
                      student_email CHAR(22) NOT NULL,
                      team_id INTEGER NOT NULL,
                      course_id CHAR(15) NOT NULL,
                      sec_no INTEGER NOT NULL,
                      PRIMARY KEY (student_email, team_id, course_id, sec_no),
                      FOREIGN KEY (course_id, sec_no, team_id) REFERENCES Capstone_team(course_id, sec_no, team_id))""")

    import_conn.commit()


def populate_capstone_grades():
    print("populating Capstone_grades")

    cursor = import_conn.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS Capstone_grades(
                      course_id CHAR(15) NOT NULL,
                      sec_no INTEGER NOT NULL,
                      team_id INTEGER NOT NULL,
                      grade INTEGER NOT NULL,
                      PRIMARY KEY (course_id, sec_no, team_id),
                      FOREIGN KEY (course_id, sec_no, team_id) REFERENCES Capstone_team(course_id, sec_no, team_id))""")

    import_conn.commit()


populate_all()
