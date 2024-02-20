from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import pandas as pd


app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:qwerty@localhost/gradebookproject' #подключение к таблицам(учителей, студентов и тд)
app.config['SQLALCHEMY_BINDS'] = {'users_db': 'postgresql://postgres:qwerty@localhost/gradebookusers'} #подключение к бд пользователей
db = SQLAlchemy(app)
migrate = Migrate(app, db)



class User(db.Model):
    __bind_key__ = 'users_db'
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(255), unique=True)
    role = db.Column(db.String(50), nullable=False)

class Teachers(db.Model):
    __tablename__ = 'teachers'

    teacher_id = db.Column(db.Integer, primary_key=True)
    teacher_name = db.Column(db.String(255), nullable=True)
    email = db.Column(db.String(255), nullable=True)
    phone = db.Column(db.String(100), nullable=True)

class Students(db.Model):
    __tablename__ = 'students'

    student_id = db.Column(db.Integer, primary_key=True)
    student_name = db.Column(db.String(255), nullable=True)
    birth_date = db.Column(db.Date, nullable=False)
    email = db.Column(db.String(255), nullable=True)

class Subjects(db.Model):
    __tablename__= 'subjects'

    subject_id = db.Column(db.Integer, primary_key=True)
    subject_name = db.Column(db.String(100), nullable=False)
    subject_teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.teacher_id'), nullable=False)
    teacher = db.relationship('Teachers', backref='subjects')

class Grades(db.Model):
    __tablename__ = 'grades'

    grade_id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.student_id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.subject_id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.teacher_id'), nullable=False)
    grade = db.Column(db.Integer, nullable=False)

    student = db.relationship('Students', backref='grades')
    subject = db.relationship('Subjects', backref='grades')
    teacher = db.relationship('Teachers', backref='grades')

# @app.route('/')
# def login():
#     return render_template('login.html')

