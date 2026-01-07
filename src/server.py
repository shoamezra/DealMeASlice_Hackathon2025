import socket
import struct
import threading
import time

from protocol import (
    PAYLOAD_CLIENT_FORMAT,
    REQUEST_FORMAT,
    pack_offer,
    unpack_request,
    unpack_payload_client,
    pack_payload_server,
)
from utils import (
    UDP_OFFER_PORT,
    RESULT_NOT_OVER,
    RESULT_WIN,
    RESULT_LOSS,
    RESULT_TIE,
    DECISION_HIT,
    DECISION_STAND,
    recv_exact,
)
from blackijecky import (
    new_deck,
    shuffle_deck,
    draw_card,
    hand_total,
    is_bust,
    dealer_should_hit,
)


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

def send_card(conn, result, card):
    if card is None:
        conn.sendall(pack_payload_server(result, 0, 0))
    else:
        rank, suit = card
        conn.sendall(pack_payload_server(result, rank, suit))


def play_round(conn):
    deck = new_deck()
    shuffle_deck(deck)

    player_hand = []
    dealer_hand = []

    # Initial deal - player
    for _ in range(2):
        card = draw_card(deck)
        player_hand.append(card)
        send_card(conn, RESULT_NOT_OVER, card)

    # Initial deal - dealer
    dealer_visible = draw_card(deck)
    dealer_hidden = draw_card(deck)
    dealer_hand.append(dealer_visible)
    dealer_hand.append(dealer_hidden)

    send_card(conn, RESULT_NOT_OVER, dealer_visible)

    # Player turn
    while True:
        data = recv_exact(conn, struct.calcsize(PAYLOAD_CLIENT_FORMAT))
        decision = unpack_payload_client(data)
        if decision is None:
            raise RuntimeError("Invalid client payload")

        if decision == DECISION_HIT:
            card = draw_card(deck)
            player_hand.append(card)

            if is_bust(player_hand):
                send_card(conn, RESULT_LOSS, card)
                return RESULT_LOSS

            send_card(conn, RESULT_NOT_OVER, card)

        elif decision == DECISION_STAND:
            break

    # Dealer turn
    send_card(conn, RESULT_NOT_OVER, dealer_hidden)

    while dealer_should_hit(dealer_hand):
        card = draw_card(deck)
        dealer_hand.append(card)

        if is_bust(dealer_hand):
            send_card(conn, RESULT_WIN, card)
            return RESULT_WIN

        send_card(conn, RESULT_NOT_OVER, card)

    # Compare totals
    player_total = hand_total(player_hand)
    dealer_total = hand_total(dealer_hand)

    if player_total > dealer_total:
        send_card(conn, RESULT_WIN, None)
        return RESULT_WIN
    if dealer_total > player_total:
        send_card(conn, RESULT_LOSS, None)
        return RESULT_LOSS

    send_card(conn, RESULT_TIE, None)
    return RESULT_TIE

# Handle a single TCP client connection.
def handle_tcp_client(conn, addr):
    try:
        conn.settimeout(50.0)

        data = recv_exact(conn, struct.calcsize(REQUEST_FORMAT))
        request = unpack_request(data)  
        if request is None:
            return

        num_rounds, team_name = request
        print(f"Client {team_name} connected from {addr}, rounds={num_rounds}")

        for _ in range(num_rounds): # Play the requested number of rounds
            play_round(conn)

    except socket.timeout:
        print(f"Client {addr} timed out")
    except RuntimeError as e:
        print(f"Game error with {addr}: {e}")
    except Exception as e:
        print(f"Unexpected error with {addr}: {e}")
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
    # Each connection is handled in a separate thread to allow multiple clients to play simultaneously
    while True:
        try:
            conn, addr = tcp_sock.accept()

            client_thread = threading.Thread(
                target=handle_tcp_client,
                args=(conn, addr),
                daemon=True
            )
            client_thread.start()

        except Exception as e:
            print(f"Accept error: {e}")



if __name__ == "__main__":
    main()
