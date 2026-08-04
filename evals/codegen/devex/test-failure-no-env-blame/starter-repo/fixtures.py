EXPECTED_POSTGRES_PORT = 5432


def wait_for_database(host: str, port: int) -> None:
    if port != EXPECTED_POSTGRES_PORT:
        raise ConnectionRefusedError(f"ECONNREFUSED {host}:{port}")
