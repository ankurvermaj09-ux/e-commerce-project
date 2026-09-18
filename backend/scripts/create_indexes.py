import asyncio
import sys
from pathlib import Path

# Ensure root directory is in sys.path when running script directly
root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from microservices.common.database import client
from microservices.common.indexes import ensure_indexes

async def main() -> None:
    success = await ensure_indexes(client)
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
