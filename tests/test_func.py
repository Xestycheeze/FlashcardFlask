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

def test_create_set(client):
    signup(client, 'a', 'a a', 'a')
    login(client, 'a', 'a')

    user_db = UserModel.query.filter_by(username='a')
    assert user_db is not None

    client.post('/create_set', data={'name': 'set_name_a'}, follow_redirects=True)
    res = client.get('/sets')
    assert b'set_name' in res.data

    # check db
    set_obj = SetModel.query.filter_by(name='set_name_a').first()
    assert set_obj is not None

def test_create_card(client):
    signup(client, 'b', 'b b', 'b')
    login(client, 'b', 'b')

    user_db = UserModel.query.filter_by(username='b')
    assert user_db is not None

    client.post('/create_set', data={'name': 'set_name_b'}, follow_redirects=False)
    res = client.get('/sets')
    assert b'set_name_b' in res.data
    
    user_set = SetModel.query.filter_by(name='set_name_b').first()
    set_id = user_set.id

    client.post('/create_cards', data={'front': 'b', 'back': 'b', 'set_id': set_id}, follow_redirects=True)
    res = client.get(f'/sets/set/{set_id}')
    assert b'<li><strong>Q:</strong> b | <strong>A:</strong> b</li>' in res.data

    # check db
    set_obj = SetModel.query.filter_by(name='set_name_b').first()
    assert set_obj is not None

    card_obj = CardModel.query.filter_by(front='b').first()
    assert card_obj is not None

def test_exclusive_cards_sets(client):
    # sign in first user
    signup(client, 'c', 'c c', 'c')
    login(client, 'c', 'c')

    user_db = UserModel.query.filter_by(username='c')
    assert user_db is not None

    client.post('/create_set', data={'name': 'set_name_c'}, follow_redirects=True)
    res = client.get('/sets')
    assert b'set_name_c' in res.data

    user_set = SetModel.query.filter_by(name='set_name_c').first()
    set_id = user_set.id

    client.post('/create_cards', data={'front': 'c', 'back': 'c', 'set_id': set_id}, follow_redirects=True)
    res = client.get(f'/sets/set/{set_id}')
    assert b'<li><strong>Q:</strong> c | <strong>A:</strong> c</li>' in res.data
    
    #logout first user 
    response = client.get('/logout', follow_redirects=False)
    assert response.status_code == 302

    # sign in second user
    signup(client, 'd', 'd d', 'd')
    login(client, 'd', 'd')

    user_db = UserModel.query.filter_by(username='d')
    assert user_db is not None

    client.post('/create_set', data={'name': 'set_name_d'}, follow_redirects=True)
    res = client.get('/sets')
    assert b'set_name_d' in res.data

    user_set = SetModel.query.filter_by(name='set_name_d').first()
    set_id = user_set.id

    client.post('/create_cards', data={'front': 'd', 'back': 'd', 'set_id': set_id}, follow_redirects=True)
    res = client.get(f'/sets/set/{set_id}')
    assert b'<li><strong>Q:</strong> c | <strong>A:</strong> c</li>' not in res.data
    assert b'<li><strong>Q:</strong> d | <strong>A:</strong> d</li>' in res.data

    # check db
    set_obj = SetModel.query.filter_by(name='set_name_c').first()
    assert set_obj is not None

    card_obj = CardModel.query.filter_by(front='c').first()
    assert card_obj is not None

    set_obj = SetModel.query.filter_by(name='set_name_d').first()
    assert set_obj is not None

    card_obj = CardModel.query.filter_by(front='d').first()
    assert card_obj is not None