import logging

from homeassistant.components import mqtt
from homeassistant.components.lawn_mower import (
    LawnMowerActivity,
    LawnMowerEntity,
    LawnMowerEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PREFIX
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util.json import json_loads_object

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up lawn mower platform."""

    # Make sure MQTT integration is enabled and the client is available
    if not await mqtt.async_wait_for_mqtt_client(hass):
        _LOGGER.error("MQTT integration is not available")
        return

    async_add_entities([OpenMowerEntity(entry.data[CONF_PREFIX])])


class OpenMowerEntity(LawnMowerEntity):
    _attr_name = "OpenMower"
    _attr_unique_id = "openmower"
    _attr_supported_features = (
        LawnMowerEntityFeature.DOCK
        | LawnMowerEntityFeature.PAUSE
        | LawnMowerEntityFeature.START_MOWING
    )
    _attr_device_info = DeviceInfo(
        identifiers={(DOMAIN, "openmower")}, manufacturer="OpenMower"
    )

    def __init__(self, prefix: str) -> None:
        self._mqtt_topic_prefix = prefix
        if self._mqtt_topic_prefix and self._mqtt_topic_prefix[-1] != "/":
            self._mqtt_topic_prefix = self._mqtt_topic_prefix + "/"

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        await mqtt.async_subscribe(
            self.hass,
            self._mqtt_topic_prefix + "robot_state/json",
            self.async_robot_state_received,
            0,
        )
        _LOGGER.info("Added to Hass, subscribing to topics")

    @callback
    def async_robot_state_received(self, msg: mqtt.ReceiveMessage) -> None:
        value_json = json_loads_object(msg.payload)

        if value_json["emergency"] == 1 or (
            value_json["current_state"] == "IDLE" and value_json["is_charging"] == 0
        ):
            self._attr_activity = LawnMowerActivity.ERROR
        elif value_json["is_charging"] == 1:
            self._attr_activity = LawnMowerActivity.DOCKED
        # elif self.hass.states.get('button.openmower_pause_mowing').state == 'unavailable' and self.hass.states.get('button.openmower_continue_mowing').state != 'unavailable':
        # TODO    self._attr_activity = LawnMowerActivity.PAUSED
        elif value_json["current_state"] in ["MOWING", "DOCKING", "UNDOCKING"]:
            self._attr_activity = LawnMowerActivity.MOWING
        else:
            self._attr_activity = None

        self.async_write_ha_state()

    async def async_start_mowing(self) -> None:
        await mqtt.async_publish(
            self.hass,
            self._mqtt_topic_prefix + "action",
            "mower_logic:idle/start_mowing",
        )

    async def async_dock(self) -> None:
        await mqtt.async_publish(
            self.hass,
            self._mqtt_topic_prefix + "action",
            "mower_logic:idle/abort_mowing",
        )

    async def async_pause(self) -> None:
        await mqtt.async_publish(
            self.hass, self._mqtt_topic_prefix + "action", "mower_logic:idle/pause"
        )
