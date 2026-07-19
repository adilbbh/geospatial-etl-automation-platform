import os

import psycopg2
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    """Create a PostgreSQL/PostGIS database connection."""

    required_variables = [
        "DB_HOST",
        "DB_PORT",
        "DB_NAME",
        "DB_USER",
        "DB_PASSWORD",
    ]

    missing_variables = [
        variable for variable in required_variables if not os.getenv(variable)
    ]

    if missing_variables:
        raise RuntimeError(
            "Missing database environment variables: " + ", ".join(missing_variables)
        )

    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", "5433")),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )


def check_database_health() -> dict[str, str]:
    """Check the database connection and PostGIS availability."""

    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            SELECT
                current_database(),
                PostGIS_Version();
            """)

        result = cursor.fetchone()

        if result is None:
            raise RuntimeError("The database health query returned no result.")

        database_name, postgis_version = result

        return {
            "status": "healthy",
            "database": database_name,
            "postgis_version": postgis_version,
        }

    finally:
        cursor.close()
        connection.close()
