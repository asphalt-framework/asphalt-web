from datetime import datetime, timezone
from typing import Union, Optional
from uuid import UUID

from sqlalchemy import DateTime

from asphalt.core import Context
from asyncio_extras.threads import call_in_executor
from sqlalchemy import Column, MetaData, Table, String, LargeBinary
from sqlalchemy.engine import Connectable, Engine
from typeguard import check_argument_types

from asphalt.web.session import WebSession
from asphalt.web.session.stores.base import BaseSessionStore


class SQLAlchemySessionStore(BaseSessionStore):
    __slots__ = ('engine', 'table')

    def __init__(self, *, engine: Union[Connectable, str], table_name: str = 'asphalt_sessions',
                 **kwargs):
        assert check_argument_types()
        super().__init__(**kwargs)
        self.engine = engine
        self.table = Table(
            table_name, MetaData(),
            Column('id', String(32), primary_key=True),
            Column('expires', DateTime, nullable=False, index=True),
            Column('data', LargeBinary(self.max_session_size), nullable=False)
        )

    async def start(self, ctx: Context) -> None:
        await super().start(ctx)
        if isinstance(self.engine, str):
            self.engine = await ctx.request_resource(Engine, self.engine)

        await call_in_executor(self.table.create, self.engine, executor=self.executor)

    async def load(self, session_id: UUID) -> Optional[WebSession]:
        query = self.table.select([self.table.c.expires, self.table.c.data]).\
            where(self.table.c.id == session_id.hex)
        expires_timestamp, serialized_data = await call_in_executor(
            self.engine.execute, query, executor=self.executor)
        if serialized_data:
            expires = datetime.fromtimestamp(expires_timestamp, timezone.utc)
            data = await call_in_executor(self.serializer.deserialize, serialized_data)
            return WebSession(session_id, expires, data)
        else:
            return None

    async def save(self, session: WebSession) -> None:
        serialized_data = await call_in_executor(self.serializer.serialize, session.data)
        self._check_serialized_data_length(serialized_data)

        query = self.table.insert().values(id=session.id.hex, expires=session.expires,
                                           data=serialized_data)
        query = self.table.update().where(self.table.c.id == session.id.hex).\
            values(expires=session.expires, data=serialized_data)
        await self.engine.execute(query)

    async def purge_expired_sessions(self):
        query = self.table.delete().where(self.table.c.expires <= datetime.utcnow())
        await self.engine.execute(query)
