# MCP Server Troubleshooting

## Issue
The Pylance MCP server is not responding:
```
Error sending message to http://localhost:5419/stream: TypeError: fetch failed
```

## Root Cause
The MCP (Model Context Protocol) server requires the Pylance extension to be running in VS Code with the MCP server enabled. The server should be listening on `localhost:5419`.

## Troubleshooting Steps

1. **Verify Pylance Extension**
   - Check if the Pylance extension is installed and enabled in VS Code
   - Extension ID: `ms-python.vscode-pylance`

2. **Check MCP Server Status**
   - Open VS Code Command Palette (Cmd+Shift+P)
   - Look for "Pylance: Restart Server" or similar commands
   - Check VS Code output panel for Pylance logs

3. **Verify Port Availability**
   ```bash
   lsof -i :5419
   ```
   If nothing is listening, the MCP server process isn't running.

4. **Restart VS Code**
   - Close and reopen VS Code completely
   - The MCP server should start automatically if properly configured

5. **Check VS Code Settings**
   Create/edit `.vscode/settings.json`:
   ```json
   {
     "python.analysis.mcpEnabled": true,
     "python.analysis.mcpPort": 5419
   }
   ```

## Alternative: Use Direct Python Tools
If MCP server cannot be started, all Python analysis can still be done using:
- `pytest` for testing
- `ruff` for linting
- `black` for formatting
- `mypy` for type checking (optional)

## Status
- **Current State**: MCP server not responding
- **Impact**: Cannot use MCP-specific tools (pylanceRunCodeSnippet, pylanceSyntaxErrors, etc.)
- **Workaround**: Using standard Python tools (pytest, ruff, black) successfully
- **Action Required**: Manual VS Code/Pylance configuration by user

## Resolution Notes
The user should:
1. Verify Pylance extension is up to date
2. Check for any Pylance errors in VS Code
3. Restart VS Code to reinitialize the MCP server
4. Confirm port 5419 is not blocked by firewall

If the issue persists, the MCP features are optional - all core functionality works without them.
