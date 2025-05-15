import pytest
from app import app
from db import db
from models import SetModel, CardModel, UserModel

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.secret_key = 'test_secret'

    with app.app_context():
        db.drop_all()
        db.create_all()

    with app.test_client() as client:
        yield client

def signup(client, username, fullname, password):
    return client.post('/signup', data={'username': username, 'fullname': fullname, 'password': password}, follow_redirects=True)

def login(client, username, password):
    return client.post('/login', data={'username': username, 'password': password}, follow_redirects=True)

def decode_html(res):
    html = res.data.decode().replace('\n', '').replace('  ', ' ')
    return html

def create_set(client, name):
    client.post('/sets/create_set', data={'name': name}, follow_redirects=True)
    user_set = SetModel.query.filter_by(name=name).first()
    set_id = user_set.id
    return set_id

def create_set_and_card(client, name, cards):
    client.post('/sets/create_set', data={'name': name}, follow_redirects=True)
    user_set = SetModel.query.filter_by(name=name).first()
    set_id = user_set.id
    for front, back in cards:
        client.post(f'/sets/{set_id}/create_cards', data={'front': front, 'back': back, 'set_id': set_id}, follow_redirects=True)
    return set_id

def test_create_set(client):
    signup(client, 'a', 'a a', 'a')
    login(client, 'a', 'a')

    # check db for user
    user_db = UserModel.query.filter_by(username='a')
    assert user_db is not None

    create_set(client, 'set_name_a')
    res = client.get('/sets')
    assert b'set_name_a' in res.data

    # check db for set
    set_db = SetModel.query.filter_by(name='set_name_a').first()
    assert set_db is not None

def test_create_card(client):
    signup(client, 'b', 'b b', 'b')
    login(client, 'b', 'b')

    user_db = UserModel.query.filter_by(username='b')
    assert user_db is not None

    set_id = create_set_and_card(client, 'set_name_b', [('b', 'b')])

    res = client.get(f'/sets/{set_id}')
    assert b'<li><strong>Q:</strong> b' in res.data

    # check db for set, card
    set_db = SetModel.query.filter_by(id=set_id).first()
    assert set_db is not None

    card_db = CardModel.query.filter_by(front='b').first()
    assert card_db is not None

def test_exclusive_cards_sets(client):
    # sign in first user
    signup(client, 'c', 'c c', 'c')
    login(client, 'c', 'c')

    user_db = UserModel.query.filter_by(username='c')
    assert user_db is not None

    set_id_c = create_set_and_card(client, 'set_name_c', [('c', 'c')])

    res = client.get('/sets')
    assert b'set_name_c' in res.data

    res = client.get(f'/sets/{set_id_c}')
    assert b'<li><strong>Q:</strong> c | <strong>A:</strong> c</li>' in res.data
    
    #logout first user 
    response = client.get('/logout', follow_redirects=False)
    assert response.status_code == 302

    # sign in second user
    signup(client, 'd', 'd d', 'd')
    login(client, 'd', 'd')

    user_db = UserModel.query.filter_by(username='d')
    assert user_db is not None

    set_id_d = create_set_and_card(client, 'set_name_d', [('d', 'd')])

    res = client.get('/sets')
    assert b'set_name_d' in res.data

    res = client.get(f'/sets/{set_id_d}')
    # check if user: c persists
    assert b'<li><strong>Q:</strong> c | <strong>A:</strong> c</li>' not in res.data
    assert b'<li><strong>Q:</strong> d | <strong>A:</strong> d</li>' in res.data

    # check db for set, card
    set_db = SetModel.query.filter_by(name='set_name_c').first()
    assert set_db is not None

    card_db = CardModel.query.filter_by(front='c').first()
    assert card_db is not None

    set_db = SetModel.query.filter_by(name='set_name_d').first()
    assert set_db is not None

    card_db = CardModel.query.filter_by(front='d').first()
    assert card_db is not None

def test_parent_automation(client):
    signup(client, 'e', 'e e', 'e')
    login(client, 'e', 'e')

    set_e = create_set(client, 'set_e')
    set_f = create_set(client, 'set_f')

    res = client.get(f'/sets/{set_e}/create_cards')
    html = decode_html(res)
    assert f'<option value="{set_e}" selected' in html
    assert f'<option value="{set_f}"' in html

    res = client.get(f'/sets/{set_f}/create_cards')
    html = decode_html(res)
    assert f'<option value="{set_e}"' in html
    assert f'<option value="{set_f}" selected' in html

    client.get('/logout', follow_redirects=False)

    signup(client, 'f', 'f f', 'f')
    login(client, 'f', 'f')

    set_x = create_set(client, 'set_x')
    set_y = create_set(client, 'set_y')

    res = client.get(f'/sets/{set_x}/create_cards')
    html = decode_html(res)
    assert f'<option value="{set_x}" selected' in html
    assert f'<option value="{set_y}"' in html
    assert f'<option value="{set_e}" selected' not in html
    assert f'<option value="{set_f}"' not in html

    res = client.get(f'/sets/{set_y}/create_cards')
    html = decode_html(res)
    assert f'<option value="{set_x}"' in html
    assert f'<option value="{set_y}" selected' in html
    assert f'<option value="{set_e}" selected' not in html
    assert f'<option value="{set_f}"' not in html
