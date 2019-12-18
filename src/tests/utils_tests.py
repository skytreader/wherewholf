import unittest

from ..utils import ValueTieCounter


class ValueTieCounterTest(unittest.TestCase):

    def test_elements(self):
        minuend = ValueTieCounter(a=4, b=2, c=0, d=-2)
        subtrahend = {"a": 1, "b": 2, "c": 3, "d": 4}
        minuend.subtract(subtrahend)

        self.assertEqual(3, minuend["a"])
        self.assertEqual(0, minuend["b"])
        self.assertEqual(-3, minuend["c"])
        self.assertEqual(-6, minuend["d"])
