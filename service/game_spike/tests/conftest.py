import pytest


@pytest.fixture(autouse=True)
def procrastinate_jobs(in_memory_procrastinate):
    return in_memory_procrastinate
