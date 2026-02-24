"""
Firebase Functions entry point.
Bridges Firebase Functions WSGI-style requests to FastAPI ASGI app.
"""
import sys
import os
import asyncio
import io

from firebase_functions import https_fn

# Ensure the functions src directory is in path
this_dir = os.path.abspath(os.path.dirname(__file__))
if this_dir not in sys.path:
    sys.path.insert(0, this_dir)

from src.main import app


def asgi_to_response(asgi_app, request: https_fn.Request) -> https_fn.Response:
    """
    Manually bridges a Firebase Functions Request to a FastAPI (ASGI) app.
    """
    # Build ASGI scope from the Firebase request
    path = request.path or "/"
    query_string = request.query_string if isinstance(request.query_string, bytes) else request.query_string.encode("utf-8")
    
    headers = []
    for key, value in request.headers.items():
        headers.append((key.lower().encode("utf-8"), value.encode("utf-8")))

    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": request.method.upper(),
        "headers": headers,
        "path": path,
        "query_string": query_string,
        "root_path": "",
        "scheme": request.scheme,
        "server": (request.host, 443),
    }

    # Capture the request body
    body = request.get_data()
    body_iter = iter([body])

    response_started = {}
    response_body = io.BytesIO()

    async def receive():
        body_chunk = next(body_iter, b"")
        return {"type": "http.request", "body": body_chunk, "more_body": False}

    async def send(message):
        if message["type"] == "http.response.start":
            response_started["status"] = message["status"]
            response_started["headers"] = {
                k.decode("utf-8"): v.decode("utf-8")
                for k, v in message.get("headers", [])
            }
        elif message["type"] == "http.response.body":
            response_body.write(message.get("body", b""))

    # Run the ASGI app
    asyncio.run(asgi_app(scope, receive, send))

    status_code = response_started.get("status", 200)
    resp_headers = response_started.get("headers", {})
    content_type = resp_headers.pop("content-type", "application/json")

    return https_fn.Response(
        response_body.getvalue(),
        status=status_code,
        headers=resp_headers,
        content_type=content_type,
    )


@https_fn.on_request(timeout_sec=120, memory=1024)
def api_handler(req: https_fn.Request) -> https_fn.Response:
    try:
        return asgi_to_response(app, req)
    except Exception as e:
        import traceback
        error = f"Fatal error: {e}\n{traceback.format_exc()}"
        print(error)
        return https_fn.Response(error, status=500, content_type="text/plain")
