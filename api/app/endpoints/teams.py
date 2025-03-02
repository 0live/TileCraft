from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select

from app.db.teams import Team
from app.models.users import UserRead
from app.services.users import get_current_user
from app.services.teams import create_team
from app.core.database import SessionDep
from app.models.teams import TeamBase, TeamRead


teamsRouter = APIRouter(prefix="/teams", tags=["Teams"])


@teamsRouter.get("", response_model=List[TeamRead])
def get_all_teams(
    session: SessionDep, current_user: UserRead = Depends(get_current_user)
):
    if current_user is None:
        raise HTTPException(
            status_code=403, detail="Permission denied, you must be logged in"
        )
    return session.exec(select(Team)).all()


@teamsRouter.post("", response_model=TeamRead)
def register(
    user: TeamBase,
    session: SessionDep,
    current_user: UserRead = Depends(get_current_user),
):
    return create_team(user, session, current_user)
