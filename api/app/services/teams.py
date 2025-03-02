from fastapi import HTTPException
from sqlmodel import select
from app.models.user_roles import UserRole
from app.models.users import UserRead
from app.db.teams import Team
from app.core.database import SessionDep
from app.models.teams import TeamBase, TeamRead


def create_team(
    team: TeamBase, session: SessionDep, current_user: UserRead
) -> TeamRead:
    if all(
        role not in current_user.roles
        for role in [UserRole.ADMIN, UserRole.MANAGE_TEAMS]
    ):
        raise HTTPException(
            status_code=403, detail="You don't have permission to create teams"
        )
    if session.exec(select(Team).where(Team.name == team.name)).first():
        raise HTTPException(status_code=400, detail="This name already exists")
    new_team = Team(**team.model_dump())
    session.add(new_team)
    session.commit()
    session.refresh(new_team)
    return TeamRead(**new_team.model_dump())
