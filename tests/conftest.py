import os
import sys
import tempfile
import pytest

os.environ.setdefault('SECRET_KEY', 'test-secret-key')

db_fd, db_path = tempfile.mkstemp(suffix='.db')
os.environ['DATABASE_PATH'] = db_path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from setup_db import criar_tabelas

criar_tabelas()


@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    app.config['DATABASE_PATH'] = db_path
    yield app
    app.config['DATABASE_PATH'] = ''


@pytest.fixture
def client(app):
    return app.test_client()
