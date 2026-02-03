from typing import Optional

from sqlalchemy import select

from app.core.repository import BaseRepository
from app.modules.auth.models import RefreshToken


class AuthRepository(BaseRepository):
    """
    Repository for Auth module, handling Refresh Tokens.
    """

    async def create_refresh_token(self, token: RefreshToken) -> RefreshToken:
        self.session.add(token)
        await self.session.flush()
        await self.session.refresh(token)
        return token

    async def get_refresh_token_by_hash(
        self, token_hash: str
    ) -> Optional[RefreshToken]:
        stmt = select(RefreshToken).where(
            RefreshToken.token_hash == token_hash, ~RefreshToken.revoked
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def revoke_refresh_token(self, token_id: int) -> None:
        stmt = select(RefreshToken).where(RefreshToken.id == token_id)
        result = await self.session.execute(stmt)
        token = result.scalars().first()
        if token:
            token.revoked = True
            await self.session.flush()
