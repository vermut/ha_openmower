from __future__ import annotations

import logging

from homeassistant.components import mqtt
from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PREFIX
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .entity import OpenMowerMqttEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    # Make sure MQTT integration is enabled and the client is available
    if not await mqtt.async_wait_for_mqtt_client(hass):
        _LOGGER.error("MQTT integration is not available")
        return

    prefix = entry.data[CONF_PREFIX]
    async_add_entities(
        [
            OpenMowerSkipAreaButton("Skip Area", prefix, "DUMMY", None),
            OpenMowerSkipPathButton("Skip Path", prefix, "DUMMY", None),
        ]
    )


class OpenMowerMqttButtonEntity(OpenMowerMqttEntity, ButtonEntity):
    async def async_added_to_hass(self) -> None:
        pass

    def _async_robot_state_received(self, msg: mqtt.ReceiveMessage) -> None:
        pass

    def _update_state(self, msg):
        pass


class OpenMowerSkipAreaButton(OpenMowerMqttButtonEntity):
    async def async_press(self) -> None:
        await mqtt.async_publish(
            self.hass,
            self._mqtt_topic_prefix + "action",
            "mower_logic:mowing/skip_area",
        )


class OpenMowerSkipPathButton(OpenMowerMqttButtonEntity):
    async def async_press(self) -> None:
        await mqtt.async_publish(
            self.hass,
            self._mqtt_topic_prefix + "action",
            "mower_logic:mowing/skip_path",
        )
