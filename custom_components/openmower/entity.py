from __future__ import annotations

from datetime import timedelta
from typing import Optional

from homeassistant.components import mqtt
from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity
from homeassistant.util import slugify, Throttle
from homeassistant.util.json import json_loads_object
from .const import DOMAIN

MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=5)


class OpenMowerMqttEntity(Entity):
    _attr_has_entity_name = True

    def __init__(self, name: str, prefix: str, topic: str, key: Optional[str]) -> None:
        self._attr_name = name
        self._attr_unique_id = slugify(f"{prefix}_{name}").lower()

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, slugify(prefix))},
            manufacturer="OpenMower",
            name=slugify(prefix).capitalize(),
        )

        self._mqtt_topic = topic
        self._mqtt_topic_prefix = prefix
        self._mqtt_payload_json_key = key

        if self._mqtt_topic_prefix and self._mqtt_topic_prefix[-1] != "/":
            self._mqtt_topic_prefix = self._mqtt_topic_prefix + "/"

    async def async_added_to_hass(self) -> None:
        await mqtt.async_subscribe(
            self.hass,
            self._mqtt_topic_prefix + self._mqtt_topic,
            self._async_robot_state_received,
            0,
        )

    @callback
    def _async_robot_state_received(self, msg: mqtt.ReceiveMessage) -> None:
        self._update_state(msg)

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def _update_state(self, msg):
        if self._mqtt_payload_json_key:
            value_json = json_loads_object(msg.payload)
            self._process_update(value_json[self._mqtt_payload_json_key])
        else:
            self._process_update(msg.payload)
        self.async_write_ha_state()

    def _process_update(self, value):
        raise NotImplementedError("Subclasses should implement this!")
