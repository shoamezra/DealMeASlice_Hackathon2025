
import struct

from utils import (
    MAGIC_COOKIE,
    MSG_TYPE_OFFER,
    MSG_TYPE_REQUEST,
    MSG_TYPE_PAYLOAD,
    TEAM_NAME_SIZE,
    DECISION_HIT,
    DECISION_STAND,
    MIN_RANK,
    MAX_RANK,
    SUITS,
)


# ----- Struct formats (network byte order) -----

# I = 4 bytes (unsigned int)
# B = 1 byte (unsigned char)
# H = 2 bytes (unsigned short)
# 5s = 5 byte string
# 32s = 32 byte string

OFFER_FORMAT = "!I B H 32s"
REQUEST_FORMAT = "!I B B 32s"
PAYLOAD_CLIENT_FORMAT = "!I B 5s"
PAYLOAD_SERVER_FORMAT = "!I B B H B"

# Encode a team or server name into exactly 32 bytes. 
# Pads with 0x00 or truncates if needed.
def _encode_name(name: str) -> bytes:

    raw = name.encode("utf-8")
    if len(raw) > TEAM_NAME_SIZE:
        return raw[:TEAM_NAME_SIZE]              # truncate
    return raw.ljust(TEAM_NAME_SIZE, b"\x00")    # pad with null bytes

# Decode a fixed-length name field by stripping null bytes.
def _decode_name(raw: bytes) -> str:
    return raw.rstrip(b"\x00").decode("utf-8", errors="ignore")



# ----- Offer (UDP) -----

# pack to bytes according to OFFER_FORMAT
def pack_offer(tcp_port: int, server_name: str) -> bytes:
    return struct.pack(
        OFFER_FORMAT,
        MAGIC_COOKIE,
        MSG_TYPE_OFFER,
        tcp_port,
        _encode_name(server_name),
    )


# unpack from bytes according to OFFER_FORMAT
def unpack_offer(data: bytes):
    if len(data) != struct.calcsize(OFFER_FORMAT):
        return None

    cookie, msg_type, tcp_port, raw_name = struct.unpack(OFFER_FORMAT, data)

    if cookie != MAGIC_COOKIE:
        return None                    #error handling
    if msg_type != MSG_TYPE_OFFER:
        return None                    #error handling

    return tcp_port, _decode_name(raw_name)


# ----- Request (TCP) -----

# pack request to bytes according to REQUEST_FORMAT
def pack_request(num_rounds: int, team_name: str) -> bytes:
    return struct.pack(
        REQUEST_FORMAT,
        MAGIC_COOKIE,
        MSG_TYPE_REQUEST,
        num_rounds,
        _encode_name(team_name),
    )

# unpack request from bytes according to REQUEST_FORMAT
def unpack_request(data: bytes):
    if len(data) != struct.calcsize(REQUEST_FORMAT):
        return None

    cookie, msg_type, num_rounds, raw_name = struct.unpack(REQUEST_FORMAT, data)

    if cookie != MAGIC_COOKIE: 
        return None                   #error handling
    if msg_type != MSG_TYPE_REQUEST:
        return None                   #error handling

    return num_rounds, _decode_name(raw_name)



# ----- Payload: Client -> Server -----

# pack client decision to bytes according to PAYLOAD_CLIENT_FORMAT
def pack_payload_client(decision: bytes) -> bytes:
    if decision not in (DECISION_HIT, DECISION_STAND):
        raise ValueError("Invalid client decision")    #invalid protocol value

    return struct.pack(
        PAYLOAD_CLIENT_FORMAT,
        MAGIC_COOKIE,
        MSG_TYPE_PAYLOAD,
        decision,
    )

# unpack client decision from bytes according to PAYLOAD_CLIENT_FORMAT
def unpack_payload_client(data: bytes):
    if len(data) != struct.calcsize(PAYLOAD_CLIENT_FORMAT):
        return None

    cookie, msg_type, decision = struct.unpack(PAYLOAD_CLIENT_FORMAT, data)

    if cookie != MAGIC_COOKIE:
        return None                                       #error handling
    if msg_type != MSG_TYPE_PAYLOAD:
        return None                                       #error handling
    if decision not in (DECISION_HIT, DECISION_STAND):
        return None                                       #error handling
    return decision


# ----- Payload: Server -> Client -----

# pack server payload to bytes according to PAYLOAD_SERVER_FORMAT
def pack_payload_server(result_code: int, rank: int, suit: int) -> bytes:
    return struct.pack(
        PAYLOAD_SERVER_FORMAT,
        MAGIC_COOKIE,
        MSG_TYPE_PAYLOAD,
        result_code,
        rank,
        suit,
    )

# unpack server payload from bytes according to PAYLOAD_SERVER_FORMAT
def unpack_payload_server(data: bytes):
    if len(data) != struct.calcsize(PAYLOAD_SERVER_FORMAT):
        return None

    cookie, msg_type, result_code, rank, suit = struct.unpack(
        PAYLOAD_SERVER_FORMAT, data
    )

    if cookie != MAGIC_COOKIE:
        return None                                      #error handling
    if msg_type != MSG_TYPE_PAYLOAD:
        return None                                      #error handling
    if rank != 0:                                     
        if not (MIN_RANK <= rank <= MAX_RANK):
            return None
        if suit not in SUITS:
            return None
    # else: rank == 0 (special case: no card dealt)
    return result_code, rank, suit