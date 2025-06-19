from flask import Flask, render_template, request, redirect, session, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date, datetime
import os
import sys

print("📂 app.py loaded successfully")

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
db = SQLAlchemy(app)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    tasks = db.relationship('Task', backref='user', lazy=True)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    due_date = db.Column(db.String(20), nullable=True)
    status = db.Column(db.String(20), default="Pending")
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# Create DB
with app.app_context():
    db.create_all()

@app.route('/')
def home():
    if 'user_id' not in session:
        return redirect('/login')

    query = request.args.get('q', '')
    tasks_query = Task.query.filter_by(user_id=session['user_id'])
    if query:
        tasks_query = tasks_query.filter(Task.content.ilike(f"%{query}%"))

    tasks = tasks_query.all()
    today = datetime.today().date()

    # Convert due_date from str to datetime.date
    for task in tasks:
        if task.due_date:
            try:
                task.due_date = datetime.strptime(task.due_date, '%Y-%m-%d').date()
            except ValueError:
                task.due_date = None

    return render_template('home.html', tasks=tasks, today=today)

@app.route('/add', methods=['POST'])
def add():
    if 'user_id' not in session:
        return redirect('/login')
    task_content = request.form['task']
    due = request.form.get('due_date')
    new_task = Task(content=task_content, due_date=due, user_id=session['user_id'])
    db.session.add(new_task)
    db.session.commit()
    return redirect('/')

@app.route('/delete/<int:id>')
def delete(id):
    task = Task.query.get_or_404(id)
    if task.user_id != session['user_id']:
        return "Unauthorized", 403
    db.session.delete(task)
    db.session.commit()
    return redirect('/')

@app.route('/edit/<int:id>')
def edit(id):
    task = Task.query.get_or_404(id)
    if task.user_id != session['user_id']:
        return "Unauthorized", 403
    return render_template('edit.html', task=task)

@app.route('/update/<int:id>', methods=['POST'])
def update(id):
    task = Task.query.get_or_404(id)
    if task.user_id != session['user_id']:
        return "Unauthorized", 403
    task.content = request.form['task']
    task.due_date = request.form['due_date']
    task.status = request.form['status']
    db.session.commit()
    return redirect('/')

@app.route('/complete/<int:id>')
def complete(id):
    task = Task.query.get_or_404(id)
    if task.user_id != session['user_id']:
        return "Unauthorized", 403
    task.status = 'Completed'
    db.session.commit()
    return redirect('/')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            return redirect('/')
        else:
            return render_template('login.html', error="Invalid credentials")

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])

        if User.query.filter_by(username=username).first():
            return render_template('register.html', error="Username already exists")

        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        return redirect('/login')

    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/export')
def export():
    if 'user_id' not in session:
        return redirect('/login')
    tasks = Task.query.filter_by(user_id=session['user_id']).all()
    lines = [f"{t.content}, {t.due_date}, {t.status}" for t in tasks]
    return "<br>".join(lines)

# Start server
if __name__ == '__main__':
    print("✅ Flask server is starting...")
    app.run(debug=True)
