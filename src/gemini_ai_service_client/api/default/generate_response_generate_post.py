from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.generate_response_request import GenerateResponseRequest
from ...models.generate_response_response import GenerateResponseResponse
from ...models.http_validation_error import HTTPValidationError
from typing import cast


def _get_kwargs(
    *,
    body: GenerateResponseRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/generate",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> GenerateResponseResponse | HTTPValidationError | None:
    if response.status_code == 200:
        response_200 = GenerateResponseResponse.from_dict(response.json())

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
) -> Response[GenerateResponseResponse | HTTPValidationError]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: GenerateResponseRequest,
) -> Response[GenerateResponseResponse | HTTPValidationError]:
    """Generate Response

     Generate a response from the AI with optional structured output.

    Supports:
    - Conversational mode: user_input + system_prompt, no schema
    - Structured output mode: user_input + system_prompt + response_schema

    Args:
        body (GenerateResponseRequest): Request model for generating a response from the AI.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GenerateResponseResponse | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    body: GenerateResponseRequest,
) -> GenerateResponseResponse | HTTPValidationError | None:
    """Generate Response

     Generate a response from the AI with optional structured output.

    Supports:
    - Conversational mode: user_input + system_prompt, no schema
    - Structured output mode: user_input + system_prompt + response_schema

    Args:
        body (GenerateResponseRequest): Request model for generating a response from the AI.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GenerateResponseResponse | HTTPValidationError
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: GenerateResponseRequest,
) -> Response[GenerateResponseResponse | HTTPValidationError]:
    """Generate Response

     Generate a response from the AI with optional structured output.

    Supports:
    - Conversational mode: user_input + system_prompt, no schema
    - Structured output mode: user_input + system_prompt + response_schema

    Args:
        body (GenerateResponseRequest): Request model for generating a response from the AI.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GenerateResponseResponse | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: GenerateResponseRequest,
) -> GenerateResponseResponse | HTTPValidationError | None:
    """Generate Response

     Generate a response from the AI with optional structured output.

    Supports:
    - Conversational mode: user_input + system_prompt, no schema
    - Structured output mode: user_input + system_prompt + response_schema

    Args:
        body (GenerateResponseRequest): Request model for generating a response from the AI.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GenerateResponseResponse | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
