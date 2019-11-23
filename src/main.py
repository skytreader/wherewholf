from .game_characters import GameCharacter, Player, Werewolf, Villager
from .moderator import Moderator

from typing import Set


if __name__ == "__main__":
    players: Set[Player] = set()
    players.add(Player("Christine", Werewolf()))
    players.add(Player("Shara", Werewolf()))
    players.add(Player("Chad", Villager()))
    players.add(Player("JE", Villager()))
    players.add(Player("Gab", Villager()))
    players.add(Player("Charles", Villager()))

    mod: Moderator = Moderator(players)
    mod.play()
