from unittest import mock

from twisted.test.proto_helpers import MemoryReactor

import synapse
from synapse.api.errors import SynapseError

from synapse.server import HomeServer
from synapse.util import Clock
from synapse.types import create_requester

from synapse.rest.client import room
from synapse.rest.client import login
from synapse.rest.client import register

from tests import unittest


class CreatePollHandlerTest(unittest.HomeserverTestCase):
    servlets = [
        synapse.rest.admin.register_servlets_for_client_rest_resource,
        room.register_servlets,
        login.register_servlets,
        register.register_servlets,
    ]

    def make_homeserver(self, reactor: MemoryReactor, clock: Clock) -> HomeServer:
        return self.setup_test_homeserver(replication_layer=mock.Mock())

    def prepare(self, reactor: MemoryReactor, clock: Clock, hs: HomeServer) -> None:
        self.handler = hs.get_poll_creating_handler()

    def test_create_poll_for_room(self) -> None:
        user_id = self.register_user("user", "pass")
        token = self.login("user", "pass")
        room_id = self.helper.create_room_as(user_id, tok=token)
        r = self.get_success(
            self.handler.create_poll(
                requester=create_requester(user_id),
                config={
                    "poll_alias_name": "Test poll",
                    "room_id": room_id,
                    "options": ["Opt1", "Opt2", "Opt3"]
                }
            )
        )
        self.assertTrue("options" in r.keys())
        self.assertTrue(len(r["options"]) == 3)


class PollWorkingHandlerTest(unittest.HomeserverTestCase):
    servlets = [
        synapse.rest.admin.register_servlets_for_client_rest_resource,
        room.register_servlets,
        login.register_servlets,
        register.register_servlets,
    ]

    def make_homeserver(self, reactor: MemoryReactor, clock: Clock) -> HomeServer:
        return self.setup_test_homeserver(replication_layer=mock.Mock())

    def prepare(self, reactor: MemoryReactor, clock: Clock, hs: HomeServer) -> None:
        self.handler = hs.get_poll_working_handler()
        self.poll_creating_handler = hs.get_poll_creating_handler()
        self.user_id = self.register_user("user", "pass")
        self.token = self.login("user", "pass")
        self.room_id = self.helper.create_room_as(self.user_id, tok=self.token)
        poll_data = self.get_success(
            self.poll_creating_handler.create_poll(
                requester=create_requester(self.user_id),
                config={
                    "poll_alias_name": "Test poll",
                    "room_id": self.room_id,
                    "options": ["Opt1", "Opt2", "Opt3"]
                }
            )
        )
        self.poll_id = poll_data["info"]["poll_id"]

    def test_vote_for_option(self) -> None:
        users = [self.register_user(f"user{i}", "pass") for i in range(3)]
        for user in users:
            r = self.get_success(
                self.handler.vote_for_option(
                    requester=create_requester(user),
                    config={
                        "option_number": 1,
                        "poll_id": self.poll_id
                    }
                )
            )

        self.assertEqual(r["count"], 3)

    def test_user_already_voted_for_option(self) -> None:
        self.get_success(
            self.handler.vote_for_option(
                requester=create_requester(self.user_id),
                config={
                    "option_number": 1,
                    "poll_id": self.poll_id
                }
            )
        )
        self.get_failure(
            self.handler.vote_for_option(
                requester=create_requester(self.user_id),
                config={
                    "option_number": 2,
                    "poll_id": self.poll_id
                }
            ),
            exc=SynapseError
        )

