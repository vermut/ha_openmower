from __future__ import annotations

import logging

from homeassistant.components import mqtt
from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
    SensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    CONF_PREFIX,
    EntityCategory,
    UnitOfTemperature,
    UnitOfElectricPotential,
    UnitOfElectricCurrent,
    UnitOfLength,
)
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
            OpenMowerBatterySensor(
                "Battery", prefix, "robot_state/json", "battery_percentage"
            ),
            OpenMowerDisabledSensor(
                "Current action progress",
                prefix,
                "robot_state/json",
                "current_action_progress",
            ),
            OpenMowerGpsPercentageSensor(
                "GPS Percentage", prefix, "robot_state/json", "gps_percentage"
            ),
            OpenMowerCurrentStateEntity(
                "Current State", prefix, "robot_state/json", "current_state"
            ),
            OpenMowerCurrentSensor(
                "Charge Current", prefix, "sensors/om_charge_current/data", None
            ),
            OpenMowerGpsAccuracySensor(
                "GPS Accuracy", prefix, "sensors/om_gps_accuracy/data", None
            ),
            OpenMowerTemperatureSensor(
                "Left ESC Temperature", prefix, "sensors/om_left_esc_temp/data", None
            ),
            OpenMowerTemperatureSensor(
                "Mow ESC Temperature", prefix, "sensors/om_mow_esc_temp/data", None
            ),
            OpenMowerCurrentSensor(
                "Mow Motor Current", prefix, "sensors/om_mow_motor_current/data", None
            ),
            OpenMowerTemperatureSensor(
                "Mow Motor Temperature", prefix, "sensors/om_mow_motor_temp/data", None
            ),
            OpenMowerTemperatureSensor(
                "Right ESC Temperature", prefix, "sensors/om_right_esc_temp/data", None
            ),
            OpenMowerVoltageSensor(
                "Battery Voltage", prefix, "sensors/om_v_battery/data", None
            ),
            OpenMowerVoltageSensor(
                "Charge Voltage", prefix, "sensors/om_v_charge/data", None
            ),
        ]
    )


class OpenMowerMqttSensorEntity(OpenMowerMqttEntity, SensorEntity):
    def _process_update(self, value):
        self._attr_native_value = value


class OpenMowerCurrentStateEntity(OpenMowerMqttSensorEntity):
    _attr_icon = "mdi:robot-mower"


class OpenMowerBatterySensor(OpenMowerMqttSensorEntity):
    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT

    def _process_update(self, value):
        self._attr_native_value = int(float(value) * 100)


class OpenMowerGpsPercentageSensor(OpenMowerMqttSensorEntity):
    _attr_icon = "mdi:crosshairs-gps"
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT

    def _process_update(self, value):
        self._attr_native_value = int(float(value) * 100)


class OpenMowerDisabledSensor(OpenMowerMqttSensorEntity):
    entity_description = SensorEntityDescription(
        key="currentStateProgress",
        entity_registry_enabled_default=False,
        entity_category=EntityCategory.DIAGNOSTIC,
    )


class OpenMowerRawDiagnosticSensor(OpenMowerMqttSensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_state_class = SensorStateClass.MEASUREMENT

    def _process_update(self, value):
        self._attr_native_value = float(value)


class OpenMowerCurrentSensor(OpenMowerRawDiagnosticSensor):
    _attr_device_class = SensorDeviceClass.CURRENT
    _attr_native_unit_of_measurement = UnitOfElectricCurrent.AMPERE
    _attr_suggested_display_precision = 1


class OpenMowerTemperatureSensor(OpenMowerRawDiagnosticSensor):
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_suggested_display_precision = 0


class OpenMowerVoltageSensor(OpenMowerRawDiagnosticSensor):
    _attr_device_class = SensorDeviceClass.VOLTAGE
    _attr_native_unit_of_measurement = UnitOfElectricPotential.VOLT
    _attr_suggested_display_precision = 1


class OpenMowerGpsAccuracySensor(OpenMowerRawDiagnosticSensor):
    _attr_device_class = SensorDeviceClass.DISTANCE
    _attr_native_unit_of_measurement = UnitOfLength.METERS
    _attr_suggested_display_precision = 4

    def _process_update(self, value):
        super()._process_update(value)
        if self._attr_native_value == 999:
            self._attr_native_value = None
