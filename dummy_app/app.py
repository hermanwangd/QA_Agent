from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import urlparse


class OrderStore:
    def __init__(self) -> None:
        self._orders: dict[str, dict[str, Any]] = {}
        self._next_id = 1

    def health(self) -> dict[str, str]:
        return {"status": "UP", "service": "dummy-order-app"}

    def create_order(self, payload: dict[str, Any]) -> dict[str, Any]:
        order_id = f"ORD-{self._next_id:04d}"
        self._next_id += 1
        order = {
            "id": order_id,
            "customer_id": payload["customer_id"],
            "sku": payload["sku"],
            "quantity": int(payload["quantity"]),
            "status": "ACCEPTED",
        }
        self._orders[order_id] = order
        return order

    def get_order(self, order_id: str) -> dict[str, Any] | None:
        return self._orders.get(order_id)


def make_handler(store: OrderStore) -> type[BaseHTTPRequestHandler]:
    class DummyOrderHandler(BaseHTTPRequestHandler):
        server_version = "DummyOrderApp/0.1"

        def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
            path = urlparse(self.path).path
            if path == "/health":
                self._write_json(200, store.health())
                return

            if path.startswith("/orders/"):
                order = store.get_order(path.removeprefix("/orders/"))
                if order is None:
                    self._write_json(404, {"error": "order_not_found"})
                    return
                self._write_json(200, order)
                return

            self._write_json(404, {"error": "not_found"})

        def do_POST(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
            path = urlparse(self.path).path
            if path != "/orders":
                self._write_json(404, {"error": "not_found"})
                return

            try:
                payload = self._read_json()
                order = store.create_order(payload)
            except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
                self._write_json(400, {"error": "invalid_order", "detail": str(exc)})
                return

            self._write_json(201, order)

        def log_message(self, format: str, *args: Any) -> None:
            return

        def _read_json(self) -> dict[str, Any]:
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length)
            decoded = json.loads(body.decode("utf-8"))
            if not isinstance(decoded, dict):
                raise TypeError("JSON body must be an object")
            return decoded

        def _write_json(self, status: int, payload: dict[str, Any]) -> None:
            body = json.dumps(payload, sort_keys=True).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    return DummyOrderHandler


def run_server(host: str, port: int) -> None:
    store = OrderStore()
    server = ThreadingHTTPServer((host, port), make_handler(store))
    print(f"dummy-order-app listening on http://{host}:{server.server_port}", flush=True)
    server.serve_forever()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the PI-run dummy order app.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=18080)
    args = parser.parse_args()
    run_server(args.host, args.port)


if __name__ == "__main__":
    main()
