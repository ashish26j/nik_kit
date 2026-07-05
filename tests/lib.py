"""Tiny zero-dependency test harness for Nik_kiT phase gates.

Stdlib only (urllib) so it runs anywhere with Python 3 — no pip installs.
Tests hit the LIVE localhost stack (docker compose up), matching our
"localhost only, no prod" constraint. Each test is tagged TEST_P<phase>_T<NN>.
"""
import json
import os
import urllib.error
import urllib.request

BASE_URL = os.environ.get("NIKKIT_API", "http://localhost:6061")
UI_URL = os.environ.get("NIKKIT_UI", "http://localhost:8080")

_REGISTRY = []


def test(tid, desc):
    """Decorator: register a test under its TEST_P<phase>_T<NN> id."""
    def deco(fn):
        _REGISTRY.append((tid, desc, fn))
        return fn
    return deco


def all_tests():
    return list(_REGISTRY)


def http_get(url, timeout=8):
    """Return (status_code, body_text). HTTP errors return their code, not raise."""
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()


def get_json(path):
    """GET BASE_URL+path, assert 200, return parsed JSON."""
    status, body = http_get(BASE_URL + path)
    assert status == 200, f"GET {path} → HTTP {status}"
    return json.loads(body)


def request(method, path, body=None, headers=None, timeout=8):
    """Return (status_code, parsed_json_or_text). Body is JSON-encoded."""
    data = json.dumps(body).encode() if body is not None else None
    h = {"Content-Type": "application/json", "Accept": "application/json"}
    if headers:
        h.update(headers)
    req = urllib.request.Request(BASE_URL + path, data=data, method=method, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read().decode()
            status = r.status
    except urllib.error.HTTPError as e:
        raw, status = e.read().decode(), e.code
    try:
        return status, json.loads(raw) if raw else None
    except ValueError:
        return status, raw


def post(path, body=None, headers=None):
    return request("POST", path, body, headers)


def patch(path, body=None, headers=None):
    return request("PATCH", path, body, headers)


def delete(path, headers=None):
    return request("DELETE", path, None, headers)


def bearer(token):
    return {"Authorization": f"Bearer {token}"}


def status_no_redirect(url, timeout=8):
    """Return the HTTP status WITHOUT following redirects (so /admin/ → 302)."""
    class _NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *a, **k):
            return None

    opener = urllib.request.build_opener(_NoRedirect)
    try:
        with opener.open(urllib.request.Request(url), timeout=timeout) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code
