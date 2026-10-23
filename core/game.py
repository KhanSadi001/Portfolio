"""Server-side rules for the Bit Flip game.

The browser can't be trusted, so the server:
  * hands out a signed, single-use session token when a round starts,
  * only accepts a score once a full round's time has really passed,
  * caps how many numbers anyone can plausibly solve in that time, and
  * computes the score itself from the solved count.
A determined cheater can still script the game, but they can't submit
an impossible score or replay a token.
"""
import time
import uuid

from django.core import signing
from django.core.cache import cache

ROUND_SECONDS = 60
MIN_SECONDS_PER_SOLVE = 0.6     # faster than this isn't humanly possible with mouse or keys
MAX_SOLVED = int(ROUND_SECONDS / MIN_SECONDS_PER_SOLVE)
TOKEN_MAX_AGE = 15 * 60         # a round must be submitted within 15 minutes of starting
SALT = "bitflip-round"

# Levels: (first solve index of this level, label, points per solve)
LEVELS = [
    (0, "4-bit", 10),
    (5, "8-bit", 20),
    (12, "Hex", 30),
]


def points_for(solved):
    total = 0
    for i in range(solved):
        total += [pts for start, _, pts in LEVELS if i >= start][-1]
    return total


def new_round_token():
    return signing.dumps({"sid": uuid.uuid4().hex, "t": time.time()}, salt=SALT)


class RoundError(Exception):
    pass


def validate_round(token, solved):
    try:
        data = signing.loads(token, salt=SALT, max_age=TOKEN_MAX_AGE)
    except signing.SignatureExpired:
        raise RoundError("This round is too old to submit. Play another one.")
    except signing.BadSignature:
        raise RoundError("This round isn't valid. Start a new one.")

    elapsed = time.time() - float(data["t"])
    if elapsed < ROUND_SECONDS - 2:
        raise RoundError("The round hasn't finished yet.")
    if not isinstance(solved, int) or solved < 0 or solved > MAX_SOLVED:
        raise RoundError("That score isn't possible in one round.")

    # Single use: the first submission for a token wins.
    if not cache.add(f"bitflip:used:{data['sid']}", 1, TOKEN_MAX_AGE + 60):
        raise RoundError("This round was already submitted.")
    return points_for(solved)
