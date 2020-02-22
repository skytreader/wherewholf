from abc import ABC, abstractmethod
from collections import Counter
from src.errors import AlwaysMeException
from src.pubsub import PubSubBroker
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Set, Tuple, Type
from .utils import NominationTracker, ValueTieCounter

import os
import random
import logging


CONFIGURED_LOGGERS: Dict[str, Any] = {}


class Player(object):

    UNIQUE_PICK_LIMIT = 100

    def __init__(
        self,
        name: str,
        role: "GameCharacter",
        aggression: float=0.3,
        suggestibility: float=0.4,
        persuasiveness: float=0.5,
        hive_affinity: float=0.6,
        nomination_recency: int=3
    ):
        self.name: str = name
        self.role: GameCharacter = role
        self.__player_attr_value_check(aggression)
        self.__player_attr_value_check(suggestibility)
        self.__player_attr_value_check(persuasiveness)
        # number between [0, 1]; determines how likely is this player to suggest
        # others for lynching.
        self.aggression: float = aggression
        # number between [0, 1]; determines how likely the suggestion of others
        # influence this player's vote. This applies for any instance where a
        # player needs to participate in consensus.
        self.suggestibility: float = suggestibility
        # determines how likely this player is to persuade others in hive
        # actions. Can also be a measure of how good this player is at lying.
        self.persuasiveness: float = persuasiveness
        self.nomination_tracker: NominationTracker = NominationTracker(
            nomination_recency
        )
        self.__turn_counter: int = 0
        # Players who belong to particular Hives (e.g., werewolves) have a
        # mental model of who their teammates are. This knowledge should be
        # regulated by the moderator.
        # TODO When players change allegiances, other players in their (old)
        # Hive should not know of this automatically.
        self.hive_members: Set[Player] = set()
        self.hive_affinity: float = hive_affinity
        self.logger = logging.getLogger("Player")
        self.__configure_logger()

    def __player_attr_value_check(self, v: float):
        if v < 0 or v > 1:
            raise ValueError("Attribute should be in the range [0, 1]")

    def __configure_logger(self, _cfg: Dict=None) -> None:
        global CONFIGURED_LOGGERS
        if CONFIGURED_LOGGERS.get("Player") is None:
            cfg = _cfg if _cfg is not None else {}
            log_level = cfg.get("logLevel", os.environ.get("WHEREWHOLF_LOGGER", "INFO"))
            self.logger.setLevel(logging.getLevelName(log_level))

            log_format = cfg.get("logFormat", "%(asctime)s - %(levelname)s - %(message)s")
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter(log_format))
            self.logger.addHandler(handler)
            CONFIGURED_LOGGERS["Player"] = True

    def __is_persecuted(self, players: Sequence["SanitizedPlayer"]) -> bool:
        return len(players) == 1 and SanitizedPlayer.is_the_same_player(self, players[0])
    
    def night_action(self, players: Sequence["SanitizedPlayer"]) -> Optional["SanitizedPlayer"]:
        return self.role.night_action(players)

    def _pick_not_me(
        self,
        players: Sequence["SanitizedPlayer"],
        chooser: Callable[[Sequence["SanitizedPlayer"]], Optional["SanitizedPlayer"]],
        player_compare: Callable[["Player", "SanitizedPlayer"], bool]
    ) -> Optional["SanitizedPlayer"]:
        """
        Given a sequence of players, use the chooser function to pick a player
        that is not _this_ player.
        """
        pick_count = 0
        candidate: Optional[SanitizedPlayer] = chooser(players)

        while candidate and player_compare(self, candidate):
            if pick_count >= Player.UNIQUE_PICK_LIMIT:
                return None
            pick_count += 1
            candidate = chooser(players)

        return candidate

    def __pick_from_hive_suggestion(self, nominations: Sequence["Nomination"]) -> Optional["SanitizedPlayer"]:
        # FIXME Maybe: *Can* be slow
        # Filter out the nominations first...
        def is_hivemate(sp: SanitizedPlayer) -> bool:
            """
            This method is placed here so as to prevent other methods of this
            class from deducing possible game state changes it should not be
            privy to; you can potentially use this to observe allegiance changes!
            """
            for member in self.hive_members:
                if SanitizedPlayer.is_the_same_player(member, sp):
                    return True

            return False

        teammate_noms: Set["Nomination"] = set([
            nom for nom in nominations if is_hivemate(nom.nominated_by)
        ])

        if not teammate_noms:
            return None
        else:
            return random.choice(list(teammate_noms)).nomination

    def daytime_behavior(self, nominations: Sequence["Nomination"]) -> Optional["SanitizedPlayer"]:
        will_follow_hive = random.random()

        if will_follow_hive <= self.hive_affinity and self.hive_members:
            return self.__pick_from_hive_suggestion(nominations)

        players: Sequence[SanitizedPlayer] = [nom.nomination for nom in nominations]
        chance = random.random()
        # If you are persecuted, might as well abstain. In a final show of
        # defiance, you might want to vote someone else just for the heck of it.
        # But ultimately, it is meaningless since everyone else might just
        # choose you. So we won't waste instruction cycles on your admirable yet
        # all the same pointless act.
        if chance <= self.aggression and not self.__is_persecuted(players):
            return self._pick_not_me(
                players,
                self.role.daytime_behavior,
                SanitizedPlayer.is_the_same_player
            )
        return None

    def ask_lynch_nomination(self, players: Sequence["SanitizedPlayer"]) -> Optional["Nomination"]:
        """
        Given the players still alive in the game, get a nomination from this
        player on who to lynch.
        """
        pick_on: SanitizedPlayer = self._pick_not_me(
            players,
            self.role.daytime_behavior,
            SanitizedPlayer.is_the_same_player
        )
        return Nomination(pick_on, SanitizedPlayer.sanitize(self))

    def accept_night_suggestion(
        self,
        voted_for: "SanitizedPlayer",
        suggested_by: "SanitizedPlayer"
    ) -> bool:
        """
        Use this for consensus calls during the night.
        """
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
        for speed and tracking and it's messy to do that in the constructor. To
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
            sanitized: SanitizedPlayer = SanitizedPlayer(player)
            SanitizedPlayer.__SANITATION_CACHE[player] = sanitized
            SanitizedPlayer.__PLAYER_MEMORY[sanitized] = player
            return sanitized

    @staticmethod
    def recover_player_identity(splayer: "SanitizedPlayer") -> Player:
        """
        WARNING: For adults only!

        Since this gives you access to a `Player` object--and so, subsequently,
        the role of the given `SanitizedPlayer` using this method is greatly
        discouraged. Whenever possible, use the method `is_the_same_player`
        instead.
        """
        return SanitizedPlayer.__PLAYER_MEMORY[splayer]

    @staticmethod
    def is_the_same_player(player: Player, splayer: "SanitizedPlayer") -> bool:
        _sanitize_player: Optional[SanitizedPlayer] = SanitizedPlayer.__SANITATION_CACHE.get(player)
        _actual_player: Optional[Player] = SanitizedPlayer.__PLAYER_MEMORY.get(splayer)

        return player is _actual_player and splayer is _sanitize_player

    def __eq__(self, other: Any) -> bool:
        return self is other

    def __hash__(self) -> int:
        return id(self)

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return str(self)


