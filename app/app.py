import random
from functools import lru_cache
from flask import Flask, render_template, abort, Response, request, make_response, redirect, url_for
from faker import Faker

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

if __name__ == '__main__':
    app.run(debug=True)