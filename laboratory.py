from src.game_characters import GameCharacter, Player, Werewolf, Villager
from src.moderator import EndGameState, Moderator

from collections import Counter
from typing import Set


class Experiment(object):

    def __init__(self, werewolf_count: int=2, villager_count: int=4, game_iterations=100):
        self.werewolves: Set[Player] = set()
        werewolf_role = Werewolf()

        for i in range(werewolf_count):
            self.werewolves.add(self.__make_player(werewolf_role, i))

        self.villagers: Set[Player] = set()
        villager_role = Villager()

        for i in range(villager_count):
            self.villagers.add(self.__make_player(villager_role, i))

        self.game_iterations = game_iterations
    
    def __make_player(self, role: GameCharacter, count: int) -> Player:
        return Player("%s Player #%s" % (role, count), role)

    def run(self) -> Counter:
        wins: Counter = Counter()

        for i in range(self.game_iterations):
            moderator = Moderator(self.werewolves | self.villagers, str(i))
            wins.update([moderator.play()])

        return wins


if  __name__ == "__main__":
    experiment = Experiment()
    print(experiment.run())
