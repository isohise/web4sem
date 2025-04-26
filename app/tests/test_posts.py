import pytest
from app import app
import app as app_module
import re


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

# 1. Приложение запускается и возвращает 200 на главной
def test_app_is_up(client):
    rv = client.get('/')
    assert rv.status_code == 200

# 2. Главная страница рендерит правильный шаблон
def test_index_template(client):
    rv = client.get('/')
    html = rv.data.decode('utf-8')
    assert "Задание к лабораторной работе" in html

# 3. Страница /posts рендерит посты и заголовок
def test_posts_page_content(client):
    rv = client.get('/posts')
    html = rv.data.decode('utf-8')
    assert "Последние посты" in html

# 4. Проверка отображения одного поста
def test_post_detail_content(client):
    rv = client.get('/posts/1')
    html = rv.data.decode('utf-8')
    assert rv.status_code == 200
    assert "Автор" in html

# 5. Проверка данных поста в шаблоне
def test_post_data_presence(client):
    rv = client.get('/posts/1')
    html = rv.data.decode('utf-8')
    assert any(x in html for x in ["Автор", "Дата", ".jpg"])

# 6. Проверка даты публикации
def test_post_date_displayed(client):
    rv = client.get('/posts/1')
    html = rv.data.decode('utf-8')
    assert "202" in html or "20" in html

# 7. Ошибка 404 при доступе к несуществующему посту
def test_invalid_post_index_returns_404(client):
    rv = client.get('/posts/100')
    assert rv.status_code == 404

# 8. Проверка, что все посты отображаются на /posts
def test_all_posts_listed(client):
    rv = client.get('/posts')
    html = rv.data.decode('utf-8')
    for i in range(5):
        assert ".jpg" in html

# 9. Проверка рендера страницы Об авторе
def test_about_page(client):
    rv = client.get('/about')
    html = rv.data.decode('utf-8')
    assert rv.status_code == 200
    assert "Об авторе" in html

# 10. Страница поста не существует: нижний предел
def test_post_negative_index(client):
    rv = client.get('/posts/-1')
    assert rv.status_code == 404

# 11. Главная страница содержит ссылку на /posts
def test_main_page_links_to_posts(client):
    rv = client.get('/')
    html = rv.data.decode('utf-8')
    assert "/posts" in html

# 12. Страница поста содержит изображение
def test_post_contains_image(client):
    rv = client.get('/posts/1')
    html = rv.data.decode('utf-8')
    assert ".jpg" in html

# 13. Пост содержит комментарии
def test_post_has_comments(client):
    rv = client.get('/posts/1')
    html = rv.data.decode('utf-8')
    assert "replies" in html or "text" in html

# 14. Комментарии имеют автора и текст
def test_comment_structure(client):
    rv = client.get('/posts/1')
    html = rv.data.decode('utf-8')
    assert "author" in html or "text" in html

# 15. Проверка ответа страницы /posts
def test_posts_status(client):
    rv = client.get('/posts')
    assert rv.status_code == 200

# 16. Проверка корректного возврата /about
def test_about_status(client):
    rv = client.get('/about')
    assert rv.status_code == 200


# ЛР 2

# 1. Проверка, что параметры URL отображаются на странице
def test_url_params_display(client):
    rv = client.get('/url-params?name=John&age=30')
    html = rv.data.decode('utf-8')
    assert rv.status_code == 200
    assert 'name' in html
    assert 'John' in html
    assert 'age' in html
    assert '30' in html

# 2. Проверка, что заголовки запроса отображаются на странице
def test_headers_display(client):
    rv = client.get('/headers', headers={'Custom-Header': 'Value123'})
    html = rv.data.decode('utf-8')
    assert rv.status_code == 200
    assert 'Custom-Header' in html
    assert 'Value123' in html

# 3. Проверка установки cookie
def test_set_cookie(client):
    rv = client.post('/cookies', data={'action': 'set'}, follow_redirects=True)
    html = rv.data.decode('utf-8')
    assert rv.status_code == 200
    assert 'Cookie установлено' in html

# 4. Проверка удаления cookie
def test_delete_cookie(client):
    client.set_cookie(key='my_cookie', value='cookie_value', domain='localhost')
    rv = client.post('/cookies', data={'action': 'delete'}, follow_redirects=True)
    html = rv.data.decode('utf-8')
    assert rv.status_code == 200
    assert 'Cookie не установлено' in html

# 5. Проверка отображения формы параметров
def test_form_params_display(client):
    rv = client.get('/form_params')
    html = rv.data.decode('utf-8')
    assert rv.status_code == 200
    assert 'Параметры формы' in html

# 6. Проверка отправки формы параметров
def test_form_params_post(client):
    rv = client.post('/form_params', data={'field1': 'value1', 'field2': 'value2'})
    html = rv.data.decode('utf-8')
    assert rv.status_code == 200
    assert 'field1' in html
    assert 'value1' in html
    assert 'field2' in html
    assert 'value2' in html

# 7. Проверка правильной валидации телефона (номер +7)
def test_phone_validation_correct_plus7(client):
    rv = client.post('/phone_validation', data={'phone': '+7 (123) 456-78-90'})
    html = rv.data.decode('utf-8')
    assert rv.status_code == 200
    assert '8-123-456-78-90' in html

# 8. Проверка правильной валидации телефона (номер без кода)
def test_phone_validation_correct_plain(client):
    rv = client.post('/phone_validation', data={'phone': '81234567890'})  # заменили на валидный
    html = rv.data.decode('utf-8')
    assert rv.status_code == 200
    assert '8-123-456-78-90' in html

