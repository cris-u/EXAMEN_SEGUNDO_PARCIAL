from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "supersecretkey"

# -------------------- DB --------------------
def get_db_connection():
    conn = sqlite3.connect('tareas.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            completed INTEGER NOT NULL DEFAULT 0,
            user_id INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# -------------------- Rutas --------------------
@app.route('/register', methods=['GET','POST'])
def register():
    if request.method=='POST':
        username=request.form['username']
        password=request.form['password']
        if not username or not password:
            flash("Todos los campos son obligatorios")
            return redirect(url_for('register'))
        hashed_password = generate_password_hash(password)
        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO users (username,password,created_at) VALUES (?,?,?)',
                         (username, hashed_password, datetime.now()))
            conn.commit()
            flash("Usuario registrado con éxito")
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash("El usuario ya existe")
        finally:
            conn.close()
    return render_template('register.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method=='POST':
        username=request.form['username']
        password=request.form['password']
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username=?',(username,)).fetchone()
        conn.close()
        if user and check_password_hash(user['password'], password):
            session['user_id']=user['id']
            session['username']=user['username']
            return redirect(url_for('dashboard'))
        else:
            flash("Usuario o contraseña incorrectos")
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/', methods=['GET','POST'])
@app.route('/dashboard', methods=['GET','POST'])
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    user_id = session['user_id']
    if request.method=='POST':
        title = request.form['title']
        description = request.form['description']
        if title:
            conn.execute('INSERT INTO tasks (title,description,completed,user_id,created_at) VALUES (?,?,?,?,?)',
                         (title,description,0,user_id,datetime.now()))
            conn.commit()
            flash("Tarea creada")
        return redirect(url_for('dashboard'))
    tasks = conn.execute('SELECT * FROM tasks WHERE user_id=?',(user_id,)).fetchall()
    conn.close()
    return render_template('dashboard.html', tasks=tasks)

@app.route('/complete/<int:task_id>')
def complete_task(task_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    conn.execute('UPDATE tasks SET completed=1 WHERE id=? AND user_id=?',(task_id,session['user_id']))
    conn.commit()
    conn.close()
    return redirect(url_for('dashboard'))

@app.route('/edit/<int:task_id>', methods=['GET','POST'])
def edit_task(task_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    task = conn.execute('SELECT * FROM tasks WHERE id=? AND user_id=?',(task_id,session['user_id'])).fetchone()
    if request.method=='POST':
        title=request.form['title']
        description=request.form['description']
        completed=1 if 'completed' in request.form else 0
        conn.execute('UPDATE tasks SET title=?, description=?, completed=? WHERE id=? AND user_id=?',
                     (title,description,completed,task_id,session['user_id']))
        conn.commit()
        conn.close()
        return redirect(url_for('dashboard'))
    conn.close()
    return render_template('edit_task.html', task=task)

@app.route('/delete/<int:task_id>')
def delete_task(task_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    conn.execute('DELETE FROM tasks WHERE id=? AND user_id=?',(task_id,session['user_id']))
    conn.commit()
    conn.close()
    return redirect(url_for('dashboard'))

# -------------------- Run --------------------
if __name__=="__main__":
    app.run(debug=True)
