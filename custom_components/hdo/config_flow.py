"""Config flow for hDo (email + password login against Supabase Auth)."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import HdoApiClient, HdoApiError, HdoAuthError
from .const import CONF_EMAIL, CONF_PASSWORD, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_EMAIL): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


class HdoConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for hDo."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            email = user_input[CONF_EMAIL]
            password = user_input[CONF_PASSWORD]

            await self.async_set_unique_id(email.lower())
            self._abort_if_unique_id_configured()

            session = async_get_clientsession(self.hass)
            client = HdoApiClient(session, email, password)

            try:
                await client.async_login()
            except HdoAuthError:
                errors["base"] = "invalid_auth"
            except HdoApiError:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Unexpected error during hDo login")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title=email, data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )
