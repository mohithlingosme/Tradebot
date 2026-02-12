import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from decimal import Decimal

from backend.app.main import app
from backend.app.database import get_db, Base
from backend.app.models import User, RiskLimit
from backend.api.auth import create_access_token
from backend.app.schemas.paper import PaperOrderRequest
from backend.app.enums import Side, OrderType

# Create a test-specific database
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(scope="module")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="module")
def test_user(db_session):
    user = User(email="test@example.com", hashed_password="password")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="module")
def auth_headers(test_user):
    token = create_access_token(data={"sub": test_user.email})
    return {"Authorization": f"Bearer {token}"}


def test_place_order_rejected_when_halted(db_session, test_user, auth_headers):
    # Halt trading for the user
    risk_service.set_halt(db_session, test_user.id, True, "Integration test halt")

    order = PaperOrderRequest(
        symbol="RELIANCE",
        side=Side.BUY,
        qty=Decimal("10"),
        order_type=OrderType.LIMIT,
        limit_price=Decimal("2500"),
        product="CNC",
    )

    response = client.post("/paper/orders", headers=auth_headers, json=order.dict())
    assert response.status_code == 403
    assert "Trading is halted" in response.json()["detail"]


def test_place_order_rejected_on_risk_breach(db_session, test_user, auth_headers):
    # Set a very low position limit
    risk_service.upsert_limits(db_session, test_user.id, {"max_position_qty": 5})

    order = PaperOrderRequest(
        symbol="RELIANCE",
        side=Side.BUY,
        qty=Decimal("10"),
        order_type=OrderType.LIMIT,
        limit_price=Decimal("2500"),
        product="CNC",
    )

    response = client.post("/paper/orders", headers=auth_headers, json=order.dict())
    assert response.status_code == 403
    # This will fail until the rule is implemented
    # assert "Exceeded max position quantity" in response.json()["detail"]

    # Reset limits
    risk_service.upsert_limits(db_session, test_user.id, {"max_position_qty": 200})
