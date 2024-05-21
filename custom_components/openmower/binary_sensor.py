from __future__ import annotations

import logging

from homeassistant.components import mqtt
from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorDeviceClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PREFIX, EntityCategory
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
            OpenMowerMqttBinarySensorEntity(
                "Emergency", prefix, "robot_state/json", "emergency"
            ),
            OpenMowerMqttBinarySensorEntity(
                "Is charging", prefix, "robot_state/json", "is_charging"
            ),
        ]
    )


class OpenMowerMqttBinarySensorEntity(OpenMowerMqttEntity, BinarySensorEntity):
    def _process_update(self, value):
        self._attr_is_on = bool(value)
