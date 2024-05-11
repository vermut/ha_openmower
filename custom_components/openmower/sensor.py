from __future__ import annotations

import logging

from homeassistant.const import PERCENTAGE, SIGNAL_STRENGTH_DECIBELS, CONF_PREFIX
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import DOMAIN
from homeassistant.components import mqtt
from homeassistant.util.json import json_loads_object

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

    async_add_entities([OpenMowerBatterySensor(entry.data[CONF_PREFIX])])


class OpenMowerBatterySensor(SensorEntity):
    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_native_unit_of_measurement = PERCENTAGE

    _attr_name = "Battery"
    _attr_unique_id = "openmower_battery"
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

        self._attr_native_value = int(float(value_json["battery_percentage"]) * 100)
        self.async_write_ha_state()
