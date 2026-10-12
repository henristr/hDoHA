"""DataUpdateCoordinator for hDo."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import HdoApiClient, HdoApiError, HdoAuthError
from .const import DOMAIN, UPDATE_INTERVAL_SECONDS

_LOGGER = logging.getLogger(__name__)


class HdoDataUpdateCoordinator(DataUpdateCoordinator[list[dict[str, Any]]]):
    """Coordinates fetching the todo list from Supabase."""

    def __init__(self, hass: HomeAssistant, client: HdoApiClient) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=UPDATE_INTERVAL_SECONDS),
        )
        self.client = client

    async def _async_update_data(self) -> list[dict[str, Any]]:
        try:
            return await self.client.async_get_todos()
        except HdoAuthError as err:
            raise UpdateFailed(f"Authentication failed: {err}") from err
        except HdoApiError as err:
            raise UpdateFailed(f"Error communicating with Supabase: {err}") from err
