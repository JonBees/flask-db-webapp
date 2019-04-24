from flask import render_template, flash, redirect, url_for, request
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse
from app import app
from app.forms import *
from app.models import *
from app.adminfunc import *


@app.route('/')
@app.route('/home')
@login_required
def home():
    # each element in courses consists of [course_id, section_no]
    sid_list = []
    sections = []
    if current_user.user_type == "P":
        sid_list = current_user.get_sections_teaching()
    if current_user.user_type == "S":
        sid_list = current_user.get_enrollments()

    for sec_id in sid_list:
        sec = Section(sec_id[0], sec_id[1])
        link = ""
        if current_user.user_type == "P":
            link = url_for('managecourse', section_id=sec.sec_id)
        if current_user.user_type == "S":
            link = url_for('course', section_id=sec.sec_id)
        sections.append(
            {"cid": sec.course_id, "sno": sec.sec_no, "link": link, "name": sec.course_name, "desc": sec.course_desc})
    return render_template('home.html', title='Home', sections=sections)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User(form.username.data)
        if user.id == "" or not user.check_password(form.password.data):
            flash('Invalid login', category='alert-danger')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('home')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ChangePWForm()
    if form.validate_on_submit():
        if current_user.check_password(form.oldpw.data):
            current_user.set_password(form.newpw.data)
            flash('Password Changed.', category='alert-success')
        else:
            flash('Current Password is incorrect.', category='alert-danger')
    return render_template('profile.html', title='Profile', form=form)


@app.route('/course/<section_id>')
@login_required
def course(section_id):
    cid = section_id[:-3]
    sid = section_id[-2:].lstrip("0")
    try:
        sec = Section(cid, sid)
    except IndexError:
        flash("Course {} section {} was not found.".format(cid, sid), category='alert-warning')
        return redirect(url_for('home'))
    if (cid, int(sid)) in current_user.get_enrollments():
        prof_ids = sec.get_professors()
        profs = []
        for prof in prof_ids:
            user = User(prof)
            profs.append([user.name, user.id, user.office_address])
        hw_grades = sec.get_student_hw_grades(current_user.id)
        print(hw_grades)
        exam_grades = sec.get_student_exam_grades(current_user.id)
        print(exam_grades)
        projects = sec.get_student_projects(current_user.id)
        return render_template('course.html', title=sec.course_id, section=sec, profs=profs, hw_grades=hw_grades,
                               exam_grades=exam_grades, projects=projects)
    else:
        flash('You are not taking {} Section {}.'.format(sec.course_id, sec.sec_no), category='alert-warning')
    return redirect(url_for('home'))


