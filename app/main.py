from dataclasses import dataclass
import socket
import threading  # noqa: F401

reason_phrases = {200: "OK", 404: "Not Found"}


@dataclass
class Request:
    method: str
    target_path: str
    headers: dict[str, str]

    def get_header(self, key: str, default) -> str | None:
        return self.headers.get(key, default)


@dataclass
class Response:
    message: str
    code: int = 200


class HttpServerException(Exception):
    def __init__(self, code, message):
        self.code = code
        self.message = message
        super().__init__(code, message)


def index_action(request: Request) -> Response:
    return Response(message="")


def not_found_action(request: Request) -> Response:
    raise HttpServerException(404, "Not Found")


def echo_action(request: Request) -> Response:
    return Response(message=request.target_path.replace("/echo/", ""))


def user_agent_action(request: Request) -> Response:
    return Response(message=request.get_header("User-Agent", ""))


def find_controller(target_path: str):
    if target_path.startswith("/echo/"):
        return echo_action
    if target_path == "/user-agent":
        return user_agent_action
    if target_path == "/":
        return index_action
    return not_found_action


def create_request(recv: str) -> Request:
    [sections, body] = recv.split("\\r\\n\\r\\n")
    line, *raw_headers = sections.split("\\r\\n")
    [method, target, version] = line.split(" ")
    headers = {
        key.strip(): value.strip()
        for header in raw_headers
        for key, value in [header.split(":", 1)]
    }
    return Request(method=method, target_path=target, headers=headers)


def handle(connection):
    request = create_request(str(connection.recv(1024)))
    try:
        controller = find_controller(request.target_path)
        response = controller(request)
    except HttpServerException as e:
        response = Response(message=e.message, code=e.code)

    res = (
        f"HTTP/1.1 {response.code} {reason_phrases.get(response.code, '')}\r\n"
        f"Content-Type: text/plain\r\n"
        f"Content-Length: {len(response.message)}"
        f"\r\n\r\n{response.message}"
    )
    connection.sendall(res.encode("utf-8"))
    connection.close()


def main():
    server_socket = socket.create_server(("localhost", 4221), reuse_port=True)
    while True:
        conn, _ = server_socket.accept()
        thread = threading.Thread(target=handle, args=(conn,))
        thread.start()


if __name__ == "__main__":
    main()
