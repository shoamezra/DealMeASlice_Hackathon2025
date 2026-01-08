import socket
import struct

from protocol import (
    PAYLOAD_SERVER_FORMAT,
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
    format_card,
    recv_exact,
    print_cards,
)
from blackijecky import hand_total


TEAM_NAME = "DealMeASliceClient"



def choose_mode():
    while True:
        try:
            choice = input("Choose mode:\n1) dealer like mode \n2) manual mode\n3) careful mode\n4) risk mode\n").strip().lower()
            if choice in ("1", "2", "3", "4"):
                return choice
            print("Please type '1' for dealer like mode, '2' for manual mode, '3' for careful mode, or '4' for risk mode")
        except KeyboardInterrupt:
            print("\nInterrupted by user.")
            raise


def as_dealer_decision(hand):
    decision = DECISION_HIT if hand_total(hand) < 17 else DECISION_STAND
    print(f"Decision: {decision.decode()}")
    return decision

def careful_decision(hand):
    decision = DECISION_HIT if hand_total(hand) < 15 else DECISION_STAND
    print(f"Decision: {decision.decode()}")
    return decision

def risk_decision(hand):
    decision = DECISION_HIT if hand_total(hand) < 20 else DECISION_STAND
    print(f"Decision: {decision.decode()}")
    return decision

def manual_decision(_hand):
    while True:
        try:
            choice = input("Hit or Stand? ").strip().lower()
            if choice == "hit":
                return DECISION_HIT
            if choice == "stand":
                return DECISION_STAND
            print("Invalid choice, please type 'Hit' or 'Stand'")
        except KeyboardInterrupt:
            print("\nInterrupted by user.")
            raise


def play_round(tcp_sock, decision_func):
    player_hand = []
    dealer_hand = []

    # -------- Phase 1: Initial deal --------
    # Expect: 2 player cards + 1 dealer visible card
    for _ in range(3):
        data = recv_exact(tcp_sock, struct.calcsize(PAYLOAD_SERVER_FORMAT))
        payload = unpack_payload_server(data)
        if payload is None:
            raise RuntimeError("Invalid payload from server")

        result, rank, suit = payload

        if rank == 0:
            raise RuntimeError("Expected card during initial deal")

        if len(player_hand) < 2:
            player_hand.append((rank, suit))
            print(f"You received: {format_card(rank, suit)} (total: {hand_total(player_hand)})")
            print("your hand:")
            print_cards(player_hand)
        else:
            dealer_hand.append((rank, suit))
            print(f"Dealer's visible card: {format_card(rank, suit)} (total: {hand_total(dealer_hand)})")
            print("dealer hand:")
            print_cards(dealer_hand)

    # -------- Phase 2: Player turn --------
    while True:
        decision = decision_func(player_hand)
        tcp_sock.sendall(pack_payload_client(decision))

        if decision == DECISION_STAND:
            break

        data = recv_exact(tcp_sock, struct.calcsize(PAYLOAD_SERVER_FORMAT))
        payload = unpack_payload_server(data)
        if payload is None:
            raise RuntimeError("Server sent invalid payload, disconnecting")

        result, rank, suit = payload

        if rank != 0:
            player_hand.append((rank, suit))
            print(f"You received: {format_card(rank, suit)} (total: {hand_total(player_hand)})")
            print("your hand:")
            print_cards(player_hand)

        if result != RESULT_NOT_OVER:
            return result



    # -------- Phase 3: Dealer turn --------
    # Reveal hidden card
    data = recv_exact(tcp_sock, struct.calcsize(PAYLOAD_SERVER_FORMAT))
    payload = unpack_payload_server(data)
    if payload is None:
        raise RuntimeError("Invalid payload from server")

    _, rank, suit = payload
    if rank == 0:
        raise RuntimeError("Expected dealer hidden card")

    dealer_hand.append((rank, suit))
    print(f"Dealer's hidden card: {format_card(rank, suit)} (total: {hand_total(dealer_hand)})")
    print("dealer hand:")
    print_cards(dealer_hand)

    # Dealer hit loop
    while True:
        data = recv_exact(tcp_sock, struct.calcsize(PAYLOAD_SERVER_FORMAT))
        payload = unpack_payload_server(data)
        if payload is None:
            raise RuntimeError("Invalid payload from server")

        result, rank, suit = payload

        if rank != 0:
            dealer_hand.append((rank, suit))
            print(f"Dealer received: {format_card(rank, suit)} (total: {hand_total(dealer_hand)})")
            print("dealer hand:")
            print_cards(dealer_hand)

        if result != RESULT_NOT_OVER:
            return result


def main():
    # User setup
    while True:
        while True:
            try:
                # Ask user for number of rounds
                num_rounds = int(input("Enter number of rounds to play: "))
                if 1 <= num_rounds <= 255:
                    break
                print("Please enter a number between 1 and 255.")
            except ValueError:
                print("Invalid number.")
            except KeyboardInterrupt:
                print("\nInterrupted by user.")
                return
        try:
            mode = choose_mode()
            if mode == "1":
                decision_func = as_dealer_decision
            elif mode == "2":
                decision_func = manual_decision
            elif mode == "3":
                decision_func = careful_decision
            elif mode == "4":
                decision_func = risk_decision
        except KeyboardInterrupt:
            return


    
        print("Client started, listening for offer requests...")

        # Create UDP socket for listening to offers
        udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        udp_sock.bind(("", UDP_OFFER_PORT))
        data, (server_ip, _) = udp_sock.recvfrom(1024)
        offer = unpack_offer(data)
        if offer is None:
            continue

        tcp_port, server_name = offer
        print(f"Received offer from {server_ip}, server name: {server_name}")


        try:
            # Connect to server over TCP
            tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            tcp_sock.settimeout(60.0)
            tcp_sock.connect((server_ip, tcp_port))
            tcp_sock.sendall(pack_request(num_rounds, TEAM_NAME))

            wins, losses, ties = 0, 0, 0
            print("\nWelcome to \"Deal Me A Slice\" Casino!")
            print("Sit comfortably and enjoy your pizza 🍕!\n")
            for i in range(num_rounds):
                result = play_round(tcp_sock, decision_func)
                if result == RESULT_WIN:
                    wins += 1
                    print(f"Round {i+1} result: 🏆 WIN 🏆\n")
                    
                elif result == RESULT_LOSS:
                    losses += 1
                    print(f"Round {i+1} result: LOSS\n")
                    
                elif result == RESULT_TIE:
                    ties += 1
                    print(f"Round {i+1} result: TIE\n")
                print("-" * 30)
                    
            print(f"Finished playing {num_rounds} rounds.")
            print("Game statistics:")
            print(f"Wins: {wins}")
            print(f"Losses: {losses}")
            print(f"Ties: {ties}")
            print(f"Win rate: {wins / num_rounds:.2f}") # tie not counted as win
            print("-" * 30)



        except Exception as e:
            print(f"Connection error: {e}")

        except KeyboardInterrupt:
            return

        finally:
            tcp_sock.close()

        while True:
            try:
                play_again = input("\nGame over, do you want to play again? (yes/no): ").strip().lower()
            except KeyboardInterrupt:
                print("\nInterrupted by user.")
                return 

            if play_again == "yes":
                break  
            elif play_again == "no":
                return  
            else:
                print("Please type 'yes' or 'no'.")


if __name__ == "__main__":
    main()
