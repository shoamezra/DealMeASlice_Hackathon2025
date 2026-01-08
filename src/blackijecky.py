# Blackjack game logic.
# This module contains only game-related logic.


import random
from typing import List, Tuple

from utils import (
    MIN_RANK,
    MAX_RANK,
    SUITS,
)

# Card is represented as a tuple: (rank, suit)
Card = Tuple[int, int]

# Create a new standard 52-card deck.
def new_deck() -> List[Card]:
    deck: list[Card]= []
    for suit in SUITS.keys():
        for rank in range(MIN_RANK, MAX_RANK + 1):
            deck.append((rank, suit))
    return deck

# Shuffle the deck in place.
def shuffle_deck(deck: List[Card]) -> None:
    random.shuffle(deck)


def draw_card(deck: List[Card]) -> Card:
    if not deck:
        raise RuntimeError("Deck is empty")
    return deck.pop()

# Convert a card rank to its blackjack value
def card_value(rank: int) -> int:
    if rank == 1:
        return 11
    if 2 <= rank <= 10:
        return rank
    # J, Q, K
    return 10

# Calculate the total value of a hand.
def hand_total(hand: List[Card]) -> int:
    total = 0
    aces = 0

    for rank, _ in hand:
        if rank == 1:  # Ace
            aces += 1
        total += card_value(rank)

    # Downgrade Ace from 11 to 1 if bust
    while total > 21 and aces > 0:
        total -= 10
        aces -= 1

    return total



def is_bust(hand: List[Card]) -> bool:
    return hand_total(hand) > 21


def dealer_should_hit(hand: List[Card]) -> bool:
    return hand_total(hand) < 17        # hit if total is less than 17 otherwise stand  
