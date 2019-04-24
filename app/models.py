import sqlite3 as sql
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import login


# the classes here are a vague analogue to an ORM. I thought it was probably
# more in the spirit of the class to write my own SQL rather than using a pre-made ORM.


@login.user_loader
def load_user(id):
    return User(id)


class User(UserMixin):
    # each user is identified by their email, and all their main info is stored in the User table
    id = ""
    pw_hash = ""
    name = ""
    age = -1
    gender = ""
    # The type is "S" (student), "P" (professor), or "A" (administrator)
    user_type = ""
    # Fields specific to students:
    major = ""
    street = ""
    city = ""
    # Fields specific to faculty:
    office_address = ""
    department = ""
    title = ""

    def __init__(self, id):
        connection = sql.connect('canvaspath.sqlite')
        cursor = connection.cursor()
        cursor.execute("""SELECT * FROM User WHERE User.email = ?""", [id])
        try:
            user_entry = cursor.fetchone()
            # print(user_entry)
            self.id = user_entry[0]
            self.pw_hash = user_entry[1]
            self.name = user_entry[2]
            self.age = int(user_entry[3])
            self.gender = user_entry[4]
            self.user_type = user_entry[5]

            if self.user_type == "S":
                cursor.execute('SELECT * FROM Student WHERE Student.email = ?', [id])
                student_entry = cursor.fetchone()
                self.major = student_entry[1]
                self.street = student_entry[2]
                cursor.execute("""SELECT * from Zipcode Z WHERE Z.zipcode = ?""", [str(student_entry[3])])
                zip_entry = cursor.fetchone()
                self.city = zip_entry[1] + ", " + zip_entry[2] + " " + str(zip_entry[0])

            if self.user_type == "P":
                cursor.execute('SELECT * FROM Professor WHERE Professor.email = ?', [id])
                prof_entry = cursor.fetchone()
                self.office_address = prof_entry[1]
                self.department = prof_entry[2]
                self.title = prof_entry[3]
        except TypeError as te:
            print("ERROR: Failed to fetch info for user \"{}\"".format(id))
            print(te)

        cursor.close()
        connection.close()

    def set_password(self, newpw):
        connection = sql.connect('canvaspath.sqlite')
        cursor = connection.cursor()
        self.pw_hash = generate_password_hash(newpw)
        cursor.execute('UPDATE User SET password = ? WHERE User.email = ?', [self.pw_hash, self.id])
        connection.commit()
        cursor.close()
        connection.close()

    def check_password(self, pw):
        return check_password_hash(self.pw_hash, pw)

    def get_enrollments(self):
        connection = sql.connect('canvaspath.sqlite')
        cursor = connection.cursor()
        enrollments = set()
        # sql to get sections a student is enrolled in
        cursor.execute('SELECT course_id, section_no FROM Enrolls WHERE student_email = ?', [self.id])
        for row in cursor:
            enrollments.add((row[0], row[1]))
        cursor.close()
        connection.close()
        return enrollments

    def get_sections_teaching(self):
        connection = sql.connect('canvaspath.sqlite')
        cursor = connection.cursor()
        sections = set()
        # get all teams a professor is on from Prof_team_members
        # for each of those teams, find all rows in Section where
        # Section.prof_team_id is in the list of teams where this professor is a member
        cursor.execute(
            """SELECT S.course_id, S.sec_no FROM Section S WHERE S.prof_team_id IN 
            (SELECT team_id FROM Prof_team_members T WHERE T.prof_email = ?)""", [self.id])
        for row in cursor:
            sections.add((row[0], row[1]))
        cursor.close()
        connection.close()
        return sections


