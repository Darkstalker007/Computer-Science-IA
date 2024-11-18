#app.py
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Class, Attendance
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['EMAIL_SENDER'] = 'edunet657@gmail.com'  # Replace with your email
app.config['EMAIL_PASSWORD'] = 'yakb ysyg ogkm aoqz'  # Replace with your email password or app password
from datetime import datetime



db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']
        
        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already exists')
            return redirect(url_for('register'))
        
        new_user = User(name=name, email=email, password=generate_password_hash(password, method='sha256'), role=role)
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'teacher':
        classes = Class.query.filter_by(teacher_id=current_user.id).all()
        return render_template('dashboard.html', classes=classes)
    else:
        return redirect(url_for('student_dashboard'))


class_stack = []

@app.route('/create_class', methods=['GET', 'POST'])
@login_required
def create_class():
    if current_user.role != 'teacher':
        flash('Only teachers can create classes')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        class_name = request.form['class_name']
        new_class = Class(name=class_name, teacher_id=current_user.id)
        class_stack.append(new_class)
        
        while class_stack:
            class_to_save = class_stack.pop()
            db.session.add(class_to_save)
        
        db.session.commit()
        flash('Class created successfully')
        return redirect(url_for('dashboard'))
    
    return render_template('create_class.html')

@app.route('/student_dashboard')
@login_required
def student_dashboard():
    if current_user.role != 'student':
        flash('Only students can access this dashboard')
        return redirect(url_for('dashboard'))
    
    # Get all classes the student is enrolled in
    classes = current_user.classes
    
    # Get attendance records for the student
    attendance_records = Attendance.query.filter_by(student_id=current_user.id).all()
    
    # Calculate attendance statistics
    total_classes = len(attendance_records)
    present_count = sum(1 for record in attendance_records if record.status == 'present')
    absent_count = total_classes - present_count
    attendance_rate = (present_count / total_classes) * 100 if total_classes > 0 else 0
    
    return render_template('student_dashboard.html', 
                           classes=classes, 
                           attendance_records=attendance_records,
                           total_classes=total_classes,
                           present_count=present_count,
                           absent_count=absent_count,
                           attendance_rate=attendance_rate)


@app.route('/add_student/<int:class_id>', methods=['POST'])
@login_required
def add_student(class_id):
    if current_user.role != 'teacher':
        flash('Only teachers can add students')
        return redirect(url_for('dashboard'))
    
    student_email = request.form['student_email']
    student = User.query.filter_by(email=student_email, role='student').first()
    
    if not student:
        flash('Student not found')
        return redirect(url_for('dashboard'))
    
    class_obj = Class.query.get(class_id)
    if student not in class_obj.students:
        class_obj.students.append(student)
        db.session.commit()
        flash('Student added to class')
    else:
        flash('Student already in class')
    
    return redirect(url_for('dashboard'))

from collections import deque

attendance_queue = deque()

@app.route('/mark_attendance/<int:class_id>', methods=['GET', 'POST'])
@login_required
def mark_attendance(class_id):
    if current_user.role != 'teacher':
        flash('Only teachers can mark attendance')
        return redirect(url_for('dashboard'))
    
    class_obj = Class.query.get(class_id)
    
    if request.method == 'POST':
        date_str = request.form['date']
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')  # Convert string to datetime object
        absent_students = []
        for student in class_obj.students:
            status = request.form.get(f'status_{student.id}')
            attendance = Attendance(
                class_id=class_id,
                student_id=student.id,
                status=status,
                attendance_date=date_obj  # Make sure this matches the model field
            )
            attendance_queue.append(attendance)
            if status == 'absent':
                absent_students.append(student)        
        while attendance_queue:
            attendance = attendance_queue.popleft()
            db.session.add(attendance)
        
        db.session.commit()
        
        # Send emails to absent students
        for student in absent_students:
            send_absence_email(student.email, class_obj.name, date_str)
        
        flash('Attendance marked successfully and absence emails sent')
        return redirect(url_for('dashboard'))
    
    return render_template('mark_attendance.html', class_obj=class_obj)
def send_absence_email(student_email, class_name, date):
    sender_email = "edunet657@gmail.com"  # Replace with your email
    sender_password = "yakb ysyg ogkm aoqz"  # Replace with your email password or app password

    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = student_email
    message['Subject'] = f"Absence Notification - {class_name}"

    body = f"""
    Dear Student,

    This is to inform you that you were marked absent for the class {class_name} on {date}.

    If you believe this is an error, please contact your teacher.

    Best regards,
    Attendance System
    """

    message.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(message)
        print(f"Absence email sent to {student_email}")
    except Exception as e:
        print(f"Failed to send email to {student_email}. Error: {str(e)}")


@app.route('/remove_student/<int:class_id>/<int:student_id>', methods=['POST'])
@login_required
def remove_student(class_id, student_id):
    if current_user.role != 'teacher':
        flash('Only teachers can remove students')
        return redirect(url_for('dashboard'))
    
    class_obj = Class.query.get(class_id)
    student = User.query.get(student_id)
    
    if class_obj and student and student in class_obj.students:
        class_obj.students.remove(student)
        db.session.commit()
        flash('Student removed from class')
    else:
        flash('Student or class not found')
    
    return redirect(url_for('dashboard'))



@app.route('/attendance_history/<int:class_id>')
@login_required
def attendance_history(class_id):
    if current_user.role != 'teacher':
        flash('Only teachers can view attendance history')
        return redirect(url_for('dashboard'))
    
    class_obj = Class.query.get(class_id)
    sort_by = request.args.get('sort_by', 'date')  # Default sort by date
    
    # Get all attendance records for the class
    attendance_records = Attendance.query.filter_by(class_id=class_id).all()
    
    # Create a dictionary to store student attendance statistics
    student_stats = {}
    for student in class_obj.students:
        student_records = [r for r in attendance_records if r.student_id == student.id]
        absent_count = sum(1 for r in student_records if r.status == 'absent')
        present_count = sum(1 for r in student_records if r.status == 'present')
        attendance_rate = (present_count / len(student_records) * 100) if student_records else 0
        
        student_stats[student.id] = {
            'name': student.name,
            'absent_count': absent_count,
            'present_count': present_count,
            'attendance_rate': attendance_rate,
            'records': student_records
        }
    
    # Sort the statistics based on selected criteria
    if sort_by == 'absent':
        sorted_stats = dict(sorted(student_stats.items(), 
                                 key=lambda x: x[1]['absent_count'], 
                                 reverse=True))
    elif sort_by == 'present':
        sorted_stats = dict(sorted(student_stats.items(), 
                                 key=lambda x: x[1]['present_count'], 
                                 reverse=True))
    elif sort_by == 'rate':
        sorted_stats = dict(sorted(student_stats.items(), 
                                 key=lambda x: x[1]['attendance_rate'], 
                                 reverse=True))
    else:  # sort by name
        sorted_stats = dict(sorted(student_stats.items(), 
                                 key=lambda x: x[1]['name']))
    
    return render_template('attendance_history.html', 
                         class_obj=class_obj,
                         student_stats=sorted_stats,
                         sort_by=sort_by)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

