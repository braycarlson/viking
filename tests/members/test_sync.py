from __future__ import annotations

import pytest

from datetime import datetime, UTC

from members.models import DiscordMember
from members.sync import MemberSynchronizer, MemberSyncPlan


MOMENT = datetime(2026, 7, 27, tzinfo=UTC)


class RoleStub:
    def __init__(self, identifier: int) -> None:
        self.id = identifier


class MemberStub:
    def __init__(
        self,
        *,
        identifier: int,
        name: str,
        nickname: str | None,
        display_name: str,
        role_identifier: int
    ) -> None:
        self.display_name = display_name
        self.id = identifier
        self.name = name
        self.nick = nickname
        self.top_role = RoleStub(role_identifier)


class GuildStub:
    def __init__(self, members: list[MemberStub]) -> None:
        self.members = members


class RepositoryStub:
    def __init__(self, stored: dict[int, DiscordMember]) -> None:
        self.calls = []
        self.stored = stored

    async def ban_many(self, identifiers: list[int]) -> None:
        call = ('ban_many', identifiers)
        self.calls.append(call)

    async def create_many(self, members: list[MemberStub]) -> None:
        call = ('create_many', members)
        self.calls.append(call)

    async def profile_synchronize(self, records: list[tuple]) -> None:
        call = ('profile_synchronize', records)
        self.calls.append(call)

    async def records_all(self) -> dict[int, DiscordMember]:
        return self.stored

    async def remove_many(self, identifiers: list[int]) -> None:
        call = ('remove_many', identifiers)
        self.calls.append(call)

    async def restore_many(self, records: list[tuple]) -> None:
        call = ('restore_many', records)
        self.calls.append(call)

    async def unban_many(self, identifiers: list[int]) -> None:
        call = ('unban_many', identifiers)
        self.calls.append(call)


def member_build(
    *,
    identifier: int = 1,
    name: str = 'braycarlson',
    nickname: str | None = None,
    display_name: str = 'braycarlson',
    role_identifier: int = 100
) -> MemberStub:
    return MemberStub(
        identifier=identifier,
        name=name,
        nickname=nickname,
        display_name=display_name,
        role_identifier=role_identifier,
    )


def stored_build(
    *,
    identifier: int = 1,
    name: str = 'braycarlson',
    nickname: str | None = None,
    display_name: str = 'braycarlson',
    role_identifier: int = 100,
    banned_at: datetime | None = None,
    removed_at: datetime | None = None
) -> DiscordMember:
    return DiscordMember(
        identifier=identifier,
        name=name,
        display_name=display_name,
        nickname=nickname,
        role_identifier=role_identifier,
        banned_at=banned_at,
        removed_at=removed_at,
    )


def plan_empty_build() -> MemberSyncPlan:
    return MemberSyncPlan(
        create=[],
        update=[],
        restore=[],
        remove=[],
        ban=[],
        unban=[],
    )


async def plan_build(
    members: list[MemberStub],
    stored: dict[int, DiscordMember],
    banned_identifiers: set[int] | None = None
) -> MemberSyncPlan:
    repository = RepositoryStub(stored)
    synchronizer = MemberSynchronizer(repository)
    guild = GuildStub(members)

    return await synchronizer.plan(guild, banned_identifiers)


def test_bans_plan_without_bans() -> None:
    stored = {1: stored_build()}

    ban, unban = MemberSynchronizer._bans_plan(stored, None)

    assert ban == []
    assert unban == []


def test_bans_plan_bans_stored_member() -> None:
    stored = {1: stored_build()}

    ban, unban = MemberSynchronizer._bans_plan(stored, {1})

    assert ban == [1]
    assert unban == []


def test_bans_plan_ignores_unknown_member() -> None:
    stored = {1: stored_build()}

    ban, unban = MemberSynchronizer._bans_plan(stored, {2})

    assert ban == []
    assert unban == []


def test_bans_plan_ignores_banned_member() -> None:
    stored = {1: stored_build(banned_at=MOMENT)}

    ban, unban = MemberSynchronizer._bans_plan(stored, {1})

    assert ban == []
    assert unban == []


