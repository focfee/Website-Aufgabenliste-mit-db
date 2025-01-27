from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from datetime import datetime
from models import db, User, Task
import hashlib

app = Flask(__name__)
app.secret_key = 'eto_ne_sekretnyi_klyuch_eto_prosto_klyuch_ne_sekretnyi_ne_trogai_ego'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form['login']
        password = hashlib.sha256(request.form['password'].encode()).hexdigest()
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session['logged_in'] = True
            session['username'] = username
            return redirect(url_for('index'))
        error = "Неправильный логин или пароль"
        return render_template('login.html', error=error)
    return render_template('login.html', username=session.get('username'))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form['login']
        password = hashlib.sha256(request.form['password'].encode()).hexdigest()
        if User.query.filter_by(username=username).first():
            error = "Пользователь уже существует"
            return render_template('register.html', error=error)
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html', username=session.get('username'))

@app.route("/")
def start():
    return redirect(url_for('index'))

@app.route("/documents")
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('main.html', username=session.get('username'))

@app.route("/account", methods=["GET", "POST"])
def account():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    if request.method == "POST":
        username = session['username']
        user = User.query.filter_by(username=username).first()
        new_login = request.form.get('login')
        new_password = request.form.get('password')
        if new_login:
            user.username = new_login
            session['username'] = new_login
        if new_password:
            user.password = hashlib.sha256(new_password.encode()).hexdigest()
        db.session.commit()
        return redirect(url_for('account'))
    return render_template('account.html', username=session.get('username'))

@app.route("/delete_account")
def delete_account():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    username = session['username']
    user = User.query.filter_by(username=username).first()
    if user:
        Task.query.filter_by(user_id=user.id).delete()
        db.session.delete(user)
        db.session.commit()
        session.clear()
    return redirect(url_for('register'))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route("/tasks")
def all_tasks():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    username = session['username']
    user = User.query.filter_by(username=username).first()
    user_tasks = Task.query.filter_by(user_id=user.id).all()
    tasks = [{"id": task.id, "name": task.name, "status": task.status, "data": task.data} for task in user_tasks]
    return jsonify(tasks)

@app.route("/tasks/status/<status>")
def tasks_by_status(status):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    username = session['username']
    user = User.query.filter_by(username=username).first()
    user_tasks = Task.query.filter_by(user_id=user.id, status=status).all()
    tasks = [{"id": task.id, "name": task.name, "status": task.status, "data": task.data} for task in user_tasks]
    return jsonify(tasks)

@app.route("/tasks/overdue")
def overdue_tasks():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    username = session['username']
    user = User.query.filter_by(username=username).first()
    today = datetime.today().strftime('%Y-%m-%d')
    user_tasks = Task.query.filter(Task.user_id == user.id, Task.data < today).all()
    tasks = [{"id": task.id, "name": task.name, "status": task.status, "data": task.data} for task in user_tasks]
    return jsonify(tasks)

@app.route("/tasks/add", methods=["POST"])
def add_task():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    username = session['username']
    user = User.query.filter_by(username=username).first()
    name = request.json['name']
    status = request.json['status']
    data = request.json['data']
    new_task = Task(name=name, status=status, data=data, user_id=user.id)
    db.session.add(new_task)
    db.session.commit()
    return jsonify({"id": new_task.id, "name": new_task.name, "status": new_task.status, "data": new_task.data})

@app.route("/tasks/update/<int:task_id>", methods=["PUT"])
def update_task(task_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    task = Task.query.get(task_id)
    if task:
        task.name = request.json['name']
        task.status = request.json['status']
        task.data = request.json['data']
        task.user_id = User.query.filter_by(username=session['username']).first().id  # Ensure user_id is set
        db.session.commit()
        return jsonify({"id": task.id, "name": task.name, "status": task.status, "data": task.data})
    return "Дело не найдено", 404

@app.route("/tasks/delete/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    task = Task.query.get(task_id)
    if task:
        db.session.delete(task)
        db.session.commit()
        return "Дело удалено", 200
    return "Дело не найдено", 404

if __name__ == "__main__":
    app.run(debug=True)