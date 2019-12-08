from src.game_characters import GameCharacter, Player, Werewolf, Villager
from src.moderator import EndGameState, Moderator

from argparse import ArgumentParser
from collections import Counter
from typing import Set


class Experiment(object):

    def __init__(self, werewolf_count: int=2, villager_count: int=4):
        self.werewolves: Set[Player] = set()
        werewolf_role = Werewolf()

        for i in range(werewolf_count):
            self.werewolves.add(self.__make_player(werewolf_role, i))

        self.villagers: Set[Player] = set()
        villager_role = Villager()

        for i in range(villager_count):
            self.villagers.add(self.__make_player(villager_role, i))
    
    def __make_player(self, role: GameCharacter, count: int) -> Player:
        return Player("%s Player #%s" % (role, count), role)

    def run(self, game_iterations=100) -> Counter:
        wins: Counter = Counter()

        for i in range(game_iterations):
            moderator = Moderator(self.werewolves | self.villagers, str(i))
            wins.update([moderator.play()])

        return wins


if  __name__ == "__main__":
    parser = ArgumentParser(description="Run WhereWholf experiments")
    parser.add_argument(
        "--werewolves", "-w", required=False, default=2,
        help="The number of werewolves in games."
    )
    parser.add_argument(
        "--villagers", "-v", required=False, default=4,
        help="The number of villagers in games."
    )
    parser.add_argument(
        "--games", "-n", required=False, default=100,
        help="The number of games to play."
    )
    args = vars(parser.parse_args())
    experiment = Experiment(args["werewolves"], args["villagers"])
    print(experiment.run(args["games"]))
