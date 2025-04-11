import socket  # noqa: F401


def main():
    server_socket = socket.create_server(("localhost", 4221), reuse_port=True)
    conn, _ = server_socket.accept()
    line = str(conn.recv(1024)).split("\\r\\n")[0]
    [method, target, version] = line.split(" ")
    if target.startswith("/echo/"):
        slug = target.replace("/echo/", "")
        response = f"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: {len(slug)}\r\n\r\n{slug}"
        conn.sendall(response.encode('utf-8'))
    if target == "/":
        conn.sendall(b'HTTP/1.1 200 OK\r\n\r\n')
    else:
        conn.sendall(b'HTTP/1.1 404 Not Found\r\n\r\n')
    conn.close()


if __name__ == "__main__":
    main()