class Nomination(object):

    def __init__(self, nomination: SanitizedPlayer, nominated_by: SanitizedPlayer):
        self.nomination: SanitizedPlayer = nomination
        self.nominated_by: SanitizedPlayer = nominated_by

    def __eq__(self, other: Any) -> bool:
        return all((
            self.nomination == other.nomination,
            self.nominated_by == other.nominated_by
        ))

    def __hash__(self) -> int:
        return hash((self.nomination, self.nominated_by))


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
    def daytime_behavior(self, players: Sequence[SanitizedPlayer]) -> Optional[SanitizedPlayer]:
        pass

    @abstractmethod
    def __str__(self) -> str:
        return "Generic GameCharacter"


class Werewolf(GameCharacter):

    def prerequisites(self) -> Set[Type[GameCharacter]]:
        return set()

    def night_action(self, players: Sequence[SanitizedPlayer]) -> Optional[SanitizedPlayer]:
        return random.choice(players)

    def daytime_behavior(self, players: Sequence[SanitizedPlayer]) -> Optional[SanitizedPlayer]:
        return random.choice(players)

    def __str__(self) -> str:
        return "Werewolf"


class Villager(GameCharacter):

    def prerequisites(self) -> Set[Type[GameCharacter]]:
        return set((Werewolf,))

    def night_action(self, players: Sequence[SanitizedPlayer]) -> Optional[SanitizedPlayer]:
        return random.choice(players)

    def daytime_behavior(self, players: Sequence[SanitizedPlayer]) -> Optional[SanitizedPlayer]:
        if players:
            return random.choice(players)
        return None

    def __str__(self) -> str:
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

    @property
    def can_members_know_each_other(self) -> bool:
        return False

    def __configure_logger(self, _cfg: Dict=None) -> None:
        global CONFIGURED_LOGGERS
        if CONFIGURED_LOGGERS.get("Hive") is None:
            cfg = _cfg if _cfg is not None else {}
            log_level = cfg.get("logLevel", os.environ.get("WHEREWHOLF_LOGGER", "INFO"))
            self.logger.setLevel(logging.getLevelName(log_level))

            log_format = cfg.get("logFormat", "%(asctime)s - %(levelname)s - %(message)s")
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter(log_format))
            self.logger.addHandler(handler)
            CONFIGURED_LOGGERS["Hive"] = True

    def _publish_event(self, event_type: str, body: str) -> None:
        if self.pubsub_broker:
            self.pubsub_broker.broadcast_message(event_type, body)

    def _get_most_aggressive(self, n: int=3) -> Tuple[Player, ...]:
        """
        Return the n most aggressive members of this Hive, ordered descending
        with respect to aggression.
        """
        player_list: List[Player] = list(self.alive_players)
        aggression_map: Dict[Player, float] = {p:p.aggression for p in player_list}
        c = ValueTieCounter(aggression_map)
        return tuple(kv[0] for kv in c.most_common(n))
    
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

    def __gather_votes(self, nominations: Sequence[Nomination]) -> List[Tuple[Player, int]]:
        candidates = [nom.nomination for nom in nominations]
        vote_counter: Counter = ValueTieCounter()

        # Force these players to vote!
        while len(vote_counter.most_common(1)) == 0:
            for player in self.alive_players:
                voted_for: Optional[SanitizedPlayer] = player.daytime_behavior(nominations)
                if voted_for is not None:
                    self.logger.info("%s voted to lynch %s." % (player.name, voted_for))
                    vote_counter[SanitizedPlayer.recover_player_identity(voted_for)] += 1

        return vote_counter.most_common(1)

    def __gather_nominations(self, players: Sequence[SanitizedPlayer]) -> Sequence[Nomination]:
        aggressive_players: Tuple[Player, ...] = self._get_most_aggressive()
        candidates: Set[Nomination] = set()
        for ap in aggressive_players:
            candidate: Optional[Nomination] = ap.ask_lynch_nomination(players)
            if candidate is not None:
                self.logger.info("%s nominated %s for lynching." % (ap, candidate))
                candidates.add(candidate)
        return list(candidates)

    def day_consensus(self, players: Sequence[SanitizedPlayer]) -> Optional[SanitizedPlayer]:
        initial_candidates: Sequence[Nomination] = self.__gather_nominations(players)
        # Build a nomination map for easy reference
        nomination_map: Dict[SanitizedPlayer, SanitizedPlayer] = {
            nom.nomination: nom.nominated_by for nom in initial_candidates
        }

        self.logger.info("The candidates for lynching are %s" % initial_candidates)
        consensus: List[Tuple[Player, int]] = self.__gather_votes(initial_candidates)

        while len(consensus) > 1:
            candidate_players: List[Player] = [vote_tuple[0] for vote_tuple in consensus]
            self.logger.info("Tie between %s" % str(candidate_players))
            tied_nominations = [
                Nomination(
                    SanitizedPlayer.sanitize(p),
                    nomination_map[SanitizedPlayer.sanitize(p)]
                ) for p in candidate_players
            ]
            consensus = self.__gather_votes(tied_nominations)
            self.logger.debug(consensus)
        return SanitizedPlayer.sanitize(consensus[0][0])


class WerewolfHive(Hive):

    def __init__(self) -> None:
        super().__init__()

    @property
    def can_members_know_each_other(self) -> bool:
        return True

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
                        1 if hive_member.accept_night_suggestion(suggestion, SanitizedPlayer.sanitize(potato)) else 0
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
        return None


CHARACTER_HIVE_MAPPING: Dict[Type["GameCharacter"], Type["Hive"]] = {
    Werewolf: WerewolfHive,
    Villager: VillagerHive
}
