from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Class, Attendance

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


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
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']
        
        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already exists')
            return redirect(url_for('register'))
        
        new_user = User(email=email, password=generate_password_hash(password, method='sha256'), role=role)
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
    else:
        classes = current_user.classes
    return render_template('dashboard.html', classes=classes)

@app.route('/create_class', methods=['GET', 'POST'])
@login_required
def create_class():
    if current_user.role != 'teacher':
        flash('Only teachers can create classes')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        class_name = request.form['class_name']
        new_class = Class(name=class_name, teacher_id=current_user.id)
        db.session.add(new_class)
        db.session.commit()
        flash('Class created successfully')
        return redirect(url_for('dashboard'))
    
    return render_template('create_class.html')

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

@app.route('/mark_attendance/<int:class_id>', methods=['GET', 'POST'])
@login_required
def mark_attendance(class_id):
    if current_user.role != 'teacher':
        flash('Only teachers can mark attendance')
        return redirect(url_for('dashboard'))
    
    class_obj = Class.query.get(class_id)
    
    if request.method == 'POST':
        date = request.form['date']
        for student in class_obj.students:
            status = request.form.get(f'status_{student.id}')
            attendance = Attendance(class_id=class_id, student_id=student.id, date=date, status=status)
            db.session.add(attendance)
        db.session.commit()
        flash('Attendance marked successfully')
        return redirect(url_for('dashboard'))
    
    return render_template('mark_attendance.html', class_obj=class_obj)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