class Section:
    course_id = ""
    course_name = ""
    course_desc = ""
    sec_no = ""
    sec_id = ""
    sec_type = ""
    sec_limit = ""
    prof_team_id = ""

    def __init__(self, cid, sec):
        connection = sql.connect('canvaspath.sqlite')
        cursor = connection.cursor()
        self.course_id = cid
        self.sec_no = sec
        cursor.execute(
            """SELECT C.course_name, C.course_description, S.section_type, S.sec_limit, S.prof_team_id 
            FROM Course C, Section S WHERE C.course_id = ? AND C.course_id = S.course_id AND S.sec_no = ?""",
            [self.course_id, self.sec_no])
        try:
            sec_entry = cursor.fetchone()
            self.course_id = cid
            self.sec_no = sec
            self.sec_id = cid + "S" + ("{:02d}".format(int(sec)))
            self.course_name = sec_entry[0]
            self.course_desc = sec_entry[1]
            self.sec_type = sec_entry[2]
            self.sec_limit = sec_entry[3]
            self.prof_team_id = sec_entry[4]
        except TypeError as te:
            print("ERROR: Failed to fetch info for course {} section {}".format(cid, sec))
            print(te)
        cursor.close()
        connection.close()

    def get_homeworks(self):
        connection = sql.connect('canvaspath.sqlite')
        cursor = connection.cursor()
        homeworks = []
        cursor.execute("""SELECT hw_no, hw_details FROM Homework H WHERE H.course_id = ? AND H.sec_no = ?""",
                       [self.course_id, self.sec_no])
        for row in cursor:
            homeworks.append([row[0], row[1]])
        cursor.close()
        connection.close()
        return homeworks

    def get_exams(self):
        connection = sql.connect('canvaspath.sqlite')
        cursor = connection.cursor()
        exams = []
        cursor.execute("""SELECT exam_no, exam_details FROM Exams E WHERE E.course_id = ? AND E.sec_no = ?""",
                       [self.course_id, self.sec_no])
        for row in cursor:
            exams.append([row[0], row[1]])
        cursor.close()
        connection.close()
        return exams

    def get_professors(self):
        connection = sql.connect('canvaspath.sqlite')
        cursor = connection.cursor()
        profs = []
        cursor.execute(
            """SELECT P.prof_email FROM Prof_team_members P WHERE P.team_id = ?""", [self.prof_team_id])
        for row in cursor:
            profs.append(row[0])
        cursor.close()
        connection.close()
        return profs

    def get_students(self):
        connection = sql.connect('canvaspath.sqlite')
        cursor = connection.cursor()
        students = []
        # Enrolls.student_email
        #
        cursor.execute(
            """SELECT E.student_email FROM Enrolls E WHERE E.course_id = ? AND E.section_no = ?""",
            [self.course_id, self.sec_no])
        for row in cursor:
            students.append(row[0])
        cursor.close()
        connection.close()
        return students

    # Get all of a specified student's homework grades for this section
    def get_student_hw_grades(self, sid):
        connection = sql.connect('canvaspath.sqlite')
        cursor = connection.cursor()
        hw_grades = []
        cursor.execute(
            """SELECT G.hw_no, H.hw_details, G.grade FROM Homework_grades G, Homework H
            WHERE G.student_email = ? AND G.course_id = ? AND G.sec_no = ? 
            AND G.course_id = H.course_id AND G.sec_no = H.sec_no""",
            [sid, self.course_id, self.sec_no])
        for row in cursor:
            hw_grades.append([row[0], row[1], row[2]])
        cursor.close()
        connection.close()
        return hw_grades

    # Get all of a specified student's exam grades for this section
    def get_student_exam_grades(self, sid):
        connection = sql.connect('canvaspath.sqlite')
        cursor = connection.cursor()
        exam_grades = []
        cursor.execute(
            """SELECT G.exam_no, E.exam_details, G.grade FROM Exam_grades G, Exams E
            WHERE G.student_email = ? AND G.course_id = ? AND G.sec_no = ? 
            AND G.course_id = E.course_id AND G.sec_no = E.sec_no""",
            [sid, self.course_id, self.sec_no])
        for row in cursor:
            exam_grades.append([row[0], row[1], row[2]])
        cursor.close()
        connection.close()
        return exam_grades

    def get_student_projects(self, sid):
        connection = sql.connect('canvaspath.sqlite')
        cursor = connection.cursor()
        projects = []
        cursor.execute(
            """SELECT G.team_id, S.project_no, G.grade, S.sponsor_id FROM Capstone_grades G, Capstone_section S 
            WHERE G.course_id = ? AND G.sec_no = ? AND G.course_id = S.course_id AND G.sec_no = S.sec_no 
            AND G.team_id IN (SELECT team_id FROM Capstone_team_members M 
            WHERE M.student_email = ? AND M.course_id = G.course_id AND M.sec_no = G.sec_no)""",
            [self.course_id, self.sec_no, sid])
        for row in cursor:
            spon = User(row[3])
            projects.append([row[0], row[1], row[2], row[3], spon.name, spon.office_address])
        cursor.close()
        connection.close()
        return projects

    def get_teams(self):
        connection = sql.connect('canvaspath.sqlite')
        cursor = connection.cursor()
        teams = {}
        # Create a teams dict which consists of all team ids indexed by this section's project numbers
        cursor.execute("""SELECT team_id, project_no FROM Capstone_team WHERE course_id = ? AND sec_no = ?""",
                       [self.course_id, self.sec_no])
        for row in cursor:
            teams[row[0]] = row[1]

        cursor.close()
        connection.close()
        return teams

    def get_projects(self):
        connection = sql.connect('canvaspath.sqlite')
        cursor = connection.cursor()
        projects = set()
        cursor.execute("""SELECT DISTINCT project_no FROM Capstone_section WHERE course_id = ? AND sec_no = ?""",
                       [self.course_id, self.sec_no])
        for row in cursor:
            projects.add(row[0])
        cursor.close()
        connection.close()
        return projects

    def new_project(self, project_no, sponsor):
        projects = self.get_teams()
        # figure out of project number is unique for this class
        if project_no in projects.values():
            return False
        # figure out if sponsor is a valid professor
        user = User(sponsor)
        if user.user_type != "P":
            return False

        connection = sql.connect('canvaspath.sqlite')
        cursor = connection.cursor()

        # insert into capstone_section
        # The Capstone_section table is essentially a list of projects connected with their sponsors.
        print("creating project in course {} section {} with number {} sponsor {}.".format(self.course_id, self.sec_no,
                                                                                           project_no, sponsor))
        cursor.execute(
            """INSERT INTO Capstone_section (course_id, sec_no, project_no, sponsor_id)  VALUES (?, ?, ?, ?)""",
            [self.course_id, self.sec_no, project_no, sponsor])

        print("Created new project {} for course {} sec {}.".format(project_no, self.course_id, self.sec_no))

        connection.commit()
        cursor.close()
        connection.close()
        return True

    # to remove a project, we need to remove all team and team member entries referring to it
    def remove_project(self, project_no):
        if int(project_no) in self.get_projects():

            # call remove_team to remove all teams assigned to the project
            teams = self.get_teams()
            for team in teams.keys():
                if teams[team] == int(project_no):
                    self.remove_team(team)

            # remove project from capstone_section.
            connection = sql.connect('canvaspath.sqlite')
            cursor = connection.cursor()
            cursor.execute("""DELETE FROM Capstone_section WHERE course_id = ? AND sec_no = ? AND project_no = ?""",
                           [self.course_id, self.sec_no, project_no])
            connection.commit()
            cursor.close()
            connection.close()
            return True

        return False

    def new_team(self, students, project_no):

        teams = self.get_teams()

        # figure out if all students are in the course
        course_students = self.get_students()
        for student in students:
            if student not in course_students:
                return False
        # find the smallest unused team_id
        team_id = -1
        tmp_id = 1
        while team_id < 0:
            if tmp_id in teams.keys():
                tmp_id = tmp_id + 1
            else:
                team_id = tmp_id

        connection = sql.connect('canvaspath.sqlite')
        cursor = connection.cursor()

        # insert into capstone_team
        cursor.execute("""INSERT INTO Capstone_team (course_id, sec_no, team_id, project_no) VALUES (?, ?, ?, ?)""",
                       [self.course_id, self.sec_no, team_id, project_no])

        # insert into capstone_team_members
        studentinsert = []
        for student in students:
            studentinsert.append([student, team_id, self.course_id, self.sec_no])
        cursor.executemany(
            """INSERT INTO Capstone_team_members (student_email, team_id, course_id, sec_no) VALUES (?, ?, ?, ?)""",
            studentinsert)

        # insert into capstone_grades
        cursor.execute(
            """INSERT INTO Capstone_grades (course_id, sec_no, team_id, grade) VALUES (?, ?, ?, NULL)""",
            [self.course_id, self.sec_no, team_id])

        connection.commit()
        cursor.close()
        connection.close()
        return team_id

    def remove_team(self, team_id):
        if int(team_id) in self.get_teams().keys():
            connection = sql.connect('canvaspath.sqlite')
            cursor = connection.cursor()

            # remove all students from team in Capstone_team_members
            cursor.execute("""DELETE FROM Capstone_team_members WHERE course_id = ? AND sec_no = ? AND team_id = ?""",
                           [self.course_id, self.sec_no, team_id])
            # remove grade entry from Capstone_grades
            cursor.execute("""DELETE FROM Capstone_grades WHERE course_id = ? AND sec_no = ? AND team_id = ?""",
                           [self.course_id, self.sec_no, team_id])
            # remove team entry from Capstone_team
            cursor.execute("""DELETE FROM Capstone_team WHERE course_id = ? AND sec_no = ? AND team_id = ?""",
                           [self.course_id, self.sec_no, team_id])
            connection.commit()
            cursor.close()
            connection.close()
            return True

        return False


