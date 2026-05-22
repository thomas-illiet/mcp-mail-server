# Python Client Examples

Examples assume the server is running at `http://localhost:8000/mcp`.

## Simple Text Email

```bash
uv run python - <<'PY'
import asyncio
from fastmcp import Client

async def main():
    async with Client("http://localhost:8000/mcp") as client:
        result = await client.call_tool(
            "send_email",
            {
                "to": ["alice@example.com"],
                "subject": "Test message",
                "text": "Hello Alice, this is a test email.",
            },
        )
        print(result.structured_content)

asyncio.run(main())
PY
```

## Bearer Auth

```bash
uv run python - <<'PY'
import asyncio
from fastmcp import Client
from fastmcp.client.auth.bearer import BearerAuth

async def main():
    async with Client(
        "http://localhost:8000/mcp",
        auth=BearerAuth("change-me"),
    ) as client:
        result = await client.call_tool("test_smtp_connection", {})
        print(result.structured_content)

asyncio.run(main())
PY
```

## HTML Email

```bash
uv run python - <<'PY'
import asyncio
from fastmcp import Client

async def main():
    async with Client("http://localhost:8000/mcp") as client:
        result = await client.call_tool(
            "send_email",
            {
                "to": ["alice@example.com"],
                "subject": "HTML test",
                "text": "Fallback text for clients that do not render HTML.",
                "html": "<h1>Hello Alice</h1><p>This email was sent by MCP.</p>",
            },
        )
        print(result.structured_content)

asyncio.run(main())
PY
```

## CC, BCC, And Reply-To

```bash
uv run python - <<'PY'
import asyncio
from fastmcp import Client

async def main():
    async with Client("http://localhost:8000/mcp") as client:
        result = await client.call_tool(
            "send_email",
            {
                "to": ["alice@example.com"],
                "cc": ["team@example.com"],
                "bcc": ["audit@example.com"],
                "reply_to": "support@example.com",
                "subject": "Visible and hidden recipients",
                "text": "BCC is used only in the SMTP envelope.",
            },
        )
        print(result.structured_content)

asyncio.run(main())
PY
```

## Base64 Attachment

```bash
uv run python - <<'PY'
import asyncio
import base64
from fastmcp import Client

async def main():
    content = base64.b64encode(b"hello from an attachment\n").decode()
    async with Client("http://localhost:8000/mcp") as client:
        result = await client.call_tool(
            "send_email",
            {
                "to": ["alice@example.com"],
                "subject": "Attachment",
                "text": "The file is attached.",
                "attachments": [
                    {
                        "filename": "hello.txt",
                        "content_base64": content,
                        "mime_type": "text/plain",
                    },
                ],
            },
        )
        print(result.structured_content)

asyncio.run(main())
PY
```