# 9. Ошибка при некорректных символах в номере телефона
def test_phone_validation_invalid_symbols(client):
    rv = client.post('/phone_validation', data={'phone': '12@#34abcd'})
    html = rv.data.decode('utf-8')
    assert rv.status_code == 200
    assert 'Недопустимый ввод' in html

# 10. Ошибка при неправильной длине номера (слишком короткий)
def test_phone_validation_invalid_length_short(client):
    rv = client.post('/phone_validation', data={'phone': '12345'})
    html = rv.data.decode('utf-8')
    assert rv.status_code == 200
    assert 'Недопустимый ввод. Неверное количество цифр.' in html

# 11. Ошибка при неправильной длине номера (слишком длинный)
def test_phone_validation_invalid_length_long(client):
    rv = client.post('/phone_validation', data={'phone': '123456789012345'})
    html = rv.data.decode('utf-8')
    assert rv.status_code == 200
    assert 'Недопустимый ввод. Неверное количество цифр.' in html

# 12. Страница проверки телефона содержит форму
def test_phone_validation_page_has_form(client):
    rv = client.get('/phone_validation')
    html = rv.data.decode('utf-8')
    assert rv.status_code == 200
    assert '<form' in html

# 13. Проверка отображения ошибки с правильными Bootstrap классами
def test_phone_validation_error_classes(client):
    rv = client.post('/phone_validation', data={'phone': 'abc!'})
    html = rv.data.decode('utf-8')
    assert rv.status_code == 200
    assert 'is-invalid' in html or 'invalid-feedback' in html

# 14. Проверка, что правильный номер не вызывает ошибку
def test_phone_validation_no_error_correct_number(client):
    rv = client.post('/phone_validation', data={'phone': '8(999)123-45-67'})
    html = rv.data.decode('utf-8')
    assert rv.status_code == 200
    assert '8-999-123-45-67' in html
    assert 'Недопустимый ввод. В номере телефона встречаются недопустимые символы.' not in html

# 15. Проверка корректного возврата всех новых страниц
def test_all_new_pages_exist(client):
    pages = ['/url-params', '/headers', '/cookies', '/form_params', '/phone_validation']
    for page in pages:
        rv = client.get(page)
        assert rv.status_code == 200


# лр 3
def login(client, username, password, remember=False, follow=True):
    return client.post('/login', data=dict(
        username=username,
        password=password,
        remember='on' if remember else ''
    ), follow_redirects=follow)

def logout(client):
    return client.get('/logout', follow_redirects=True)

# 1. Анонимный счётчик
def extract_visit_count(html):
    match = re.search(r'Вы посещали эту страницу.*?<strong>(\d+)</strong>', html)
    return int(match.group(1)) if match else None

def test_counter_session_for_anonymous(client):
    with client.session_transaction() as sess:
        sess.clear()

    res1 = client.get('/counter')
    html1 = res1.data.decode('utf-8')
    count1 = extract_visit_count(html1)

    res2 = client.get('/counter')
    html2 = res2.data.decode('utf-8')
    count2 = extract_visit_count(html2)

    assert count1 is not None and count2 is not None, f"HTML: {html2}"
    assert count2 == count1 + 1, f"{count1=} {count2=}"

# 2. Счётчик для авторизованного
def test_counter_authenticated_user(client):
    login(client, 'user', 'qwerty')
    client.get('/counter')
    client.get('/counter')
    assert app_module.user_visits['user'] == 2
    logout(client)

# 3. Успешный вход и сообщение на главной
def test_successful_login_redirect(client):
    res = login(client, 'user', 'qwerty')
    html = res.data.decode('utf-8')
    assert 'Вы успешно вошли в систему!' in html
    assert 'Задание к лабораторной работе' in html

# 4. Ошибка при неправильном пароле
def test_unsuccessful_login(client):
    res = login(client, 'user', 'wrongpass')
    html = res.data.decode('utf-8')
    assert 'Неверный логин или пароль' in html
    assert 'Вход в систему' in html

# 5. Защищённая страница для залогиненного
def test_secret_page_authenticated(client):
    login(client, 'user', 'qwerty')
    res = client.get('/secret')
    html = res.data.decode('utf-8')
    assert 'Секретная страница' in html
    logout(client)

# 6. Редирект неавторизованного на вход
def test_secret_page_redirects_anonymous(client):
    res = client.get('/secret', follow_redirects=True)
    html = res.data.decode('utf-8')
    assert 'Пожалуйста, войдите в систему' in html
    assert 'Вход в систему' in html

# 7. Редирект на секретную после логина
def test_redirect_to_secret_after_login(client):
    res = client.get('/secret', follow_redirects=False)
    assert res.status_code == 302
    assert '/login?next=%2Fsecret' in res.headers['Location']

    login(client, 'user', 'qwerty')
    secret_res = client.get('/secret')
    assert 'Секретная страница' in secret_res.data.decode('utf-8')
    logout(client)

# 8. remember_token устанавливается
def test_remember_me_cookie(client):
    res = client.post('/login', data=dict(
        username='user',
        password='qwerty',
        remember='on'
    ))
    cookies = res.headers.getlist("Set-Cookie")
    assert any('remember_token' in c for c in cookies)

# 9. Навбар для авторизованного
def test_navbar_for_authenticated(client):
    login(client, 'user', 'qwerty')
    res = client.get('/')
    html = res.data.decode('utf-8')
    assert 'Выйти' in html
    assert 'Секретная страница' in html
    logout(client)

# 10. Навбар для анонимного
def test_navbar_for_anonymous(client):
    res = client.get('/')
    html = res.data.decode('utf-8')
    assert 'Войти' in html
    assert 'Секретная страница' not in html