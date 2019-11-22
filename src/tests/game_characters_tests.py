import unittest

from ..game_characters import Player, SanitizedPlayer, Villager, Werewolf, WholeGameHive
from typing import Sequence


class InspectablePlayer(Player):

    def __init__(
        self,
        name: str,
        role: "GameCharacter",
        aggression: float=0.3,
        suggestibility: float=0.4,
        persuasiveness: float=0.5
    ):
        super().__init__(name, role, aggression, suggestibility, persuasiveness)
        self.was_asked_for_daytime = False

    def day_consensus(self, players: Sequence[SanitizedPlayer]) -> SanitizedPlayer:
        self.was_asked_for_daytime = True
        return super().day_consensus(players)


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


class WholeGameHiveTest(unittest.TestCase):

    def setUp(self):
        self.me = InspectablePlayer("Chad", Villager())
        self.players: Set[Player] = set()
        self.players.add(Player("Christine", Werewolf()))
        self.players.add(Player("Shara", Werewolf()))
        self.players.add(self.me)
        self.players.add(Player("JE", Villager()))
        self.players.add(Player("Gab", Villager()))

        self.whole_game_hive = WholeGameHive()
        self.whole_game_hive.add_players(self.players)

    def test_player_death(self):
        # Betrayed by my so-called "friends", let's say
        self.whole_game_hive.notify_player_death(self.me)
        sanitized = [SanitizedPlayer.sanitize(p) for p in self.players]
        for _ in range(100):
            self.whole_game_hive.day_consensus(sanitized)
            self.assertFalse(self.me.was_asked_for_daytime)
