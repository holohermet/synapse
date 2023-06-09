import logging
from synapse.storage._base import SQLBaseStore

logger = logging.getLogger(__name__)


class PollsWorkerStore(SQLBaseStore):

    async def store_poll(self, poll_id, poll_creator_user_id, poll_alias, room_id):
        def store_poll_txn(txn):
            self.db_pool.simple_insert_txn(
                txn,
                "polls",
                {
                    "room_id": room_id,
                    "poll_creator_user_id": poll_creator_user_id,
                    "poll_alias": poll_alias,
                    "poll_id": poll_id,
                    "active": True
                },
            )

        await self.db_pool.runInteraction("store_poll_txn", store_poll_txn)

    async def add_option_to_poll(self, option_name, poll_id, option_number):
        def store_option_txn(txn):
            self.db_pool.simple_insert_txn(
                txn,
                "polls_options",
                {
                    "poll_id": poll_id,
                    "name": option_name,
                    "count": 0,
                    "number": option_number
                },
            )

        await self.db_pool.runInteraction("store_option_txn", store_option_txn)

    async def increment_vote(self, option_number, poll_id):
        old_count = await self.db_pool.simple_select_one_onecol(
            table="polls_options",
            keyvalues={"poll_id": poll_id, "number": str(option_number)},
            retcol="count",
            desc="get_old_count",
        )
        await self.db_pool.simple_update_one(
            table="polls_options",
            keyvalues={"poll_id": poll_id, "number": str(option_number)},
            updatevalues={"count": old_count + 1},
            desc="update_count",
        )

        return old_count + 1

    async def log_voted_user(self, option_number, poll_id, user_id):
        def store_voted_user_txn(txn):
            self.db_pool.simple_insert_txn(
                txn,
                "voted_users",
                {
                    "poll_id": poll_id,
                    "user_id": user_id,
                    "number": option_number
                },
            )

        await self.db_pool.runInteraction("store_voted_user_txn", store_voted_user_txn)

    async def deactivate_poll(self, poll_id):
        await self.db_pool.simple_update_one(
            table="polls",
            keyvalues={"poll_id": poll_id},
            updatevalues={"active": False},
            desc="deactivate_poll",
        )

    async def get_polls_from_room(self, room_id):
        poll_info = await self.db_pool.simple_select_list(
            table="polls",
            keyvalues={"room_id": room_id},
            retcols=["poll_creator_user_id", "poll_id", "poll_alias", "active"],
            desc="get_polls_creator"
        )
        return poll_info

    async def get_poll(self, poll_id):
        poll_info = await self.db_pool.simple_select_list(
            table="polls",
            keyvalues={"poll_id": poll_id},
            retcols=["poll_creator_user_id", "poll_alias", "active"],
            desc="get_polls_creator"
        )
        return poll_info

    async def get_poll_options(self, poll_id):
        options = await self.db_pool.simple_select_list(
            table="polls_options",
            keyvalues={"poll_id": poll_id},
            retcols=["name", "number", "count"],
            desc="get_polls_options"
        )

        return options

    async def is_user_voted(self, poll_id, user_id):
        option_number = await self.db_pool.simple_select_onecol(
            "voted_users",
            {
                "poll_id": poll_id,
                "user_id": user_id
            },
            "number",
            desc="get_association_from_poll_options",
        )

        return option_number[0] if option_number else False

    async def get_association_from_poll_ids(self, poll_id):
        poll_id = await self.db_pool.simple_select_onecol(
            "polls",
            {"poll_id": poll_id},
            "room_id",
            desc="get_association_from_poll_alias",
        )
        return bool(poll_id)

    async def get_association_from_poll_options(self, poll_id, option_number):
        option_number = await self.db_pool.simple_select_onecol(
            "polls_options",
            {
                "poll_id": poll_id,
                "number": option_number
            },
            "number",
            desc="get_association_from_poll_options",
        )

        return bool(option_number)

