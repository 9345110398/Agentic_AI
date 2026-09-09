"""
HTTP tool for calling external APIs and fetching web resources.
"""

import requests

from tools.registry import tool

MAX_RESPONSE_CHARS = 6000


@tool(
    name="http_request",
    description=(
        "Make an HTTP request to a URL (e.g. to call a REST API) and return "
        "the status code and response body as text. Use this for pulling "
        "data from external services. Response body is truncated if very "
        "large."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "Full URL to request."},
            "method": {
                "type": "string",
                "enum": ["GET", "POST", "PUT", "PATCH", "DELETE"],
                "description": "HTTP method. Defaults to GET.",
            },
            "json_body": {
                "type": "object",
                "description": "Optional JSON body to send with the request.",
            },
            "headers": {
                "type": "object",
                "description": "Optional HTTP headers as key/value pairs.",
            },
        },
        "required": ["url"],
    },
)
def http_request(url: str, method: str = "GET", json_body: dict = None, headers: dict = None) -> str:
    try:
        response = requests.request(
            method.upper(),
            url,
            json=json_body,
            headers=headers or {},
            timeout=15,
        )
    except requests.RequestException as exc:
        return f"Request failed: {exc}"

    body = response.text
    truncated = len(body) > MAX_RESPONSE_CHARS
    body = body[:MAX_RESPONSE_CHARS]

    result = f"Status: {response.status_code}\n\n{body}"
    if truncated:
        result += f"\n\n[...truncated, {len(response.text)} total characters]"
    return result
