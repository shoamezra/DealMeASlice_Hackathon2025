import socket
import threading
import time

from protocol import pack_offer, unpack_request
from utils import UDP_OFFER_PORT


SERVER_NAME = "DealMeASliceServer"  

# Broadcast offer messages over UDP once per second.
def udp_offer_broadcaster(tcp_port: int):

    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    while True:
        try:
            offer_msg = pack_offer(tcp_port, SERVER_NAME)
            udp_sock.sendto(offer_msg, ("<broadcast>", UDP_OFFER_PORT)) # Send UDP broadcast so all clients listening on UDP_OFFER_PORT can receive the offer
            time.sleep(1)       # Broadcast every second
        except Exception:
            # UDP errors should not crash the server
            time.sleep(1)


# Handle a single TCP client connection.
def handle_tcp_client(conn: socket.socket, addr):
    try:
        conn.settimeout(5.0)    # 5 second timeout for client response  
        data = conn.recv(1024)  # Receive request from client
        if not data:            # No data received
            return

        result = unpack_request(data)
        if result is None:
            print(f"Invalid request from {addr}")
            return

        num_rounds, team_name = result
        print(
            f"Accepted connection from {addr[0]}, "
            f"team name: {team_name}, rounds requested: {num_rounds}"
        )

    except socket.timeout:
        print(f"Connection with {addr} timed out")
    except Exception as e:
        print(f"Error handling client {addr}: {e}")
    finally:
        conn.close()


def main():
    # Create TCP socket
    tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_sock.bind(("", 0))  # Bind to any available port
    tcp_sock.listen()

    tcp_port = tcp_sock.getsockname()[1]
    print(f"Server started, listening on port {tcp_port}")

    # Start UDP offer broadcaster thread
    udp_thread = threading.Thread(
        target=udp_offer_broadcaster,
        args=(tcp_port,),
        daemon=True,
    )
    udp_thread.start()

    # Accept incoming TCP connections
    while True:
        try:
            conn, addr = tcp_sock.accept()
            handle_tcp_client(conn, addr)
        except Exception as e:
            print(f"Error accepting connection: {e}")


if __name__ == "__main__":
    main()
