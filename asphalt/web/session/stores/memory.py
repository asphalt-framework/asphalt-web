from datetime import datetime, timezone
from typing import Dict, Optional, Tuple
from uuid import UUID

from asyncio_extras.threads import call_in_executor

from asphalt.web.session import WebSession
from asphalt.web.session.stores.base import BaseSessionStore


class MemorySessionStore(BaseSessionStore):
    """Stores sessions in memory. Not recommended for production use."""

    __slots__ = 'sessions'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.sessions = {}  # type: Dict[UUID, Tuple[datetime, bytes]]

    async def load(self, session_id: UUID) -> Optional[WebSession]:
        expires, serialized_data = self.sessions.get(session_id, (None, None))
        if serialized_data:
            data = self.serializer.deserialize(serialized_data)
            return WebSession(session_id, expires, data)
        else:
            return None

    async def save(self, session: WebSession) -> None:
        serialized_data = await call_in_executor(self.serializer.serialize, session.data,
                                                 executor=self.executor)
        self._check_serialized_data_length(serialized_data)
        self.sessions[session.id] = session.expires, serialized_data

    async def purge_expired_sessions(self) -> None:
        now_timestamp = int(datetime.now(timezone.utc).timestamp())
        self.sessions = {sid: (expires, data) for sid, (expires, data) in self.sessions.items()
                         if expires > now_timestamp}
