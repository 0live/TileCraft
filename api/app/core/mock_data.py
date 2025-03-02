from sqlalchemy import Engine
from sqlmodel import Session
from app.db.teams import Team
from app.db.users import User
from app.models.user_roles import UserRole
from app.services.auth.auth import pwd_context


def create_mock_data(engine: Engine):
    with Session(engine) as session:
        team1 = Team(name="Team 1")
        team2 = Team(name="Team 2")
        admin = User(
            email="admin@test.com",
            username="admin",
            hashed_password=pwd_context.hash("admin"),
            roles=[UserRole.USER, UserRole.ADMIN],
            teams=[team1, team2],
        )
        user = User(
            email="user@test.com",
            username="user",
            hashed_password=pwd_context.hash("user"),
            roles=[UserRole.USER],
            teams=[team1],
        )

        session.add(admin)
        session.add(user)
        session.commit()
        session.refresh(admin)
        session.refresh(user)
