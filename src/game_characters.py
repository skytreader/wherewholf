from abc import ABC, abstractmethod
from typing import Optional, Sequence, Set, Type

import random


class Player(object):

    def __init__(self, name: str, role: "GameCharacter"):
        self.name: str = name
        self.role: GameCharacter = role


class GameCharacter(ABC):

    @property
    @abstractmethod
    def prerequisites(self) -> Set[Type["GameCharacter"]]:
        pass

    @abstractmethod
    def night_action(self, players: Sequence[Player]) -> Optional[Player]:
        pass

    @abstractmethod
    def daytime_behavior(self, players: Sequence[Player]) -> Player:
        pass
    
    @property
    @abstractmethod
    def hive(self) -> "Hive":
        pass


class Werewolf(GameCharacter):

    def prerequisites(self) -> Set[Type[GameCharacter]]:
        return set()

    def night_action(self, players: Sequence[Player]) -> Optional[Player]:
        return random.choice(players)

    def daytime_behavior(self, players: Sequence[Player]) -> Player:
        return random.choice(players)

    @property
    def hive(self) -> "Hive":
        return WerewolfHive(Werewolf)


class Villager(GameCharacter):

    def prerequisites(self) -> Set[Type[GameCharacter]]:
        return set((Werewolf,))

    def night_action(self, players: Sequence[Player]) -> Optional[Player]:
        return random.choice(players)

    def daytime_behavior(self, players: Sequence[Player]) -> Player:
        return random.choice(players)

    @property
    def hive(self) -> "Hive":
        return VillagerHive(Villager)


class Hive(ABC):

    def __init__(self, hivetype: Type[GameCharacter]):
        self.hivetype = GameCharacter
        self.players: Set[Player] = set()
    
    def add_player(self, player: Player):
        self.players.add(player)

    @abstractmethod
    def night_consensus(self, players: Sequence[Player]) -> Optional[Player]:
        pass

    @abstractmethod
    def day_consensus(self, players: Sequence[Player]) -> Player:
        pass


class WerewolfHive(Hive):

    def night_consensus(self, players: Sequence[Player]) -> Optional[Player]:
        potato: Player = random.choice(list(self.players))
        return potato.role.night_action(players)

    def day_consensus(self, players: Sequence[Player]) -> Player:
        potato: Player = random.choice(list(self.players))
        return potato.role.daytime_behavior(players)


class VillagerHive(Hive):

    def night_consensus(self, players: Sequence[Player]) -> Optional[Player]:
        return None

    def day_consensus(self, players: Sequence[Player]) -> Player:
        potato: Player = random.choice(list(self.players))
        return potato.role.daytime_behavior(players)
