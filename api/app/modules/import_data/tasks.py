import os
import subprocess

from app.core.celery_app import celery_app
from app.core.config import get_settings


@celery_app.task(name="import_file_task")
def import_file_task(file_path: str, schema: str, table_name: str):
    """
    Celery task to import a file into PostGIS using ogr2ogr.
    """
    settings = get_settings()
    db_url = settings.database_url
    # Prepare connection string for OGR
    # PG:"host=addr port=5432 user=x password=y dbname=z"
    # We parse the SQLAlchemy URL or construct it.
    # Since we are in the worker container, 'postgis' hostname works.

    # settings.DATABASE_URL is postgresql://user:pass@host:5432/db
    # We can rely on env vars or settings.
    # We need to extract credentials.

    # Simplified construction assuming standard format
    # user:password@host:port/dbname
    from urllib.parse import urlparse

    u = urlparse(str(db_url))

    pg_conn = f"PG:host={u.hostname} port={u.port} user={u.username} password={u.password} dbname={u.path.lstrip('/')}"

    # Ensure schema exists (worker should do this? or init script did it?)
    # Init script did it.

    # ogr2ogr command
    # ogr2ogr -f "PostgreSQL" PG:"..." source_file -lco SCHEMA=target_schema -lco GEOMETRY_NAME=geometry -nln target_table -overwrite

    cmd = [
        "ogr2ogr",
        "-f",
        "PostgreSQL",
        pg_conn,
        file_path,
        "-lco",
        f"SCHEMA={schema}",
        "-lco",
        "GEOMETRY_NAME=geometry",
        "-nln",
        table_name,
        "-overwrite",  # Or -append
        "-progress",
        "--config",
        "PG_USE_COPY",
        "YES",
    ]

    print(f"Running command: {' '.join(cmd)}")

    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        # Cleanup file after success
        if os.path.exists(file_path):
            os.remove(file_path)

        print(f"Successfully imported {file_path} into {schema}.{table_name}")
        return {"status": "success", "schema": schema, "table": table_name}

    except subprocess.CalledProcessError as e:
        print(f"ogr2ogr failed: {e.stderr}")
        raise e
