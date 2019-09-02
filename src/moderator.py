from game_characters import GameCharacter, Hive, Player
from typing import Dict, Iterable, Set


class Moderator(object):

    def __init__(self, assignments: Dict[Player, GameCharacter]):
        self.assignments: Dict[Player, GameCharacter] = assignments
        self.players: Set[Player] = assignments.keys()
        self.classes: Dict[GameCharacter, Set[Player]] = {}

        for player, character in assignments:
            if character in self.classes:
                self.classes[character].add(player)
            else:
                self.classes[character] = Set((player,))

    def __kill_player(self, player) -> None:
        self.players.remove(player)

    def play(self) -> None:
        # Ideally we want this to topo-sort the included characters and then
        # play them based on that but right now we only have Werewolves and
        # Villagers, so f*ck that fancy algorithmic shit.
        pass
