"""Tests for the config and options flow."""
from homeassistant import config_entries
from homeassistant.const import CONF_FRIENDLY_NAME, CONF_PORT, CONF_PROTOCOL
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.dscriptmodule.const import CONF_AESKEY, CONF_LISTENIP, DOMAIN

USER_INPUT = {
    CONF_FRIENDLY_NAME: "My dScript",
    CONF_LISTENIP: "127.0.0.1",
    CONF_PORT: 17999,
    CONF_PROTOCOL: "binary",
    CONF_AESKEY: "",
}


async def test_user_flow_creates_entry(hass: HomeAssistant) -> None:
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "resource"

    result = await hass.config_entries.flow.async_configure(result["flow_id"], USER_INPUT)
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "My dScript"
    assert result["data"] == USER_INPUT


async def test_options_flow_updates_entry_data(hass: HomeAssistant) -> None:
    entry = MockConfigEntry(domain=DOMAIN, data=USER_INPUT, source=config_entries.SOURCE_USER)
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "resource"

    new_input = {**USER_INPUT, CONF_PORT: 18000}
    result = await hass.config_entries.options.async_configure(result["flow_id"], new_input)
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert entry.data[CONF_PORT] == 18000
