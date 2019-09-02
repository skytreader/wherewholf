from abc import ABC, abstractmethod
from typing import Iterable, Optional, Set

import random


class Player(object):

    def __init__(self, name: str):
        self.name: str = name


class GameCharacter(ABC):

    @property
    @abstractmethod
    def prerequisites(self) -> Set[GameCharacter]:
        pass

    @abstractmethod
    def night_action(self, players: Iterable[Player]) -> Optional[Player]:
        pass

    @abstractmethod
    def daytime_behavior(self, players: Iterable[Player]) -> Player:
        pass


class Werewolf(GameCharacter):

    def prerequisites(self) -> Set[GameCharacter]:
        return set()

    def night_action(self, players: Iterable[Player]) -> Optional[Player]:
        return random.choice(players)

    def daytime_behavior(self, players: Iterable[Player]) -> Player:
        return random.choice(players)


class Villager(GameCharacter):

    def prerequisites(self) -> Set[GameCharacter]:
        return set((Werewolf,))

    def night_action(self, players: Iterable[Player]) -> Optional[Player]:
        return random.choice(players)

    def daytime_behavior(self, players: Iterable[Player]) -> Player:
        return random.choice(players)


class Hive(ABC):

    def __init__(self, hivetype: GameCharacter):
        self.hivetype = GameCharacter

    @abstractmethod
    def night_consensus(self, players: Iterable[Player]) -> Optional[Player]:
        pass

    @abstractmethod
    def day_consensus(self, players: Iterable[Player]) -> Player:
        pass


class WerewolfHive(Hive):

    def night_consensus(self, players: Iterable[Player]) -> Optional[Player]:
        return self.hivetype.night_action(players)

    def day_consensus(self, players: Iterable[Player]) -> Player:
        return self.hivetype.day_action(players)
