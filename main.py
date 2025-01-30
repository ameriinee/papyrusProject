
from flask import Flask, request, render_template
from flask_sqlalchemy import SQLAlchemy

### importy do formularzy
from flask import redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import InputRequired, Length, EqualTo

app = Flask(__name__)

################################ baza danych

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config['SECRET_KEY'] = 'mysecretkey'
db = SQLAlchemy(app)


### tabela z uzytkownikami

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, unique=True)
    posts = db.relationship("Post", backref="author", lazy=True)
    password = db.Column(db.String(100), nullable=False)

### tabela z postami

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
   
   
################################ formularze

### rejestracja - formularz

class RegistrationForm(FlaskForm):
    username = StringField("Username", validators=[InputRequired(), Length(min=4, max=80)])
    password = PasswordField("Password", validators=[InputRequired(), Length(min=6)])
    confirm_password = PasswordField("Confirm Password", validators=[InputRequired(), EqualTo('password')])

### logowanie - formularz

class LoginForm(FlaskForm):
    username = StringField("Username", validators=[InputRequired(), Length(min=4, max=80)])
    password = PasswordField("Password", validators=[InputRequired()])

### Dodawanie postów- formularz
class PostForm(FlaskForm):
    title = StringField("Tytuł", validators=[InputRequired(), Length(max=200)])
    content = StringField("Treść", validators=[InputRequired()])
################################ kod ktory sie uruchamia na poczatku

with app.app_context():
    db.create_all()
    
    ### stworzenie admina (login: admin, haslo: admin)

    admin = User.query.filter_by(username="admin").first()
    if not admin:
        new_admin = User(username="admin", password="admin")
        db.session.add(new_admin)
        db.session.commit()

################################ obsluga formularzy
### obsluga logowania

@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id  # Przechowywanie id użytkownika w sesji
            flash("Zalogowano pomyślnie!", "success")
            return redirect(url_for('profile'))
        else:
            flash("Niepoprawna nazwa użytkownika lub hasło!", "danger")
    return render_template("login.html", form=form)

### obsluga rejestracji

@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash("Użytkownik o tej nazwie już istnieje!", "danger")
        else:
            hashed_password = generate_password_hash(password)
            new_user = User(username=username, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
        flash("Rejestracja zakończona sukcesem!", "success") 
        return redirect(url_for('login'))
    return render_template("register.html", form=form)

### profil
@app.route("/profile", methods=["GET", "POST"])
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    
    # Formularz dodawania postu
    form = PostForm()
    
    if form.validate_on_submit():
        title = form.title.data
        content = form.content.data
        new_post = Post(title=title, content=content, user_id=user.id)
        db.session.add(new_post)
        db.session.commit()
        flash("Post został dodany!", "success")
        return redirect(url_for('profile'))  # Przekierowanie z powrotem na profil
    
    posts = Post.query.filter_by(user_id=user.id).all()
    
    return render_template("profile.html", user=user, form=form, posts=posts)

@app.route("/delete_post/<int:post_id>", methods=["POST"])
def delete_post(post_id):
    if 'user_id' not in session:
        flash("Musisz być zalogowany, aby usunąć post.", "danger")
        return redirect(url_for('login'))
    
    post = Post.query.get_or_404(post_id)
    if post.user_id != session['user_id']:
        flash("Nie masz uprawnień do usunięcia tego posta.", "danger")
        return redirect(url_for('profile'))

    db.session.delete(post)
    db.session.commit()
    flash("Post został usunięty!", "success")
    return redirect(url_for('profile'))   

@app.route("/choose_profile_picture", methods=["POST"])
def choose_profile_picture():
    if 'user_id' not in session:
        flash("Musisz być zalogowany!", "danger")
        return redirect(url_for('login'))
    
    selected_picture = request.form.get("profile_picture")

    # Lista dozwolonych zdjęć
    allowed_pictures = [
        "/static/profile.png",
        "/static/profile2.png",
        "/static/profile3.png",
        "/static/profile4.png"
    ]
    
    if selected_picture not in allowed_pictures:
        flash("Nieprawidłowy wybór zdjęcia!", "danger")
        return redirect(url_for('profile'))
    
    # Zapisanie wyboru w sesji
    session['profile_picture'] = selected_picture
    
    flash("Zdjęcie profilowe zostało zmienione!", "success")
    return redirect(url_for('profile'))

### obsluga wylogowywania 
@app.route("/logout")
def logout():
    session.pop('user_id', None)  # Usuwanie użytkownika z sesji
    flash("Zostałeś wylogowany!", "info")
    return redirect(url_for('login'))

### trasa do glownej strony

@app.route("/", methods=["GET", "POST"])
def index():
    posts = Post.query.all()
    return render_template("index.html", posts=posts)

### trasa do uzytkownikow (/users) - pokazuje liste uzytkownikow

@app.route("/users")
def show_users():
    users = User.query.all()

    print("Lista użytkowników:")
    for user in users:
        print(f"{user.id}, {user.username}, {user.password}")

    return "Użytkownicy zostali wyświetleni w konsoli!"


if __name__ == "__main__":
    app.run(port=8080)

 
