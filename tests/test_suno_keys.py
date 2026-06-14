"""Tests for the Suno multi-key pool: add / elect / rotate / migrate."""
import pytest
from sqlalchemy import select

from app.models import SunoKey
from app.services.settings import set_setting, get_setting
from app.services.suno import (
    KEY_API_KEY,
    add_key,
    clear_api_key,
    ensure_usable_key,
    get_active_key,
    list_keys,
    remove_key,
    rotate_active,
    set_key_credits,
)


async def _active(session):
    return (
        await session.execute(select(SunoKey).where(SunoKey.is_active.is_(True)))
    ).scalar_one_or_none()


@pytest.mark.asyncio
async def test_first_key_active_second_standby(session):
    k1 = await add_key(session, "key-aaaa-1111")
    assert k1.is_active is True
    k2 = await add_key(session, "key-bbbb-2222")
    assert k2.is_active is False
    assert len(await list_keys(session)) == 2


@pytest.mark.asyncio
async def test_get_active_key_elects_when_none_active(session):
    # insert two enabled, neither active
    session.add(SunoKey(api_key="k1", enabled=True, is_active=False))
    session.add(SunoKey(api_key="k2", enabled=True, is_active=False))
    await session.commit()
    key = await get_active_key(session)
    assert key in {"k1", "k2"}
    assert (await _active(session)).api_key == key


@pytest.mark.asyncio
async def test_legacy_key_migrated(session):
    await set_setting(session, KEY_API_KEY, "legacy-key-123456")
    key = await get_active_key(session)
    assert key == "legacy-key-123456"
    # setting cleared, row created + active
    assert await get_setting(session, KEY_API_KEY) is None
    rows = await list_keys(session)
    assert len(rows) == 1
    assert rows[0].is_active is True


@pytest.mark.asyncio
async def test_rotate_prefers_more_credits(session):
    await add_key(session, "active-key")          # active
    standby_low = await add_key(session, "low")    # standby
    standby_hi = await add_key(session, "hi")       # standby
    await set_key_credits(session, standby_low.id, 5)
    await set_key_credits(session, standby_hi.id, 200)
    nxt = await rotate_active(session)
    assert nxt == "hi"
    assert (await _active(session)).api_key == "hi"


@pytest.mark.asyncio
async def test_ensure_usable_key_rotates_when_active_low(session):
    a = await add_key(session, "active-low")
    b = await add_key(session, "backup-full")
    await set_key_credits(session, a.id, 3)     # below threshold 10
    await set_key_credits(session, b.id, 99)
    key = await ensure_usable_key(session)
    assert key == "backup-full"


@pytest.mark.asyncio
async def test_ensure_usable_key_keeps_active_when_ok(session):
    a = await add_key(session, "active-ok")
    await add_key(session, "backup")
    await set_key_credits(session, a.id, 50)
    key = await ensure_usable_key(session)
    assert key == "active-ok"


@pytest.mark.asyncio
async def test_set_credits_zero_disables(session):
    a = await add_key(session, "dying")
    await set_key_credits(session, a.id, 0)
    refreshed = await session.get(SunoKey, a.id)
    assert refreshed.enabled is False


@pytest.mark.asyncio
async def test_remove_active_promotes_another(session):
    a = await add_key(session, "first")
    b = await add_key(session, "second")
    assert a.is_active and not b.is_active
    await remove_key(session, a.id)
    # second should now be electable as active
    key = await get_active_key(session)
    assert key == "second"


@pytest.mark.asyncio
async def test_clear_removes_all(session):
    await add_key(session, "x1")
    await add_key(session, "x2")
    assert await clear_api_key(session) is True
    assert await list_keys(session) == []
    assert await get_active_key(session) is None


@pytest.mark.asyncio
async def test_set_active_key_manual_override_reenables(session):
    from app.services.suno import set_active_key, set_key_credits

    a = await add_key(session, "active-one")
    b = await add_key(session, "dead-but-wanted")
    # b auto-disabled at 0 credits
    await set_key_credits(session, b.id, 0)
    assert (await session.get(SunoKey, b.id)).enabled is False
    # owner manually picks b -> it becomes active AND re-enabled
    assert await set_active_key(session, b.id) is True
    refreshed = await session.get(SunoKey, b.id)
    assert refreshed.is_active is True
    assert refreshed.enabled is True
    assert (await _active(session)).api_key == "dead-but-wanted"
