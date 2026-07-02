from __future__ import annotations

from collections.abc import Callable
from datetime import timedelta
from typing import Optional, Union

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

    def __init__(
        self,
        name: str,
        prefix: str,
        topic: Union[str, list[str]],
        key: Optional[str],
    ) -> None:
        self._attr_name = name
        self._attr_unique_id = slugify(f"{prefix}_{name}").lower()

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, slugify(prefix))},
            manufacturer="OpenMower",
            name=slugify(prefix).capitalize(),
        )

        self._mqtt_topics = [topic] if isinstance(topic, str) else list(topic)
        self._mqtt_topic_prefix = prefix
        self._mqtt_payload_json_key = key
        self._unsub_mqtt: list[Callable] = []

        if self._mqtt_topic_prefix and self._mqtt_topic_prefix[-1] != "/":
            self._mqtt_topic_prefix = self._mqtt_topic_prefix + "/"

    async def async_added_to_hass(self) -> None:
        for topic in self._mqtt_topics:
            self._unsub_mqtt.append(
                await mqtt.async_subscribe(
                    self.hass,
                    self._mqtt_topic_prefix + topic,
                    self._async_robot_state_received,
                    0,
                )
            )

    async def async_will_remove_from_hass(self) -> None:
        for unsub in self._unsub_mqtt:
            unsub()
        self._unsub_mqtt.clear()

    @callback
    def _async_robot_state_received(self, msg: mqtt.ReceiveMessage) -> None:
        self._update_state(msg)

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def _update_state(self, msg):
        if self._mqtt_payload_json_key:
            value_json = json_loads_object(msg.payload)
            if self._mqtt_payload_json_key not in value_json:
                self._attr_available = False
                self.async_write_ha_state()
                return

            self._attr_available = True
            self._process_update(value_json[self._mqtt_payload_json_key])
        else:
            self._attr_available = True
            self._process_update(msg.payload)
        self.async_write_ha_state()

    def _process_update(self, value):
        raise NotImplementedError("Subclasses should implement this!")
