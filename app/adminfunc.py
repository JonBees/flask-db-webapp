import sqlite3 as sql
from app.models import User, Section


# If I were concerned about performance, I would overload all of these functions with variants
# that take a cursor as a parameter so they wouldn't have to keep initializing new connections over and over again

def admin_get_students():
    connection = sql.connect('canvaspath.sqlite')
    cursor = connection.cursor()
    students = []
    cursor.execute("""SELECT email FROM Student""")
    for row in cursor:
        students.append(row[0])

    cursor.close()
    connection.close()
    return students


def admin_get_professors():
    connection = sql.connect('canvaspath.sqlite')
    cursor = connection.cursor()
    professors = []
    cursor.execute("""SELECT email FROM Professor""")
    for row in cursor:
        professors.append(row[0])

    cursor.close()
    connection.close()
    return professors


# sec_id = cid + "S" + ("{:02d}".format(int(sec)))
def admin_get_courses():
    connection = sql.connect('canvaspath.sqlite')
    cursor = connection.cursor()
    courses = []
    cursor.execute("""SELECT course_id, sec_no FROM Section""")
    for row in cursor:
        courses.append(row[0] + "S" + ("{:02d}".format(row[1])))

    cursor.close()
    connection.close()
    return courses


def admin_get_prof_team_id(professor):
    connection = sql.connect('canvaspath.sqlite')
    cursor = connection.cursor()
    profteamid = -1
    try:
        cursor.execute("""SELECT team_id FROM Prof_team_members P WHERE P.prof_email = ?""",
                       [professor])
        profteamid = cursor.fetchone()[0]
    except TypeError:
        print("Can't find team with professor {}".format(professor))

    cursor.close()
    connection.close()
    return profteamid


def admin_get_sections(course_id):
    connection = sql.connect('canvaspath.sqlite')
    cursor = connection.cursor()
    sections = set()
    try:
        cursor.execute("""SELECT sec_no FROM Section WHERE course_id=?""", [course_id])
        for row in cursor:
            sections.add(row[0])
    except TypeError:
        print("No sections for {} found.".format(course_id))
    cursor.close()
    connection.close()
    return sections


def admin_get_section_capacity(course_id, sec_no):
    connection = sql.connect('canvaspath.sqlite')
    cursor = connection.cursor()
    capacity = (0, 0)
    try:
        cursor.execute("""SELECT sec_limit FROM Section WHERE course_id = ? AND sec_no = ?""", [course_id, sec_no])
        limit = cursor.fetchone()[0]
        cursor.execute("""SELECT COUNT(*) FROM Enrolls WHERE course_id = ? AND section_no = ?""", [course_id, sec_no])
        enrol_no = cursor.fetchone()[0]
        capacity = (enrol_no, limit)
    except TypeError:
        print("Course {} section {} not found.".format(course_id, sec_no))
    cursor.close()
    connection.close()
    return capacity


# to make sure this is valid, check that we don't already have a course with this ID.
def admin_create_course(course_id, course_name, course_desc, sec_no, sec_type, sec_limit, prof_team_id):
    success = False
    connection = sql.connect('canvaspath.sqlite')
    cursor = connection.cursor()
    if len(admin_get_sections(course_id)) == 0:
        cursor.execute("""INSERT INTO Course (course_id, course_name, course_description) VALUES (?, ?, ?)""",
                       [course_id, course_name, course_desc])
        cursor.execute(
            """INSERT INTO Section (course_id, sec_no, section_type, sec_limit, prof_team_id) VALUES (?, ?, ?, ?, ?)""",
            [course_id, sec_no, sec_type, sec_limit, prof_team_id])
        print("Created course {} section {}".format(course_id, sec_no))
        success = True
    else:
        print("Course {} already exists.".format(course_id))
    connection.commit()
    cursor.close()
    connection.close()
    return success


# to make sure this is valid, check that the course exists and that it doesn't currently have a section with this no.
def admin_create_section(course_id, sec_no, sec_type, sec_limit, prof_team_id):
    success = False
    connection = sql.connect('canvaspath.sqlite')
    cursor = connection.cursor()
    secset = admin_get_sections(course_id)
    if len(secset) > 0 and sec_no not in secset:
        cursor.execute("""INSERT INTO Section (course_id, sec_no, section_type, sec_limit, prof_team_id) 
        VALUES (?, ?, ?, ?, ?)""", [course_id, sec_no, sec_type, sec_limit, prof_team_id])
        print("Created course {} section {}.")
        success = True
    else:
        print("Either Course {} does not exist or section {} already exists.".format(course_id, sec_no))
    connection.commit()
    cursor.close()
    connection.close()
    return success


# to make sure this is valid, check that the course exists
# and that removing the course will not cause any professor to be teaching zero sections.
def admin_remove_course(course_id):
    success = False
    connection = sql.connect('canvaspath.sqlite')
    cursor = connection.cursor()
    secs = admin_get_sections(course_id)
    if len(secs) > 0:

        # For each section of the class which would be removed, subtract 1 from the professor's course count.
        profsafe = True
        profdict = {}
        for sec in secs:
            prof = Section(course_id, sec).get_professors()[0]
            profcoursecount = len(User(prof).get_sections_teaching())
            if prof in profdict:
                profdict[prof] = profcoursecount - 1
            else:
                profdict[prof] = [prof, profcoursecount - 1]
        # If, after having all sections of this course removed,
        # the professor would have no courses left, we can't remove the course
        for prof in profdict:
            if profdict[prof] == 0:
                profsafe = False

        if profsafe:
            cursor.execute("""DELETE FROM Section WHERE course_id = ?""", [course_id])
            cursor.execute("""DELETE FROM Course WHERE course_id = ?""", [course_id])
            cursor.execute("""DELETE FROM Enrolls WHERE course_id = ?""", [course_id])
            print("Deleted course {}.".format(course_id))
            success = True
        else:
            print("Could not delete course {}, it would remove the last course from a professor.")
    connection.commit()
    cursor.close()
    connection.close()
    return success


