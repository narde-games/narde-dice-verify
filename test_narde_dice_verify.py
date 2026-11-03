"""Self-check against the published vectors (docs: narde-be guide/dice/provably-fair.md).

    python3 -m unittest test_narde_dice_verify
"""
import os
import unittest

import narde_dice_verify as v

SEED = bytes(range(32))
HERE = os.path.dirname(os.path.abspath(__file__))


class Vectors(unittest.TestCase):
    def test_formula(self):
        self.assertEqual(v.dice(SEED, "open:0"), (5, 5))
        self.assertEqual(v.dice(SEED, "open:1"), (6, 3))
        self.assertEqual(v.dice(SEED, "turn:1"), (3, 5))
        self.assertEqual(v.dice(SEED, "turn:2"), (6, 4))
        self.assertEqual(v.dice(SEED, "turn:3"), (3, 2))
        self.assertEqual(v.dice(SEED, "turn:10"), (2, 2))

    def test_opening_skips_the_tie(self):
        self.assertEqual(v.deciding_opening(SEED), (1, (6, 3)))


class MatFile(unittest.TestCase):
    def read(self):
        with open(os.path.join(HERE, "examples", "vectors.mat"), encoding="utf-8") as f:
            return f.read()

    def test_the_example_game_passes(self):
        lines = []
        self.assertEqual(v.check(self.read(), out=lines.append), 0)
        self.assertEqual(lines[-1], "Every throw matches the seed.")

    def test_reads_throws_in_order_from_both_columns(self):
        _, throws = v.parse_mat(self.read())
        self.assertEqual(throws, [(3, 5), (6, 4), (3, 2)])

    def test_a_changed_throw_fails(self):
        changed = self.read().replace("64: 24/14", "66: 24/12")
        lines = []
        self.assertEqual(v.check(changed, out=lines.append), 1)
        self.assertIn("FAIL turn 2: 6-6 (turn:2 gives 6-4)", lines)

    def test_a_fingerprint_other_than_the_one_seen_fails(self):
        lines = []
        self.assertEqual(v.check(self.read(), seen_hash="00", out=lines.append), 1)


if __name__ == "__main__":
    unittest.main()
