from abc import ABC, abstractmethod
from collections import Counter
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple, Type
from src.pubsub import PubSubBroker

import random
import logging


CONFIGURED_LOGGERS: Dict[str, Any] = {}


class Player(object):

    def __init__(
        self,
        name: str,
        role: "GameCharacter",
        aggression: float=0.3,
        suggestibility: float=0.4,
        persuasiveness: float=0.5
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
        # determines how likely this player is to persuade others in hive
        # actions. Can also be a measure of how good this player is at lying.
        self.persuasiveness = persuasiveness
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
        candidate: "SanitizedPlayer" = self.role.daytime_behavior(players)
        while SanitizedPlayer.is_the_same_player(self, candidate):
            candidate = self.role.daytime_behavior(players)

        return candidate

    def accept_suggestion(
        self,
        voted_for: "SanitizedPlayer",
        suggested_by: "SanitizedPlayer"
    ) -> bool:
        vote_accepted = random.random()
        return vote_accepted <= (
            self.suggestibility * suggested_by.persuasiveness
        )

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
    
    __SANITATION_CACHE: Dict[Player, "SanitizedPlayer"] = {}
    __PLAYER_MEMORY: Dict["SanitizedPlayer", Player] = {}

    def __init__(self, player: Player):
        """
        NOTE: DO NOT USE THIS CONSTRUCTOR! This class "caches" SanitizedPlayers
        for speed and tracking and it messy to do that in the constructor. To
        sanitize players, use the `sanitize` static method instead.
        """
        self.name: str = player.name
        self.aggression: float = player.aggression
        self.persuasiveness : float = player.persuasiveness

    @staticmethod
    def sanitize(player: Player) -> "SanitizedPlayer":
        exists: Optional[SanitizedPlayer] = SanitizedPlayer.__SANITATION_CACHE.get(player)

        if exists:
            return exists
        else:
            sanitized = SanitizedPlayer(player)
            SanitizedPlayer.__SANITATION_CACHE[player] = sanitized
            SanitizedPlayer.__PLAYER_MEMORY[sanitized] = player
            return sanitized

    @staticmethod
    def recover_player_identity(splayer: "SanitizedPlayer") -> Player:
        return SanitizedPlayer.__PLAYER_MEMORY[splayer]

    @staticmethod
    def is_the_same_player(player: Player, splayer: "SanitizedPlayer") -> bool:
        _sanitize_player = SanitizedPlayer.__SANITATION_CACHE.get(player)
        _actual_player = SanitizedPlayer.__PLAYER_MEMORY.get(splayer)

        return player is _actual_player and splayer is _sanitize_player

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

    def __init__(self, pubsub_broker: Optional[PubSubBroker]=None):
        # These are the players included in the hive
        self.players: Set[Player] = set()
        # Set of _all_ dead players
        self.dead_players: Set[Player] = set()
        self.pubsub_broker: Optional[PubSubBroker] = pubsub_broker
        self.logger: logging.Logger = logging.getLogger("Hive")
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

    def _publish_event(self, event_type: str, body: str):
        if self.pubsub_broker:
            self.pubsub_broker.broadcast_message(event_type, body)

    def _get_most_aggressive(self, n: int=3) -> Tuple[Player, ...]:
        """
        Return the n most aggressive members of this Hive, ordered descending
        with respect to aggression.
        """
        player_list: List[Player] = list(self.alive_players)
        player_list.sort(key=lambda p: p.aggression, reverse=True)
        return tuple(player_list[:n])
    
    def add_player(self, player: Player) -> None:
        self.players.add(player)

    def add_players(self, players: Set[Player]) -> None:
        self.players = self.players.union(players)

    def notify_player_death(self, player: Player) -> None:
        self.logger.debug("%s learned of %s death" % (
            self.__class__.__name__, player
        ))
        self.dead_players.add(player)

    @property
    def alive_players(self) -> Iterable[Player]:
        return set(self.players) - self.dead_players

    @property
    def consensus(self) -> int:
        """
        For this Hive (implementation), how many hive members must agreee before
        we call a consensus?
        """
        return int(len(self.players) / 2)

    @abstractmethod
    def night_consensus(self, players: Sequence[SanitizedPlayer]) -> Optional[SanitizedPlayer]:
        """
        Given the players currently in the game, this hive must decide on their
        night action for this turn.
        """
        pass

    @abstractmethod
    def day_consensus(self, players: Sequence[SanitizedPlayer]) -> Optional[SanitizedPlayer]:
        """
        Given the list of players still in the game, this hive must decide on
        their day action for this turn.
        """
        raise NotImplemented("This faction will not reveal itself!")


class WholeGameHive(Hive):
    """
    This is a special hive that should contain all players. The purpose is for
    arriving at a consensus during the day. Hence, the night_consensus is not
    implemented.
    """

    def night_consensus(self, players: Sequence[SanitizedPlayer]) -> Optional[SanitizedPlayer]:
        raise NotImplemented("WholeGameHive is for lynching decisions only.")

    def day_consensus(self, players: Sequence[SanitizedPlayer]) -> Optional[SanitizedPlayer]:
        vote_counter: Counter = Counter()
        for player in self.alive_players:
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
            potato: Player = random.choice(self._get_most_aggressive())
            suggestion = potato.night_action(players)
            self.logger.info("%s suggested to kill %s" % (potato, suggestion))
            for hive_member in self.players:
                if hive_member is not potato and suggestion is not None:
                    consensus_count += (
                        1 if hive_member.accept_suggestion(suggestion, SanitizedPlayer.sanitize(potato)) else 0
                    )

            if consensus_count < self.consensus:
                self._publish_event("CONSENSUS_NOT_REACHED", "werewolves")
                self.logger.info("Suggestion not accepted")
            else:
                self.logger.info("Suggestion accepted")
        return suggestion

    def day_consensus(self, players: Sequence[SanitizedPlayer]) -> Optional[SanitizedPlayer]:
        raise NotImplemented("This faction will not reveal itself!")


class VillagerHive(Hive):

    def night_consensus(self, players: Sequence[SanitizedPlayer]) -> Optional[SanitizedPlayer]:
        return None

    def day_consensus(self, players: Sequence[SanitizedPlayer]) -> Optional[SanitizedPlayer]:
        potato: Player = random.choice(list(self.players))
        return potato.daytime_behavior(players)


CHARACTER_HIVE_MAPPING: Dict[Type["GameCharacter"], Type["Hive"]] = {
    Werewolf: WerewolfHive,
    Villager: VillagerHive
}
