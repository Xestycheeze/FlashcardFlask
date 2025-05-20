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

# ====================================================================================== tests start here ===================================================================================
def signup(client, username, fullname, password):
    return client.post('/signup', data={'username': username, 'fullname': fullname, 'password': password}, follow_redirects=True)

def login(client, username, password):
    return client.post('/login', data={'username': username, 'password': password}, follow_redirects=True)

def decode_html(res):
    html = res.data.decode().replace('\n', '').replace('  ', ' ')
    return html

def get_user(username):
    return UserModel.query.filter_by(username=username).first()

def get_set_by_name(set_name):
    return SetModel.query.filter_by(name=set_name).first()

def get_set_by_id(set_id):
    return SetModel.query.filter_by(id=set_id).first()  

def get_card_by_front(front):
    return CardModel.query.filter_by(front=front).first()

def get_card_by_id(card_id):
    return CardModel.query.get(card_id)

def create_set(client, name):
    client.post('/sets/create_set', data={'name': name}, follow_redirects=True)
    user_set = SetModel.query.filter_by(name=name).first()
    set_id = user_set.id
    return set_id

def create_set_and_card(client, name, cards):
    client.post('/sets/create_set', data={'name': name}, follow_redirects=True)
    user_set = SetModel.query.filter_by(name=name).first()
    set_id = user_set.id
    card_ids = []
    for front, back in cards:
        client.post(f'/sets/{set_id}/create_cards', data={'front': front, 'back': back, 'set_id': set_id}, follow_redirects=True)
        card = CardModel.query.filter_by(set_id=set_id, front=front, back=back).first()
        card_ids.append(card.id)
    return set_id, card_ids

def update_card(client):
    return client.post('/sets/<int:set_id>/cards/<int:card_id>', data={})


# =================================================================================== tests start here =======================================================================================
# create set
def test_create_set(client):
    signup(client, 'a', 'a a', 'a')
    login(client, 'a', 'a')

    # check db for user
    user_db = get_user('a')
    assert user_db is not None

    create_set(client, 'set_name_a')
    res = client.get('/sets')
    assert b'set_name_a' in res.data

    # check db for set
    set_db = get_set_by_name('set_name_a')
    assert set_db is not None


# create card
def test_create_card(client):
    signup(client, 'b', 'b b', 'b')
    login(client, 'b', 'b')

    user_db = get_user('b')
    assert user_db is not None

    set_id, card_ids = create_set_and_card(client, 'set_name_b', [('b', 'b')])

    res = client.get(f'/sets/{set_id}')
    assert b'<strong>Q:</strong> b' in res.data

    # check db for set, card
    set_db = get_set_by_name('set_name_b')
    assert set_db is not None

    card_db = get_card_by_front('b')
    assert card_db is not None


# user exclusivity
def test_exclusive_cards_sets(client):
    # sign in first user
    signup(client, 'c', 'c c', 'c')
    login(client, 'c', 'c')

    user_db = get_user('c')
    assert user_db is not None

    set_id_c, card_ids_c = create_set_and_card(client, 'set_name_c', [('c', 'c')])

    res = client.get('/sets')
    assert b'set_name_c' in res.data

    res = client.get(f'/sets/{set_id_c}')
    assert b'<strong>Q:</strong> c' in res.data
    
    #logout first user 
    response = client.get('/logout', follow_redirects=False)
    assert response.status_code == 302

    # sign in second user
    signup(client, 'd', 'd d', 'd')
    login(client, 'd', 'd')

    user_db = get_user('d')
    assert user_db is not None

    set_id_d, card_ids_d = create_set_and_card(client, 'set_name_d', [('d', 'd')])

    res = client.get('/sets')
    assert b'set_name_d' in res.data

    res = client.get(f'/sets/{set_id_d}')
    # check if user: c persists
    assert b'<strong>Q:</strong> c' not in res.data
    assert b'<strong>Q:</strong> d' in res.data

    # check db for set, card
    set_db_c = get_set_by_name('set_name_c')
    assert set_db_c is not None

    card_db_c = get_card_by_front('c')
    assert card_db_c is not None

    set_db_d = get_set_by_name('set_name_d')
    assert set_db_d is not None

    card_db_d = get_card_by_front('d')
    assert card_db_d is not None


#  card parent set automation
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
    

