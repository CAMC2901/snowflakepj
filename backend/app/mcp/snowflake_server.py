# Mirror of C:/Users/Camco/mcp/snowflake_server.py for repo versioning
import sys
from pathlib import Path

# Ejecutar el servidor principal
mcp_path = Path("C:/Users/Camco/mcp/snowflake_server.py")
if mcp_path.exists():
    with open(mcp_path, "r", encoding="utf-8") as f:
        code = f.read()
    exec(code)
else:
    print("Servidor MCP no encontrado en C:/Users/Camco/mcp/snowflake_server.py")
