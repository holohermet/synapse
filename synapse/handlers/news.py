import logging
from synapse.api.errors import Codes, SynapseError
from synapse.types import NewsID
from synapse.util import stringutils

logger = logging.getLogger(__name__)


class NewsCreatingHandler:

    def __init__(self, hs):
        self.hs = hs
        self.store = hs.get_datastores().main
        self.auth = hs.get_auth()
        self.event_creation_handler = hs.get_event_creation_handler()

    async def create_news(self, requester, config) -> dict:
        user_id = requester.user.to_string()
        room_id = config.get("room_id")
        content = config.get("news_content")

        if not "room_id" in config:
            raise SynapseError(
                400,
                "Request body should contain 'room_id' param",
                "NOT_CONTAIN_ROOM_ID"
            )

        is_room_exist = await self.store.get_association_from_room_ids(
            config["room_id"]
        )
        if not is_room_exist:
            raise SynapseError(
                400,
                "This room_id does not exist",
                Codes.ROOM_IN_USE
            )

        news_id = await self._generate_news_id(
            room_id=room_id,
            news_content=content
        )
        await self.event_creation_handler.create_and_send_nonmember_event(
            requester, {
                "type": 'm.room.news',
                "state_key": '',
                "room_id": room_id,
                "sender": user_id,
                "content": {
                    "news_id": news_id
                },
            }, ratelimit=False,
        )
        return {"news_id": news_id}

    async def _generate_news_id(self, room_id, news_content):
        random_string = stringutils.random_string(18)
        gen_news_id = NewsID(random_string, room_id).to_string()
        if isinstance(gen_news_id, bytes):
            gen_news_id = gen_news_id.decode("utf-8")
        await self.store.store_news(
            news_id=gen_news_id,
            news_content=news_content,
            room_id=room_id
        )
        return gen_news_id


class NewsModificationHandler:

    def __init__(self, hs):
        self.hs = hs
        self.store = hs.get_datastores().main

    async def get_news_by_room_id(self, room_id):
        news = await self.store.get_news_by_room_id(room_id)
        return {"news_info": [elem for elem in news]}

    async def get_unread_news_by_room_id(self, room_id, user_id):
        return {"news_info": await self.store.get_unread_news(room_id, user_id)}

    async def get_news_by_news_id(self, news_id):
        return await self.store.get_news_by_news_id(news_id)

    async def set_news_read_marker(self, requester, config):
        user_id = requester.user.to_string()
        news_id = config.get("news_id")
        room_id = config.get("room_id")

        if not all([news_id, room_id]):
            raise SynapseError(
                400,
                "Request body should contain 'news_id' param",
                "NOT_CONTAIN_NEWS_ID"
            )
        is_news_exist = await self.store.get_association_from_news_ids(news_id)
        is_room_exist = await self.store.get_association_from_room_ids(room_id)
        if not all([is_news_exist, is_room_exist]):
            raise SynapseError(
                400,
                "Fetched not existing news",
                "NOT_CONTAIN_NEWS_ID"
            )

        await self.store.set_read_marker(news_id=news_id,
                                         user_id=user_id,
                                         room_id=room_id)

        return {"news_id": news_id, "seen": True}
