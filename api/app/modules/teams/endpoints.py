from typing import List

from fastapi import APIRouter, Depends

from app.core.security import get_current_user
from app.modules.teams.schemas import (
    TeamBase,
    TeamDetail,
    TeamSummary,
    TeamUpdate,
)
from app.modules.teams.service import TeamServiceDep
from app.modules.users.schemas import UserDetail

teamsRouter = APIRouter(prefix="/teams", tags=["Teams"])


@teamsRouter.get("", response_model=List[TeamSummary])
async def get_all_teams(
    service: TeamServiceDep, current_user: UserDetail = Depends(get_current_user)
):
    return await service.get_all_teams(current_user)


@teamsRouter.get("/{team_id}", response_model=TeamDetail)
async def get_team(
    team_id: int,
    service: TeamServiceDep,
    current_user: UserDetail = Depends(get_current_user),
):
    return await service.get_team_by_id(team_id, current_user)


@teamsRouter.patch("/{team_id}", response_model=TeamDetail)
async def update_team(
    team_id: int,
    team: TeamUpdate,
    service: TeamServiceDep,
    current_user: UserDetail = Depends(get_current_user),
):
    return await service.update_team(team_id, team, current_user)


@teamsRouter.post("", response_model=TeamDetail)
async def create(
    team: TeamBase,
    service: TeamServiceDep,
    current_user: UserDetail = Depends(get_current_user),
):
    return await service.create_team(team, current_user)


@teamsRouter.delete("/{team_id}")
async def delete_team(
    team_id: int,
    service: TeamServiceDep,
    current_user: UserDetail = Depends(get_current_user),
):
    return await service.delete_team(team_id, current_user)
