from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_openapi_schema_openapi_json_get_response_get_openapi_schema_openapi_json_get import (
    GetOpenapiSchemaOpenapiJsonGetResponseGetOpenapiSchemaOpenapiJsonGet,
)
from ...types import Response


def _get_kwargs() -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/openapi.json",
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> GetOpenapiSchemaOpenapiJsonGetResponseGetOpenapiSchemaOpenapiJsonGet | None:
    if response.status_code == 200:
        response_200 = GetOpenapiSchemaOpenapiJsonGetResponseGetOpenapiSchemaOpenapiJsonGet.from_dict(response.json())

        return response_200

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[GetOpenapiSchemaOpenapiJsonGetResponseGetOpenapiSchemaOpenapiJsonGet]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
) -> Response[GetOpenapiSchemaOpenapiJsonGetResponseGetOpenapiSchemaOpenapiJsonGet]:
    """Get Openapi Schema

     Serve the OpenAPI schema.

    Returns:
        The OpenAPI schema as a dictionary.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GetOpenapiSchemaOpenapiJsonGetResponseGetOpenapiSchemaOpenapiJsonGet]
    """

    kwargs = _get_kwargs()

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
) -> GetOpenapiSchemaOpenapiJsonGetResponseGetOpenapiSchemaOpenapiJsonGet | None:
    """Get Openapi Schema

     Serve the OpenAPI schema.

    Returns:
        The OpenAPI schema as a dictionary.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GetOpenapiSchemaOpenapiJsonGetResponseGetOpenapiSchemaOpenapiJsonGet
    """

    return sync_detailed(
        client=client,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
) -> Response[GetOpenapiSchemaOpenapiJsonGetResponseGetOpenapiSchemaOpenapiJsonGet]:
    """Get Openapi Schema

     Serve the OpenAPI schema.

    Returns:
        The OpenAPI schema as a dictionary.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GetOpenapiSchemaOpenapiJsonGetResponseGetOpenapiSchemaOpenapiJsonGet]
    """

    kwargs = _get_kwargs()

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
) -> GetOpenapiSchemaOpenapiJsonGetResponseGetOpenapiSchemaOpenapiJsonGet | None:
    """Get Openapi Schema

     Serve the OpenAPI schema.

    Returns:
        The OpenAPI schema as a dictionary.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GetOpenapiSchemaOpenapiJsonGetResponseGetOpenapiSchemaOpenapiJsonGet
    """

    return (
        await asyncio_detailed(
            client=client,
        )
    ).parsed
