from datetime import datetime, timezone
from typing import Union, Optional
from uuid import UUID

from asphalt.core import Context
from asyncio_extras.threads import call_in_executor
from motor.core import AgnosticClient
from motor.motor_asyncio import AsyncIOMotorClient
from typeguard import check_argument_types

from asphalt.web.session import WebSession
from asphalt.web.session.stores.base import BaseSessionStore


class MongoDBSessionStore(BaseSessionStore):
    """
    Stores sessions in a MongoDB database.

    :param client: a MongoDB client or a resource name
    :param database: name of the database to use
    :param collection: name of the collection to use
    """

    __slots__ = ('client', 'database', 'collection')

    def __init__(self, *, client: Union[AgnosticClient, str], database: str,
                 collection: str = 'asphalt_sessions', **kwargs):
        assert check_argument_types()
        super().__init__(**kwargs)
        self.client = client
        self.database = database
        self.collection = collection

    async def start(self, ctx: Context) -> None:
        await super().start(ctx)
        if isinstance(self.client, str):
            self.client = await ctx.request_resource(AsyncIOMotorClient, self.client)

        self.collection = self.client[self.database][self.collection]
        await self.collection.create_index('expires', expireAt=1)

    async def load(self, session_id: UUID) -> Optional[WebSession]:
        document = await self.collection.find_one(session_id.hex)
        if document:
            expires = document['expires'].replace(tzinfo=timezone.utc)
            data = await call_in_executor(self.serializer.deserialize, document['data'])
            return WebSession(session_id, expires, data)
        else:
            return None

    async def save(self, session: WebSession) -> None:
        serialized_data = await call_in_executor(self.serializer.serialize, session.data)
        self._check_serialized_data_length(serialized_data)
        await self.collection.save({
            '_id': session.id.hex,
            'expires': session.expires,
            'data': serialized_data
        })

    async def purge_expired_sessions(self):
        # Should not be necessary due to the TTL index on the "expires" field
        now = datetime.now(timezone.utc)
        await self.collection.remove({'expires': {'lte': now}})