from typing import Union

from sqlalchemy import Engine, text
from sqlmodel import Session

from app.db.atlases import Atlas, AtlasTeamLink
from app.db.teams import Team
from app.db.users import User
from app.models.user_roles import UserRole
from app.services.auth.auth import hash_password


def run_seed(db: Union[Engine, Session], commit: bool = True):
    """
    Seed the database with initial mock data for development.
    Includes users, teams, and atlases with their respective links.
    """
    if isinstance(db, Engine):
        with Session(db) as session:
            _seed_data(session, commit)
    elif isinstance(db, Session):
        _seed_data(db, commit)
    else:
        raise ValueError("db must be an Engine or Session")


def _seed_data(session: Session, commit: bool):
    # --- Cleanup existing data (Optional but recommended for idempotency) ---
    # This prevents "UniqueViolation" errors if you run the script multiple times
    # Order matters because of Foreign Key constraints
    session.execute(
        text(
            'TRUNCATE TABLE userteamlink, atlasteamlink, atlasmaplink, atlas, map, team, "user" RESTART IDENTITY CASCADE;'
        )
    )
    if commit:
        session.commit()

    # --- 1. Create Teams ---
    team1 = Team(name="Atlas editor")
    team2 = Team(name="Atlas viewer")
    session.add(team1)
    session.add(team2)
    if commit:
        session.commit()
        session.refresh(team1)
        session.refresh(team2)
    else:
        session.flush()
        session.refresh(team1)
        session.refresh(team2)

    # --- 2. Create Users ---
    admin = User(
        email="admin@test.com",
        username="admin",
        hashed_password=hash_password("admin"),
        roles=[UserRole.USER, UserRole.ADMIN],
    )
    editor = User(
        email="editor@test.com",
        username="editor",
        hashed_password=hash_password("editor"),
        roles=[UserRole.USER, UserRole.MANAGE_ATLASES_AND_MAPS],
        teams=[team1],
    )
    user = User(
        email="user@test.com",
        username="user",
        hashed_password=hash_password("user"),
        roles=[UserRole.USER],
        teams=[team2],
    )

    session.add_all([admin, editor, user])
    if commit:
        session.commit()
    else:
        session.flush()

    # --- 3. Create Atlases ---
    atlas1 = Atlas(name="Atlas 1", description="Only editor has access")
    atlas2 = Atlas(name="Atlas 2", description="Everyone has access")

    session.add(atlas1)
    session.add(atlas2)
    if commit:
        session.commit()
        session.refresh(atlas1)
        session.refresh(atlas2)
    else:
        session.flush()
        session.refresh(atlas1)
        session.refresh(atlas2)

    # --- 4. Create Links (Atlas <-> Team) ---
    links = [
        AtlasTeamLink(
            atlas_id=atlas1.id,
            team_id=team1.id,
            can_manage_atlas=True,
            can_create_maps=True,
            can_edit_maps=True,
        ),
        AtlasTeamLink(
            atlas_id=atlas2.id,
            team_id=team1.id,
            can_manage_atlas=True,
            can_create_maps=True,
            can_edit_maps=True,
        ),
        AtlasTeamLink(atlas_id=atlas2.id, team_id=team2.id),
    ]

    session.add_all(links)
    if commit:
        session.commit()
    else:
        session.flush()

    print("✅ Database successfully seeded with mock data.")


if __name__ == "__main__":
    # This block is executed from the Makefile
    try:
        from app.core.database import get_engine

        run_seed(get_engine(), commit=True)
    except Exception as e:
        print(f"❌ Error while seeding database: {e}")
        exit(1)
