import logging

import voluptuous as vol
from homeassistant.components import mqtt
from homeassistant.components.lawn_mower import (
    LawnMowerActivity,
    LawnMowerEntity,
    LawnMowerEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PREFIX
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_platform, config_validation as cv
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import slugify
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

    async_add_entities([(OpenMowerEntity(entry.data[CONF_PREFIX]))])

    platform = entity_platform.async_get_current_platform()
    platform.async_register_entity_service(
        "command_idle_start_mowing", {}, "command_idle_start_mowing"
    )
    platform.async_register_entity_service(
        "command_mowing_pause", {}, "command_mowing_pause"
    )
    platform.async_register_entity_service(
        "command_mowing_continue", {}, "command_mowing_continue"
    )
    platform.async_register_entity_service(
        "command_mowing_abort_mowing", {}, "command_mowing_abort_mowing"
    )
    platform.async_register_entity_service(
        "command_mowing_skip_area", {}, "command_mowing_skip_area"
    )
    platform.async_register_entity_service(
        "command_mowing_skip_path", {}, "command_mowing_skip_path"
    )
    platform.async_register_entity_service(
        "send_command",
        cv.make_entity_service_schema({vol.Required("payload"): cv.string}),
        "send_command",
    )


class OpenMowerEntity(LawnMowerEntity):
    _attr_name = "OpenMower"
    _attr_supported_features = (
        LawnMowerEntityFeature.DOCK
        | LawnMowerEntityFeature.PAUSE
        | LawnMowerEntityFeature.START_MOWING
    )

    def __init__(self, prefix: str) -> None:
        self._mqtt_topic_prefix = prefix

        self._attr_unique_id = slugify(f"{prefix}").lower()
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, slugify(prefix))},
            manufacturer="OpenMower",
        )

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
        elif value_json["current_state"] in ["MOWING", "DOCKING", "UNDOCKING"]:
            self._attr_activity = LawnMowerActivity.MOWING
        elif value_json["current_state"] in ["PAUSED"]:
            self._attr_activity = LawnMowerActivity.PAUSED
        else:
            self._attr_activity = None

        self.async_write_ha_state()

    async def async_start_mowing(self) -> None:
        if self.state == LawnMowerActivity.PAUSED:
            await self.command_mowing_continue()
        else:
            await self.command_idle_start_mowing()

    async def async_dock(self) -> None:
        await self.command_mowing_abort_mowing()

    async def async_pause(self) -> None:
        await self.command_mowing_pause()

    async def send_command(self, payload) -> None:
        await mqtt.async_publish(self.hass, self._mqtt_topic_prefix + "action", payload)

    async def command_area_recording_start_recording(self) -> None:
        await self.send_command("mower_logic:area_recording/start_recording")

    async def command_area_recording_exit_recording_mode(self) -> None:
        await self.send_command("mower_logic:area_recording/exit_recording_mode")

    async def command_area_recording_finish_discard(self) -> None:
        await self.send_command("mower_logic:area_recording/finish_discard")

    async def command_area_recording_finish_mowing_area(self) -> None:
        await self.send_command("mower_logic:area_recording/finish_mowing_area")

    async def command_area_recording_finish_navigation_area(self) -> None:
        await self.send_command("mower_logic:area_recording/finish_navigation_area")

    async def command_area_recording_record_dock(self) -> None:
        await self.send_command("mower_logic:area_recording/record_dock")

    async def command_area_recording_stop_recording(self) -> None:
        await self.send_command("mower_logic:area_recording/stop_recording")

    async def command_idle_start_area_recording(self) -> None:
        await self.send_command("mower_logic:idle/start_area_recording")

    async def command_idle_start_mowing(self) -> None:
        await self.send_command("mower_logic:idle/start_mowing")

    async def command_mowing_abort_mowing(self) -> None:
        await self.send_command("mower_logic:mowing/abort_mowing")

    async def command_mowing_pause(self) -> None:
        await self.send_command("mower_logic:mowing/pause")

    async def command_mowing_skip_area(self) -> None:
        await self.send_command("mower_logic:mowing/skip_area")

    async def command_mowing_skip_path(self) -> None:
        await self.send_command("mower_logic:mowing/skip_path")

    async def command_mowing_continue(self) -> None:
        await self.send_command("mower_logic:mowing/continue")
