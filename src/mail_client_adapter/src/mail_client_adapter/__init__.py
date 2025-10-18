"""Mail Client Adapter - HTTP service adapter implementing mail_client_api.Client.

This adapter provides a concrete implementation of the mail_client_api.Client protocol
that communicates with the Mail Client Service over HTTP.
"""

from ._impl import ServiceClient, ServiceMessage

__all__ = ["ServiceClient", "ServiceMessage"]
