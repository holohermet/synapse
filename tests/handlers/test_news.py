from unittest import mock

from twisted.test.proto_helpers import MemoryReactor

import synapse

from synapse.server import HomeServer
from synapse.util import Clock
from synapse.types import create_requester

from synapse.rest.client import room
from synapse.rest.client import login
from synapse.rest.client import register


from tests import unittest


class CreateNewsHandlerTest(unittest.HomeserverTestCase):
    servlets = [
        synapse.rest.admin.register_servlets_for_client_rest_resource,
        room.register_servlets,
        login.register_servlets,
        register.register_servlets,
    ]

    def make_homeserver(self, reactor: MemoryReactor, clock: Clock) -> HomeServer:
        return self.setup_test_homeserver(replication_layer=mock.Mock())

    def prepare(self, reactor: MemoryReactor, clock: Clock, hs: HomeServer) -> None:
        self.handler = hs.get_news_creating_handler()

    def test_create_news_for_user_room(self) -> None:
        user_id = self.register_user("user", "pass")
        token = self.login("user", "pass")
        room_id = self.helper.create_room_as(user_id, tok=token)
        self.get_success(
            self.handler.create_news(
                requester=create_requester(user_id),
                config={
                    "room_id": room_id,
                    "news_content": "<html></html>"
                }
            )
        )


class NewsModificationHandler(unittest.HomeserverTestCase):
    servlets = [
        synapse.rest.admin.register_servlets_for_client_rest_resource,
        room.register_servlets,
        login.register_servlets,
        register.register_servlets,
    ]

    def make_homeserver(self, reactor: MemoryReactor, clock: Clock) -> HomeServer:
        return self.setup_test_homeserver(replication_layer=mock.Mock())

    def prepare(self, reactor: MemoryReactor, clock: Clock, hs: HomeServer) -> None:
        self.handler = hs.get_news_working_handler()
        self.create_news_handler = hs.get_news_creating_handler()
        self.user_id = self.register_user("user", "pass")
        self.token = self.login("user", "pass")
        self.room_id = self.helper.create_room_as(self.user_id, tok=self.token)
        self.news_id = self.get_success(
            self.create_news_handler.create_news(
                requester=create_requester(self.user_id),
                config={
                    "room_id": self.room_id,
                    "news_content": "<html></html>"
                }
            )
        )["news_id"]

    def test_get_news_by_room_id(self) -> None:
        r = self.get_success(
            self.handler.get_news_by_room_id(self.room_id)
        )
        self.assertEqual(r, {"news_info": [{"news_id": self.news_id}]})

    def test_get_unread_news_by_room_id(self) -> None:
        r = self.get_success(
            self.handler.get_unread_news_by_room_id(self.room_id, self.user_id)
        )
        self.assertEqual(r, {"news_info": [{"news_id": self.news_id, "seen": False}]})

    def test_get_news_by_news_id(self) -> None:
        r = self.get_success(
            self.handler.get_news_by_news_id(self.news_id)
        )
        self.assertEqual(
            r, {
                "news_id": self.news_id,
                "news_content": "<html></html>",
                "active": True
            }
        )

    def test_set_news_read_marker(self) -> None:
        r = self.get_success(
            self.handler.get_unread_news_by_room_id(self.room_id, self.user_id)
        )
        seen = r["news_info"][0]["seen"]
        self.assertFalse(seen)
        self.get_success(
            self.handler.set_news_read_marker(
                requester=create_requester(self.user_id),
                config={
                    "room_id": self.room_id,
                    "news_id": self.news_id
                })
        )
        r = self.get_success(
            self.handler.get_unread_news_by_room_id(self.room_id, self.user_id)
        )
        self.assertEqual(len(r["news_info"]), 0)