# we can use a Gradebook to interface with all of a class's grades.
class Gradebook:
    course_id = ""
    sec_no = ""
    sec_id = ""

    def __init__(self, cid, sec):
        self.course_id = cid
        self.sec_no = sec
        self.sec_id = cid + "S" + ("{:02d}".format(int(sec)))

    def get_hw_gradebook(self):
        connection = sql.connect('canvaspath.sqlite')
        cursor = connection.cursor()

        # get a list of all homework numbers, make each of those element 1 in a list
        # make the corresponding homework description element 2 in that list
        # for each homework, get all students' grades for that homework & add that list as element 3

        hw_grades = []
        cursor.execute("""SELECT hw_no, hw_details FROM Homework H WHERE H.course_id = ? AND H.sec_no = ?""",
                       [self.course_id, self.sec_no])
        for row in cursor:
            hw_grades.append([row[0], row[1]])

        for hw in hw_grades:
            cursor.execute("""SELECT U.name, G.student_email, G.grade FROM Homework_grades G, User U WHERE 
            G.course_id = ? AND G.sec_no = ? AND G.hw_no = ? AND G.student_email = U.email""",
                           [self.course_id, self.sec_no, hw[0]])
            grades = []
            for row in cursor:
                grades.append([row[0], row[1], row[2]])
            hw.append(grades)

        # print(hw_grades)

        cursor.close()
        connection.close()
        return hw_grades

    def get_exam_gradebook(self):
        connection = sql.connect('canvaspath.sqlite')
        cursor = connection.cursor()
        exam_grades = []
        cursor.execute("""SELECT exam_no, exam_details FROM Exams E WHERE E.course_id = ? AND E.sec_no = ?""",
                       [self.course_id, self.sec_no])
        for row in cursor:
            exam_grades.append([row[0], row[1]])

        for exam in exam_grades:
            cursor.execute("""SELECT U.name, G.student_email, G.grade FROM Exam_grades G, User U WHERE 
                    G.course_id = ? AND G.sec_no = ? AND G.exam_no = ? AND G.student_email = U.email""",
                           [self.course_id, self.sec_no, exam[0]])
            grades = []
            for row in cursor:
                grades.append([row[0], row[1], row[2]])
            exam.append(grades)

        cursor.close()
        connection.close()
        return exam_grades

    def set_hw_grade(self, sid, hw_no, grade):
        connection = sql.connect('canvaspath.sqlite')
        cursor = connection.cursor()
        cursor.execute(
            """UPDATE Homework_grades SET grade = ?
            WHERE student_email = ? AND course_id = ? AND sec_no = ? AND hw_no = ?""",
            [grade, sid, self.course_id, self.sec_no, hw_no])
        # print("set hw grade for {} to {}.".format(sid, grade))
        connection.commit()
        cursor.close()
        connection.close()

    def set_exam_grade(self, sid, exam_no, grade):
        connection = sql.connect('canvaspath.sqlite')
        cursor = connection.cursor()
        cursor.execute(
            """UPDATE Exam_grades SET grade = ? 
            WHERE student_email = ? AND course_id = ? AND sec_no = ? AND exam_no = ?""",
            [grade, sid, self.course_id, self.sec_no, exam_no])
        # print("set exam grade for {} to {}.".format(sid, grade))
        connection.commit()
        cursor.close()
        connection.close()

    def create_hw(self, hw_no, details):
        connection = sql.connect('canvaspath.sqlite')
        cursor = connection.cursor()
        cursor.execute(
            """INSERT INTO Homework (course_id, sec_no, hw_no, hw_details) VALUES (?, ?, ?, ?)""",
            [self.course_id, self.sec_no, hw_no, details])
        print("created new homework: {}".format(str(hw_no)))
        section = Section(self.course_id, self.sec_no)
        grades_insert = []
        for student in section.get_students():
            grades_insert.append([student, self.course_id, self.sec_no, hw_no])

        print(grades_insert)
        cursor.executemany(
            """INSERT INTO Homework_grades (student_email, course_id, sec_no, hw_no, grade) 
            VALUES (?, ?, ?, ?, NULL) """, grades_insert)

        connection.commit()
        cursor.close()
        connection.close()

    def create_exam(self, exam_no, details):
        connection = sql.connect('canvaspath.sqlite')
        cursor = connection.cursor()
        cursor.execute(
            """INSERT INTO Exams (course_id, sec_no, exam_no, exam_details) VALUES (?, ?, ?, ?)""",
            [self.course_id, self.sec_no, exam_no, details])
        print("created new exam: {}".format(str(exam_no)))
        section = Section(self.course_id, self.sec_no)
        grades_insert = []
        for student in section.get_students():
            grades_insert.append([student, self.course_id, self.sec_no, exam_no])
        cursor.executemany(
            """INSERT INTO Exam_grades (student_email, course_id, sec_no, exam_no, grade) 
            VALUES (?, ?, ?, ?, NULL) """, grades_insert)

        connection.commit()
        cursor.close()
        connection.close()

    # capstone team info should probably have its own object


