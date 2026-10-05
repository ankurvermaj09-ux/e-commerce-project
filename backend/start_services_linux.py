import subprocess
import sys
import os
import time

script_dir = os.path.dirname(os.path.abspath(__file__))
venv_python = os.path.join(script_dir, ".venv", "bin", "python")
python_exec = venv_python if os.path.exists(venv_python) else sys.executable

services = [
    ("AUTH", "microservices.auth_service.main:app", "microservices/auth_service", 8001),
    ("PRODUCT", "microservices.product_service.main:app", "microservices/product_service", 8002),
    ("CART", "microservices.cart_service.main:app", "microservices/cart_service", 8003),
    ("ORDER", "microservices.order_service.main:app", "microservices/order_service", 8004),
    ("ADMIN", "microservices.admin_service.main:app", "microservices/admin_service", 8005),
    ("REVIEW", "microservices.review_service.main:app", "microservices/review_service", 8006),
    ("WISHLIST", "microservices.wishlist_service.main:app", "microservices/wishlist_service", 8007),
    ("TICKET", "microservices.ticket_service.main:app", "microservices/ticket_service", 8008),
    ("GATEWAY", "microservices.gateway.main:app", "microservices/gateway", 8000),
]

processes = []

print("Starting all microservices for Linux...\n")

env = {**os.environ, "PYTHONPATH": script_dir}

host = os.getenv("HOST", "0.0.0.0")

for name, module, reload_dir, port in services:
    service_cwd = os.path.join(script_dir, reload_dir)
    cmd = [
        python_exec, "-m", "uvicorn", module,
        "--host", host,
        "--reload",
        "--reload-dir", service_cwd,
        "--port", str(port)
    ]
    process = subprocess.Popen(cmd, cwd=service_cwd, env=env)
    processes.append(process)
    print(f"[{name}] service running on http://{host}:{port}")
    time.sleep(0.5)

print(f"\nAll {len(services)} services started successfully! Press Ctrl+C to terminate all services.\n")

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\nShutting down all services...")
    for p in processes:
        p.terminate()
    print("All services stopped.")