@app.route('/managecourse/<section_id>', methods=['GET', 'POST'])
@login_required
def managecourse(section_id):
    cid = section_id[:-3]
    sid = section_id[-2:].lstrip("0")
    try:
        sec = Section(cid, sid)
    except IndexError:
        flash("Course {} section {} was not found.".format(cid, sid), category='alert-warning')
        return redirect(url_for('home'))
    if (cid, int(sid)) in current_user.get_sections_teaching():
        gradebook = Gradebook(cid, sid)
        hw_gradebook = gradebook.get_hw_gradebook()
        exam_gradebook = []

        teams = sec.get_teams()
        team_grade_forms = []
        add_proj_form = AddProjectForm(prefix="addproj")
        add_team_form = AddTeamForm(prefix="addteam")
        add_students_form = AddStudentsToTeamForm(prefix="addstudents")
        remove_project_form = RemoveProjectForm(prefix="remproj")
        remove_team_form = RemoveTeamForm(prefix="remteam")
        remove_student_form = RemoveStudentFromTeamForm(prefix="remstudent")

        for hw in hw_gradebook:
            for grade in hw[2]:
                hw_form = SetGradeForm(prefix="hw" + str(hw[0]) + grade[1])
                if not hw_form.grade.data:
                    hw_form.grade.data = grade[2]
                grade.append(hw_form)
                if hw_form.submit.data and hw_form.validate_on_submit():
                    # grade[1] is the grade's attached student ID, hw[0] is the homework number
                    gradebook.set_hw_grade(grade[1], hw[0], hw_form.grade.data)
                    flash("Set Homework {} grade for {} to {}.".format(hw[0], grade[1], hw_form.grade.data))
                    return redirect(url_for('managecourse', section_id=section_id))

        if sec.sec_type == "Reg":

            exam_gradebook = gradebook.get_exam_gradebook()

            for exam in exam_gradebook:
                for grade in exam[2]:
                    exam_form = SetGradeForm(prefix="exam" + str(exam[0]) + grade[1])
                    if not exam_form.grade.data:
                        exam_form.grade.data = grade[2]
                    grade.append(exam_form)
                    if exam_form.submit.data and exam_form.validate_on_submit():
                        # grade[1] is the grade's attached student ID, exam[0] is the exam number
                        gradebook.set_exam_grade(grade[1], exam[0], exam_form.grade.data)
                        flash("Set Exam {} grade for {} to {}.".format(exam[0], grade[1], exam_form.grade.data))
                        return redirect(url_for('managecourse', section_id=section_id))

        if sec.sec_type == "Cap":

            # team grade form (one inside each team entry in the table)
            for teamid in teams.keys():
                team = Team(sec.course_id, sec.sec_no, teamid)
                team_grade_form = SetGradeForm(prefix="team" + str(team.team_id))
                if not team_grade_form.grade.data:
                    team_grade_form.grade.data = team.get_team_grade()
                team_grade_forms.append([team.team_id, team.proj_no, team_grade_form])
                if team_grade_form.submit.data and team_grade_form.validate_on_submit():
                    team.set_team_grade(team_grade_form.grade.data)
                    return redirect(url_for('managecourse', section_id=section_id))

            professors = admin_get_professors()
            proflist = []
            for p in professors:
                proflist.append((p, p))

            students = sec.get_students()
            studentlist = []
            for s in students:
                studentlist.append((s, s))

            projects = sec.get_projects()
            projectlist = []
            for p in projects:
                projectlist.append((p, p))

            teamlist = []
            for t in teams:
                teamlist.append((t, t))

            # add project form
            add_proj_form.sponsor.choices = proflist
            if add_proj_form.submit.data and add_proj_form.validate_on_submit():
                s = sec.new_project(add_proj_form.project_no.data, add_proj_form.sponsor.data)
                if s:
                    flash("Added project {} with professor {}".format(add_proj_form.project_no.data,
                                                                      add_proj_form.sponsor.data))
                else:
                    flash("FAILED to add project {} with professor {}".format(add_proj_form.project_no.data,
                                                                              add_proj_form.sponsor.data))
                return redirect(url_for('managecourse', section_id=section_id))

            # add team form
            add_team_form.students.choices = studentlist
            add_team_form.project.choices = projectlist
            if add_team_form.submit.data:
                tid = sec.new_team(add_team_form.students.data, add_team_form.project.data)
                if tid > 0:
                    flash("Added students {} to team {} for project {}.".format(add_team_form.students.data,
                                                                                add_team_form.project.data, tid))
                else:
                    flash("FAILED to add students to project {}.".format(add_team_form.project.data))
                return redirect(url_for('managecourse', section_id=section_id))

            # add students to team form
            add_students_form.team.choices = teamlist
            add_students_form.students.choices = studentlist
            if add_students_form.submit.data:
                team = Team(sec.course_id, sec.sec_no, add_students_form.team.data)
                for student in add_students_form.students.data:
                    s = team.add_member(student)
                    if s:
                        flash("Added {} to team {}".format(student, add_students_form.team.data))
                    else:
                        flash("Failed to add {} to team {}".format(student, add_students_form.team.data))
                return redirect(url_for('managecourse', section_id=section_id))

            # remove project form
            remove_project_form.project_no.choices = projectlist
            if remove_project_form.submit.data:
                s = sec.remove_project(remove_project_form.project_no.data)
                if s:
                    flash("Removed project {}.".format(remove_project_form.project_no.data))
                else:
                    flash("FAILED to remove project {}.".format(remove_project_form.project_no.data))
                return redirect(url_for('managecourse', section_id=section_id))

            # remove team form
            remove_team_form.team.choices = teamlist
            if remove_team_form.submit.data:
                s = sec.remove_team(remove_team_form.team.data)
                if s:
                    flash("Removed team {}.".format(remove_team_form.team.data))
                else:
                    flash("FAILED to remove team {}.".format(remove_team_form.team.data))
                return redirect(url_for('managecourse', section_id=section_id))

            # remove student from team form
            remove_student_form.student.choices = studentlist
            if remove_student_form.submit.data and remove_student_form.validate_on_submit():
                team = Team(sec.course_id, sec.sec_no, remove_student_form.team.data)
                if team.team_id > 0:
                    s = team.remove_member(remove_student_form.student.data)
                    if s:
                        flash("Removed {} from team {}.".format(remove_student_form.student.data,
                                                                remove_student_form.team.data))
                    else:
                        flash("FAILED to remove {} from team {}.".format(remove_student_form.student.data,
                                                                         remove_student_form.team.data))
                else:
                    flash("This section doesn't have a team # {}.".format(remove_student_form.team.data))

                return redirect(url_for('managecourse', section_id=section_id))

        new_hw = NewAssignmentForm(prefix="newassign")

        if new_hw.submit.data and new_hw.validate_on_submit():
            gradebook.create_hw(new_hw.number.data, new_hw.desc.data)
            flash('Homework {} created.'.format(new_hw.number.data), category='alert-success')
            return redirect(url_for('managecourse', section_id=section_id))

        new_exam = NewAssignmentForm(prefix="newexam")

        if new_exam.submit.data and new_exam.validate_on_submit():
            gradebook.create_exam(new_exam.number.data, new_exam.desc.data)
            flash('Exam {} created.'.format(new_exam.number.data), category='alert-success')
            return redirect(url_for('managecourse', section_id=section_id))

        return render_template('managecourse.html', title=sec.course_id, section=sec, hw_gradebook=hw_gradebook,
                               exam_gradebook=exam_gradebook, new_hw=new_hw, new_exam=new_exam, teams=teams,
                               team_grade_forms=team_grade_forms, add_proj_form=add_proj_form,
                               add_team_form=add_team_form, add_students_form=add_students_form,
                               remove_project_form=remove_project_form, remove_team_form=remove_team_form,
                               remove_student_form=remove_student_form)
    else:
        flash('You are not teaching {} Section {}.'.format(sec.course_id, sec.sec_no), category='alert-warning')
    return redirect(url_for('home'))