@app.route('/', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            return render_template('index.html')
        else:
            error = 'Invalid username or password. Please try again.'
    return render_template('login.html', error=error)

@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/teachers')
def teachers():
    teachers = Teachers.query.all()
    return render_template('teachers.html', teachers=teachers)

@app.route('/add_teacher', methods=['GET', 'POST'])
def add_teacher():
    if request.method == 'POST':
        teacher_name = request.form['teacher_name']
        email = request.form['email']
        phone = request.form['phone']
        new_teacher = Teachers(teacher_name=teacher_name, email=email, phone=phone)
        db.session.add(new_teacher)
        db.session.commit()
        return redirect(url_for('teachers'))
    return render_template('add_teacher.html')

@app.route('/delete_teacher/<int:teacher_id>', methods=['GET'])
def delete_teacher(teacher_id):
    teacher = Teachers.query.get_or_404(teacher_id)
    db.session.delete(teacher)
    db.session.commit()
    return redirect(url_for('teachers'))

@app.route('/edit_teacher/<int:teacher_id>', methods=['GET', 'POST'])
def edit_teacher(teacher_id):
    teacher = Teachers.query.get_or_404(teacher_id)

    if request.method == 'POST':
        teacher.teacher_name = request.form['teacher_name']
        teacher.email = request.form['email']
        teacher.phone = request.form['phone']
        db.session.commit()
        return redirect(url_for('teachers'))
    
    return render_template('edit_teacher.html', teacher=teacher)

@app.route('/students')
def students():
    students = Students.query.all()
    return render_template('students.html', students=students)

@app.route('/add_student', methods=['GET', 'POST'])
def add_student():
    if request.method == 'POST':
        student_name = request.form['student_name']
        birth_date = request.form['birth_date']
        email = request.form['email']
        new_student = Students(student_name=student_name, email=email, birth_date=birth_date)
        db.session.add(new_student)
        db.session.commit()
        return redirect(url_for('students'))
    return render_template('add_student.html')


@app.route('/search_students', methods=['GET'])
def search_students():
    query = request.args.get('query')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    students_query = Students.query
    
    if query:
        students_query = students_query.filter((Students.student_name.ilike(f'%{query}%')) | (Students.email.ilike(f'%{query}%')))
    
    if start_date:
        students_query = students_query.filter(Students.birth_date >= start_date)
    
    if end_date:
        students_query = students_query.filter(Students.birth_date <= end_date)
    
    students = students_query.all()
    
    return render_template('students.html', students=students)

@app.route('/subjects')
def subjects():
    subjects = Subjects.query.all()
    return render_template('subjects.html', subjects=subjects)

@app.route('/grades', methods=['GET'])
def grades():
    search_query = request.args.get('search')
    min_grade = request.args.get('min_grade')
    max_grade = request.args.get('max_grade')

    grades_query = Grades.query.join(Students).join(Subjects).join(Teachers)

    if search_query:
        grades_query = grades_query.filter(
            (Students.student_name == search_query) |
            (Subjects.subject_name == search_query) |
            (Teachers.teacher_name == search_query)
        )

    if min_grade:
        grades_query = grades_query.filter(Grades.grade >= int(min_grade))

    if max_grade:
        grades_query = grades_query.filter(Grades.grade <= int(max_grade))

    grades_query = grades_query.order_by(Grades.grade_id.asc())
    grades = grades_query.all()

    return render_template('grades.html', grades=grades)

@app.route('/add_grade', methods=['GET', 'POST'])
def add_grade():
    if request.method == 'POST':
        student_id = request.form['student_id']
        subject_id = request.form['subject_id']
        grade = request.form['grade']
        
        new_grade = Grades(student_id=student_id, subject_id=subject_id, grade=grade)
        db.session.add(new_grade)
        db.session.commit()
        
        return redirect(url_for('grades'))
    
    students = Students.query.all()
    subjects = Subjects.query.all()
    return render_template('add_grade.html', students=students, subjects=subjects)

@app.route('/gradebook_analysis')
def gradebook_analysis():
    # Загрузка данных из базы данных в DataFrame с помощью Pandas
    query = """
    SELECT students.student_name, grades.grade, subjects.subject_name
    FROM students
    JOIN grades ON students.student_id = grades.student_id
    JOIN subjects ON subjects.subject_id = grades.subject_id
    """
    df = pd.read_sql_query(query, db.engine)

    # 1) Студенты с высоким баллом (балл равен 100)
    high_grades = df[df['grade'] == 100]

    # 2) Студенты с низким баллом (балл равен 30)
    low_grades = df[df['grade'] == 30]

    # 3) Общий средний балл
    average_grade = df['grade'].mean()

    # 4) Средний балл по каждому предмету
    average_grade_by_subject = df.groupby('subject_name')['grade'].mean().reset_index()

     # Предметы с максимальным и минимальным средним баллом
    max_average_subject = average_grade_by_subject.loc[average_grade_by_subject['grade'].idxmax()]
    min_average_subject = average_grade_by_subject.loc[average_grade_by_subject['grade'].idxmin()]

    # 5) Ученики с максимальным и минимальным баллом по каждому предмету
    max_grade_students = df.loc[df.groupby('subject_name')['grade'].idxmax()]
    min_grade_students = df.loc[df.groupby('subject_name')['grade'].idxmin()]

    # Преобразование результатов в словарь для передачи в шаблон
    context = {
        'high_grades': high_grades.to_dict(orient='records'),
        'low_grades': low_grades.to_dict(orient='records'),
        'average_grade': average_grade,
        'average_grade_by_subject': average_grade_by_subject.to_dict(orient='records'),
        'max_average_subject': max_average_subject,
        'min_average_subject': min_average_subject,
        'max_grade_students': max_grade_students.to_dict(orient='records'),
        'min_grade_students': min_grade_students.to_dict(orient='records'),
    }

    return render_template('gradebook_analysis.html', **context)


if __name__ == '__main__':
    app.run(debug=True)

if __name__ == '__main__':
    app.run(debug=True)