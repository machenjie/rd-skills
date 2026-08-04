from db_config import DATABASE_HOST, DATABASE_PORT
from fixtures import wait_for_database


def run_integration_setup() -> None:
    wait_for_database(DATABASE_HOST, DATABASE_PORT)
