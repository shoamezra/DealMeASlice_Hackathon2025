

import socket

from protocol import unpack_offer, pack_request
from utils import UDP_OFFER_PORT


TEAM_NAME = "DealMeASliceClient" 

def main():
    # Ask user for number of rounds
    while True:
        try:
            num_rounds = int(input("Enter number of rounds to play: "))
            if 1 <= num_rounds <= 255:
                break
            print("Please enter a number between 1 and 255.")
        except ValueError:
            print("Invalid input. Please enter a number.")

    print("Client started, listening for offer requests...")

    # Create UDP socket for listening to offers
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) #!for windows?????
    udp_sock.bind(("", UDP_OFFER_PORT))

    while True:
        try:
            data, (server_ip, _) = udp_sock.recvfrom(1024)

            offer = unpack_offer(data)
            if offer is None:
                continue

            tcp_port, server_name = offer
            print(f"Received offer from {server_ip}, server name: {server_name}")

            # Connect to server over TCP
            tcp_sock = None
            try:
                tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                tcp_sock.settimeout(5.0)
                tcp_sock.connect((server_ip, tcp_port))

                request_msg = pack_request(num_rounds, TEAM_NAME)
                tcp_sock.sendall(request_msg)

            except Exception as e:
                print(f"Failed to connect to server {server_ip}:{tcp_port} ({e})")

            finally:
                if tcp_sock is not None:
                    tcp_sock.close()

        except Exception as e:
            print(f"Error receiving offer: {e}")


if __name__ == "__main__":
    main()