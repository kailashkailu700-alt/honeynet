"""A small, deliberately fake network honeypot for a controlled lab/demo."""
import http.server
import socket
import threading
import time

import requests

# Point this to your deployed backend before starting the agent.
API_URL = "https://honeynet-api.onrender.com"# ⚠️ CHANGE THIS TO YOUR RENDER URL
NODE_ID = "node-001"
NODE_NAME = "Laptop Honeypot"


class Honeypot:
    def __init__(self, api_url=API_URL, node_id=NODE_ID, node_name=NODE_NAME):
        self.api_url = api_url.rstrip("/")
        self.node_id = node_id
        self.node_name = node_name

    def report_online(self):
        """Tell the backend that this sensor has started."""
        try:
            response = requests.post(
                f"{self.api_url}/api/register",
                json={"node_id": self.node_id, "name": self.node_name},
                timeout=5,
            )
            response.raise_for_status()
            print(f"Registered honeypot node {self.node_id}")
        except requests.RequestException as error:
            print(f"Could not register honeypot node: {error}")

    def report_attack(self, ip, service, port, payload):
        """Forward a captured connection without allowing API errors to stop listening."""
        try:
            response = requests.post(
                f"{self.api_url}/api/attack",
                json={"attacker_ip": ip, "service": service, "port": port, "payload": payload},
                timeout=5,
            )
            response.raise_for_status()
            print(f"🚨 Reported {service} activity from {ip}:{port}")
        except Exception as error:
            print(f"Could not report {service} activity from {ip}: {error}")

    @staticmethod
    def _listen_socket(port):
        """Create a reusable TCP listener on all interfaces for a lab sensor."""
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(("0.0.0.0", port))
        server.listen(20)
        return server

    def ssh_honeypot(self, port=2222):
        """Accept SSH-like TCP connections and record the first client bytes."""
        server = self._listen_socket(port)
        print(f"SSH honeypot listening on port {port}")
        while True:
            client, address = server.accept()
            with client:
                try:
                    client.settimeout(3)
                    client.sendall(b"SSH-2.0-OpenSSH_8.2p1 Ubuntu\r\n")
                    try:
                        data = client.recv(4096)
                        payload = data.decode("utf-8", errors="replace") if data else "connection attempt"
                    except socket.timeout:
                        payload = "connection attempt"
                    self.report_attack(address[0], "ssh", port, payload[:10000])
                except OSError as error:
                    print(f"SSH connection handling failed: {error}")

    def http_honeypot(self, port=8080):
        """Serve a fake router page and record submitted form data."""
        honeypot = self

        class Handler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                page = ("<!doctype html><html><head><meta charset='utf-8'><title>Router Admin</title>"
                        "</head><body><h1>Router Administration</h1>"
                        "<form method='post' action='/admin'>"
                        "<label>Username <input name='username'></label>"
                        "<label>Password <input name='password' type='password'></label>"
                        "<button type='submit'>Log in</button></form></body></html>")
                body = page.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_POST(self):
                length = min(int(self.headers.get("Content-Length", "0")), 10000)
                body = self.rfile.read(length).decode("utf-8", errors="replace")
                honeypot.report_attack(self.client_address[0], "http", port,
                                       f"{self.path} {body}"[:10000])
                self.send_response(401)
                self.send_header("Content-Length", "0")
                self.end_headers()

            def log_message(self, fmt, *args):
                pass

        server = http.server.ThreadingHTTPServer(("0.0.0.0", port), Handler)
        server.daemon_threads = True
        print(f"HTTP honeypot listening on port {port}")
        server.serve_forever()

    def ftp_honeypot(self, port=2121):
        """Accept FTP-like TCP connections and record the first client bytes."""
        server = self._listen_socket(port)
        print(f"FTP honeypot listening on port {port}")
        while True:
            client, address = server.accept()
            with client:
                try:
                    client.settimeout(5)
                    client.sendall(b"220 FTP Server Ready\r\n")
                    try:
                        data = client.recv(4096)
                        payload = data.decode("utf-8", errors="replace") if data else "connection attempt"
                    except socket.timeout:
                        payload = "connection attempt"
                    self.report_attack(address[0], "ftp", port, payload[:10000])
                except OSError as error:
                    print(f"FTP connection handling failed: {error}")


def main():
    honeypot = Honeypot()
    honeypot.report_online()
    services = (
        ("SSH", honeypot.ssh_honeypot, 2222),
        ("HTTP", honeypot.http_honeypot, 8080),
        ("FTP", honeypot.ftp_honeypot, 2121),
    )
    for name, target, port in services:
        thread = threading.Thread(target=target, kwargs={"port": port}, name=f"{name}-honeypot", daemon=True)
        thread.start()
    print("\n🍯 HoneyNet sensor is running")
    print("SSH: 2222 | HTTP: 8080 | FTP: 2121")
    print("Expose these ports only on a controlled, authorized network. Press Ctrl+C to stop.\n")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping HoneyNet sensor. Goodbye!")


if __name__ == '__main__':
    main()
