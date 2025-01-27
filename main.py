from flask import Flask, render_template, request, redirect, url_for, jsonify, make_response
from datetime import datetime, timedelta
from models import db, User, Task
import hashlib
import jwt

app = Flask(__name__)
app.secret_key = 'eto_ne_sekretnyi_klyuch_eto_prosto_klyuch_ne_sekretnyi_ne_trogai_ego'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()

def token_required(f):
    def wrapper(*args, **kwargs):
        token = request.cookies.get('token')
        if not token:
            return redirect(url_for('login'))
        try:
            data = jwt.decode(token, app.secret_key, algorithms=["HS256"])
            current_user = User.query.filter_by(username=data['username']).first()
        except:
            return redirect(url_for('login'))
        return f(current_user, *args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form['login']
        password = hashlib.sha256(request.form['password'].encode()).hexdigest()
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            token = jwt.encode({'username': username, 'exp': datetime.utcnow() + timedelta(hours=1)}, app.secret_key, algorithm="HS256")
            resp = make_response(redirect(url_for('index')))
            resp.set_cookie('token', token)
            return resp
        error = "Неправильный логин или пароль"
        return render_template('login.html', error=error)
    return render_template('login.html')

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
    return render_template('register.html')

@app.route("/")
def start():
    return redirect(url_for('index'))

@app.route("/documents")
@token_required
def index(current_user):
    return render_template('main.html', username=current_user.username)

@app.route("/account", methods=["GET", "POST"])
@token_required
def account(current_user):
    if request.method == "POST":
        new_login = request.form.get('login')
        new_password = request.form.get('password')
        if new_login:
            current_user.username = new_login
        if new_password:
            current_user.password = hashlib.sha256(new_password.encode()).hexdigest()
        db.session.commit()
        return redirect(url_for('account'))
    return render_template('account.html', username=current_user.username)

@app.route("/delete_account")
@token_required
def delete_account(current_user):
    Task.query.filter_by(user_id=current_user.id).delete()
    db.session.delete(current_user)
    db.session.commit()
    resp = make_response(redirect(url_for('register')))
    resp.delete_cookie('token')
    return resp

@app.route("/logout")
def logout():
    resp = make_response(redirect(url_for('login')))
    resp.delete_cookie('token')
    return resp

@app.route("/tasks")
@token_required
def all_tasks(current_user):
    user_tasks = Task.query.filter_by(user_id=current_user.id).all()
    tasks = [{"id": task.id, "name": task.name, "status": task.status, "data": task.data} for task in user_tasks]
    return jsonify(tasks)

@app.route("/tasks/status/<status>")
@token_required
def tasks_by_status(current_user, status):
    user_tasks = Task.query.filter_by(user_id=current_user.id, status=status).all()
    tasks = [{"id": task.id, "name": task.name, "status": task.status, "data": task.data} for task in user_tasks]
    return jsonify(tasks)

@app.route("/tasks/overdue")
@token_required
def overdue_tasks(current_user):
    today = datetime.today().strftime('%Y-%m-%d')
    user_tasks = Task.query.filter(Task.user_id == current_user.id, Task.data < today).all()
    tasks = [{"id": task.id, "name": task.name, "status": task.status, "data": task.data} for task in user_tasks]
    return jsonify(tasks)

@app.route("/tasks/add", methods=["POST"])
@token_required
def add_task(current_user):
    name = request.json['name']
    status = request.json['status']
    data = request.json['data']
    new_task = Task(name=name, status=status, data=data, user_id=current_user.id)
    db.session.add(new_task)
    db.session.commit()
    return jsonify({"id": new_task.id, "name": new_task.name, "status": new_task.status, "data": new_task.data})

@app.route("/tasks/update/<int:task_id>", methods=["PUT"])
@token_required
def update_task(current_user, task_id):
    task = Task.query.get(task_id)
    if task:
        task.name = request.json['name']
        task.status = request.json['status']
        task.data = request.json['data']
        task.user_id = current_user.id
        db.session.commit()
        return jsonify({"id": task.id, "name": task.name, "status": task.status, "data": task.data})
    return "Дело не найдено", 404

@app.route("/tasks/delete/<int:task_id>", methods=["DELETE"])
@token_required
def delete_task(current_user, task_id):
    task = Task.query.get(task_id)
    if task:
        db.session.delete(task)
        db.session.commit()
        return "Дело удалено", 200
    return "Дело не найдено", 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)