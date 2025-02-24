# FastAPI

## Example with SQLAlchemy and pytest
```python
from contextlib import contextmanager
from random import Random
from typing import Annotated, Any, Callable, Dict, Iterator

import pytest
from fastapi import Depends, FastAPI
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker
from starlette.testclient import TestClient

from injection import DeclarativeContainer, Provide, inject, providers


@contextmanager
def db_session_resource(session_factory: Callable[..., Session]) -> Iterator[Session]:
    session = session_factory()
    try:
        yield session
    except Exception:
        session.rollback()
    finally:
        session.close()


class SomeDAO:
    def __init__(self, db_session: Session) -> None:
        self.db_session = db_session

    def get_some_data(self, num: int) -> int:
        stmt = text("SELECT :num").bindparams(num=num)
        data: int = self.db_session.execute(stmt).scalar_one()
        return data


class DIContainer(DeclarativeContainer):
    db_engine = providers.Singleton(
        create_engine,
        url="sqlite:///db.db",
        pool_size=20,
        max_overflow=0,
        pool_pre_ping=False,
    )

    session_factory = providers.Singleton(
        sessionmaker,
        db_engine.cast,
        autoflush=False,
        autocommit=False,
    )

    db_session = providers.Resource(
        db_session_resource,
        session_factory=session_factory.cast,
        function_scope=True,
    )

    some_dao = providers.Factory(SomeDAO, db_session=db_session.cast)


SomeDAODependency = Annotated[SomeDAO, Depends(Provide[DIContainer.some_dao])]

app = FastAPI()


@app.get("/values/{value}")
@inject
async def sqla_resource_handler_async(
    value: int,
    some_dao: SomeDAODependency,
) -> Dict[str, Any]:
    value = some_dao.get_some_data(num=value)
    return {"detail": value}


@pytest.fixture(scope="session")
def test_client() -> TestClient:
    client = TestClient(app)
    return client


def test_sqla_resource(test_client: TestClient) -> None:
    rnd = Random()
    random_int = rnd.randint(-(10**6), 10**6)

    response = test_client.get(f"/values/{random_int}")

    assert response.status_code == 200
    assert not DIContainer.db_session.initialized
    body = response.json()
    assert body["detail"] == random_int
    
```
