import pytest
import fakeredis
from fastapi.testclient import TestClient
from app.database.redis_client import set_redis_client, get_redis_client

@pytest.fixture(autouse=True)
def mock_redis():
    """Substitui o cliente Redis por um mock em memória do Fakeredis em todos os testes."""
    fake_client = fakeredis.FakeRedis(decode_responses=True)
    set_redis_client(fake_client)
    yield fake_client
    fake_client.flushall()

@pytest.fixture
def test_client():
    """Fornece um TestClient do FastAPI para realizar requisições de teste."""
    from app.main import app
    return TestClient(app)
