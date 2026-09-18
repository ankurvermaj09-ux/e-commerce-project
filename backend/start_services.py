import subprocess
import sys
import os
import time

script_dir = os.path.dirname(os.path.abspath(__file__))
if sys.platform == "win32":
    venv_python = os.path.join(script_dir, ".venv", "Scripts", "python.exe")
else:
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

print("Starting microservices...")

for name, module, reload_dir, port in services:
    if sys.platform == "win32":
        command = f'title {name} && "{python_exec}" -m uvicorn {module} --reload --reload-dir {reload_dir} --port {port}'
        process = subprocess.Popen(command, shell=True)
    else:
        cmd_args = [
            python_exec, "-m", "uvicorn", module,
            "--reload",
            "--reload-dir", reload_dir,
            "--port", str(port)
        ]
        process = subprocess.Popen(cmd_args)

    processes.append(process)
    print(f"[{name}] started on http://127.0.0.1:{port}")
    time.sleep(0.5)

print("\nAll services started. Press Ctrl+C to stop all.\n")

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\nStopping services...")
    for p in processes:
        p.terminate()
    print("All services stopped.")