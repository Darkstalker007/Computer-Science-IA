from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import date

db = SQLAlchemy()

class BaseModel(db.Model):
    __abstract__ = True
    id = db.Column(db.Integer, primary_key=True)

    def save(self):
        db.session.add(self)
        db.session.commit()

    @classmethod
    def get_by_id(cls, id):
        return cls.query.get(id)

class User(UserMixin, BaseModel):
    __tablename__ = 'user'
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    classes = db.relationship('Class', secondary='user_class', back_populates='students')

    def __init__(self, name, email, password, role):
        self.name = name
        self.email = email
        self.password = password
        self.role = role
    def is_teacher(self):
        return self.role == 'teacher'

    def is_student(self):
        return self.role == 'student'

class Class(BaseModel):
    __tablename__ = 'class'
    name = db.Column(db.String(100), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    students = db.relationship('User', secondary='user_class', back_populates='classes')
    attendances = db.relationship('Attendance', back_populates='class_')

    def __init__(self, name, teacher_id):
        self.name = name
        self.teacher_id = teacher_id

    def add_student(self, student):
        if student not in self.students:
            self.students.append(student)
            db.session.commit()

    def remove_student(self, student):
        if student in self.students:
            self.students.remove(student)
            db.session.commit()

class UserClass(BaseModel):
    __tablename__ = 'user_class'
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'))

class Attendance(BaseModel):
    __tablename__ = 'attendance'
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False)
    class_ = db.relationship('Class', back_populates='attendances')

    def __init__(self, class_id, student_id, status, attendance_date=None):
        self.class_id = class_id
        self.student_id = student_id
        self.status = status
        self.date = attendance_date or date.today()

    @classmethod
    def get_student_attendance(cls, student_id, class_id):
        return cls.query.filter_by(student_id=student_id, class_id=class_id).all()

    @classmethod
    def mark_attendance(cls, class_id, student_id, status):
        attendance = cls(class_id, student_id, status)
        attendance.save()
        return attendance