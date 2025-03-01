from fastapi import APIRouter, Depends

from app.models.users import UserRead
from app.services.users import get_current_user
from app.services.teams import create_team
from app.core.database import SessionDep
from app.models.teams import TeamBase, TeamRead


teamsRouter = APIRouter(prefix="/teams", tags=["Teams"])


@teamsRouter.post("", response_model=TeamRead)
def register(
    user: TeamBase,
    session: SessionDep,
    current_user: UserRead = Depends(get_current_user),
):
    return create_team(user, session, current_user)
