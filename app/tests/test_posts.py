import pytest
from app import app
from app import db
from models import User, Role

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture(autouse=True)
def setup_db(app):
    with app.app_context():
        db.create_all()

        admin_role = Role.query.filter_by(name='Administrator').first()
        if not admin_role:
            admin_role = Role(name='Administrator', description='Суперпользователь')
            db.session.add(admin_role)
        user_role = Role.query.filter_by(name='User').first()
        if not user_role:
            user_role = Role(name='User', description='Обычный пользователь')
            db.session.add(user_role)
        db.session.commit()

        admin_user = User.query.filter_by(login='admin1234').first()
        if not admin_user:
            admin_user = User(
                login='admin1234',
                name='admin1234',
                surname='admin1234',
                patronymic='',
                role=admin_role
            )
            admin_user.set_password('Admin1234')
            db.session.add(admin_user)
            db.session.commit()
    yield


@pytest.fixture
def login(client):
    # Вспомогательный метод для входа под пользователем.
    def _login(username, password):
        return client.post(
            '/login',
            data={'username': username, 'password': password},
            follow_redirects=True
        )
    return _login


@pytest.fixture
def logout(client):
    # Вспомогательный метод для выхода из системы.
    def _logout():
        return client.get('/logout', follow_redirects=True)
    return _logout


# Тесты просмотра пользователя
def test_view_user(client):
    rv = client.get('/view_user/2')
    assert rv.status_code == 200
    html = rv.get_data(as_text=True)
    assert 'admin1234' in html 
    assert 'admin1234' in html           


# Тесты создания пользователя
def test_create_user_requires_login(client):
    # Анонимный GET /create_user → редирект на /login.
    rv = client.get('/create_user')
    assert rv.status_code in (301, 302)
    assert '/login' in rv.headers['Location']


def test_display_create_form(client, login):
    # Залогиненный admin видит форму создания (поле login и password).
    login('admin1234', 'Admin1234')
    rv = client.get('/create_user')
    assert rv.status_code == 200
    html = rv.get_data(as_text=True)
    assert '<form' in html and 'name="login"' in html and 'name="password"' in html


def test_create_user_success(client, login):
    # Успешное создание user1 → flash + появление в /dump.
    login('admin1234', 'Admin1234')
    rv = client.post(
        '/create_user',
        data={
            'login': 'user1',
            'password': 'Abcdef1!',
            'surname': 'Ivanov',
            'name': 'Ivan',
            'patronymic': 'Ivanovich',
            'role_id': '2'
        },
        follow_redirects=True
    )
    assert 'Пользователь успешно создан' in rv.get_data(as_text=True)

    dump = client.get('/dump').json
    assert any(u['login'] == 'user1' for u in dump['users'])
    
    dump_before = client.get('/dump').json
    user3 = next((u for u in dump_before['users'] if u['login'] == 'user1'), None)
    assert user3 is not None, "User3 не появился в дампе перед удалением"
    user3_id = user3['id']

    # удаляем его
    rv = client.post(f'/delete_user/{user3_id}', follow_redirects=True)
    html = rv.get_data(as_text=True)
    assert 'успешно удалён' in html


def test_create_user_validation_errors(client, login):
    """
    POST /create_user с коротким login, пустым password/name → 
    должны быть ошибки валидации в ответе.
    """
    login('admin1234', 'Admin1234')
    rv = client.post(
        '/create_user',
        data={
            'login': 'usr',
            'password': '',
            'surname': '',
            'name': '',
            'role_id': ''
        }
    )
    html = rv.get_data(as_text=True)
    assert 'Логин должен состоять из латинских букв и цифр' in html
    assert 'Поле не может быть пустым' in html


