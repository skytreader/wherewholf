import unittest

from collections import Counter
from typing import Any, Iterable, List, Sequence, Tuple
from ..utils import MarkovChain, NominationRecencyTracker, ValueTieCounter, WorldModel
from ..game_characters import Player, SanitizedPlayer, Villager, Werewolf


def _take_ndex(it: Iterable, n: int) -> Sequence:
    return [_[n] for _ in it]


class ValueTieCounterTest(unittest.TestCase):

    def test_falsey(self) -> None:
        self.assertFalse(Counter())
        self.assertFalse(ValueTieCounter())

    def test_truthy(self) -> None:
        self.assertTrue(Counter(a=1))
        self.assertTrue(ValueTieCounter(a=1))

    def test_elements(self) -> None:
        minuend = ValueTieCounter(a=4, b=2, c=0, d=-2)
        subtrahend = {"a": 1, "b": 2, "c": 3, "d": 4}
        minuend.subtract(subtrahend)

        self.assertEqual(3, minuend["a"])
        self.assertEqual(0, minuend["b"])
        self.assertEqual(-3, minuend["c"])
        self.assertEqual(-6, minuend["d"])

    def test_total(self) -> None:
        test = ValueTieCounter(a=4, b=2, c=0, d=2)
        self.assertEqual(8, test.total())
    
    def test_update(self) -> None:
        c = ValueTieCounter("which")
        c.update("witch")
        c.update(Counter("watch"))
        self.assertEqual(4, c["h"])

    def test_update_builds_index_properly(self) -> None:
        c = ValueTieCounter("which")
        c.update("witch")
        c.update(Counter("watch"))
        self.assertEqual(4, c["h"])
        top2: List[Tuple[Any, int]] = c.most_common(2)
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

    def test_most_common(self) -> None:
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

    def test_most_common_game_usage(self) -> None:
        christine: Player = Player("Christine", Werewolf())
        gab: Player = Player("Gab", Villager())
        charles: Player = Player("Charles", Villager())
        chad: Player = Player("Chad", Villager())
        c: ValueTieCounter = ValueTieCounter()

        # gab will have 2 and everyone else will have 1. However, don't set
        # them straightaway to that. The bug we are reproducing seems to rely
        # on the += operator to work
        c[christine] += 1
        c[gab] += 1
        c[charles] += 1
        c[gab] += 1
        c[chad] += 1

        self.assertEqual(2, c[gab])
        self.assertEqual(1, c[christine])
        self.assertEqual(1, c[charles])
        self.assertEqual(1, c[chad])

class MarkovChainTests(unittest.TestCase):

    def test_add_event_and_probs(self) -> None:
        mc: MarkovChain = MarkovChain()
        mc.add_event("shara", "villager dead")
        mc.add_event("shara", "werewolf dead")

        self.assertAlmostEqual(0.5, mc.running_probability("shara", "villager dead"))
        self.assertAlmostEqual(0.5, mc.running_probability("shara", "werewolf dead"))

        mc.add_event("shara", "villager dead")
        self.assertAlmostEqual(0.66, mc.running_probability("shara", "villager dead"), delta=0.01)
        self.assertAlmostEqual(0.33, mc.running_probability("shara", "werewolf dead"), delta=0.01)

class NominationRecencyTrackerTests(unittest.TestCase):

    def test_nomination_recency_tracker(self) -> None:
        tracker = NominationRecencyTracker(3)
        christine: SanitizedPlayer = SanitizedPlayer.sanitize(Player("Christine", Werewolf()))
        self.assertEqual([], tracker.get_recent_turns_nomination_made(christine))
        tracker.notemination(christine, 1)
        tracker.notemination(christine, 2)
        tracker.notemination(christine, 3)
        self.assertEqual([1, 2, 3], tracker.get_recent_turns_nomination_made(christine))

class WorldModelTests(unittest.TestCase):

    def test_one_hive_policy(self) -> None:
        world_model = WorldModel()
        chad: SanitizedPlayer = SanitizedPlayer.sanitize(Player("Chad", Villager()))
        # This is a mistake. Chad is never a werewolf!
        world_model.map(chad, Werewolf)
        self.assertEqual(world_model.query_player(chad), Werewolf)
        self.assertTrue(chad in world_model.get_hive(Werewolf))
        # Let's correct this grave mistake
        world_model.map(chad, Villager)
        self.assertEqual(world_model.query_player(chad), Villager)
        self.assertNotEqual(world_model.query_player(chad), Werewolf)
        self.assertTrue(chad in world_model.get_hive(Villager))
        self.assertFalse(chad in world_model.get_hive(Werewolf))
