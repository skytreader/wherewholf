import unittest

from ..game_characters import (
    GameCharacter, Hive, Player, SanitizedPlayer, Villager, Werewolf,
    WholeGameHive
)
from typing import Optional, Sequence


class InspectablePlayer(Player):

    def __init__(
        self,
        name: str,
        role: GameCharacter,
        aggression: float=0.3,
        suggestibility: float=0.4,
        persuasiveness: float=0.5
    ):
        super().__init__(name, role, aggression, suggestibility, persuasiveness)
        self.was_asked_for_daytime = False

    def daytime_behavior(self, players: Sequence[SanitizedPlayer]) -> SanitizedPlayer:
        self.was_asked_for_daytime = True
        return super().daytime_behavior(players)


class DummyHive(Hive):

    def night_consensus(self, players: Sequence[SanitizedPlayer]) -> Optional[SanitizedPlayer]:
        print("Just a dummy hive...")
        return None

    def day_consensus(self, players: Sequence[SanitizedPlayer]) -> Optional[SanitizedPlayer]:
        print("Just a dummy hive...")
        return None


class PlayerTest(unittest.TestCase):

    def setUp(self):
        self.me = Player("Chad", Villager())
        self.players: Set[Player] = set()
        self.players.add(Player("Christine", Werewolf()))
        self.players.add(Player("Shara", Werewolf()))
        self.players.add(self.me)
        self.players.add(Player("JE", Villager()))
        self.players.add(Player("Gab", Villager()))

        self.sanitized = [SanitizedPlayer.sanitize(p) for p in self.players]

    def test_daytime_behavior(self):
        for _ in range(100):
            lynch: SanitizedPlayer = self.me.daytime_behavior(self.sanitized)
            self.assertFalse(SanitizedPlayer.is_the_same_player(self.me, lynch))


class HiveTest(unittest.TestCase):

    def setUp(self):
        self.some_hive: Hive = DummyHive()
        self.christine = Player("Christine", Werewolf(), aggression=0.9)
        self.chad = Player("Chad", Villager(), aggression=0.7)
        self.josh = Player("Josh", Werewolf, aggression=0.65)

        self.some_hive.add_player(self.christine)
        self.some_hive.add_player(self.chad)
        self.some_hive.add_player(self.josh)
        self.some_hive.add_player(Player("JE", Villager()))
        self.some_hive.add_player(Player("Alvin", Villager(), aggression=0.1))
    
    def test_get_most_aggressive(self):
        expected_top_aggressors = (
            self.christine, self.chad, self.josh
        )
        actual_aggressors = self.some_hive._get_most_aggressive(3)
        self.assertEqual(len(expected_top_aggressors), len(actual_aggressors))

        for eta, aa in zip(expected_top_aggressors, actual_aggressors):
            self.assertEqual(eta, aa)
    
    def test_dead_is_not_aggressive(self):
        # was not invited and will be dead
        charles: Player = Player("Charles", Villager(), aggression=1)
        self.some_hive.add_player(charles)
        aggressors = self.some_hive._get_most_aggressive(3)
        expected_top_aggressors = (
            charles, self.christine, self.chad
        )
        self.assertEqual(expected_top_aggressors, aggressors)

        # Goodbye Charles
        self.some_hive.notify_player_death(charles)
        aggressors = self.some_hive._get_most_aggressive(3)
        expected_top_aggressors = (
            self.christine, self.chad, self.josh
        )
        self.assertEqual(expected_top_aggressors, aggressors)


class WholeGameHiveTest(unittest.TestCase):

    def setUp(self):
        self.me = InspectablePlayer("Chad", Villager())
        self.players: Set[Player] = set()
        self.players.add(Player("Christine", Werewolf()))
        self.players.add(Player("Shara", Werewolf()))
        self.players.add(self.me)
        self.players.add(Player("JE", Villager()))
        self.players.add(Player("Gab", Villager()))

        self.whole_game_hive: WholeGameHive = WholeGameHive()
        self.whole_game_hive.add_players(self.players)

    def test_player_death(self):
        # Betrayed by my so-called "friends", let's say
        self.whole_game_hive.notify_player_death(self.me)
        sanitized = [SanitizedPlayer.sanitize(p) for p in self.players]
        for _ in range(100):
            self.whole_game_hive.day_consensus(sanitized)
            self.assertFalse(self.me.was_asked_for_daytime)
