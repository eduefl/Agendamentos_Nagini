from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import pytest

from domain.task.task_entity import Task
from domain.user.user_entity import User
from infrastructure.api.database import Base


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
            "is_active": True,
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

# The scope parameter defines the lifespan of the fixture. 
# In this case, scope="session" means that the fixture will be created once per test session. 
# This is useful for expensive setup operations that you want to run only once, rather than before each test or module.
# Use if the tests get slow because of the database setup, otherwise you can use the default scope which is "function" (a new fixture instance for each test function).
# @pytest.fixture(scope="session")

@pytest.fixture()
def engine():
    """
    Fixture that creates an in-memory SQLite database engine for testing.

    This fixture sets up a SQLite database that resides in memory, which is useful for running tests
    without the need for a physical database file. It also creates the necessary tables defined in
    the SQLAlchemy Base metadata.

    Returns:
        engine: A SQLAlchemy engine connected to an in-memory SQLite database.
    """
    
    # Create an in-memory SQLite database engine for testing
    engine = create_engine(
        "sqlite://",  # Connection string for an in-memory SQLite database
        future=True,  # Use the future API of SQLAlchemy
        connect_args={"check_same_thread": False},  # Allow connections from different threads
        poolclass=StaticPool,  # Use a static pool for the database connections
    )
    
    # Create all tables defined in the Base metadata in the in-memory database
    Base.metadata.create_all(bind=engine)
    
    # Return the created engine for use in tests
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
        