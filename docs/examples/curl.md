# Curl Example

The Streamable HTTP MCP transport is session-based. With `curl`, initialize the session first, then call the `send_email` tool.

```bash
MCP_URL="http://localhost:8000/mcp"
HEADERS_FILE="$(mktemp)"

curl -sS -D "$HEADERS_FILE" -o /tmp/email-mcp-init.out \
  -X POST "$MCP_URL" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  --data '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
      "protocolVersion": "2024-11-05",
      "capabilities": {},
      "clientInfo": {
        "name": "curl",
        "version": "1.0.0"
      }
    }
  }'

SESSION_ID="$(awk 'tolower($1)=="mcp-session-id:" {print $2}' "$HEADERS_FILE" | tr -d "\r")"

curl -sS -o /dev/null \
  -X POST "$MCP_URL" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  --data '{
    "jsonrpc": "2.0",
    "method": "notifications/initialized",
    "params": {}
  }'

curl -sS -N \
  -X POST "$MCP_URL" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  --data '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/call",
    "params": {
      "name": "send_email",
      "arguments": {
        "to": ["alice@example.com"],
        "subject": "Curl test",
        "text": "Hello from curl through MCP."
      }
    }
  }'
```

If `MCP_BEARER_TOKEN` is enabled, add this header to each `curl` command:

```bash
-H "Authorization: Bearer change-me"
```