def test_bans_plan_unbans_member() -> None:
    stored = {1: stored_build(banned_at=MOMENT)}

    ban, unban = MemberSynchronizer._bans_plan(stored, set())

    assert ban == []
    assert unban == [1]


def test_bans_plan_bans_and_unbans() -> None:
    stored = {
        1: stored_build(identifier=1),
        2: stored_build(identifier=2, banned_at=MOMENT),
    }

    ban, unban = MemberSynchronizer._bans_plan(stored, {1})

    assert ban == [1]
    assert unban == [2]


@pytest.mark.asyncio
async def test_plan_creates_unknown_member() -> None:
    member = member_build()

    plan = await plan_build([member], {})

    assert plan.create == [member]
    assert plan.update == []
    assert plan.restore == []
    assert plan.remove == []


@pytest.mark.asyncio
async def test_plan_ignores_unchanged_member() -> None:
    plan = await plan_build([member_build()], {1: stored_build()})

    assert plan.create == []
    assert plan.update == []
    assert plan.restore == []
    assert plan.remove == []


@pytest.mark.asyncio
async def test_plan_updates_renamed_member() -> None:
    member = member_build(name='viking', display_name='viking')
    stored = {1: stored_build()}

    plan = await plan_build([member], stored)

    assert plan.update == [(member, 'braycarlson', None)]


@pytest.mark.asyncio
async def test_plan_updates_renamed_nickname() -> None:
    member = member_build(nickname='Viking', display_name='Viking')
    stored = {1: stored_build(nickname='Brayden', display_name='Brayden')}

    plan = await plan_build([member], stored)

    assert plan.update == [(member, None, 'Brayden')]


@pytest.mark.asyncio
async def test_plan_updates_first_nickname() -> None:
    member = member_build(nickname='Viking', display_name='Viking')
    stored = {1: stored_build()}

    plan = await plan_build([member], stored)

    assert plan.update == [(member, None, None)]


@pytest.mark.asyncio
async def test_plan_updates_promoted_member() -> None:
    member = member_build(role_identifier=200)
    stored = {1: stored_build()}

    plan = await plan_build([member], stored)

    assert plan.update == [(member, None, None)]


@pytest.mark.asyncio
async def test_plan_restores_removed_member() -> None:
    member = member_build()
    stored = {1: stored_build(removed_at=MOMENT)}

    plan = await plan_build([member], stored)

    assert plan.restore == [(member, None, None)]
    assert plan.update == []


@pytest.mark.asyncio
async def test_plan_restores_banned_member() -> None:
    member = member_build(name='viking', display_name='viking')
    stored = {1: stored_build(banned_at=MOMENT)}

    plan = await plan_build([member], stored)

    assert plan.restore == [(member, 'braycarlson', None)]
    assert plan.update == []


@pytest.mark.asyncio
async def test_plan_removes_departed_member() -> None:
    stored = {1: stored_build()}

    plan = await plan_build([], stored)

    assert plan.remove == [1]


@pytest.mark.asyncio
async def test_plan_ignores_departed_member_already_removed() -> None:
    stored = {1: stored_build(removed_at=MOMENT)}

    plan = await plan_build([], stored)

    assert plan.remove == []


@pytest.mark.asyncio
async def test_plan_bans_member() -> None:
    stored = {1: stored_build()}

    plan = await plan_build([member_build()], stored, {1})

    assert plan.ban == [1]
    assert plan.unban == []


@pytest.mark.asyncio
async def test_apply_empty_plan() -> None:
    repository = RepositoryStub({})
    synchronizer = MemberSynchronizer(repository)

    await synchronizer.apply(plan_empty_build())

    assert repository.calls == []


@pytest.mark.asyncio
async def test_apply_dispatches_every_change() -> None:
    member = member_build()
    record = (member, 'braycarlson', None)

    plan = MemberSyncPlan(
        create=[member],
        update=[record],
        restore=[record],
        remove=[2],
        ban=[3],
        unban=[4],
    )

    repository = RepositoryStub({})
    synchronizer = MemberSynchronizer(repository)

    await synchronizer.apply(plan)

    names = [name for name, _ in repository.calls]

    assert names == [
        'create_many',
        'restore_many',
        'profile_synchronize',
        'remove_many',
        'ban_many',
        'unban_many',
    ]
