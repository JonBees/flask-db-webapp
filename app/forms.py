from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, IntegerField, SelectField, \
    SelectMultipleField, TextAreaField
from wtforms.validators import DataRequired, EqualTo, Length, NumberRange


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember me')
    submit = SubmitField('Sign in')


class ChangePWForm(FlaskForm):
    oldpw = PasswordField('Current Password', validators=[DataRequired()])
    newpw = PasswordField('New Password', validators=[DataRequired(),
                                                      Length(min=8,
                                                             message='New password must be at least 8 characters')])
    newpwchk = PasswordField('Confirm New Password', validators=[EqualTo('newpw', message='Passwords must match')])
    submit = SubmitField('Confirm Password Change')


class SetGradeForm(FlaskForm):
    grade = IntegerField(validators=[NumberRange(min=0, max=100, message='Grade must be between 0 and 100')])
    submit = SubmitField('Update Grade')


class NewAssignmentForm(FlaskForm):
    number = IntegerField('New Assignment #', validators=[DataRequired(), NumberRange(min=1, max=100,
                                                                                      message='Assignment number must be between 1 and 100')],
                          render_kw={"placeholder": "New Assignment #"})
    desc = StringField('Description', validators=[DataRequired()], render_kw={"placeholder": "Assignment Description"})
    submit = SubmitField('Create')


class EnrollStudentsForm(FlaskForm):
    courses = SelectField('Course', validators=[DataRequired()])
    students = SelectMultipleField('Students', validators=[DataRequired()])
    submit = SubmitField('Enroll')


class UnenrollStudentForm(FlaskForm):
    courses = SelectField('Course', validators=[DataRequired()])
    students = StringField('Student', validators=[DataRequired()])
    submit = SubmitField('Unenroll')


class SetProfessorForm(FlaskForm):
    professor = SelectField('Professor', validators=[DataRequired()])
    course = SelectField('Course', validators=[DataRequired()])
    submit = SubmitField('Assign')


class AddSectionForm(FlaskForm):
    course_id = StringField('Course ID', validators=[DataRequired()])
    sec_no = IntegerField('Section #', validators=[DataRequired()])
    sec_type = SelectField('Section Type', choices=[('Reg', 'Reg'), ('Cap', 'Cap')], validators=[DataRequired()])
    sec_limit = IntegerField('Enrollment Limit', validators=[DataRequired()])
    professor = SelectField('Professor', validators=[DataRequired()])
    submit = SubmitField('Add Section')


class AddCourseForm(FlaskForm):
    course_id = StringField('Course ID', validators=[DataRequired()])
    course_name = StringField('Course Name', validators=[DataRequired()])
    course_desc = TextAreaField('Course Description', validators=[DataRequired()])
    sec_no = IntegerField('Section #', validators=[DataRequired()])
    sec_type = SelectField('Section Type', choices=[('Reg', 'Reg'), ('Cap', 'Cap')], validators=[DataRequired()])
    sec_limit = IntegerField('Enrollment Limit', validators=[DataRequired()])
    professor = SelectField('Professor', validators=[DataRequired()])
    submit = SubmitField('Create Course')


class RemoveSectionForm(FlaskForm):
    course_id = StringField('Course ID', validators=[DataRequired()])
    sec_no = IntegerField('Section #', validators=[DataRequired()])
    submit = SubmitField('Remove Section')


class RemoveCourseForm(FlaskForm):
    course_id = StringField('Course ID', validators=[DataRequired()])
    submit = SubmitField('Remove Course')


class AddProjectForm(FlaskForm):
    project_no = IntegerField('Project #', validators=[DataRequired()])
    sponsor = SelectField('Sponsor')
    submit = SubmitField('Add Project')


class RemoveProjectForm(FlaskForm):
    project_no = SelectField('Project')
    submit = SubmitField('Remove Project')


class AddTeamForm(FlaskForm):
    # project = SelectField('Project', validators=[DataRequired()])
    project = SelectField('Project')
    # students = SelectMultipleField('Students', validators=[DataRequired()])
    students = SelectMultipleField('Students')
    submit = SubmitField('Add Team')


class RemoveTeamForm(FlaskForm):
    # use a single-select with all teams in the class
    team = SelectField('Team')
    submit = SubmitField('Remove Team')


class AddStudentsToTeamForm(FlaskForm):
    # use a multi-select with all students in the class
    team = SelectField('Team')
    students = SelectMultipleField('Students')
    submit = SubmitField('Add Students')


class RemoveStudentFromTeamForm(FlaskForm):
    # don't want to dynamically populate - so make them type in the team & select student
    team = IntegerField('Team', validators=[DataRequired()])
    student = SelectField('Student')
    submit = SubmitField('Remove Student')
