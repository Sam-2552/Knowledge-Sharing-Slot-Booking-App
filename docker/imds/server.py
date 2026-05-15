"""Minimal AWS IMDS v1-compatible responder used for the SSRF training scenario.

Run with: python server.py
Listens on :80 inside the network. docker-compose wires the 169.254.169.254
alias on the ksp-net network.
"""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


CREDS = {
    "Code": "Success",
    "LastUpdated": "2026-05-15T10:00:00Z",
    "Type": "AWS-HMAC",
    "AccessKeyId": "ASIA5EXAMPLEKEY1234",
    "SecretAccessKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
    "Token": "FQoDYXdzEK7//////////wEaDExampleSessionTokenString",
    "Expiration": "2026-05-15T16:00:00Z",
}

ROLE_NAME = "ksp-app-role"


class IMDS(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802 (BaseHTTPRequestHandler API)
        path = self.path.rstrip("/")
        if path == "/latest/meta-data/iam/security-credentials":
            self._text(ROLE_NAME)
        elif path == f"/latest/meta-data/iam/security-credentials/{ROLE_NAME}":
            self._json(CREDS)
        elif path == "/latest/meta-data/instance-id":
            self._text("i-0abc1234def567890")
        elif path == "/latest/meta-data/hostname":
            self._text("ip-10-0-1-12.eu-west-1.compute.internal")
        elif path == "/latest/meta-data":
            self._text(
                "iam/\nhostname\ninstance-id\nlocal-ipv4\nplacement/\npublic-ipv4\n"
            )
        else:
            self.send_response(404)
            self.end_headers()

    def _text(self, body):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(body.encode("utf-8"))

    def _json(self, body):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(body).encode("utf-8"))

    def log_message(self, *args, **kwargs):  # quiet logs
        pass


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 80), IMDS).serve_forever()
