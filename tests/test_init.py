"""End-to-end tests with an emulated board: setup, heartbeat, control, push updates, unload."""
import asyncio

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_FRIENDLY_NAME, CONF_PORT, CONF_PROTOCOL, STATE_OFF, STATE_ON
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.dscriptmodule.const import CONF_AESKEY, CONF_LISTENIP, CONF_SERVER, CONF_PYOJBECT, DOMAIN

from .conftest import BOARD_IP, free_port

pytestmark = pytest.mark.usefixtures("socket_enabled")


@pytest.fixture(autouse=True)
def allow_board_ip(socket_enabled):
    """The emulated board listens on BOARD_IP - allow connections to it."""
    import pytest_socket
    pytest_socket.socket_allow_hosts(["127.0.0.1", BOARD_IP], allow_unix_socket=True)


async def wait_for(predicate, timeout=15.0):
    for _ in range(int(timeout / 0.1)):
        if predicate():
            return True
        await asyncio.sleep(0.1)
    return predicate()


async def setup_entry(hass: HomeAssistant):
    port = free_port()
    entry = MockConfigEntry(domain=DOMAIN, title="test", data={
        CONF_FRIENDLY_NAME: "test", CONF_LISTENIP: "127.0.0.1", CONF_PORT: port,
        CONF_PROTOCOL: "binary", CONF_AESKEY: ""})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry, port


def light_entity_ids(hass):
    registry = er.async_get(hass)
    return sorted(e.entity_id for e in registry.entities.values() if e.platform == DOMAIN and e.domain == "light")


async def test_setup_and_unload_without_boards(hass: HomeAssistant) -> None:
    entry, port = await setup_entry(hass)
    assert entry.state is ConfigEntryState.LOADED
    server = hass.data[DOMAIN][entry.entry_id][CONF_SERVER][CONF_PYOJBECT]
    assert server.dScriptServer.State is True

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert server.dScriptServer.State is False


async def test_heartbeat_creates_board_entities_and_controls_light(hass: HomeAssistant, fake_board) -> None:
    entry, port = await setup_entry(hass)

    # a new board announces itself with a heartbeat trigger (cmd 0, state -1)
    await fake_board.trigger(port, bytes([0, 0, 255]))
    assert await wait_for(lambda: len(light_entity_ids(hass)) == 2), light_entity_ids(hass)
    await hass.async_block_till_done()
    light = light_entity_ids(hass)[0]

    # turning the light on sends SetLight (0x40) to the board
    await hass.services.async_call("light", "turn_on", {"entity_id": light}, blocking=True)
    assert any(r[0] == 0x40 and r[2] == 1 for r in fake_board.requests)

    # the firmware pushes the new state (GetLight trigger) - entity follows without polling
    await fake_board.trigger(port, bytes([81, 1, 1]))
    assert await wait_for(lambda: hass.states.get(light) is not None and hass.states.get(light).state == STATE_ON)
    await fake_board.trigger(port, bytes([81, 1, 0]))
    assert await wait_for(lambda: hass.states.get(light).state == STATE_OFF)

    # a second heartbeat of a known board must not create duplicates
    await fake_board.trigger(port, bytes([0, 0, 255]))
    await asyncio.sleep(0.5)
    await hass.async_block_till_done()
    assert len(light_entity_ids(hass)) == 2

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()


async def test_requests_to_board_are_never_parallel(hass: HomeAssistant, fake_board) -> None:
    entry, port = await setup_entry(hass)
    active = 0
    max_active = 0
    original = fake_board.handle

    async def counting_handle(reader, writer):
        nonlocal active, max_active
        active += 1
        max_active = max(max_active, active)
        try:
            await asyncio.sleep(0.02)
            await original(reader, writer)
        finally:
            active -= 1

    fake_board.handle = counting_handle
    await fake_board.stop()
    await fake_board.start()

    await fake_board.trigger(port, bytes([0, 0, 255]))
    assert await wait_for(lambda: len(light_entity_ids(hass)) == 2)
    await hass.async_block_till_done()
    lights = light_entity_ids(hass)
    max_active = 0
    await asyncio.gather(*[hass.services.async_call("light", "toggle", {"entity_id": lights}, blocking=True) for _ in range(5)])
    assert max_active == 1

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()


