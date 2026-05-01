from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'swe441_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# إعداد نظام تسجيل الدخول
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# النماذج (Models)
class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
    todos = db.relationship('Todo', backref='owner', lazy=True)

class Todo(db.Model):
    __tablename__ = 'todo'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    complete = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# المسارات (Routes)

@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
        
    if request.method == 'POST':
        # PROJ-10: Ensuring usernames are stored without leading/trailing spaces
        username = request.form.get('username').strip()
        hashed_pw = generate_password_hash(request.form.get('password'), method='pbkdf2:sha256')
        
        new_user = User(username=username, password=hashed_pw)
        db.session.add(new_user)
        db.session.commit()
        
        login_user(new_user)
        return redirect(url_for('home'))
    return render_template("register.html")

@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
        
    if request.method == 'POST':
        username = request.form.get('username').strip()
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, request.form.get('password')):
            login_user(user)
            return redirect(url_for('home'))
        else:
            # PROJ-10: Security flash message for invalid credentials
            flash('Invalid username or password!', 'error')
            
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route("/")
@login_required
def home():
    todo_list = Todo.query.filter_by(user_id=current_user.id).all()
    return render_template("base.html", todo_list=todo_list)

@app.route("/add", methods=["POST"])
@login_required
def add():
    title = request.form.get("title")
    category = request.form.get("category", "General")
    priority = request.form.get("priority", "Medium")
    
    # --- تعديل بسيط لتمكين الكوميت (تنظيف بيانات التاريخ) ---
    start_date = request.form.get("start_date", "").strip()
    end_date = request.form.get("end_date", "").strip()
    
    if title and title.strip():
        new_todo = Todo(
            title=title.strip(), 
            complete=False, 
            category=category, 
            priority=priority, 
            start_date=start_date,
            end_date=end_date,
            user_id=current_user.id
        )
        db.session.add(new_todo)
        db.session.commit()
    return redirect(url_for("home"))

@app.route("/update/<int:todo_id>")
@login_required
def update(todo_id):
    todo = Todo.query.filter_by(id=todo_id, user_id=current_user.id).first()
    if todo:
        todo.complete = not todo.complete
        db.session.commit()
    return redirect(url_for("home"))

@app.route("/delete/<int:todo_id>")
@login_required
def delete(todo_id):
    todo = Todo.query.filter_by(id=todo_id, user_id=current_user.id).first()
    if todo:
        db.session.delete(todo)
        db.session.commit()
    return redirect(url_for("home"))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)