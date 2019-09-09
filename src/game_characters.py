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
    
    @classmethod
    @abstractmethod
    def hive(cls) -> Type["Hive"]:
        pass

    @abstractmethod
    def __str__(self):
        return "Generic GameCharacter"


class Werewolf(GameCharacter):

    def prerequisites(self) -> Set[Type[GameCharacter]]:
        return set()

    def night_action(self, players: Sequence[Player]) -> Optional[Player]:
        return random.choice(players)

    def daytime_behavior(self, players: Sequence[Player]) -> Player:
        return random.choice(players)

    @classmethod
    def hive(cls) -> Type["Hive"]:
        return WerewolfHive

    def __str__(self):
        return "Werewolf"


class Villager(GameCharacter):

    def prerequisites(self) -> Set[Type[GameCharacter]]:
        return set((Werewolf,))

    def night_action(self, players: Sequence[Player]) -> Optional[Player]:
        return random.choice(players)

    def daytime_behavior(self, players: Sequence[Player]) -> Player:
        return random.choice(players)

    @classmethod
    def hive(cls) -> Type["Hive"]:
        return VillagerHive

    def __str__(self):
        return "Villager"


class Hive(ABC):

    def __init__(self):
        self.players: Set[Player] = set()
    
    def add_player(self, player: Player):
        self.players.add(player)

    def add_players(self, players: Set[Player]):
        self.players.union(players)

    @abstractmethod
    def night_consensus(self, players: Sequence[Player]) -> Optional[Player]:
        pass

    @abstractmethod
    def day_consensus(self, players: Sequence[Player]) -> Player:
        pass

class WholeGameHive(Hive):
    """
    This is a special hive that should contain all players. The purpose is for
    arriving at a consensus during the day. Hence, the night_consensus is not
    implemented.
    """

    def night_consensus(self, players: Sequence[Player]) -> Optional[Player]:
        raise NotImplemented("WholeGameHive is for lynching decisions only.")

    def day_consensus(self, players: Sequence[Player]) -> Player:
        potato: Player = random.choice(list(self.players))
        return potato.role.daytime_behavior(players)


class WerewolfHive(Hive):

    def night_consensus(self, players: Sequence[Player]) -> Optional[Player]:
        print("my players " + str(self.players))
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
