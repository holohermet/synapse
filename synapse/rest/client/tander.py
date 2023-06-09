import logging
from typing import TYPE_CHECKING

from synapse.http.server import HttpServer
from synapse.http.servlet import RestServlet
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


def register_servlets(hs: "HomeServer", http_server: HttpServer) -> None:
    GetPermissionsRestServlet(hs).register(http_server)

