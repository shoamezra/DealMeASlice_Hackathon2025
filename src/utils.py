
# ----- Protocol constants -----

# Magic cookie (4 bytes)
MAGIC_COOKIE = 0xabcddcba

# Message types (1 byte)
MSG_TYPE_OFFER = 0x2
MSG_TYPE_REQUEST = 0x3
MSG_TYPE_PAYLOAD = 0x4

# Fixed sizes
TEAM_NAME_SIZE = 32  # bytes, fixed-length name (pad with 0x00 or truncate)
DECISION_SIZE = 5    # bytes ("Hittt" / "Stand")

# UDP listen port for offers 
UDP_OFFER_PORT = 13122

# ----- Payload / game result codes (server -> client) -----

RESULT_NOT_OVER = 0x0
RESULT_TIE = 0x1
RESULT_LOSS = 0x2
RESULT_WIN = 0x3

# ----- Player decisions (client -> server) -----

DECISION_HIT = b"Hittt"
DECISION_STAND = b"Stand"

# ----- Card encoding -----
MIN_RANK = 1
MAX_RANK = 13

# Suit encoded 0-3 in order: (Heart, Diamond, Club, Spade)

SUITS = {
    0: "Heart",
    1: "Diamond",
    2: "Club",
    3: "Spade",
}


def print_cards(cards):
    RED = "\033[31m"
    RESET = "\033[0m"

    SUITS = {
        0: "♥",  # Heart
        1: "♦",  # Diamond
        2: "♣",  # Club
        3: "♠",  # Spade
    }

    RANKS = {
        1: "A",
        11: "J",
        12: "Q",
        13: "K",
    }

    card_lines = []

    for card in cards:
        rank, suit = card 

        rank_str = RANKS.get(rank, str(rank))
        suit_str = SUITS.get(suit, "?")

        is_red = suit in (0, 1)  # Heart or Diamond are red

        symbol = (
            f"{RED}{rank_str}{suit_str}{RESET}"
            if is_red
            else f"{rank_str}{suit_str}"
        )

        lines = [
            "+--+",
            f"|{symbol}|",
            "+--+"
        ]

        card_lines.append(lines)

    for i in range(len(card_lines[0])):
        print(" ".join(card[i] for card in card_lines))




def format_card(rank, suit):
    ranks = {
        1: "Ace Yossi",
        11: "Jack Naveh",
        12: "Queen",
        13: "King Nadav"
    }
    suits = {
        0: "♥",
        1: "♦",
        2: "♣",
        3: "♠"
    }
    rank_str = ranks.get(rank, str(rank))
    suit_str = suits.get(suit, "Unknown")
    return f"{rank_str} {suit_str}"

def recv_exact(sock, n: int) -> bytes:
    data = b""
    while len(data) < n:
        chunk = sock.recv(n - len(data))
        if not chunk:
            raise ConnectionError("Socket closed while reading")
        data += chunk
    return data

