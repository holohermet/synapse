from unittest import mock

from twisted.test.proto_helpers import MemoryReactor

import synapse

from synapse.server import HomeServer
from synapse.util import Clock

from synapse.rest.client import room
from synapse.rest.client import login
from synapse.rest.client import register


from tests import unittest


class CreateChannelFromRoomHandlerTest(unittest.HomeserverTestCase):
    servlets = [
        synapse.rest.admin.register_servlets_for_client_rest_resource,
        room.register_servlets,
        login.register_servlets,
        register.register_servlets,
    ]

    def make_homeserver(self, reactor: MemoryReactor, clock: Clock) -> HomeServer:
        return self.setup_test_homeserver(replication_layer=mock.Mock())

    def prepare(
        self, reactor: MemoryReactor, clock: Clock, hs: HomeServer
    ) -> None:
        self.store = hs.get_datastores().main
        self.user_id = self.register_user("user", "pass")
        self.token = self.login("user", "pass")

    def test_create_channel_room(self) -> None:
        room_id = self.helper.create_room_as(
            self.user_id, tok=self.token,
            extra_content={"is_channel": True}
        )
        room_data = self.get_success(self.store.get_room_with_channel_flag(room_id))
        self.assertTrue(room_data["is_channel"])

        is_channel_state = self.helper.get_state(
            room_id,
            "m.room.is_channel",
            tok=self.token,
            expect_code=200
        )
        self.assertTrue(is_channel_state)

    def test_create_regular_room(self) -> None:
        room_id = self.helper.create_room_as(self.user_id, tok=self.token)
        room_data = self.get_success(self.store.get_room_with_channel_flag(room_id))
        self.assertFalse(room_data["is_channel"])

        self.helper.get_state(
            room_id,
            "m.room.is_channel",
            tok=self.token,
            expect_code=404
        )





