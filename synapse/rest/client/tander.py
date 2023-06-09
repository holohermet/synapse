import logging
from typing import TYPE_CHECKING

from synapse.http.server import HttpServer
from synapse.http.servlet import RestServlet
from synapse.http.servlet import parse_json_object_from_request
from synapse.http.site import SynapseRequest

from ._base import client_patterns

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from synapse.server import HomeServer


class GetPermissionsRestServlet(RestServlet):
    PATTERNS = client_patterns("/getPermissions(?:/.*)?$", v1=True)

    def __init__(self, hs):
        super(GetPermissionsRestServlet, self).__init__()
        self.get_info = hs.get_permissions_list_handler()
        self.auth = hs.get_auth()

    async def on_GET(self, request: SynapseRequest):
        requester = await self.auth.get_user_by_req(request)
        info = await self.get_info.get_permissions(
            requester.user.to_string(),
            request.requestHeaders.getRawHeaders(b"x-forwarded-for")
        )
        return 200, info


class CreateNewsRestServlet(RestServlet):
    PATTERNS = client_patterns("/addNews$", v1=True)

    def __init__(self, hs: "HomeServer"):
        super(CreateNewsRestServlet, self).__init__()
        self.create = hs.get_news_creating_handler()
        self.auth = hs.get_auth()

    async def on_POST(self, request: SynapseRequest):
        requester = await self.auth.get_user_by_req(request)
        info = await self.create.create_news(
            requester,
            parse_json_object_from_request(request)
        )
        return 200, info


class GetNewsByUserRestServlet(RestServlet):
    PATTERNS = client_patterns("/getNewsByRoom/(?P<room_id>[^/]*)$", v1=True)

    def __init__(self, hs: "HomeServer"):
        super(GetNewsByUserRestServlet, self).__init__()
        self.get_info = hs.get_news_working_handler()
        self.auth = hs.get_auth()

    async def on_GET(self, request, room_id):
        await self.auth.get_user_by_req(request)
        return 200, await self.get_info.get_news_by_room_id(room_id)


class GetNewsByIdRestServlet(RestServlet):
    PATTERNS = client_patterns("/getNewsByNewsId/(?P<news_id>[^/]*)$", v1=True)

    def __init__(self, hs: "HomeServer"):
        super(GetNewsByIdRestServlet, self).__init__()
        self.get_info = hs.get_news_working_handler()
        self.auth = hs.get_auth()

    async def on_GET(self, request, news_id):
        await self.auth.get_user_by_req(request)
        return 200, await self.get_info.get_news_by_news_id(news_id)


class GetUnreadNewsByUserRestServlet(RestServlet):
    PATTERNS = client_patterns("/getNewsByRoom/unread/room/(?P<room_id>[^/]*)/user/(?P<user_id>[^/]*)$", v1=True)

    def __init__(self, hs: "HomeServer"):
        super(GetUnreadNewsByUserRestServlet, self).__init__()
        self.get_info = hs.get_news_working_handler()
        self.auth = hs.get_auth()

    async def on_GET(self, request, room_id, user_id):
        await self.auth.get_user_by_req(request)
        return 200, await self.get_info.get_unread_news_by_room_id(room_id, user_id)


class PollCreateRestServlet(RestServlet):
    PATTERNS = client_patterns("/createPoll$", v1=True)

    def __init__(self, hs: "HomeServer"):
        super(PollCreateRestServlet, self).__init__()
        self.handler = hs.get_poll_creating_handler()
        self.auth = hs.get_auth()

    async def on_POST(self, request: "SynapseRequest"):
        requester = await self.auth.get_user_by_req(request)
        return 200, await self.handler.create_poll(
            requester, parse_json_object_from_request(request)
        )


class ListPollsRestServlet(RestServlet):
    PATTERNS = client_patterns("/getPollsInfo/(?P<room_id>[^/]*)$", v1=True)

    def __init__(self, hs: "HomeServer"):
        super().__init__()
        self.handler = hs.get_poll_list_handler()
        self.auth = hs.get_auth()

    async def on_GET(self, request, room_id):
        requester = await self.auth.get_user_by_req(request)
        return 200, await self.handler.list_polls_by_room_id(requester, room_id)


def register_servlets(hs: "HomeServer", http_server: HttpServer) -> None:
    GetPermissionsRestServlet(hs).register(http_server)
    CreateNewsRestServlet(hs).register(http_server)
    GetNewsByUserRestServlet(hs).register(http_server)
    GetUnreadNewsByUserRestServlet(hs).register(http_server)
    PollCreateRestServlet(hs).register(http_server)
    ListPollsRestServlet(hs).register(http_server)



