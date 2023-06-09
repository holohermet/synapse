import copy
from unittest import mock

from twisted.test.proto_helpers import MemoryReactor

from synapse.server import HomeServer
from synapse.util import Clock

from tests import unittest


class PermissionsListHandlerTest(unittest.HomeserverTestCase):

    def make_homeserver(self, reactor: MemoryReactor, clock: Clock) -> HomeServer:
        return self.setup_test_homeserver(replication_layer=mock.Mock())

    def prepare(self, reactor: MemoryReactor, clock: Clock, hs: HomeServer) -> None:
        self.handler = hs.get_permissions_list_handler()
        self.local_user = "@vadim:" + hs.hostname

    def test_get_permissions_for_user_with_empty_permissions(self) -> None:
        self.get_success(
            self.handler.get_permissions(self.local_user, forwarded_headers=[])
        )

    def test_get_permissions_for_user_with_permissions(self) -> None:
        self.get_success(
            self.handler._add_permission_for_user(self.local_user, "/api/test/", "GET")
        )
        e = self.get_success(
            self.handler.get_permissions(self.local_user, forwarded_headers=[])
        )
        print(e)

