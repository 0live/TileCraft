import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool
from sqlmodel import SQLModel

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.modules.users.models import User  # noqa
from app.modules.teams.models import Team, UserTeamLink  # noqa
from app.modules.atlases.models import Atlas, AtlasTeamLink  # noqa

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

postgres_user = os.getenv("POSTGRES_USER", "postgres")
postgres_password = os.getenv("POSTGRES_PASSWORD", "postgres")
postgres_db = os.getenv("POSTGRES_DB", "postgres")
default_host = "postgis" if os.path.exists("/.dockerenv") else "localhost"
host = os.getenv("POSTGRES_HOST", default_host)

db_url = f"postgresql+psycopg://{postgres_user}:{postgres_password}@{host}:5432/{postgres_db}"
config.set_main_option("sqlalchemy.url", db_url)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}
target_metadata = SQLModel.metadata
target_metadata.naming_convention = naming_convention
# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def include_object(object, name, type_, reflected, compare_to):
    """
    Determine which database objects should be included in the autogeneration process.
    We exclude PostGIS, Tiger Geocoder, and Topology internal tables.
    """
    # List of prefixes to ignore
    ignored_prefixes = ["tiger", "topology", "spatial_ref_sys"]

    # Specific table names to ignore
    ignored_tables = [
        "geometry_columns",
        "geography_columns",
        "spatial_ref_sys",
        "raster_columns",
        "raster_overviews",
        "layer",
        "topology",
    ]

    if type_ == "table":
        # Ignore if name is in the list or starts with a reserved prefix
        if name in ignored_tables or any(name.startswith(p) for p in ignored_prefixes):
            return False

    return True


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