MAC = "00:01:02:ab:04:05"
STATUS_PAGE = "app=3.9\ntemperature=267\nvoltage=121\ninstr_per_sec=1200\ninstr_per_sec_max=1500\n"


def board_entity(hass, entry, dSEntityType):
    devices = hass.data[DOMAIN][entry.entry_id]["devices"]
    return devices.get(MAC, {}).get("dscriptmodule_" + MAC.replace(":", "") + "_" + dSEntityType + "1")


async def test_status_page_feeds_diagnostic_sensors(hass: HomeAssistant, fake_board, aioclient_mock) -> None:
    aioclient_mock.get("http://" + BOARD_IP + "/status.htm", text=STATUS_PAGE)
    registry = er.async_get(hass)
    entry, port = await setup_entry(hass)
    # diagnostic sensors are disabled by default - enable temperature and load before they are created
    for sensor in ("sensor_temperature", "sensor_load"):
        registry.async_get_or_create("sensor", DOMAIN, "dscriptmodule_" + MAC.replace(":", "") + "_" + sensor + "1", config_entry=entry)

    await fake_board.trigger(port, bytes([0, 0, 255]))
    assert await wait_for(lambda: board_entity(hass, entry, "sensor_board") is not None)
    await hass.async_block_till_done()

    requests_before = len(fake_board.requests)
    await board_entity(hass, entry, "sensor_board").async_local_poll()
    await hass.async_block_till_done()

    temperature = board_entity(hass, entry, "sensor_temperature").entity_id
    load = board_entity(hass, entry, "sensor_load").entity_id
    assert hass.states.get(temperature).state == "26.7"
    assert hass.states.get(load).state == "1500"
    assert hass.states.get(load).attributes["last_second"] == 1200
    assert board_entity(hass, entry, "sensor_board")._board._StatusPageSupported is True
    assert len(fake_board.requests) == requests_before, "status.htm replaces the extra GetStatus connection"
    board_state = hass.states.get(board_entity(hass, entry, "sensor_board").entity_id)
    assert "temperature" not in board_state.attributes and "voltage" not in board_state.attributes  # separate entities now
    assert board_state.attributes["sw_version"] == "3.9"  # app version taken over from status.htm (GetStatus reported 3.8)

    voltage = registry.async_get_entity_id("sensor", DOMAIN, "dscriptmodule_" + MAC.replace(":", "") + "_sensor_voltage1")
    voltage_entry = registry.async_get(voltage)
    assert voltage_entry.disabled_by is er.RegistryEntryDisabler.INTEGRATION
    assert voltage_entry.entity_category == "diagnostic"

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()


async def test_older_firmware_without_status_page(hass: HomeAssistant, fake_board, aioclient_mock) -> None:
    aioclient_mock.get("http://" + BOARD_IP + "/status.htm", status=404)
    aioclient_mock.get("http://" + BOARD_IP + "/index.htm", text="<html></html>")
    entry, port = await setup_entry(hass)
    await fake_board.trigger(port, bytes([0, 0, 255]))
    assert await wait_for(lambda: board_entity(hass, entry, "sensor_board") is not None)
    await hass.async_block_till_done()

    board_sensor = board_entity(hass, entry, "sensor_board")
    requests_before = len(fake_board.requests)
    await board_sensor.async_local_poll()
    await hass.async_block_till_done()

    assert board_sensor._board._StatusPageSupported is False
    assert hass.states.get(board_sensor.entity_id).state == "200"
    assert any(r[0] == 0x30 for r in fake_board.requests[requests_before:]), "temperature/voltage still come from GetStatus"
    assert board_sensor._board._InstrPerSecMax is None

    calls = aioclient_mock.call_count
    await board_sensor.async_local_poll()  # status.htm is not requested again on every poll
    assert aioclient_mock.call_count == calls + 1

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
