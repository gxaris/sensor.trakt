"""Home Assistant component to feed the Upcoming Media Lovelace card with Trakt user's upcoming TV episodes.

https://github.com/custom-components/sensor.trakt
https://github.com/custom-cards/upcoming-media-card
"""

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ACCESS_TOKEN, CONF_CLIENT_ID, CONF_CLIENT_SECRET
from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse
from homeassistant.helpers import config_entry_oauth2_flow

from .config_flow import TraktOAuth2FlowHandler
from .coordinator import TraktDataUpdateCoordinator
from .oauth_impl import TraktOauth2Implementation

PLATFORMS = ["sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Trakt from config entry."""
    TraktOAuth2FlowHandler.async_register_implementation(
        hass,
        TraktOauth2Implementation(
            hass, entry.data[CONF_CLIENT_ID], entry.data.get(CONF_CLIENT_SECRET, "")
        ),
    )

    implementation = (
        await config_entry_oauth2_flow.async_get_config_entry_implementation(
            hass, entry
        )
    )

    session = config_entry_oauth2_flow.OAuth2Session(hass, entry, implementation)
    await session.async_ensure_token_valid()

    coordinator = TraktDataUpdateCoordinator(hass, session)
    coordinator.initialize()
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator

    async def async_test_token_refresh(call: ServiceCall) -> dict[str, str]:
        """Force an OAuth refresh and return only non-sensitive diagnostics."""
        target_id = call.data.get("entry_id")
        matches = [
            candidate for candidate in hass.config_entries.async_entries("trakt")
            if target_id is None or candidate.entry_id == target_id
        ]
        if len(matches) != 1:
            return {"result": "error", "detail": "Specify entry_id when multiple Trakt entries exist"}
        target = matches[0]
        target_coordinator = target.runtime_data
        oauth_session = target_coordinator.session
        before = oauth_session.token
        try:
            refreshed = await oauth_session.implementation.async_refresh_token(before)
            if not refreshed.get("access_token") or not refreshed.get("refresh_token"):
                return {"result": "error", "detail": "Refresh response missing required token fields"}
            hass.config_entries.async_update_entry(
                target, data={**target.data, "token": refreshed}
            )
            target_coordinator.initialize()
            await target_coordinator.async_request_refresh()
        except Exception as err:
            return {"result": "error", "detail": type(err).__name__}
        return {"result": "success", "detail": "Token refreshed and sensor update requested"}

    if not hass.services.has_service("trakt", "test_token_refresh"):
        hass.services.async_register(
            "trakt", "test_token_refresh", async_test_token_refresh,
            supports_response=SupportsResponse.ONLY,
        )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_update_options))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload Trakt integration."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update options."""
    coordinator: TraktDataUpdateCoordinator = entry.runtime_data
    await coordinator.async_request_refresh()
