import pytest
from app import app
from db import db
from models import SetModel, UserModel

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

# NOTE: helper functions
def signup(client, username, fullname, password):
    return client.post('/signup', data={'username': username, 'fullname': fullname, 'password': password}, follow_redirects=True)

def login(client, username, password):
    return client.post('/login', data={'username': username, 'password': password}, follow_redirects=True)

def create_set_and_card(client, name, cards):
    client.post('/sets/create_set', data={'name': name}, follow_redirects=True)
    user_set = SetModel.query.filter_by(name=name).first()
    set_id = user_set.id
    for front, back in cards:
        client.post(f'/sets/{set_id}/create_cards', data={'front': front, 'back': back, 'set_id': set_id}, follow_redirects=True)
    return set_id

# NOTE: tests start here
def test_quiz(client):
    signup(client, 'a', 'a a', 'a')
    login(client, 'a', 'a')

    set_id_a = create_set_and_card(client, 'set_name_a', [('a1', 'a1'), ('a2', 'a2'), ('a3', 'a3')])
    set_id_b = create_set_and_card(client, 'set_name_b', [('b1', 'b1'), ('b2', 'b2'), ('b3', 'b3')])
    set_id_c = create_set_and_card(client, 'set_name_c', [('c1', 'c1'), ('c2', 'c2')])

    # check all sets
    client.post('/quiz/select_sets', data={'set_ids': [str(set_id_a), str(set_id_b), str(set_id_c)]}, follow_redirects=True)
    res = client.get(f'/quiz/start?set_ids={set_id_a},{set_id_b},{set_id_c}')
    assert b'a1' in res.data
    assert b'b1' in res.data
    assert b'c1' in res.data

    # check set a & c
    client.post('/quiz/select_sets', data={'set_ids': [str(set_id_a), str(set_id_c)]}, follow_redirects=True)
    res = client.get(f'/quiz/start?set_ids={set_id_a},{set_id_c}')
    assert b'a1' in res.data
    assert b'b1' not in res.data
    assert b'c1' in res.data

    # check set b
    client.post('/quiz/select_sets', data={'set_ids': [str(set_id_b)]}, follow_redirects=True)
    res = client.get(f'/quiz/start?set_ids={set_id_b}')
    assert b'a1' not in res.data
    assert b'b1' in res.data
    assert b'c1' not in res.data


def test_multiuser_quiz(client):
    signup(client, 'b', 'b b', 'b')
    login(client, 'b', 'b')

    set_id_a = create_set_and_card(client, 'set_name_a', [('a1', 'a1'), ('a2', 'a2'), ('a3', 'a3'), ('a4', 'a4')])
    set_id_b = create_set_and_card(client, 'set_name_b', [('b1', 'b1'), ('b2', 'b2'), ('b3', 'b3')])
    set_id_c = create_set_and_card(client, 'set_name_c', [('c1', 'c1'), ('c2', 'c2')])

    client.get('/logout', follow_redirects=False)

    signup(client, 'c', 'c c', 'c')
    login(client, 'c', 'c')

    set_id_x = create_set_and_card(client, 'set_name_x', [('x1', 'x1'), ('x2', 'x2'), ('x3', 'x3'), ('x4', 'y4')])
    set_id_y = create_set_and_card(client, 'set_name_y', [('y1', 'y1'), ('y2', 'y2'), ('y3', 'y3')])
    set_id_z = create_set_and_card(client, 'set_name_z', [('z1', 'z1'), ('z2', 'z2')])

    # check all sets
    client.post('/quiz/select_sets', data={'set_ids': [str(set_id_x), str(set_id_b), str(set_id_y)]}, follow_redirects=True)
    res = client.get(f'/quiz/start?set_ids={set_id_x},{set_id_b},{set_id_y}')
    assert b'x1' in res.data
    assert b'b1' not in res.data
    assert b'y1' in res.data
    assert b'c1' not in res.data

    # check using all of previous user's sets
    client.post('/quiz/select_sets', data={'set_ids': [str(set_id_a), str(set_id_b), str(set_id_c)]}, follow_redirects=True)
    res = client.get(f'/quiz/start?set_ids={set_id_a},{set_id_b},{set_id_c}')
    assert b'No cards found in the selected sets!' in res.data

    # check using set x, z, and previous user's set b
    client.post('/quiz/select_sets', data={'set_ids': [str(set_id_x), str(set_id_b), str(set_id_z)]}, follow_redirects=True)
    res = client.get(f'/quiz/start?set_ids={set_id_x},{set_id_b},{set_id_z}')
    assert b'x1' in res.data
    assert b'z1' in res.data
    assert b'b1' not in res.data
    assert b'y1' not in res.data
    assert b'c1' not in res.data