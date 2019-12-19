import unittest

from collections import Counter
from ..utils import ValueTieCounter


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
        self.assertEqual(
            (8, 8, 7),
            tuple(_[1] for _ in top2)
        )
