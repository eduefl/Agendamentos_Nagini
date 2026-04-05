from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from domain.task.task_entity import Task
from domain.user.user_entity import User
from domain.service.service_entity import Service
from domain.service.provider_service_entity import ProviderService

from infrastructure.api.database import Base, get_session
from infrastructure.api.main import app
from infrastructure.user.sqlalchemy.user_model import RoleModel


@pytest.fixture
def make_user():
    def _make_user(**overrides):
        data = {
            "id": uuid4(),
            "name": "John Doe",
            "email": f"john.doe+{uuid4().hex}@example.com",
            # aqui é só um placeholder para testes de entidade/unidade
            # (em testes de use case AddUser, o hash deve vir do hasher)
            "hashed_password": "hashed-password",
            "is_active": False,
            "activation_code": None,
            "activation_code_expires_at": None,            # novo: por padrão vazio para não forçar regra do repo em testes de entidade
            # (em testes do repositório / usecase AddUser, passe roles explicitamente)
            "roles": {"cliente"},
        }
        data.update(overrides)
        return User(**data)

    return _make_user


@pytest.fixture
def make_task():
    def _make_task(**overrides):
        data = {
            "id": uuid4(),
            "user_id": uuid4(),
            "title": "Task 1",
            "description": "Description for Task",
            "completed": False,
        }
        data.update(overrides)
        return Task(**data)

    return _make_task


@pytest.fixture
def make_service():
    def _make_service(**overrides):
        data = {
            "id": uuid4(),
            "name": "Service 1",
            "description": "Description for Service",
        }
        data.update(overrides)
        return Service(**data)

    return _make_service


@pytest.fixture
def make_provider_service():
    def _make_provider_service(**overrides):
        data = {
            "id": uuid4(),
            "provider_id": uuid4(),
            "service_id": uuid4(),
            "price": Decimal("100.00"),
            "active": True,
            "created_at": None,  # Deixe como None para não forçar regra do repo em testes de entidade            
        }
        data.update(overrides)
        return ProviderService(**data)

    return _make_provider_service

# The scope parameter defines the lifespan of the fixture. 
# In this case, scope="session" means that the fixture will be created once per test session. 
# This is useful for expensive setup operations that you want to run only once, rather than before each test or module.
# Use if the tests get slow because of the database setup, otherwise you can use the default scope which is "function" (a new fixture instance for each test function).
# @pytest.fixture(scope="session")


@pytest.fixture()
def engine():
    engine = create_engine(
        "sqlite://",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture
def tst_db_session(engine):
    """
    Fixture that provides a test database session.

    This fixture creates a new database session for testing purposes. 
    It uses the provided SQLAlchemy engine to bind the session. 
    The session is automatically closed after the test completes.

    Args:
        engine: The SQLAlchemy engine used to connect to the database.

    Yields:
        session: A new SQLAlchemy session instance.
    """
    # Create a session factory bound to the provided engine
    # The autoflush=False argument disables automatic flushing of changes to the database before queries, meaning you must manually flush or commit changes to persist them.
    # The autocommit=False argument ensures that transactions are not automatically committed after each statement, allowing you to manage transactions manually.
    # The future=True argument enables the use of the new SQLAlchemy 2.0 style API, which includes changes to how sessions and queries are handled.
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    
    # Create a new session instance
    session = TestingSessionLocal()
    
    try:
        # Yield the session to the test function
        yield session
    finally:
        # Roll back any uncommitted changes to ensure a clean database state for tests
        # The code session.rollback() 
        # is a method call in SQLAlchemy that undoes any changes made to the current database transaction since the last commit
        # This is especially useful in testing scenarios,
        # where you want to ensure that each test starts with a clean database state. 
        # By rolling back the session, you prevent unwanted side effects from persisting between tests.
        session.rollback()
        # Ensure the session is closed after the test
        session.close()


@pytest.fixture(autouse=True)
def seed_roles(tst_db_session):
    """
    Garante que as roles usadas no sistema existam no banco.
    Útil para testes do userRepository.add_user (que busca role por nome).
    """
    existing = {
        r[0]
        for r in tst_db_session.query(RoleModel.name).all()
    }

    for name in ("cliente", "prestador"):
        if name not in existing:
            tst_db_session.add(RoleModel(name=name))

    tst_db_session.commit()
    return None

@pytest.fixture
def client(tst_db_session):
    def override_get_session():
        yield tst_db_session

    app.dependency_overrides[get_session] = override_get_session

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def concurrent_session_factory(tmp_path):
    """
    Cria um banco SQLite em arquivo para testes concorrentes com múltiplas sessões/threads.
    Também garante foreign_keys=ON e semeia as roles necessárias.
    """
    db_path = tmp_path / "concurrency_test.db"

    engine = create_engine(
        f"sqlite:///{db_path}",
        future=True,
        connect_args={"check_same_thread": False},
    )

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    SessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
        future=True,
    )

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    seed_session = SessionLocal()
    try:
        existing = {r[0] for r in seed_session.query(RoleModel.name).all()}
        for name in ("cliente", "prestador"):
            if name not in existing:
                seed_session.add(RoleModel(name=name))
        seed_session.commit()
    finally:
        seed_session.close()

    try:
        yield SessionLocal
    finally:
        Base.metadata.drop_all(bind=engine)
        engine.dispose()