# to make sure this is valid, check that the section exists.
# and that removing the section will not cause any professor to be teaching zero sections.
def admin_remove_section(course_id, sec_no):
    success = False
    connection = sql.connect('canvaspath.sqlite')
    cursor = connection.cursor()
    secs = admin_get_sections(course_id)
    if sec_no in secs:

        if len(secs) == 1:
            admin_remove_course(course_id)

        else:
            prof = Section(course_id, sec_no).get_professors()[0]
            profcoursecount = len(User(prof).get_sections_teaching())

            if profcoursecount > 1:
                cursor.execute("""DELETE FROM Section WHERE course_id = ? AND sec_no = ?""", [course_id, sec_no])
                cursor.execute("""DELETE FROM Enrolls WHERE course_id = ? AND section_no = ?""", [course_id, sec_no])
                print("Deleted course {} section {}.".format(course_id, sec_no))
                success = True
            else:
                print("Removing {} would remove the last section from professor {}.".format(course_id + str(sec_no),
                                                                                            prof))

    connection.commit()
    cursor.close()
    connection.close()
    return success


# to make sure this is valid, check that both the student and the section exist,
# the student is not already in the section, and the section is not full
def admin_enroll_student(student, course_id, sec_no):
    success = False
    connection = sql.connect('canvaspath.sqlite')
    cursor = connection.cursor()
    secs = admin_get_sections(course_id)
    if int(sec_no) in secs:
        user = User(student)
        if user.id != "" and (course_id, sec_no) not in user.get_enrollments():
            cap = admin_get_section_capacity(course_id, sec_no)
            if cap[0] < cap[1]:
                cursor.execute("""INSERT INTO Enrolls (student_email, course_id, section_no) VALUES (?, ?, ?)""",
                               [student, course_id, sec_no])
                print("Added student {} to course {} section {}.".format(student, course_id, sec_no))
                success = True
            else:
                print("Failed to add student: Current # enrolled is {}, Section cap is {}".format(cap[0], cap[1]))
        else:
            print("User {} does not exist or is already enrolled in {} sec {}".format(user.id, course_id, sec_no))
    else:
        print("Course {} section {} does not exist.".format(course_id, sec_no))
        print(type(sec_no))
        print(type(secs.pop()))
    connection.commit()
    cursor.close()
    connection.close()
    return success


def admin_unenroll_student(student, course_id, sec_no):
    success = False
    connection = sql.connect('canvaspath.sqlite')
    cursor = connection.cursor()
    secs = admin_get_sections(course_id)
    if int(sec_no) in secs:
        user = User(student)
        if user.id != "" and (course_id, int(sec_no)) in user.get_enrollments():
            cursor.execute("""DELETE FROM Enrolls WHERE student_email = ? AND course_id = ? AND section_no = ?""",
                           [student, course_id, sec_no])
            print("Removed student {} from course {} section {}.".format(student, course_id, sec_no))
            success = True
        else:
            print("User {} does not exist or is not enrolled in {} sec {}".format(user.id, course_id, sec_no))
    else:
        print("Course {} section {} does not exist.".format(course_id, sec_no))
        print(type(sec_no))
        print(type(secs.pop()))
    connection.commit()
    cursor.close()
    connection.close()
    return success


# I'm going to cheat here and take advantage of the fact that each team contains a single professor
# in order to simplify the interface and allow the admin to assign a single professor to a single section.

# similar to how we dealt with students, we need to make sure the professor exists, the section exists, and
# that reassigning a section to a new professor does not prevent the previous professor from teaching at least 1 course
def admin_assign_professor(professor, course_id, sec_no):
    success = False
    connection = sql.connect('canvaspath.sqlite')
    cursor = connection.cursor()
    if int(sec_no) in admin_get_sections(course_id):
        user = User(professor)
        if user.id != "" and (course_id, sec_no) not in user.get_sections_teaching():
            oldprof = Section(course_id, sec_no).get_professors()[0]
            oldprofcoursecount = len(User(oldprof).get_sections_teaching())
            # if the course doesn't currently have a professor or if the old professor is still teaching a course
            # after removal from this one, we're good.
            if oldprof == [] or oldprofcoursecount > 1:
                profteamid = admin_get_prof_team_id(professor)
                if profteamid > 0:
                    cursor.execute("""UPDATE Section SET prof_team_id = ? WHERE course_id = ? AND sec_no = ?""",
                                   [profteamid, course_id, sec_no])
                    print("Assigned professor {} to course {} section {}.".format(professor, course_id, sec_no))
                    success = True
                else:
                    print("couldn't find prof team for {}".format(user.id))
            else:
                print("Failed removal check: old professor is {}, and their course count is {}".format(oldprof,
                                                                                                       oldprofcoursecount))
        else:
            print("either user id \"{}\" is bad or course {} sec {} is already in {}".format(user.id, course_id, sec_no,
                                                                                             user.get_sections_teaching()))
    else:
        print("Course {} section {} does not exist.".format(course_id, sec_no))
    connection.commit()
    cursor.close()
    connection.close()
    return success
