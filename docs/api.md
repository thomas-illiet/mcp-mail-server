# MCP API

The server exposes two MCP tools:

- `send_email`
- `test_smtp_connection`

## `send_email`

Sends an email through the configured SMTP server, or validates it without SMTP delivery when mock mode is enabled.

Parameters:

- `to: list[str]`
- `subject: str`
- `text: str`
- `html: str | None`
- `cc: list[str] | None`
- `bcc: list[str] | None`
- `reply_to: str | None`
- `attachments: list[{ filename, content_base64, mime_type? }] | None`

Attachment payload:

```json
{
  "to": ["user@example.com"],
  "subject": "Report",
  "text": "See attached.",
  "attachments": [
    {
      "filename": "report.txt",
      "content_base64": "SGVsbG8K",
      "mime_type": "text/plain"
    }
  ]
}
```

Response:

```json
{
  "ok": true,
  "message_id": "<...>",
  "accepted_recipients": ["user@example.com"]
}
```

`bcc` recipients are part of the SMTP envelope but are never added to visible MIME headers.

## `test_smtp_connection`

Tests the configured SMTP connection without sending an email. Mock mode does not short-circuit this tool.

Response:

```json
{
  "ok": true,
  "smtp_host": "maildev",
  "smtp_port": 1025,
  "smtp_use_tls": false,
  "smtp_use_ssl": false,
  "authenticated": false,
  "error_type": null,
  "error": null
}
```

The `/health` endpoint runs the same SMTP connectivity check.