class Team:
    course_id = ""
    sec_no = ""
    team_id = -1
    proj_no = -1

    # check if the team exists before we actually assign the local vars
    def __init__(self, course_id, sec_no, team_id):
        try:
            connection = sql.connect('canvaspath.sqlite')
            cursor = connection.cursor()
            cursor.execute(
                """SELECT project_no FROM Capstone_team 
                WHERE course_id = ? AND sec_no = ? AND team_id = ?""", [course_id, sec_no, team_id])
            self.proj_no = cursor.fetchone()[0]
            self.course_id = course_id
            self.sec_no = sec_no
            self.team_id = team_id
            cursor.close()
            connection.close()
        except TypeError:
            print("Could not find course {} section {} team {}.".format(course_id, sec_no, team_id))

    def get_members(self):
        connection = sql.connect('canvaspath.sqlite')
        cursor = connection.cursor()
        # Create a members set which consists of all student emails indexed by their team ID.
        members = set()

        cursor.execute(
            """SELECT student_email FROM Capstone_team_members WHERE course_id = ? AND sec_no = ? AND team_id = ?""",
            [self.course_id, self.sec_no, self.team_id])

        for row in cursor:
            members.add(row[0])

        cursor.close()
        connection.close()
        return members

    def get_team_grade(self):
        connection = sql.connect('canvaspath.sqlite')
        cursor = connection.cursor()
        cursor.execute("""SELECT grade FROM Capstone_grades WHERE course_id = ? AND sec_no = ? AND team_id = ?""",
                       [self.course_id, self.sec_no, self.team_id])
        grade = cursor.fetchone()[0]
        cursor.close()
        connection.close()
        return grade

    def add_member(self, student):
        user = User(student)
        sec = Section(self.course_id, self.sec_no)
        class_members = sec.get_students()
        cur_members = self.get_members()
        if user.user_type == "S" and student in class_members and student not in cur_members:
            connection = sql.connect('canvaspath.sqlite')
            cursor = connection.cursor()
            cursor.execute(
                """INSERT INTO Capstone_team_members (student_email, team_id, course_id, sec_no) VALUES (?, ?, ?, ?)""",
                [student, self.team_id, self.course_id, self.sec_no])
            connection.commit()
            cursor.close()
            connection.close()
            return True
        return False

    def remove_member(self, student):
        if student in self.get_members():
            connection = sql.connect('canvaspath.sqlite')
            cursor = connection.cursor()
            cursor.execute("""DELETE FROM Capstone_team_members 
            WHERE course_id = ? AND sec_no = ? AND team_id = ? AND student_email = ?""",
                           [self.course_id, self.sec_no, self.team_id, student])
            connection.commit()
            cursor.close()
            connection.close()
            return True
        return False

    def set_team_grade(self, grade):
        if self.team_id != -1:
            connection = sql.connect('canvaspath.sqlite')
            cursor = connection.cursor()
            # set grade in the capstone_grades table
            cursor.execute(
                """UPDATE Capstone_grades SET grade = ? WHERE course_id = ? AND sec_no = ? AND team_id = ?""",
                [grade, self.course_id, self.sec_no, self.team_id])
            connection.commit()
            cursor.close()
            connection.close()
            return True
        return False
