import random
from functools import lru_cache
from flask import Flask, render_template, abort, Response, request, make_response, redirect, url_for, flash, session
from faker import Faker
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from datetime import timedelta

fake = Faker()

app = Flask(__name__)
application = app

images_ids = ['7d4e9175-95ea-4c5f-8be5-92a6b708bb3c',
              '2d2ab7df-cdbc-48a8-a936-35bba702def5',
              '6e12f3de-d5fd-4ebb-855b-8cbc485278b7',
              'afc2cfe7-5cac-4b80-9b9a-d5c65ef0c728',
              'cab5b7f2-774e-4884-a200-0c0180fa777f']

def generate_comments(replies=True):
    comments = []
    for _ in range(random.randint(1, 3)):
        comment = { 'author': fake.name(), 'text': fake.text() }
        if replies:
            comment['replies'] = generate_comments(replies=False)
        comments.append(comment)
    return comments

def generate_post(i):
    return {
        'title': fake.paragraph(nb_sentences=1),
        'text': fake.paragraph(nb_sentences=100),
        'author': fake.name(),
        'date': fake.date_time_between(start_date='-2y', end_date='now'),
        'image_id': f'{images_ids[i]}.jpg',
        'comments': generate_comments()
    }

@lru_cache
def posts_list():
    return sorted([generate_post(i) for i in range(5)], key=lambda p: p['date'], reverse=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/posts')
def posts():
    return render_template('posts.html', title='Посты', posts=posts_list())

@app.route('/posts/<int:index>')
def post(index):
    if index >= len(posts_list())-1 or index < 0:
        abort(404)
    p = posts_list()[index]
    return render_template('post.html', title=p['title'], post=p)

@app.route('/about')
def about():
    return render_template('about.html', title='Об авторе')

@app.errorhandler(404)
def page_not_found(e):
    return Response('404 Not Found', status=404)

# Параметры URL
@app.route('/url-params')
def url_params():
    params = request.args 
    return render_template('url_params.html', title='Параметры URL', params=params)

# Заголовки запроса
@app.route('/headers')
def headers():
    headers = dict(request.headers)
    return render_template('headers.html', title='Заголовки запроса', headers=headers)

# Cookie
@app.route('/cookies', methods=['GET', 'POST'])
def cookies():
    resp = make_response()
    cookie_name = 'my_cookie'

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'set':
            resp = make_response(redirect(url_for('cookies')))
            resp.set_cookie(cookie_name, 'cookie_value', max_age=60*60*24)
            return resp
        elif action == 'delete':
            resp = make_response(redirect(url_for('cookies')))
            resp.delete_cookie(cookie_name)
            return resp

    cookie_set = request.cookies.get(cookie_name)
    message = "Cookie установлено." if cookie_set else "Cookie не установлено."
    return render_template('cookies.html', title='Cookie', message=message, cookie_set=cookie_set)

# Параметры формы
@app.route('/form_params', methods=['GET', 'POST'])
def form_params():
    form_data = {}
    if request.method == 'POST':
        form_data = request.form
    return render_template('form_params.html', title='Параметры формы', form_data=form_data)

# Проверка номера телефона
import re

@app.route('/phone_validation', methods=['GET', 'POST'])
def phone_validation():
    error = None
    formatted_phone = None

    if request.method == 'POST':
        phone = request.form.get('phone', '')

        clean_phone = re.sub(r"[^\d]", "", phone)

        if not clean_phone.isdigit():
            error = "Недопустимый ввод. В номере телефона встречаются недопустимые символы."
        elif not (10 <= len(clean_phone) <= 11):
            error = "Недопустимый ввод. Неверное количество цифр."
        else:
            if clean_phone.startswith('8') or clean_phone.startswith('7'):
                clean_phone = '8' + clean_phone[-10:]
            formatted_phone = f"{clean_phone[0]}-{clean_phone[1:4]}-{clean_phone[4:7]}-{clean_phone[7:9]}-{clean_phone[9:11]}"

    return render_template('phone_validation.html', title='Проверка номера телефона', error=error, formatted_phone=formatted_phone)

# лр 3
app.secret_key = 'your-secret-key'
app.permanent_session_lifetime = timedelta(days=7)

login_manager = LoginManager()
login_manager.login_message = "Пожалуйста, войдите в систему для доступа к этой странице."
login_manager.login_message_category = "warning"
login_manager.login_view = 'login'
login_manager.init_app(app)

user_visits = {}

class User(UserMixin):
    def __init__(self, id, name, password):
        self.id = id
        self.name = name
        self.password = password

    def __repr__(self):
        return f"<User: {self.name}>"

users = {
    "user": User(id=1, name="user", password="qwerty"),
    "user1": User(id=2, name="user1", password="123")
}

@login_manager.user_loader
def load_user(user_id):
    for user in users.values():
        if str(user.id) == str(user_id):
            return user
    return None

@app.route('/counter')
def counter():
    if current_user.is_authenticated:
        username = current_user.name
        if username not in user_visits:
            user_visits[username] = 1
        else:
            user_visits[username] += 1
        visits = user_visits[username]
    else:
        session.permanent = True
        if 'visits' not in session:
            session['visits'] = 1
        else:
            session['visits'] += 1
        visits = session['visits']

    return render_template('counter.html', visits=visits)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        remember = 'remember' in request.form

        if username in users and users[username].password == password:
            login_user(users[username], remember=remember)
            flash("Вы успешно вошли в систему!", "success")
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash("Неверный логин или пароль", "danger")
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Вы вышли из системы.", "info")
    return redirect(url_for('index'))

@app.route('/secret')
@login_required
def secret():
    return render_template('secret.html')

if __name__ == '__main__':
    app.run(debug=True)