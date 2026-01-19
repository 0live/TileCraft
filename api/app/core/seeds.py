import asyncio
from typing import Union

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.security import hash_password
from app.modules.atlases.models import Atlas, AtlasTeamLink
from app.modules.teams.models import Team
from app.modules.users.models import User, UserRole


class Seeder:
    def __init__(self, db: Union[AsyncEngine, AsyncSession]):
        self.db = db

    async def run(self, commit: bool = True):
        """
        Seed the database with initial mock data for development.
        Includes users, teams, and atlases with their respective links.
        """
        if isinstance(self.db, AsyncEngine):
            async with AsyncSession(self.db) as session:
                await self._seed_data(session, commit)
        elif isinstance(self.db, AsyncSession):
            await self._seed_data(self.db, commit)
        else:
            raise ValueError("db must be an AsyncEngine or AsyncSession")

    async def _seed_data(self, session: AsyncSession, commit: bool):
        # --- Cleanup existing data (Optional but recommended for idempotency) ---
        # This prevents "UniqueViolation" errors if you run the script multiple times
        # Order matters because of Foreign Key constraints
        await session.exec(
            text(
                'TRUNCATE TABLE userteamlink, atlasteamlink, atlasmaplink, atlas, map, team, "user" RESTART IDENTITY CASCADE;'
            )
        )
        if commit:
            await session.commit()

        # --- 1. Create Teams ---
        team1 = Team(name="Atlas editor")
        team2 = Team(name="Atlas viewer")
        session.add(team1)
        session.add(team2)
        if commit:
            await session.commit()
            await session.refresh(team1)
            await session.refresh(team2)
        else:
            await session.flush()
            await session.refresh(team1)
            await session.refresh(team2)

        team1_id = team1.id
        team2_id = team2.id

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
            await session.commit()
        else:
            await session.flush()

        # --- 3. Create Atlases ---
        atlas1 = Atlas(name="Atlas 1", description="Only editor has access")
        atlas2 = Atlas(name="Atlas 2", description="Everyone has access")

        session.add(atlas1)
        session.add(atlas2)
        if commit:
            await session.commit()
            await session.refresh(atlas1)
            await session.refresh(atlas2)
        else:
            await session.flush()
            await session.refresh(atlas1)
            await session.refresh(atlas2)

        atlas1_id = atlas1.id
        atlas2_id = atlas2.id

        # --- 4. Create Links (Atlas <-> Team) ---
        links = [
            AtlasTeamLink(
                atlas_id=atlas1_id,
                team_id=team1_id,
                can_manage_atlas=True,
                can_create_maps=True,
                can_edit_maps=True,
            ),
            AtlasTeamLink(
                atlas_id=atlas2_id,
                team_id=team1_id,
                can_manage_atlas=True,
                can_create_maps=True,
                can_edit_maps=True,
            ),
            AtlasTeamLink(atlas_id=atlas2_id, team_id=team2_id),
        ]

        session.add_all(links)
        if commit:
            await session.commit()
        else:
            await session.flush()

        print("✅ Database successfully seeded with mock data.")


if __name__ == "__main__":

    async def main():
        try:
            from app.core.config import get_settings
            from app.core.database import get_engine, sessionmanager

            sessionmanager.init(str(get_settings().database_url))
            seeder = Seeder(get_engine())
            await seeder.run(commit=True)
            await sessionmanager.close()
        except Exception as e:
            print(f"❌ Error while seeding database: {e}")
            exit(1)

    asyncio.run(main())
