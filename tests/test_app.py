import pytest
from app import app, db
from models import Riparazione


@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.session.remove()
        db.drop_all()


def _crea_riparazione(client, **kwargs):
    data = {
        'nome_cliente': 'Mario Rossi',
        'telefono_cliente': '3331234567',
        'tipo_dispositivo': 'Smartphone',
        'marca_modello': 'Samsung Galaxy S21',
        'descrizione_problema': 'Schermo rotto',
        'stato': 'in_attesa',
        'tecnico': '',
        'costo': '',
        'note': '',
    }
    data.update(kwargs)
    return client.post('/riparazioni/nuova', data=data, follow_redirects=True)


def test_dashboard_loads(client):
    response = client.get('/')
    assert response.status_code == 200
    assert 'Dashboard' in response.data.decode()


def test_crea_riparazione(client):
    response = _crea_riparazione(client)
    assert response.status_code == 200
    assert 'Mario Rossi' in response.data.decode()


def test_lista_riparazioni(client):
    _crea_riparazione(client)
    response = client.get('/riparazioni')
    assert response.status_code == 200
    assert 'Mario Rossi' in response.data.decode()


def test_lista_filtro_stato(client):
    _crea_riparazione(client, stato='completata')
    response = client.get('/riparazioni?stato=completata')
    assert response.status_code == 200
    assert 'Mario Rossi' in response.data.decode()

    response_no = client.get('/riparazioni?stato=in_lavorazione')
    assert 'Mario Rossi' not in response_no.data.decode()


def test_aggiorna_stato_riparazione(client):
    _crea_riparazione(client)
    with app.app_context():
        r = Riparazione.query.first()
        rid = r.id

    update_data = {
        'nome_cliente': 'Mario Rossi',
        'telefono_cliente': '3331234567',
        'tipo_dispositivo': 'Smartphone',
        'marca_modello': 'Samsung Galaxy S21',
        'descrizione_problema': 'Schermo rotto',
        'stato': 'in_lavorazione',
        'tecnico': 'Luigi',
        'costo': '50.00',
        'note': '',
    }
    response = client.post(f'/riparazioni/{rid}/modifica', data=update_data, follow_redirects=True)
    assert response.status_code == 200
    assert 'In Lavorazione' in response.data.decode()


def test_elimina_riparazione(client):
    _crea_riparazione(client)
    with app.app_context():
        r = Riparazione.query.first()
        rid = r.id

    response = client.post(f'/riparazioni/{rid}/elimina', follow_redirects=True)
    assert response.status_code == 200

    with app.app_context():
        assert db.session.get(Riparazione, rid) is None


def test_dettaglio_riparazione(client):
    _crea_riparazione(client)
    with app.app_context():
        r = Riparazione.query.first()
        rid = r.id

    response = client.get(f'/riparazioni/{rid}')
    assert response.status_code == 200
    assert 'Samsung Galaxy S21' in response.data.decode()
