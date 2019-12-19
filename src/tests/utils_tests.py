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
