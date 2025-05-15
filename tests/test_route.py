import pytest
from app import app, check_password_hash, generate_password_hash
from db import db

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

def test_failed_login(client):
    res = client.post('/login', data={'username': 'invalid', 'password': 'wrong'})
    assert res.status_code == 302

def test_sets_redirect(client):
    res = client.get('/sets')
    assert res.status_code == 302
    
def test_create_sets_redirect(client):
    res = client.get('/create_sets')
    assert res.status_code == 404

def test_create_cards_redirect(client):
    res = client.get('/sets/create_cards')
    assert res.status_code == 302

def test_homepage_accessible(client):
    res = client.get('/')
    assert b'This is our Home Page' in res.data

def test_setspage_accessible(client):
    signup(client, 'john', 'john python', '123')
    login(client, 'john', '123')
    res = client.get('/sets')
    assert b'Here are the Flashcard sets you have:' in res.data

def test_createsetpage_accessible(client):
    signup(client, 'john', 'john python', '123')
    login(client, 'john', '123')
    res = client.get('/sets/create_set')
    assert b'<button type="submit">Create Flashcard</button>' in res.data

def test_createcardspage_accessible(client):
    signup(client, 'john', 'john python', '123')
    login(client, 'john', '123')
    res = client.get('/sets/create_cards')
    # assert b'<button>Create Set</button>' in res.data
    # redirects to create sets
    assert res.status_code == 302

def test_loginpage_accessible(client):
    res = client.get('/login')
    assert b'<button type="submit">Login</button>' in res.data

def test_signuppage_accessible(client):
    res = client.get('/signup')
    assert b'<button type="submit">Sign Up</button>' in res.data

def test_successful_login(client):
    signup(client, 'john', 'john python', '123')
    res = login(client, 'john', '123')
    assert b'You are logged in as john' in res.data

def test_successful_signup(client):
    res = signup(client, 'jane', 'jane python', '987')
    assert b'You can now login' in res.data

def test_logout_clear_and_redirect(client):
    with client.session_transaction() as session:
        session['user_id'] = 'test_user'

    response = client.get('/logout', follow_redirects=False)
    assert response.status_code == 302

    with client.session_transaction() as session:
        assert 'user_id' not in session

def test_hash_password():
    hashed = generate_password_hash('123')
    assert check_password_hash(hashed, '123')