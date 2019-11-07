import unittest

from ..game_characters import Player, SanitizedPlayer, Villager, Werewolf


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
