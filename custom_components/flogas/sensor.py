"""Sensor platform for Flogas integration."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE, UnitOfVolume
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import FlogasConfigEntry, FlogasDataUpdateCoordinator
from .const import DOMAIN


@dataclass(frozen=True, kw_only=True)
class FlogasSensorEntityDescription(SensorEntityDescription):
    """Describes Flogas sensor entity."""

    value_key: str
    attributes_fn: Callable[[dict[str, Any]], dict[str, Any]] | None = None


SENSOR_TYPES: tuple[FlogasSensorEntityDescription, ...] = (
    FlogasSensorEntityDescription(
        key="tank_level",
        name="Tank Level",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:propane-tank",
        value_key="remaining_percentage",
        attributes_fn=lambda data: {
            "source": data.get("source"),
            "last_reading_date": data.get("last_reading_date"),
            "tank_capacity_litres": data.get("tank_capacity"),
            # Daily telemetry readings, oldest first, for history graphs
            "history": data.get("history"),
        },
    ),
    FlogasSensorEntityDescription(
        key="remaining_litres",
        name="Gas Remaining",
        native_unit_of_measurement=UnitOfVolume.LITERS,
        device_class=SensorDeviceClass.VOLUME_STORAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:propane-tank",
        value_key="remaining_litres",
    ),
    FlogasSensorEntityDescription(
        key="days_remaining",
        name="Days Remaining",
        native_unit_of_measurement="days",
        icon="mdi:calendar-clock",
        state_class=SensorStateClass.MEASUREMENT,
        value_key="days_remaining",
    ),
    FlogasSensorEntityDescription(
        key="daily_usage",
        name="Daily Usage",
        native_unit_of_measurement="L/day",
        icon="mdi:fire",
        state_class=SensorStateClass.MEASUREMENT,
        value_key="daily_usage_litres",
        attributes_fn=lambda data: {
            "percentage_per_day": data.get("daily_usage_percentage"),
        },
    ),
    FlogasSensorEntityDescription(
        key="usage_this_week",
        name="Usage This Week",
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:chart-bar",
        state_class=SensorStateClass.MEASUREMENT,
        value_key="usage_this_week",
    ),
    FlogasSensorEntityDescription(
        key="usage_last_week",
        name="Usage Last Week",
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:chart-bar",
        state_class=SensorStateClass.MEASUREMENT,
        value_key="usage_last_week",
    ),
    FlogasSensorEntityDescription(
        key="next_order_date",
        name="Next Order Date",
        device_class=SensorDeviceClass.DATE,
        icon="mdi:truck-delivery",
        value_key="next_order_date",
        attributes_fn=lambda data: {
            "order_threshold_percentage": data.get("order_threshold"),
            "has_order": data.get("has_order"),
            "next_delivery_date": data.get("next_delivery_date"),
        },
    ),
    FlogasSensorEntityDescription(
        key="tank_capacity",
        name="Tank Capacity",
        native_unit_of_measurement=UnitOfVolume.LITERS,
        device_class=SensorDeviceClass.VOLUME_STORAGE,
        icon="mdi:propane-tank-outline",
        value_key="tank_capacity",
    ),
    FlogasSensorEntityDescription(
        key="last_reading_date",
        name="Last Reading Date",
        device_class=SensorDeviceClass.DATE,
        icon="mdi:calendar",
        value_key="last_reading_date",
    ),
    FlogasSensorEntityDescription(
        key="account_balance",
        name="Account Balance",
        native_unit_of_measurement="GBP",
        device_class=SensorDeviceClass.MONETARY,
        icon="mdi:currency-gbp",
        value_key="balance",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: FlogasConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Flogas sensors based on a config entry."""
    coordinator = entry.runtime_data
    async_add_entities(
        FlogasSensor(coordinator, description, entry.entry_id)
        for description in SENSOR_TYPES
    )


class FlogasSensor(CoordinatorEntity[FlogasDataUpdateCoordinator], SensorEntity):
    """Representation of a Flogas sensor."""

    entity_description: FlogasSensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: FlogasDataUpdateCoordinator,
        description: FlogasSensorEntityDescription,
        entry_id: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name="Flogas Tank",
            manufacturer="Flogas",
        )

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get(self.entity_description.value_key)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return additional state attributes."""
        if self.entity_description.attributes_fn is None or self.coordinator.data is None:
            return None
        return self.entity_description.attributes_fn(self.coordinator.data)
