import socket  # noqa: F401


def main():
    # You can use print statements as follows for debugging, they'll be visible when running tests.
    print("Logs from your program will appear here!")

    # Uncomment this to pass the first stage
    #
    server_socket = socket.create_server(("localhost", 4221), reuse_port=True)
    print(server_socket)
    sock, _ = server_socket.accept() # wait for client
    sock.sendall(b'HTTP/1.1 200 OK\r\n\r\n')
    sock.close()


if __name__ == "__main__":
    main()
