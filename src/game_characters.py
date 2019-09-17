from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Sequence, Set, Type

import random


class Player(object):

    def __init__(self, name: str, role: "GameCharacter"):
        self.name: str = name
        self.role: GameCharacter = role
    
    def night_action(self, players: Sequence["SanitizedPlayer"]) -> Optional["SanitizedPlayer"]:
        return self.role.night_action(players)

    def daytime_behavior(self, players: Sequence["SanitizedPlayer"]) -> "SanitizedPlayer":
        return self.role.daytime_behavior(players)

    def sanitize(self) -> "SanitizedPlayer":
        return SanitizedPlayer(self)

    def __eq__(self, other: Any) -> bool:
        return all((
            self.name == other.name,
            self.role is other.role
        ))


    def __hash__(self):
        return hash((self.name, self.role))


class SanitizedPlayer(object):

    def __init__(self, player: Player):
        self.name: str = player.name

    def __eq__(self, other: Any) -> bool:
        return self is other

    def __hash__(self):
        return id(self)


class GameCharacter(ABC):
    """
    GameCharacters encapsulate a role in a game of Werewolf as well as the
    behavior of an individual assigned to that role. GameCharacter subclasses
    must maintain a strict hierarachy in terms of behavior:

    1. at the root is this abstract base class
    2. following this class is a bunch of classes who represent the roles in a
       Werewolf game. They have some behavior encoded but there is little logic
       governing their behavior.
    3. following #2 are a bunch of classes that start to implement a more
       logical behavior in the game.
    """

    @property
    @abstractmethod
    def prerequisites(self) -> Set[Type["GameCharacter"]]:
        pass

    @abstractmethod
    def night_action(self, players: Sequence[SanitizedPlayer]) -> Optional[SanitizedPlayer]:
        pass

    @abstractmethod
    def daytime_behavior(self, players: Sequence[SanitizedPlayer]) -> SanitizedPlayer:
        pass

    @abstractmethod
    def __str__(self):
        return "Generic GameCharacter"


class Werewolf(GameCharacter):

    def prerequisites(self) -> Set[Type[GameCharacter]]:
        return set()

    def night_action(self, players: Sequence[SanitizedPlayer]) -> Optional[SanitizedPlayer]:
        return random.choice(players)

    def daytime_behavior(self, players: Sequence[SanitizedPlayer]) -> SanitizedPlayer:
        return random.choice(players)

    def __str__(self):
        return "Werewolf"


class Villager(GameCharacter):

    def prerequisites(self) -> Set[Type[GameCharacter]]:
        return set((Werewolf,))

    def night_action(self, players: Sequence[SanitizedPlayer]) -> Optional[SanitizedPlayer]:
        return random.choice(players)

    def daytime_behavior(self, players: Sequence[SanitizedPlayer]) -> SanitizedPlayer:
        return random.choice(players)

    def __str__(self):
        return "Villager"


class Hive(ABC):
    """
    A Hive represents a group of players (who are often under the same role)
    and their collective decisions throughout the game.
    """

    def __init__(self):
        self.players: Set[Player] = set()
    
    def add_player(self, player: Player):
        self.players.add(player)

    def add_players(self, players: Set[Player]):
        self.players = self.players.union(players)

    @abstractmethod
    def night_consensus(self, players: Sequence[SanitizedPlayer]) -> Optional[SanitizedPlayer]:
        pass

    @abstractmethod
    def day_consensus(self, players: Sequence[SanitizedPlayer]) -> SanitizedPlayer:
        pass

class WholeGameHive(Hive):
    """
    This is a special hive that should contain all players. The purpose is for
    arriving at a consensus during the day. Hence, the night_consensus is not
    implemented.
    """

    def night_consensus(self, players: Sequence[SanitizedPlayer]) -> Optional[SanitizedPlayer]:
        raise NotImplemented("WholeGameHive is for lynching decisions only.")

    def day_consensus(self, players: Sequence[SanitizedPlayer]) -> SanitizedPlayer:
        potato: Player = random.choice(list(self.players))
        return potato.daytime_behavior(players)


class WerewolfHive(Hive):

    def night_consensus(self, players: Sequence[SanitizedPlayer]) -> Optional[SanitizedPlayer]:
        potato: Player = random.choice(list(self.players))
        return potato.night_action(players)

    def day_consensus(self, players: Sequence[SanitizedPlayer]) -> SanitizedPlayer:
        potato: Player = random.choice(list(self.players))
        return potato.daytime_behavior(players)


class VillagerHive(Hive):

    def night_consensus(self, players: Sequence[SanitizedPlayer]) -> Optional[SanitizedPlayer]:
        return None

    def day_consensus(self, players: Sequence[SanitizedPlayer]) -> SanitizedPlayer:
        potato: Player = random.choice(list(self.players))
        return potato.daytime_behavior(players)


CHARACTER_HIVE_MAPPING: Dict[Type["GameCharacter"], Type["Hive"]] = {
    Werewolf: WerewolfHive,
    Villager: VillagerHive
}
