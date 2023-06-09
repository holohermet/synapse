import logging
from synapse.api.errors import Codes, SynapseError
from synapse.types import PollID
from synapse.util import stringutils

logger = logging.getLogger(__name__)


class PollCreatingHandler:

    def __init__(self, hs):
        self.hs = hs
        self.store = hs.get_datastores().main
        self.event_creation_handler = hs.get_event_creation_handler()

    async def _add_option(self, poll_id, option_name, option_number):
        if isinstance(poll_id, bytes):
            poll_id = poll_id.decode("utf-8")
        await self.store.add_option_to_poll(
            option_number=option_number,
            poll_id=poll_id,
            option_name=option_name,
        )

    async def _generate_poll_id(self, creator_id, poll_alias, room_id):
        random_string = stringutils.random_string(18)
        gen_poll_id = PollID(random_string, room_id).to_string()
        if isinstance(gen_poll_id, bytes):
            gen_poll_id = gen_poll_id.decode("utf-8")

        await self.store.store_poll(
            poll_id=gen_poll_id,
            poll_creator_user_id=creator_id,
            poll_alias=poll_alias,
            room_id=room_id
        )
        return gen_poll_id

    async def _store_options(self, options: list, poll_id: str):
        options_data = []
        for index, option in enumerate(options, 1):
            await self._add_option(poll_id, option, index)
            options_data.append({
                "option_number": index,
                "name": option,
            })
        return options_data

    async def create_poll(self, requester, config) -> dict:
        user_id = requester.user.to_string()
        poll_alias = config.get("poll_alias_name")
        room_id = config.get("room_id")
        options = config.get("options", [])

        if not await self.store.get_association_from_room_ids(room_id):
            raise SynapseError(
                400, "This room_id does not exist",
                Codes.ROOM_IN_USE
            )

        poll_id = await self._generate_poll_id(
            creator_id=user_id,
            poll_alias=poll_alias,
            room_id=room_id
        )
        options_data = await self._store_options(options, poll_id)
        await self.event_creation_handler.create_and_send_nonmember_event(
            requester,
            {
                "type": "m.room.poll",
                "room_id": room_id,
                "sender": user_id,
                "state_key": "",
                "content": {"poll_id": poll_id}
            }
        )
        return {
            "info": {
                "poll_id": poll_id,
                "poll_creator_user_id": user_id,
                "poll_alias": poll_alias,
                "room_id": room_id
            },
            "options": options_data
        }


class PollWorkingHandler:
    def __init__(self, hs):
        self.hs = hs
        self.store = hs.get_datastores().main
        self.event_creation_handler = hs.get_event_creation_handler()

    async def vote_for_option(self, requester, config):
        user_id = requester.user.to_string()

        option_index = config.get("option_number")
        poll_id = config.get("poll_id")

        if not all([option_index, poll_id]):
            raise SynapseError(400, "Poll or option is not specified")

        poll_exists = await self.store.get_association_from_poll_ids(poll_id)
        option_exists = await self.store.get_association_from_poll_options(
            poll_id, option_index
        )

        if not all([poll_exists, option_exists]):
            raise SynapseError(400, "Poll or option does not exist.")

        if await self.store.is_user_voted(poll_id, user_id):
            raise SynapseError(400, "User has already voted")

        new_count = await self.store.increment_vote(option_index, poll_id)
        await self.store.log_voted_user(option_index, poll_id, user_id)
        return {
            "info": "Option incremented successfully",
            "poll_id": poll_id,
            "number": option_index,
            "count": new_count
        }

    async def finish_poll(self, config):
        poll_id = config.get("poll_id")

        if not poll_id:
            raise SynapseError(400, "Poll or option is not specified")

        poll_exists = await self.store.get_association_from_poll_ids(poll_id)
        if not poll_exists:
            raise SynapseError(400, "Poll or option does not exist.")

        await self.store.deactivate_poll(poll_id)

        options = await self.store.get_poll_options(poll_id)
        poll = await self.store.get_poll(poll_id)
        return {
            "poll_id": poll_id,
            "poll_active": poll["active"],
            "poll_alias_name": poll["poll_alias"],
            "creator": poll["poll_creator_user_id"],
            "options": options
        }


class ListPollsHandler:

    def __init__(self, hs):
        self.hs = hs
        self.store = hs.get_datastores().main
        self.event_creation_handler = hs.get_event_creation_handler()

    async def _build_resource_for_poll(self, poll: dict, user_id: str) -> dict:
        creator = poll["poll_creator_user_id"]
        options = await self.store.get_poll_options(poll["poll_id"])
        is_voted = await self.store.is_user_voted(poll["poll_id"], user_id)
        return {
            "poll_id": poll["poll_id"],
            "poll_alias": poll["poll_alias"],
            "options": options,
            "creator": creator,
            "poll_active": poll["active"],
            "voted": is_voted
        }

    async def list_polls_by_room_id(self, requester, room_id):
        user_id = requester.user.to_string()

        if not await self.store.get_association_from_room_ids(room_id):
            raise SynapseError(400, "Specified room does not exist")

        polls = await self.store.get_polls_from_room(room_id)
        polls_resource = [
            await self._build_resource_for_poll(poll, user_id) for poll in polls
        ]
        return {"room_id": room_id, "info": polls_resource}
