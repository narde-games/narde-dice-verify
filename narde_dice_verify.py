#!/usr/bin/env python3
"""Check every dice throw of a narde.games game against its revealed seed.

Reads a game's .mat file (Replay -> download MAT), recomputes each throw from the
seed with the published formula narde-hmac-sha256-v1 and prints, per throw,
whether it matches. Needs Python 3.8+ and nothing else.

    python3 narde_dice_verify.py game.mat
    python3 narde_dice_verify.py game.mat --seen-hash <fingerprint you noted at the start>

Exit code 0 when everything matches, 1 when something does not, 2 when the file
cannot be checked.
"""
import argparse
import hashlib
import hmac
import re
import sys

FORMULA = "narde-hmac-sha256-v1"

HEADER = re.compile(r'^;\s*\[([^"\]]+?)\s+"([^"]*)"\]')
ROW = re.compile(r"^\s*\d+\)")
DICE = re.compile(r"^\s*([1-6])([1-6]):")
# A .mat row: "%3d) " then player 1's cell (28 wide), then player 2's.
LEFT, RIGHT = 5, 33


def dice(seed, message):
    """The pair a seed gives for a message: HMAC-SHA256, bytes 0-7 and 8-15
    big-endian, each mod 6 + 1."""
    mac = hmac.new(seed, message.encode("ascii"), hashlib.sha256).digest()
    return (int.from_bytes(mac[0:8], "big") % 6 + 1, int.from_bytes(mac[8:16], "big") % 6 + 1)


def deciding_opening(seed):
    """open:0, open:1, ... until the dice differ: the throw that decided who moved first."""
    for k in range(1000):
        pair = dice(seed, "open:%d" % k)
        if pair[0] != pair[1]:
            return k, pair
    raise ValueError("no opening throw in 1000 attempts")


def parse_mat(text):
    """The headers and the thrown pairs in the order they were thrown."""
    headers, throws = {}, []
    for line in text.splitlines():
        m = HEADER.match(line)
        if m:
            headers[m.group(1)] = m.group(2)
            continue
        if not ROW.match(line):
            continue
        for cell in (line[LEFT:RIGHT], line[RIGHT:]):
            d = DICE.match(cell)
            if d:
                throws.append((int(d.group(1)), int(d.group(2))))
    return headers, throws


def check(text, seen_hash=None, out=print):
    headers, throws = parse_mat(text)
    formula = headers.get("Dice Formula")
    if formula is None:
        out("This file carries no dice seed (a game from before seeds, or one in progress).")
        return 2
    if formula != FORMULA:
        out("Unknown formula %r: this script checks %s only." % (formula, FORMULA))
        return 2
    seed = bytes.fromhex(headers["Dice Seed"])
    fingerprint = hashlib.sha256(seed).hexdigest()
    rule = headers.get("Opening Dice", "carried")
    ok = True

    def verdict(passed, what):
        nonlocal ok
        ok = ok and passed
        out("%s %s" % ("OK  " if passed else "FAIL", what))

    verdict(fingerprint == headers.get("Dice Seed Hash", "").lower(),
            "fingerprint: SHA-256(seed) = %s" % fingerprint)
    if seen_hash:
        verdict(fingerprint == seen_hash.strip().lower(), "matches the fingerprint you saw at the start")

    k, opening = deciding_opening(seed)
    stored = headers.get("Opening Roll")
    shown = "%d-%d" % opening
    verdict(stored == shown, "opening roll: open:%d gives %s, file says %s" % (k, shown, stored))

    for n, thrown in enumerate(throws, start=1):
        if n == 1 and rule == "carried":
            expected, source = opening, "carried from the opening roll"
        else:
            expected, source = dice(seed, "turn:%d" % n), "turn:%d" % n
        verdict(thrown == expected, "turn %d: %d-%d (%s gives %d-%d)" % (n, thrown[0], thrown[1], source, expected[0], expected[1]))

    out("")
    out("Every throw matches the seed." if ok else "NOT every throw matches the seed.")
    return 0 if ok else 1


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("mat", help="the game's .mat file")
    parser.add_argument("--seen-hash", help="the fingerprint the app showed when the game started")
    args = parser.parse_args(argv)
    with open(args.mat, encoding="utf-8") as f:
        return check(f.read(), args.seen_hash)


if __name__ == "__main__":
    sys.exit(main())
