# MCP Server Troubleshooting

## Issue
The Pylance MCP server is not responding:
```
Error sending message to http://localhost:5419/stream: TypeError: fetch failed
```

## ✅ Resolution Steps (User Action Required)

### Step 1: Reload VS Code Window
1. Press `Cmd+Shift+P` (macOS) or `Ctrl+Shift+P` (Windows/Linux)
2. Type "Developer: Reload Window"
3. Press Enter

This will restart all VS Code extensions including Pylance and its MCP server.

### Step 2: Verify Python Extension
1. Press `Cmd+Shift+X` to open Extensions
2. Search for "Python"
3. Ensure "Python" by Microsoft is installed and enabled
4. Search for "Pylance"
5. Ensure "Pylance" by Microsoft is installed and enabled

### Step 3: Check Python Interpreter
1. Press `Cmd+Shift+P`
2. Type "Python: Select Interpreter"
3. Choose `.venv/bin/python` (should be at the top)

### Step 4: Restart VS Code Completely
If the above doesn't work:
1. Close VS Code completely (Cmd+Q on macOS)
2. Reopen VS Code
3. Open the kibray workspace folder

### Step 5: Check MCP Server Status
After reloading, verify the server is running:
```bash
lsof -i :5419
```

You should see output like:
```
COMMAND   PID  USER   FD   TYPE DEVICE SIZE/OFF NODE NAME
node    12345  user   23u  IPv4 ...           TCP localhost:5419 (LISTEN)
```

## Configuration Applied

The following VS Code settings have been configured in `.vscode/settings.json`:

- **Python Interpreter**: Set to `.venv/bin/python`
- **Type Checking**: Disabled (typeCheckingMode: "off")
- **Format on Save**: Enabled with Python formatter
- **Pytest**: Enabled as default test runner
- **Auto Import**: Enabled
- **Code Actions**: Organize imports on save

## Testing Without MCP

While the MCP server is being resolved, all Python development features work normally:

### Available Tools
```bash
# Run tests
pytest

# Run with coverage
pytest --cov=. --cov-report=term-missing

# Lint code
ruff check .

# Auto-fix linting issues
ruff check . --fix

# Format code
black .
```

### VS Code Tasks
All quality tools are available via VS Code tasks:
- `Cmd+Shift+P` → "Tasks: Run Task"
  - Run tests with coverage
  - Lint with ruff
  - Lint and fix with ruff
  - Format with black

## What is MCP?

The Model Context Protocol (MCP) is an optional feature that provides:
- Enhanced code analysis
- Better type inference
- Improved auto-completion

**Important**: MCP is NOT required for development. All core functionality (testing, linting, formatting, debugging) works without it.

## Current Status

- ✅ VS Code settings configured
- ✅ Python interpreter selected (.venv/bin/python)
- ✅ Pytest enabled as test runner
- ✅ Black/Ruff integration configured
- ⏳ MCP server needs VS Code reload (user action)

## Expected Outcome

After completing Steps 1-4 above, the MCP server should automatically start when VS Code reloads. The server runs on port 5419 and provides enhanced Python language features.

## If Issue Persists

If the MCP server still doesn't start after reloading:

1. **Check Pylance Extension Logs**
   - View → Output → Select "Pylance" from dropdown
   - Look for errors related to MCP server startup

2. **Reinstall Pylance**
   - Extensions → Pylance → Uninstall
   - Restart VS Code
   - Reinstall Pylance from Extensions

3. **Check Firewall**
   - Ensure port 5419 is not blocked by firewall
   - Add exception if needed

4. **Use Alternative**
   - Continue development without MCP
   - All features work normally via command line tools

## Summary

**Action Required**: Reload VS Code window (`Cmd+Shift+P` → "Developer: Reload Window")

**Impact**: None on development - all tools operational via command line

**Status**: Configuration complete, waiting for VS Code reload to activate MCP server
