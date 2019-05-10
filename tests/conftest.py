import os
import signal as stdlib_signal
from contextlib import closing

import psycopg2
import pytest
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

from cabbage import jobs, tasks, testing


def _execute(cursor, query, *identifiers):
    cursor.execute(
        sql.SQL(query).format(
            *(sql.Identifier(identifier) for identifier in identifiers)
        )
    )


@pytest.fixture(scope="session")
def setup_db():

    with closing(psycopg2.connect("", dbname="postgres")) as connection:
        connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        with connection.cursor() as cursor:
            _execute(cursor, "DROP DATABASE IF EXISTS {}", "cabbage_test_template")
            _execute(cursor, "CREATE DATABASE {}", "cabbage_test_template")

    with closing(psycopg2.connect("", dbname="cabbage_test_template")) as connection:
        with connection.cursor() as cursor:
            with open("init.sql") as migrations:
                cursor.execute(migrations.read())
        connection.commit()
        connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        yield connection

    with closing(psycopg2.connect("", dbname="postgres")) as connection:
        connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        with connection.cursor() as cursor:
            _execute(cursor, "DROP DATABASE IF EXISTS {}", "cabbage_test_template")


@pytest.fixture
def connection(setup_db):
    with setup_db.cursor() as cursor:
        _execute(cursor, "DROP DATABASE IF EXISTS {}", "cabbage_test")
        _execute(
            cursor,
            "CREATE DATABASE {} TEMPLATE {}",
            "cabbage_test",
            "cabbage_test_template",
        )

    with closing(psycopg2.connect("", dbname="cabbage_test")) as connection:
        yield connection

    with setup_db.cursor() as cursor:
        _execute(cursor, "DROP DATABASE IF EXISTS {}", "cabbage_test")


@pytest.fixture
def kill_own_pid():
    def f(signal=stdlib_signal.SIGTERM):
        os.kill(os.getpid(), signal)

    return f


@pytest.fixture
def job_store():
    return testing.InMemoryJobStore()


@pytest.fixture
def task_manager(job_store):
    return tasks.TaskManager(job_store=job_store)


@pytest.fixture
def job_factory(job_store):
    defaults = {
        "id": 42,
        "task_name": "bla",
        "task_kwargs": {},
        "lock": None,
        "queue": "queue",
        "job_store": job_store,
    }

    def factory(**kwargs):
        final_kwargs = defaults.copy()
        final_kwargs.update(kwargs)
        return jobs.Job(**final_kwargs)

    return factory
