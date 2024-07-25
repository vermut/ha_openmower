from __future__ import annotations

import logging
import json

from homeassistant.components import mqtt
from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PREFIX
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .entity import OpenMowerMqttEntity

_LOGGER = logging.getLogger(__name__)

AVAILABILITY_TOPIC = "actions/json"

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
            OpenMowerSkipAreaButton("Skip Area", prefix),
            OpenMowerSkipPathButton("Skip Path", prefix),
            OpenMowerResetEmergencyButton("Reset Emergency", prefix),
            OpenMowerStartAreaRecordingButton("Start Area Recording", prefix),
            OpenMowerStartRecordingButton("Start Recording", prefix),
            OpenMowerStopRecordingButton("Stop Recording", prefix),
            OpenMowerFinishNavigationAreaButton("Finish Navigation Area", prefix),
            OpenMowerFinishMowingAreaButton("Finish Mowing Area", prefix),
            OpenMowerExitRecordingModeButton("Exit Recording Mode", prefix),
            OpenMowerFinishDiscardButton("Discard Recording", prefix),
            OpenMowerRecordDockButton("Record Dock", prefix),
        ]
    )


class OpenMowerMqttButtonEntity(OpenMowerMqttEntity, ButtonEntity):
    def __init__(self, name, prefix, availability_action_id):
        super().__init__(name, prefix, "actions/json", availability_action_id)
        self._availability_action_id = availability_action_id
        self._available = False

    async def async_added_to_hass(self) -> None:
        _LOGGER.debug(f"Subscribing to {AVAILABILITY_TOPIC} for availability")
        await mqtt.async_subscribe(
            self.hass, AVAILABILITY_TOPIC, self._availability_callback, 1
        )

    def _availability_callback(self, msg: mqtt.ReceiveMessage) -> None:
        _LOGGER.debug(f"Received MQTT message on {AVAILABILITY_TOPIC}: {msg.payload}")
        try:
            payload = json.loads(msg.payload)
            _LOGGER.debug(f"Parsed payload: {payload}")
            available = self._check_availability(payload)
            self._available = available
            self.hass.async_add_job(self.async_write_ha_state)
        except json.JSONDecodeError as e:
            _LOGGER.error(f"Failed to decode JSON payload: {msg.payload} - {e}")

    def _check_availability(self, payload) -> bool:
        for action in payload:
            if action["action_id"] == self._availability_action_id:
                _LOGGER.debug(f"Found action_id {self._availability_action_id}: enabled={action['enabled']}")
                return action["enabled"] == 1
        _LOGGER.debug(f"Action_id {self._availability_action_id} not found in payload")
        return False

    @property
    def available(self) -> bool:
        return self._available

    async def async_press(self) -> None:
        await mqtt.async_publish(
            self.hass,
            self._mqtt_topic_prefix + "action",
            self._availability_action_id,
        )


class OpenMowerSkipAreaButton(OpenMowerMqttButtonEntity):
    _attr_icon = "mdi:crop-free"

    def __init__(self, name, prefix):
        super().__init__(name, prefix, "mower_logic:mowing/skip_area")


class OpenMowerSkipPathButton(OpenMowerMqttButtonEntity):
    _attr_icon = "mdi:vector-line"

    def __init__(self, name, prefix):
        super().__init__(name, prefix, "mower_logic:mowing/skip_path")


class OpenMowerResetEmergencyButton(OpenMowerMqttButtonEntity):
    _attr_icon = "mdi:alert-remove-outline"

    def __init__(self, name, prefix):
        super().__init__(name, prefix, "mower_logic/reset_emergency")


class OpenMowerStartAreaRecordingButton(OpenMowerMqttButtonEntity):
    _attr_icon = "mdi:record-circle-outline"

    def __init__(self, name, prefix):
        super().__init__(name, prefix, "mower_logic:idle/start_area_recording")


class OpenMowerStartRecordingButton(OpenMowerMqttButtonEntity):
    _attr_icon = "mdi:record-rec"

    def __init__(self, name, prefix):
        super().__init__(name, prefix, "mower_logic:area_recording/start_recording")


class OpenMowerStopRecordingButton(OpenMowerMqttButtonEntity):
    _attr_icon = "mdi:stop-circle-outline"

    def __init__(self, name, prefix):
        super().__init__(name, prefix, "mower_logic:area_recording/stop_recording")


class OpenMowerFinishNavigationAreaButton(OpenMowerMqttButtonEntity):
    _attr_icon = "mdi:map-marker-path"

    def __init__(self, name, prefix):
        super().__init__(name, prefix, "mower_logic:area_recording/finish_navigation_area")


class OpenMowerFinishMowingAreaButton(OpenMowerMqttButtonEntity):
    _attr_icon = "mdi:grass"

    def __init__(self, name, prefix):
        super().__init__(name, prefix, "mower_logic:area_recording/finish_mowing_area")


class OpenMowerExitRecordingModeButton(OpenMowerMqttButtonEntity):
    _attr_icon = "mdi:exit-to-app"

    def __init__(self, name, prefix):
        super().__init__(name, prefix, "mower_logic:area_recording/exit_recording_mode")


class OpenMowerFinishDiscardButton(OpenMowerMqttButtonEntity):
    _attr_icon = "mdi:delete-outline"

    def __init__(self, name, prefix):
        super().__init__(name, prefix, "mower_logic:area_recording/finish_discard")


class OpenMowerRecordDockButton(OpenMowerMqttButtonEntity):
    _attr_icon = "mdi:dock-top"

    def __init__(self, name, prefix):
        super().__init__(name, prefix, "mower_logic:area_recording/record_dock")