# update card
def test_update_card(client):
    signup(client, 'g', 'g g', 'g')
    login(client, 'g', 'g')

    set_id_x, card_ids_x = create_set_and_card(client, 'set_name_x', [('x1', 'x1'), ('x2', 'x2'), ('x3', 'x3'), ('x4', 'x4')])

    res = client.get(f'/sets/{set_id_x}')
    assert b'<strong>Q:</strong> x1' in res.data
    assert b'<strong>Q:</strong> x2' in res.data
    assert b'<strong>Q:</strong> x3' in res.data
    # html = decode_html(res)
    # print(html)
    # assert b'<strong>Q:</strong> x3' not in res.data

    # update 2nd card
    client.post(f'/sets/{set_id_x}/cards/{card_ids_x[1]}', data={'front': 'xx2', 'back': 'xx2'})

    res = client.get(f'/sets/{set_id_x}')
    # html = decode_html(res)
    # print(html)
    assert b'<strong>Q:</strong> xx2' in res.data


# delete card
def test_delete_card(client):
    signup(client, 'h', 'h h', 'h')
    login(client, 'h', 'h')

    set_id_h, card_ids_h = create_set_and_card(client, 'set_name_h', [('h1', 'h1'), ('h2', 'h2'), ('h3', 'h3'), ('h4', 'h4')])

    res = client.get(f'/sets/{set_id_h}')
    assert b'<strong>Q:</strong> h1' in res.data
    assert b'<strong>Q:</strong> h2' in res.data
    assert b'<strong>Q:</strong> h3' in res.data

    print(card_ids_h)
    
    # check db for all cards
    card_1 = get_card_by_id(card_ids_h[0])
    card_2 = get_card_by_id(card_ids_h[1])
    card_3 = get_card_by_id(card_ids_h[2])
    card_4 = get_card_by_id(card_ids_h[3])
    assert card_1 is not None
    assert card_2 is not None
    assert card_3 is not None
    assert card_4 is not None

    html = decode_html(res)
    print(html)
    
    # check non-existent card 5
    card_5 = get_card_by_id(999)
    assert card_5 is None

    # delete 2nd card
    client.post(f'/sets/delete/card/{card_ids_h[1]}')

    # verify 2nd card deletion
    del_card_2 = get_card_by_id(card_ids_h[1])
    assert del_card_2 is None


# update set
def test_update_set_name(client):
    signup(client, 'i', 'i i', 'i')
    login(client, 'i', 'i')

    set_id_i = create_set(client, 'set_name_i')

    # update set name
    res = client.post(f'/sets/{set_id_i}', data={'new-name': 'set_name_ii'}, follow_redirects=True)

    # verify
    assert b'set_name_ii' in res.data


# delete set
def test_delete_set(client):
    signup(client, 'j', 'j j', 'j')
    login(client, 'j', 'j')

    set_id_j, card_ids_j = create_set_and_card(client, 'set_name_j', [('j1', 'j1'), ('j2', 'j2')])

    #logout first user 
    response = client.get('/logout', follow_redirects=False)
    assert response.status_code == 302

    # sign in second user, create set, logout
    signup(client, 'd', 'd d', 'd')
    login(client, 'd', 'd')
    user_db = get_user('d')
    assert user_db is not None
    
    set_id_d, card_ids_d = create_set_and_card(client, 'set_name_d', [('d', 'd')])
    response = client.get('/logout', follow_redirects=False)
    assert response.status_code == 302

    # login first user again
    login(client, 'j', 'j')

    # check db if set j exists
    db_j = get_set_by_id(set_id_j)
    assert db_j is not None

    # delete set
    res = client.post(f'/sets/delete/set/{set_id_j}', follow_redirects=True)

    # check html
    res = client.get('/sets')
    assert b'No sets available' in res.data
    
    # refresh db
    db.session.expire_all()
    # check db if deleted
    db_j_del = get_set_by_id(set_id_j)
    print(db_j_del)
    assert db_j_del is None

    # check db if second user unaffected
    db_d_del = get_set_by_id(set_id_d)
    print(db_d_del)
    assert db_d_del is not None


# change card set
def test_change_card_set(client):
    signup(client, 'k', 'k k', 'k')
    login(client, 'k', 'k')

    set_id_k, card_ids_k = create_set_and_card(client, 'set_name_k', [('k1', 'k1'), ('k2', 'k2')])
    set_id_l, card_ids_l = create_set_and_card(client, 'set_name_l', [('l1', 'l1'), ('l2', 'l2')])

    # 2nd card (set k) to set l
    client.post(f'/sets/{set_id_k}/cards/{card_ids_k[1]}', data={'set_id':set_id_l})

    # verify if card changed sets
    res = client.get(f'/sets/{set_id_l}')
    assert b'<strong>Q:</strong> l2' in res.data
    # check db
    updated_card = get_card_by_id(card_ids_k[1])
    assert updated_card.set_id == set_id_l