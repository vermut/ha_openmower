from __future__ import annotations

import logging
import math

from homeassistant.components import mqtt
from homeassistant.components.device_tracker import TrackerEntity, SourceType
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PREFIX, CONF_LATITUDE, CONF_LONGITUDE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .entity import OpenMowerMqttEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    if not await mqtt.async_wait_for_mqtt_client(hass):
        _LOGGER.info("Datum not defined, not adding tracker")
        return

    # Make sure MQTT integration is enabled and the client is available
    if not (entry.data[CONF_LATITUDE] and entry.data[CONF_LONGITUDE]):
        _LOGGER.error("MQTT integration is not available")
        return

    async_add_entities(
        (
            OpenMowerPosition(
                entry.data[CONF_PREFIX],
                entry.data[CONF_LATITUDE],
                entry.data[CONF_LONGITUDE],
            ),
        )
    )


class OpenMowerPosition(OpenMowerMqttEntity, TrackerEntity):
    # Constants
    _EARTH = 6371008.8
    _M = 1 / ((2 * math.pi / 360) * 6371008.8)

    def __init__(self, prefix: str, datum_lat: float, datum_lon: float) -> None:
        super().__init__("Position", prefix, "robot_state/json", "pose")

        self._datum_lat = datum_lat
        self._datum_lon = datum_lon

        # Init with datum
        self._attr_longitude = datum_lon
        self._attr_latitude = datum_lat

    def _process_update(self, value):
        # https://stackoverflow.com/a/50506609
        # https://github.com/Turfjs/turf/issues/635#issuecomment-292011500

        # Calculate new latitude and longitude
        self._attr_latitude = self._datum_lat + (value["y"] * self._M)
        self._attr_longitude = self._datum_lon + (value["x"] * self._M) / math.cos(
            self._datum_lat * (math.pi / 180)
        )

    @property
    def latitude(self) -> float | None:
        return self._attr_latitude

    @property
    def longitude(self) -> float | None:
        return self._attr_longitude

    @property
    def source_type(self) -> SourceType | str:
        return SourceType.GPS