@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    if current_user.user_type == "A":

        # The WTForms SelectField expects a (value, label) pair
        courses = admin_get_courses()
        courselist = []
        for c in courses:
            courselist.append((c, c))
        # print(courselist)

        students = admin_get_students()
        studentlist = []
        for s in students:
            studentlist.append((s, s))
        # print(studentlist)

        professors = admin_get_professors()
        proflist = []
        for p in professors:
            proflist.append((p, p))
        # print(proflist)

        enroll_form = EnrollStudentsForm(prefix="enroll")
        enroll_form.courses.choices = courselist
        enroll_form.students.choices = studentlist
        if enroll_form.submit.data and enroll_form.validate_on_submit():
            cid = enroll_form.courses.data[:-3]
            sid = enroll_form.courses.data[-2:].lstrip("0")
            for student in enroll_form.students.data:
                s = admin_enroll_student(student, cid, sid)
                if s:
                    flash("Added student {} to {}.".format(student, enroll_form.courses.data))
                else:
                    flash("FAILED to add student {} to {}.".format(student, enroll_form.courses.data))
            return redirect(url_for('admin'))

        unenroll_form = UnenrollStudentForm(prefix="unenroll")
        unenroll_form.courses.choices = courselist
        if unenroll_form.submit.data and unenroll_form.validate_on_submit():
            cid = unenroll_form.courses.data[:-3]
            sid = unenroll_form.courses.data[-2:].lstrip("0")
            s = admin_unenroll_student(unenroll_form.students.data, cid, sid)
            if s:
                flash("Removed student {} from {}.".format(unenroll_form.students.data, unenroll_form.courses.data))
            else:
                flash("FAILED to remove student {} from {}.".format(unenroll_form.students.data,
                                                                    unenroll_form.courses.data))
            return redirect(url_for('admin'))

        assign_form = SetProfessorForm(prefix="assign")
        assign_form.course.choices = courselist
        assign_form.professor.choices = proflist
        if assign_form.submit.data and assign_form.validate_on_submit():
            cid = assign_form.course.data[:-3]
            sid = assign_form.course.data[-2:].lstrip("0")
            s = admin_assign_professor(assign_form.professor.data, cid, sid)
            if s:
                flash('Professor {} assigned to {}'.format(assign_form.professor.data, assign_form.course.data))
            else:
                flash(
                    "FAILED to assign professor {} to {}.".format(assign_form.professor.data, assign_form.course.data))
            return redirect(url_for('admin'))

        add_sec_form = AddSectionForm(prefix='addsec')
        add_sec_form.professor.choices = proflist
        if add_sec_form.submit.data and add_sec_form.validate_on_submit():
            profteam = admin_get_prof_team_id(add_sec_form.professor.data)
            if profteam > 0:
                s = admin_create_section(add_sec_form.course_id.data, add_sec_form.sec_no.data,
                                         add_sec_form.sec_type.data,
                                         add_sec_form.sec_limit.data, profteam)
                if s:
                    flash('Section {} added to course {}'.format(add_sec_form.sec_no.data, add_sec_form.course_id.data))
                else:
                    flash("FAILED to add section {} to course {}.".format(add_sec_form.sec_no.data,
                                                                          add_sec_form.course_id.data))
            else:
                print("Professor {} is not on any teams.".format(add_sec_form.professor.data))
            return redirect(url_for('admin'))

        rem_sec_form = RemoveSectionForm(prefix='remsec')
        if rem_sec_form.submit.data and rem_sec_form.validate_on_submit():
            s = admin_remove_section(rem_sec_form.course_id.data, rem_sec_form.sec_no.data)
            if s:
                flash(
                    "Section {} removed from course {}.".format(rem_sec_form.sec_no.data, rem_sec_form.course_id.data))
            else:
                flash("FAILED to remove section {} from course {}.".format(rem_sec_form.sec_no.data,
                                                                           rem_sec_form.course_id.data))
            return redirect(url_for('admin'))

        add_course_form = AddCourseForm(prefix='addcourse')
        add_course_form.professor.choices = proflist
        if add_course_form.submit.data and add_course_form.validate_on_submit():
            if add_course_form.submit.data and add_course_form.validate_on_submit():
                profteam = admin_get_prof_team_id(add_course_form.professor.data)
                if profteam > 0:
                    s = admin_create_course(add_course_form.course_id.data, add_course_form.course_name.data,
                                            add_course_form.course_desc.data,
                                            add_course_form.sec_no.data,
                                            add_course_form.sec_type.data,
                                            add_course_form.sec_limit.data, profteam)
                    if s:
                        flash("Course {} created.".format(add_course_form.course_id.data))
                    else:
                        flash("FAILED to create course {}.".format(add_course_form.course_id.data))
                else:
                    print("Professor {} is not on any teams.".format(add_sec_form.professor.data))
                return redirect(url_for('admin'))

        rem_course_form = RemoveCourseForm(prefix='remcourse')
        if rem_course_form.submit.data and rem_course_form.validate_on_submit():
            s = admin_remove_course(rem_course_form.course_id.data)
            if s:
                flash("Course {} removed.".format(rem_course_form.course_id.data))
            else:
                flash("FAILED to remove course {}.".format(rem_course_form.course_id.data))
            return redirect(url_for('admin'))

        return render_template('admin.html', title='Admin', enroll_form=enroll_form, assign_form=assign_form,
                               add_sec_form=add_sec_form, add_course_form=add_course_form, unenroll_form=unenroll_form,
                               rem_sec_form=rem_sec_form, rem_course_form=rem_course_form)
    else:
        flash('You are not an administrator.', category='alert-warning')
    return redirect(url_for('home'))
