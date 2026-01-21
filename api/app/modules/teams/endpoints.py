from typing import List

from fastapi import APIRouter, Depends, HTTPException

from app.core.auth_dependencies import get_current_user
from app.modules.teams.schemas import TeamBase, TeamRead, TeamUpdate
from app.modules.teams.service import TeamServiceDep
from app.modules.users.models import UserRole
from app.modules.users.schemas import UserRead

teamsRouter = APIRouter(prefix="/teams", tags=["Teams"])


@teamsRouter.get("", response_model=List[TeamRead])
async def get_all_teams(
    service: TeamServiceDep, current_user: UserRead = Depends(get_current_user)
):
    return await service.get_all_teams()


@teamsRouter.get("/{team_id}", response_model=TeamRead)
async def get_team(
    team_id: int,
    service: TeamServiceDep,
    current_user: UserRead = Depends(get_current_user),
):
    return await service.get_team_by_id(team_id)


@teamsRouter.patch("/{team_id}", response_model=TeamRead)
async def update_team(
    team_id: int,
    team: TeamUpdate,
    service: TeamServiceDep,
    current_user: UserRead = Depends(get_current_user),
):
    if all(
        role not in current_user.roles
        for role in [UserRole.ADMIN, UserRole.MANAGE_TEAMS]
    ):
        raise HTTPException(
            status_code=403, detail="You don't have permission to update teams"
        )
    return await service.update_team(team_id, team, current_user)


@teamsRouter.post("", response_model=TeamRead)
async def create(
    team: TeamBase,
    service: TeamServiceDep,
    current_user: UserRead = Depends(get_current_user),
):
    return await service.create_team(team, current_user)


@teamsRouter.delete("/{team_id}")
async def delete_team(
    team_id: int,
    service: TeamServiceDep,
    current_user: UserRead = Depends(get_current_user),
):
    return await service.delete_team(team_id)
