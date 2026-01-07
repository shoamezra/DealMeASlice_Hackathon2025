import socket

from protocol import (
    unpack_offer,
    pack_request,
    unpack_payload_server,
    pack_payload_client,
)
from utils import (
    UDP_OFFER_PORT,
    RESULT_NOT_OVER,
    RESULT_WIN,
    RESULT_LOSS,
    RESULT_TIE,
    DECISION_HIT,
    DECISION_STAND,
)
from blackijecky import hand_total


TEAM_NAME = "DealMeASliceClient"


def choose_mode():
    while True:
        choice = input("Choose mode: for automatic choose 'A' for manual choose 'M': ").strip().lower()
        if choice in ("a", "m"):
            return choice
        print("Please type 'A' for automatic or 'M' for manual")


def automatic_decision(hand):
    return DECISION_HIT if hand_total(hand) < 17 else DECISION_STAND


def manual_decision(_hand):
    while True:
        choice = input("Hit or Stand? ").strip().lower()
        if choice == "hit":
            return DECISION_HIT
        if choice == "stand":
            return DECISION_STAND
        print("Invalid choice, please type 'Hit' or 'Stand'")


def play_round(tcp_sock, decision_func):
    player_hand = []
    dealer_hand = []

    # -------- Phase 1: Initial deal --------
    # Expect: 2 player cards + 1 dealer visible card
    for _ in range(3):
        data = tcp_sock.recv(1024)
        payload = unpack_payload_server(data)
        if payload is None:
            raise RuntimeError("Invalid payload from server")

        result, rank, suit = payload

        if rank == 0:
            raise RuntimeError("Expected card during initial deal")

        if len(player_hand) < 2:
            player_hand.append((rank, suit))
        else:
            dealer_hand.append((rank, suit))

    # -------- Phase 2: Player turn --------
    while True:
        decision = decision_func(player_hand)
        tcp_sock.sendall(pack_payload_client(decision))

        data = tcp_sock.recv(1024)
        payload = unpack_payload_server(data)
        if payload is None:
            raise RuntimeError("Invalid payload from server")

        result, rank, suit = payload

        if rank != 0:
            player_hand.append((rank, suit))

        if result != RESULT_NOT_OVER:
            return result

        if decision == DECISION_STAND:
            break

    # -------- Phase 3: Dealer turn --------
    # Reveal hidden card
    data = tcp_sock.recv(1024)
    payload = unpack_payload_server(data)
    if payload is None:
        raise RuntimeError("Invalid payload from server")

    _, rank, suit = payload
    if rank == 0:
        raise RuntimeError("Expected dealer hidden card")

    dealer_hand.append((rank, suit))

    # Dealer hit loop
    while True:
        data = tcp_sock.recv(1024)
        payload = unpack_payload_server(data)
        if payload is None:
            raise RuntimeError("Invalid payload from server")

        result, rank, suit = payload

        if rank != 0:
            dealer_hand.append((rank, suit))

        if result != RESULT_NOT_OVER:
            return result


def main():
    # User setup
    while True:
        try:
            # Ask user for number of rounds
            num_rounds = int(input("Enter number of rounds to play: "))
            if 1 <= num_rounds <= 255:
                break
            print("Please enter a number between 1 and 255.")
        except ValueError:
            print("Invalid number.")

    mode = choose_mode()
    decision_func = automatic_decision if mode == 'a' else manual_decision

    print("Client started, listening for offer requests...")

    # Create UDP socket for listening to offers
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    udp_sock.bind(("", UDP_OFFER_PORT))

    while True:
        data, (server_ip, _) = udp_sock.recvfrom(1024)
        offer = unpack_offer(data)
        if offer is None:
            continue

        tcp_port, server_name = offer
        print(f"Received offer from {server_ip}, server name: {server_name}")


        try:
            # Connect to server over TCP
            tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            tcp_sock.settimeout(10.0)
            tcp_sock.connect((server_ip, tcp_port))
            tcp_sock.sendall(pack_request(num_rounds, TEAM_NAME))

            wins = 0

            for i in range(num_rounds):
                result = play_round(tcp_sock, decision_func)
                if result == RESULT_WIN:
                    print(f"Round {i + 1} result: WIN")
                    wins += 1
                elif result == RESULT_LOSS:
                    print(f"Round {i + 1} result: LOSS")
                elif result == RESULT_TIE:
                    print(f"Round {i + 1} result: TIE")

            win_rate = wins / num_rounds
            print(f"Finished playing rounds, win rate: {win_rate:.2f}")

        except Exception as e:
            print(f"Connection error: {e}")

        finally:
            tcp_sock.close()


if __name__ == "__main__":
    main()
