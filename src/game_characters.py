from abc import ABC, abstractmethod
from collections import Counter
from typing import Any, Dict, Optional, Sequence, Set, Type

import random
import logging


CONFIGURED_LOGGERS = {}


class Player(object):

    def __init__(
        self,
        name: str,
        role: "GameCharacter",
        aggression: float=0.3,
        suggestibility: float=0.4
    ):
        self.name: str = name
        self.role: GameCharacter = role
        # number between [0, 1]; determines how likely is this player to suggest
        # others for lynching.
        self.aggression: float = aggression
        # number between [0, 1]; determines how likely the suggestion of others
        # influence this player's vote. This applies for any instance where a
        # player needs to participate in consensus.
        self.suggestibility = suggestibility
        self.logger = logging.getLogger("Player")
        self.__configure_logger()

    def __configure_logger(self, _cfg=None):
        global CONFIGURED_LOGGERS
        if CONFIGURED_LOGGERS.get("Player") is None:
            cfg = _cfg if _cfg is not None else {}
            log_level = cfg.get("logLevel", "INFO")
            self.logger.setLevel(logging.getLevelName(log_level))

            log_format = cfg.get("logFormat", "%(asctime)s - %(levelname)s - %(message)s")
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter(log_format))
            self.logger.addHandler(handler)
            CONFIGURED_LOGGERS["Player"] = True
    
    def night_action(self, players: Sequence["SanitizedPlayer"]) -> Optional["SanitizedPlayer"]:
        return self.role.night_action(players)

    def daytime_behavior(self, players: Sequence["SanitizedPlayer"]) -> "SanitizedPlayer":
        return self.role.daytime_behavior(players)

    def accept_vote(self, voted_for: "SanitizedPlayer") -> bool:
        vote_accepted = random.random()
        return vote_accepted <= self.suggestibility

    def __eq__(self, other: Any) -> bool:
        return all((
            self.name == other.name,
            self.role is other.role
        ))

    def __hash__(self) -> int:
        return hash((self.name, self.role))
    
    def __str__(self) -> str:
        return "%s, %s" % (self.name, self.role)
    
    def __repr__(self) -> str:
        return str(self)


class SanitizedPlayer(object):

    def __init__(self, player: Player):
        self.name: str = player.name

    def __eq__(self, other: Any) -> bool:
        return self is other

    def __hash__(self) -> int:
        return id(self)

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return str(self)


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
        self.logger = logging.getLogger("Hive")
        self.__configure_logger()

    def __configure_logger(self, _cfg=None):
        global CONFIGURED_LOGGERS
        if CONFIGURED_LOGGERS.get("Hive") is None:
            cfg = _cfg if _cfg is not None else {}
            log_level = cfg.get("logLevel", "INFO")
            self.logger.setLevel(logging.getLevelName(log_level))

            log_format = cfg.get("logFormat", "%(asctime)s - %(levelname)s - %(message)s")
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter(log_format))
            self.logger.addHandler(handler)
            CONFIGURED_LOGGERS["Hive"] = True
    
    def add_player(self, player: Player):
        self.players.add(player)

    def add_players(self, players: Set[Player]):
        self.players = self.players.union(players)

    @property
    def consensus(self) -> int:
        """
        For this Hive (implementation), how many hive members must agreee before
        we call a consensus?
        """
        return int(len(self.players) / 2)

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
        vote_counter: Counter = Counter()
        for player in self.players:
            voted_for: SanitizedPlayer = player.daytime_behavior(players)
            self.logger.info("%s voted to lynch %s." % (player.name, voted_for.name))
            vote_counter[voted_for] += 1
        # For simplicity's sake, just take the 1 most common; no tie breaks.
        return vote_counter.most_common(1)[0][0]


class WerewolfHive(Hive):

    def __init__(self):
        super().__init__()

    def night_consensus(self, players: Sequence[SanitizedPlayer]) -> Optional[SanitizedPlayer]:
        consensus_count: int = 0
        suggestion: Optional[SanitizedPlayer] = None

        while consensus_count < self.consensus:
            # Pick a random Werewolf to create an initial suggestion.
            potato: Player = random.choice(list(self.players))
            suggestion = potato.night_action(players)
            self.logger.info("%s suggested to kill %s" % (potato, suggestion))
            for hive_member in self.players:
                if hive_member is not potato and suggestion is not None:
                    consensus_count += (
                        1 if hive_member.accept_vote(suggestion) else 0
                    )

            if consensus_count < self.consensus:
                self.logger.info("Suggestion not accepted")
            else:
                self.logger.info("Suggestion accepted")
        return suggestion

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
