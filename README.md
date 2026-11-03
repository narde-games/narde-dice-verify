# narde-dice-verify

Check, without trusting narde.games, that every dice throw of a game was the one its
secret seed gave — and that the seed is the one committed to before the first throw.

Every game on narde.games gets a random 32-byte seed when it is created. Before the
first throw both players see its **fingerprint**, `SHA-256(seed)`. Every throw is
computed from the seed with the public formula below. When the game is over, the seed
is revealed in the replay and in the game's `.mat` file. Changing a throw in the middle
of a game would need another seed — and another seed has another fingerprint.

## Use it

1. Open the finished game's replay in the app and download its `.mat` file.
2. Either
   - open `index.html` in a browser (works offline; nothing is sent anywhere), choose
     the file and press **Check**, or
   - run `python3 narde_dice_verify.py game.mat` (Python 3.8+, no dependencies).
3. If you noted the fingerprint when the game started, pass it too
   (`--seen-hash <fingerprint>`, or the second field of the page): only that compares
   the seed with what was shown *before* the dice were thrown.

## The formula `narde-hmac-sha256-v1`

```
bytes = HMAC-SHA256(key = seed, message)
die 1 = (bytes 0–7 as an unsigned big-endian 64-bit integer) mod 6 + 1
die 2 = (bytes 8–15 as an unsigned big-endian 64-bit integer) mod 6 + 1
```

| Throw | Message |
|---|---|
| attempt k of the opening roll, k = 0, 1, 2… (die 1 is player 1's, die 2 player 2's) | `open:k` |
| the turn numbered n, n = 1, 2, 3… | `turn:n` |

- The opening roll repeats while the dice are equal; the first pair that differs
  decides who moves first. The file stores it as `; [Opening Roll "a-b"]`.
- `; [Opening Dice "carried"]`: turn 1 is played with that deciding pair, `turn:1` is not
  used. `"fresh"`: turn 1 is `turn:1`.
- The n-th throw written in the move list is turn n. A double is written once (`55:`).

## Test vectors

Seed `000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f`:

| | |
|---|---|
| fingerprint | `630dcd2966c4336691125448bbb25b4ff412a49c732db2c8abc1b8581bd710dd` |
| `open:0` | 5-5 (a tie, rolled again) |
| `open:1` | 6-3 (decides: player 1 moves first) |
| `turn:1` | 3-5 |
| `turn:2` | 6-4 |
| `turn:3` | 3-2 |
| `turn:10` | 2-2 |

`examples/vectors.mat` is a game built from them; `python3 -m unittest test_narde_dice_verify`
checks the script against them.

## One throw by hand

```bash
printf 'turn:1' | openssl dgst -sha256 -mac HMAC \
  -macopt hexkey:000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f
```

The first 16 hex digits are the first number, the next 16 the second; each mod 6, plus 1.

## What it does not prove

- That the server did not pick the seed with intent before the game began.
- That the bot does not peek: it runs on the server. The seed is out of its reach by
  how the code is built, but that cannot be proven to a player by maths.
