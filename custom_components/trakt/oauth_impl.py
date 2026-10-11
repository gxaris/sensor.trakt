"""Local implementation of OAuth2 with PKCE support."""

from homeassistant.core import HomeAssistant
from homeassistant.helpers.config_entry_oauth2_flow import LocalOAuth2ImplementationWithPkce

from .const import DOMAIN, OAUTH2_AUTHORIZE, OAUTH2_TOKEN


class TraktOauth2Implementation(LocalOAuth2ImplementationWithPkce):
    """Local implementation of OAuth2 with PKCE support."""

    def __init__(self, hass: HomeAssistant, client_id: str, client_secret: str = "") -> None:
        """Just init default class with default values."""
        super().__init__(
            hass,
            DOMAIN,
            client_id,
            OAUTH2_AUTHORIZE,
            OAUTH2_TOKEN,
            client_secret=client_secret,
        )

    @property
    def name(self) -> str:
        """Name of the implementation."""
        return "trakt"
