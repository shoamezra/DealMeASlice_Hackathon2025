
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
# ! Rank encoded 01-13
MIN_RANK = 1
MAX_RANK = 13

# Suit encoded 0-3 in order: (Heart, Diamond, Club, Spade)

SUITS = {
    0: "Heart",
    1: "Diamond",
    2: "Club",
    3: "Spade",
}
