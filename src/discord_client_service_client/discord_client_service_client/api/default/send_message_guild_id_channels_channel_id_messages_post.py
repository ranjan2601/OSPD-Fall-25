from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.operation_response import OperationResponse
from ...models.send_message_request import SendMessageRequest
from ...types import UNSET, Response, Unset


def _get_kwargs(
    guild_id: str,
    channel_id: str,
    *,
    body: SendMessageRequest,
    session_id: None | str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    cookies = {}
    if session_id is not UNSET:
        cookies["session_id"] = session_id

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": f"/{guild_id}/channels/{channel_id}/messages",
        "cookies": cookies,
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | OperationResponse | None:
    if response.status_code == 200:
        response_200 = OperationResponse.from_dict(response.json())

        return response_200

    if response.status_code == 422:
        response_422 = HTTPValidationError.from_dict(response.json())

        return response_422

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[HTTPValidationError | OperationResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    guild_id: str,
    channel_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: SendMessageRequest,
    session_id: None | str | Unset = UNSET,
) -> Response[HTTPValidationError | OperationResponse]:
    """Send message to channel

     Send a message to a Discord channel.

    Args:
        guild_id (str):
        channel_id (str):
        session_id (None | str | Unset):
        body (SendMessageRequest): Request to send a message.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | OperationResponse]
    """

    kwargs = _get_kwargs(
        guild_id=guild_id,
        channel_id=channel_id,
        body=body,
        session_id=session_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    guild_id: str,
    channel_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: SendMessageRequest,
    session_id: None | str | Unset = UNSET,
) -> HTTPValidationError | OperationResponse | None:
    """Send message to channel

     Send a message to a Discord channel.

    Args:
        guild_id (str):
        channel_id (str):
        session_id (None | str | Unset):
        body (SendMessageRequest): Request to send a message.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | OperationResponse
    """

    return sync_detailed(
        guild_id=guild_id,
        channel_id=channel_id,
        client=client,
        body=body,
        session_id=session_id,
    ).parsed


async def asyncio_detailed(
    guild_id: str,
    channel_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: SendMessageRequest,
    session_id: None | str | Unset = UNSET,
) -> Response[HTTPValidationError | OperationResponse]:
    """Send message to channel

     Send a message to a Discord channel.

    Args:
        guild_id (str):
        channel_id (str):
        session_id (None | str | Unset):
        body (SendMessageRequest): Request to send a message.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | OperationResponse]
    """

    kwargs = _get_kwargs(
        guild_id=guild_id,
        channel_id=channel_id,
        body=body,
        session_id=session_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    guild_id: str,
    channel_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: SendMessageRequest,
    session_id: None | str | Unset = UNSET,
) -> HTTPValidationError | OperationResponse | None:
    """Send message to channel

     Send a message to a Discord channel.

    Args:
        guild_id (str):
        channel_id (str):
        session_id (None | str | Unset):
        body (SendMessageRequest): Request to send a message.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | OperationResponse
    """

    return (
        await asyncio_detailed(
            guild_id=guild_id,
            channel_id=channel_id,
            client=client,
            body=body,
            session_id=session_id,
        )
    ).parsed
