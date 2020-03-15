import unittest

from ..game_characters import GameCharacter, Player, Werewolf, Villager
from ..moderator import Moderator, EndGameState

from typing import Set


class ModeratorTest(unittest.TestCase):

    def test_endgame(self) -> None:
        players: Set[Player] = set()
        players.add(Player("Christine", Werewolf()))
        players.add(Player("Shara", Werewolf()))
        players.add(Player("Chad", Villager()))
        players.add(Player("JE", Villager()))
        players.add(Player("Gab", Villager()))
        players.add(Player("Charles", Villager()))

        for _ in range(100):
            mod: Moderator = Moderator(players)
            self.assertNotEqual(EndGameState.UNKNOWN_CONDITION, mod.play())