# Тесты редактирования пользователя
def test_edit_user_success(client, login):
    """
    ▶ Создать user2, изменить surname → flash + проверка через /dump.
    """
    login('admin1234', 'Admin1234')

    # Создаём user2
    client.post(
        '/create_user',
        data={
            'login': 'user2',
            'password': 'Abcdef1!',
            'surname': 'Petrov',
            'name': 'Petr',
            'patronymic': '',
            'role_id': '2'
        }
    )

    # Редактируем user2
    rv = client.post(
        '/edit_user/2',
        data={
            'surname': 'Petrovich',
            'name': 'Petr',
            'patronymic': '',
            'role_id': ''
        },
        follow_redirects=True
    )
    assert 'Пользователь успешно обновлён' in rv.get_data(as_text=True)

    dump = client.get('/dump').json
    assert any(u['ФИО'].startswith('Petrovich') for u in dump['users'])
    
    # находим ID только что созданного user2
    dump_before = client.get('/dump').json
    user3 = next((u for u in dump_before['users'] if u['login'] == 'user2'), None)
    assert user3 is not None, "User3 не появился в дампе перед удалением"
    user3_id = user3['id']

    # удаляем его
    rv = client.post(f'/delete_user/{user3_id}', follow_redirects=True)
    html = rv.get_data(as_text=True)
    assert 'успешно удалён' in html


# Тесты удаления пользователя
def test_delete_user_success(client, login):
    login('admin1234', 'Admin1234')

    # создаём user3
    client.post(
        '/create_user',
        data={
            'login': 'user3',
            'password': 'Abcdef1!',
            'surname': 'Delete',
            'name': 'Me',
            'patronymic': '',
            'role_id': '2'
        }
    )

    # находим ID только что созданного user3
    dump_before = client.get('/dump').json
    user3 = next((u for u in dump_before['users'] if u['login'] == 'user3'), None)
    assert user3 is not None, "User3 не появился в дампе перед удалением"
    user3_id = user3['id']

    # удаляем его
    rv = client.post(f'/delete_user/{user3_id}', follow_redirects=True)
    html = rv.get_data(as_text=True)
    assert 'успешно удалён' in html

    # проверяем, что user3 больше нет
    dump_after = client.get('/dump').json
    assert not any(u['login'] == 'user3' for u in dump_after['users']), "User3 всё ещё присутствует после удаления"


# Тесты смены пароля
def test_change_password_success(client, login, logout):
    login('admin1234', 'Admin1234')
    rv = client.post(
        '/change_password',
        data={
            'old_password': 'Admin1234',
            'new_password': 'Newpass1!',
            'confirm_password': 'Newpass1!'
        },
        follow_redirects=True
    )
    assert 'Пароль успешно изменён' in rv.get_data(as_text=True)

    logout()
    rv2 = client.post(
        '/login',
        data={'username': 'admin1234', 'password': 'Newpass1!'},
        follow_redirects=True
    )
    assert 'Успешный вход' in rv2.get_data(as_text=True)
    
    dump_before = client.get('/dump').json
    user3 = next((u for u in dump_before['users'] if u['login'] == 'admin1234'), None)
    assert user3 is not None, "admin1234 не появился в дампе перед удалением"
    user3_id = user3['id']

    # удаляем его
    rv = client.post(f'/delete_user/{user3_id}', follow_redirects=True)
    html = rv.get_data(as_text=True)
    assert 'успешно удалён' in html


def test_change_password_validation_errors(client, login):
    login('admin1234', 'Admin1234')

    # a) неверный старый пароль
    rv = client.post(
        '/change_password',
        data={
            'old_password': 'wrong',
            'new_password': 'Newpass1!',
            'confirm_password': 'Newpass1!'
        }
    )
    assert 'Неверный старый пароль' in rv.get_data(as_text=True)

    # b) новый пароль и подтверждение не совпадают
    rv2 = client.post(
        '/change_password',
        data={
            'old_password': 'Admin1234',
            'new_password': 'Newpass1!',
            'confirm_password': 'Mismatch1!'
        }
    )
    assert 'Пароли не совпадают' in rv2.get_data(as_text=True)
    