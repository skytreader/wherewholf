import unittest

from collections import Counter
from typing import Iterable, List, Sequence
from ..utils import ValueTieCounter


def _take_ndex(it: Iterable, n: int) -> Sequence:
    return [_[n] for _ in it]


class ValueTieCounterTest(unittest.TestCase):

    def test_falsey(self):
        self.assertFalse(Counter())
        self.assertFalse(ValueTieCounter())

    def test_truthy(self):
        self.assertTrue(Counter(a=1))
        self.assertTrue(ValueTieCounter(a=1))

    def test_elements(self):
        minuend = ValueTieCounter(a=4, b=2, c=0, d=-2)
        subtrahend = {"a": 1, "b": 2, "c": 3, "d": 4}
        minuend.subtract(subtrahend)

        self.assertEqual(3, minuend["a"])
        self.assertEqual(0, minuend["b"])
        self.assertEqual(-3, minuend["c"])
        self.assertEqual(-6, minuend["d"])
    
    def test_update(self):
        c = ValueTieCounter("which")
        c.update("witch")
        c.update(Counter("watch"))
        self.assertEqual(4, c["h"])

    def test_update_builds_index_properly(self):
        c = ValueTieCounter("which")
        c.update("witch")
        c.update(Counter("watch"))
        self.assertEqual(4, c["h"])
        top2: List[Tuple, Any] = c.most_common(2)
        top2_counts: Sequence = _take_ndex(top2, 1)
        self.assertEqual(3, len(top2))
        self.assertEqual(2, len(set(top2_counts)))
        # h, w, and c
        self.assertEqual((4, 3, 3), tuple(_take_ndex(top2, 1)))

        c.update("who")
        top2 = c.most_common(2)
        top2_counts = _take_ndex(top2, 1)
        self.assertEqual(2, len(top2))
        self.assertEqual(2, len(set(top2_counts)))
        self.assertEqual((5, 4), tuple(_take_ndex(top2, 1)))

    def test_most_common(self):
        test_string = "".join((
            "a" * 8,
            "b" * 2,
            "c" * 8,
            "d" * 7,
            "e" * 1,
            "f" * 1,
            "g" * 2
        ))
        c = ValueTieCounter(test_string)
        top2 = c.most_common(2)
        self.assertEqual(3, len(top2))
        self.assertEqual((8, 8, 7), tuple(_take_ndex(top2, 1)))
    
    def test_wherewholf(self):
        c = ValueTieCounter(JE=1, Chad=1, Christine=2)
        christine = c.most_common(1)
        self.assertEqual(1, len(christine))
