from game_characters import GameCharacter, Hive, Player
from typing import Dict, Iterable, Set


class Moderator(object):

    def __init__(self, players: Set[Player]):
        self.players: Set[Player] = players
        self.classes: Dict[GameCharacter, Set[Player]] = {}

        for player in players:
            if player.role in self.classes:
                self.classes[type(player.role)].add(player)
            else:
                self.classes[type(player.role)] = Set((player,))

    def __kill_player(self, player) -> None:
        self.players.remove(player)

    def play(self) -> None:
        # Ideally we want this to topo-sort the included characters and then
        # play them based on that but right now we only have Werewolves and
        # Villagers, so f*ck that fancy algorithmic shit.
        pass
