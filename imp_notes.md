# Implementation Notes

Schema modifications
---

Including a Users table, which contains all of the info common to Students and Professors, 
along with a "type" column which determines which additional fields to fill during object init

User(email, password, name, age, gender)
Student(email, major, street, zipcode)
Professor(email, office_address, department, title)


Object Relational Models:
---

User

Section

Gradebook


# Pages


Login
---
Accessible to everyone pre-login


Personal Info
---
Accessible to professors and students


Courses I'm Taking
---
Accessible to students


Enrolled course
---
Accessible to students who are enrolled in a course

* course description
* professor contact info (email + office)
* course grades
* For capstone courses:
    * team number
    * info about team members (probably just email)
    * mentor contact info


Courses I'm Teaching
---
Accessible to professors


Course Administration
---
Accessible to professors who are assigned to a course

#### Creating Assignments


a faculty member must be able to create assignments inside courses/sections they teach 
(divided into homework and exams)
which are then visible to enrolled students


#### Submitting Scores


a faculty member must be able to enter scores for each student(out of 100) 
for the assignments they have created

#### Organizing Teams


a faculty member teaching a capstone course must be able to create a list of projects and the
team assigned to each. Faculty should be able to assign the project a grade which will apply
to all team members.




CanvasPath Administration
---
Only accessible to the user admin@lionstate.edu

* add/remove courses & sections, 
* assign professors to those sections,
* enroll students in sections 

Make sure to enforce the requirements that 
* every prof must be assigned to at least one course 
* adding a student to a course won't exceed the course's size limit