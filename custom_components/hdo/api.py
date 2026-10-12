"""Minimal Supabase client for hDo (auth + REST on the todos table)."""
from __future__ import annotations

import logging
import time
from typing import Any

import aiohttp

from .const import (
    FIELD_CONTENT,
    FIELD_IS_COMPLETED,
    FIELD_NAME,
    SUPABASE_ANON_KEY,
    SUPABASE_AUTH_REFRESH_URL,
    SUPABASE_AUTH_TOKEN_URL,
    SUPABASE_REST_URL,
)

_LOGGER = logging.getLogger(__name__)


class HdoAuthError(Exception):
    """Raised when login/token refresh fails (bad credentials etc.)."""


class HdoApiError(Exception):
    """Raised for general API / network errors."""


class HdoApiClient:
    """Handles Supabase auth and REST calls for the todos table."""

    def __init__(self, session: aiohttp.ClientSession, email: str, password: str) -> None:
        self._session = session
        self._email = email
        self._password = password

        self._access_token: str | None = None
        self._refresh_token: str | None = None
        self._expires_at: float = 0.0  # epoch seconds

    async def async_login(self) -> None:
        """Log in with email + password via Supabase Auth."""
        headers = {
            "apikey": SUPABASE_ANON_KEY,
            "Content-Type": "application/json",
        }
        payload = {"email": self._email, "password": self._password}

        try:
            async with self._session.post(
                SUPABASE_AUTH_TOKEN_URL, headers=headers, json=payload
            ) as resp:
                data = await resp.json()
                if resp.status != 200 or "access_token" not in data:
                    msg = data.get("error_description") or data.get("msg") or data
                    raise HdoAuthError(f"Login failed: {msg}")
                self._store_tokens(data)
        except aiohttp.ClientError as err:
            raise HdoApiError(f"Network error during login: {err}") from err

    async def _async_refresh(self) -> None:
        """Refresh the access token using the stored refresh token."""
        if not self._refresh_token:
            await self.async_login()
            return

        headers = {
            "apikey": SUPABASE_ANON_KEY,
            "Content-Type": "application/json",
        }
        payload = {"refresh_token": self._refresh_token}

        try:
            async with self._session.post(
                SUPABASE_AUTH_REFRESH_URL, headers=headers, json=payload
            ) as resp:
                data = await resp.json()
                if resp.status != 200 or "access_token" not in data:
                    # Refresh token expired/invalid -> fall back to full login
                    await self.async_login()
                    return
                self._store_tokens(data)
        except aiohttp.ClientError as err:
            raise HdoApiError(f"Network error during token refresh: {err}") from err

    def _store_tokens(self, data: dict[str, Any]) -> None:
        self._access_token = data["access_token"]
        self._refresh_token = data.get("refresh_token", self._refresh_token)
        expires_in = data.get("expires_in", 3600)
        # refresh a bit early (60s buffer)
        self._expires_at = time.time() + int(expires_in) - 60

    async def _async_ensure_token(self) -> None:
        if not self._access_token:
            await self.async_login()
        elif time.time() >= self._expires_at:
            await self._async_refresh()

    def _auth_headers(self) -> dict[str, str]:
        return {
            "apikey": SUPABASE_ANON_KEY,
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
        }

    async def async_get_todos(self) -> list[dict[str, Any]]:
        """Fetch all todos belonging to the logged-in user."""
        await self._async_ensure_token()
        params = {"select": "*", "order": "created_at.desc"}

        try:
            async with self._session.get(
                SUPABASE_REST_URL, headers=self._auth_headers(), params=params
            ) as resp:
                if resp.status == 401:
                    # token might have just expired server-side, retry once
                    await self._async_refresh()
                    async with self._session.get(
                        SUPABASE_REST_URL, headers=self._auth_headers(), params=params
                    ) as retry_resp:
                        retry_resp.raise_for_status()
                        return await retry_resp.json()
                resp.raise_for_status()
                return await resp.json()
        except aiohttp.ClientError as err:
            raise HdoApiError(f"Error fetching todos: {err}") from err

    async def async_add_todo(self, name: str, content: str = "") -> dict[str, Any]:
        """Create a new todo item."""
        await self._async_ensure_token()
        payload = {
            FIELD_NAME: name,
            FIELD_CONTENT: content,
            FIELD_IS_COMPLETED: False,
        }
        headers = self._auth_headers()
        headers["Prefer"] = "return=representation"

        try:
            async with self._session.post(
                SUPABASE_REST_URL, headers=headers, json=payload
            ) as resp:
                resp.raise_for_status()
                result = await resp.json()
                return result[0] if isinstance(result, list) else result
        except aiohttp.ClientError as err:
            raise HdoApiError(f"Error creating todo: {err}") from err

    async def async_update_todo(
        self, todo_id: int, name: str | None = None, is_completed: bool | None = None
    ) -> None:
        """Update an existing todo (name and/or completion state)."""
        await self._async_ensure_token()
        payload: dict[str, Any] = {}
        if name is not None:
            payload[FIELD_NAME] = name
        if is_completed is not None:
            payload[FIELD_IS_COMPLETED] = is_completed
        if not payload:
            return

        headers = self._auth_headers()
        headers["Prefer"] = "return=minimal"
        url = f"{SUPABASE_REST_URL}?id=eq.{todo_id}"

        try:
            async with self._session.patch(url, headers=headers, json=payload) as resp:
                resp.raise_for_status()
        except aiohttp.ClientError as err:
            raise HdoApiError(f"Error updating todo {todo_id}: {err}") from err

    async def async_delete_todo(self, todo_id: int) -> None:
        """Delete a todo item."""
        await self._async_ensure_token()
        headers = self._auth_headers()
        url = f"{SUPABASE_REST_URL}?id=eq.{todo_id}"

        try:
            async with self._session.delete(url, headers=headers) as resp:
                resp.raise_for_status()
        except aiohttp.ClientError as err:
            raise HdoApiError(f"Error deleting todo {todo_id}: {err}") from err
