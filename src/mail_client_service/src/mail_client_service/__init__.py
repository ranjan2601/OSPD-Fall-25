import mail_client_api

from ._impl import ServiceClient

__all__ = ["ServiceClient", "get_client_impl"]


def get_client_impl(interactive: bool = False, base_url: str = "http://localhost:8000") -> mail_client_api.Client:
    """Get an instance of the ServiceClient.

    Args:
        interactive (bool): Ignored for service client (kept for compatibility).
        base_url (str): Base URL of the mail service API.

    Returns:
        mail_client_api.Client: A ServiceClient instance implementing the
        mail_client_api.Client protocol.

    """
    return ServiceClient(base_url=base_url)


mail_client_api.get_client = get_client_impl
