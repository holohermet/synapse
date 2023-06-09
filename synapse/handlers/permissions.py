import logging
from typing import TYPE_CHECKING

from synapse.types import Dict

if TYPE_CHECKING:
    from synapse.server import HomeServer

logger = logging.getLogger(__name__)


class PermissionsListHandler:
    def __init__(self, hs: "HomeServer"):
        self.store = hs.get_datastores().main

    async def get_permissions(
        self, user_id: str, forwarded_headers: list
    ) -> Dict:
        is_client_from_internet = len(forwarded_headers) > 1
        result_permissions = []
        permissions = await self.store.get_all_user_permissions(user_id)
        for permission in permissions:
            if permission.get("path") == "remote_forbidden":
                if is_client_from_internet:
                    result_permissions.append(permission)
            else:
                result_permissions.append(permission)
        return {"permissions": result_permissions}

    async def _add_permission_for_user(
        self, user_id: str, path: str, method: str
    ) -> tuple:
        await self.store.add_permission_for_user_none_room(
            path, method, user_id
        )
        return path, method, user_id
