from typing import List

from fastapi import APIRouter, Depends, HTTPException

from app.modules.teams.schemas import TeamBase, TeamRead
from app.modules.teams.service import TeamServiceDep
from app.modules.users.schemas import UserRead
from app.modules.users.service import get_current_user

teamsRouter = APIRouter(prefix="/teams", tags=["Teams"])


@teamsRouter.get("", response_model=List[TeamRead])
async def get_all_teams(
    service: TeamServiceDep, current_user: UserRead = Depends(get_current_user)
):
    if current_user is None:
        raise HTTPException(
            status_code=403, detail="Permission denied, you must be logged in"
        )
    return await service.get_all_teams()


@teamsRouter.post("", response_model=TeamRead)
async def create(
    team: TeamBase,
    service: TeamServiceDep,
    current_user: UserRead = Depends(get_current_user),
):
    return await service.create_team(team, current_user)
