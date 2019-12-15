import unittest

from ..utils import ValueTieCounter


class ValueTieCounterTest(unittest.TestCase):

    def test_elements(self):
        vtc = ValueTieCounter(a=4, b=2, c=0, d=2)
