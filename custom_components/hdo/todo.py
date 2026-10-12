"""Todo platform for hDo."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.todo import (
    TodoItem,
    TodoItemStatus,
    TodoListEntity,
    TodoListEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    FIELD_CONTENT,
    FIELD_ID,
    FIELD_IS_COMPLETED,
    FIELD_NAME,
)
from .coordinator import HdoDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the hDo todo entity."""
    coordinator: HdoDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([HdoTodoListEntity(coordinator, entry)])


class HdoTodoListEntity(CoordinatorEntity[HdoDataUpdateCoordinator], TodoListEntity):
    """A todo list entity backed by the Supabase 'todos' table."""

    _attr_has_entity_name = True
    _attr_name = "hDo"
    _attr_icon = "mdi:check-circle-outline"
    _attr_supported_features = (
        TodoListEntityFeature.CREATE_TODO_ITEM
        | TodoListEntityFeature.UPDATE_TODO_ITEM
        | TodoListEntityFeature.DELETE_TODO_ITEM
    )

    def __init__(self, coordinator: HdoDataUpdateCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_todo"

    @property
    def todo_items(self) -> list[TodoItem]:
        items = self.coordinator.data or []
        result: list[TodoItem] = []
        for item in items:
            status = (
                TodoItemStatus.COMPLETED
                if item.get(FIELD_IS_COMPLETED)
                else TodoItemStatus.NEEDS_ACTION
            )
            result.append(
                TodoItem(
                    uid=str(item[FIELD_ID]),
                    summary=item.get(FIELD_NAME, ""),
                    status=status,
                    description=item.get(FIELD_CONTENT),
                )
            )
        return result

    async def async_create_todo_item(self, item: TodoItem) -> None:
        await self.coordinator.client.async_add_todo(
            name=item.summary or "", content=item.description or ""
        )
        await self.coordinator.async_request_refresh()

    async def async_update_todo_item(self, item: TodoItem) -> None:
        is_completed = item.status == TodoItemStatus.COMPLETED
        await self.coordinator.client.async_update_todo(
            todo_id=int(item.uid),
            name=item.summary,
            is_completed=is_completed,
        )
        await self.coordinator.async_request_refresh()

    async def async_delete_todo_items(self, uids: list[str]) -> None:
        for uid in uids:
            await self.coordinator.client.async_delete_todo(int(uid))
        await self.coordinator.async_request_refresh()
