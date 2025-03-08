from sqlalchemy import Engine
from sqlmodel import Session
from app.db.atlases import Atlas, AtlasTeamLink
from app.db.teams import Team
from app.db.users import User
from app.models.user_roles import UserRole
from app.services.auth.auth import pwd_context


def create_mock_data(engine: Engine):
    with Session(engine) as session:
        team1 = Team(name="Atlas editor")
        team2 = Team(name="Atlas viewer")
        session.add(team1)
        session.add(team2)
        session.commit()
        session.refresh(team1)
        session.refresh(team2)

        admin = User(
            email="admin@test.com",
            username="admin",
            hashed_password=pwd_context.hash("admin"),
            roles=[UserRole.USER, UserRole.ADMIN],
        )
        editor = User(
            email="editor@test.com",
            username="editor",
            hashed_password=pwd_context.hash("editor"),
            roles=[UserRole.USER, UserRole.MANAGE_ATLASES_AND_MAPS],
            teams=[team1],
        )
        user = User(
            email="user@test.com",
            username="user",
            hashed_password=pwd_context.hash("user"),
            roles=[UserRole.USER],
            teams=[team2],
        )
        session.add(admin)
        session.add(editor)
        session.add(user)
        session.commit()
        session.refresh(admin)
        session.refresh(editor)
        session.refresh(user)

        atlas1 = Atlas(name="Atlas 1", description="Only editor has access")
        atlas2 = Atlas(name="Atlas 2", description="Everyone has access")

        session.add(atlas1)
        session.commit()
        session.refresh(atlas1)
        session.add(atlas2)
        session.commit()
        session.refresh(atlas2)

        assert atlas1.id is not None
        assert atlas2.id is not None
        assert team1.id is not None
        assert team2.id is not None
        session.add_all(
            [
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
        )

        # Valider les changements
        session.commit()
