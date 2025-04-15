from dataclasses import dataclass
import os
import socket
import sys
import threading

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
    _content_type = "text/plain"

    @property
    def content_length(self):
        return len(self.message)

    @property
    def content_type(self):
        return self._content_type

    def with_content_type(self, content_type: str):
        self._content_type = content_type
        return self


class HttpServerException(Exception):
    def __init__(self, code, message):
        self.code = code
        self.message = message
        super().__init__(code, message)


class NotFoundException(HttpServerException):
    def __init__(self):
        super().__init__(404, "")


def index_action(request: Request) -> Response:
    return Response(message="")


def not_found_action(request: Request) -> Response:
    raise NotFoundException()


def echo_action(request: Request) -> Response:
    return Response(message=request.target_path.replace("/echo/", ""))


def user_agent_action(request: Request) -> Response:
    return Response(message=request.get_header("User-Agent", ""))


def files_action(request: Request) -> Response:
    file_name = request.target_path.replace("/files/", "")
    global directory
    file_path = f"{directory}{file_name}"
    if not os.path.isfile(file_path):
        raise NotFoundException()
    with open(file_path, "r") as f:
        message = f.read()
    return Response(message=message).with_content_type("application/octet-stream")


# todo 1. pattern matching
# todo 2. decorator
def find_controller(target_path: str):
    if target_path.startswith("/echo/"):
        return echo_action
    if target_path.startswith("/files/"):
        return files_action
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


def make_response(response: Response) -> str:
    res = [
        f"HTTP/1.1 {response.code} {reason_phrases.get(response.code, '')}",
        f"Content-Type: {response.content_type}",
    ]
    if response.message:
        res.append(f"Content-Length: {response.content_length}")
        res.append(f"\r\n{response.message}")
    return "\r\n".join(res)


def handle(connection):
    request = create_request(str(connection.recv(1024)))
    try:
        controller = find_controller(request.target_path)
        response = controller(request)
    except HttpServerException as e:
        response = Response(message=e.message, code=e.code)
    connection.sendall(make_response(response).encode("utf-8"))
    connection.close()


# global variables
directory: str = ""


def main():
    if "--directory" in sys.argv:
        global directory
        i = sys.argv.index("--directory")
        directory = sys.argv[i + 1]

    server_socket = socket.create_server(("localhost", 4221), reuse_port=True)
    while True:
        conn, _ = server_socket.accept()
        thread = threading.Thread(target=handle, args=(conn,))
        thread.start()


if __name__ == "__main__":
    main()
