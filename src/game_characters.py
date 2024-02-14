from abc import ABC, abstractmethod
from collections import Counter
from src.errors import GameDeadLockError, InvalidGameStateError
from src.pubsub import PubSubBroker
from typing import Any, Callable, Dict, Iterable, List, Optional, override, Sequence, Set, Tuple, Type
from .utils import NominationRecencyTracker, ValueTieCounter, WorldModel

import os
import random
import logging


CONFIGURED_LOGGERS: Dict[str, Any] = {}
VoteTable = Dict["SanitizedPlayer", Optional["SanitizedPlayer"]]
NominationMap = Dict["SanitizedPlayer", "SanitizedPlayer"]


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
        self.nomination_recency: NominationRecencyTracker = NominationRecencyTracker(
            nomination_recency
        )
        self.__turn_count: int = 0
        self.hive_affinity: float = hive_affinity
        self.world_model = WorldModel()
        self.nominated_this_turn: Optional["SanitizedPlayer"] = None
        self.logger = logging.getLogger("Player")
        self.__configure_logger()

    def __player_attr_value_check(self, v: float):
        if v < 0 or v > 1:
            raise ValueError("Attribute should be in the range [0, 1]")

    def __configure_logger(self, _cfg: Optional[Dict]=None) -> None:
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
        # TODO Maybe if you know your hivemates for certain, don't pick them.
        # Don't use players.remove because we don't want to modify the argument
        without_me: List["SanitizedPlayer"] = [
            _player for _player in players if not player_compare(self, _player)
       ]
        if len(without_me):
            return chooser(without_me)

        return None

    @property
    def hive_members(self):
        return self.world_model.get_hive(type(self.role))

    def __pick_from_hive_suggestion(self, nominations: Sequence["Nomination"]) -> Optional["SanitizedPlayer"]:
        teammate_noms: Set["Nomination"] = set([
            nom for nom in nominations if (
                nom.nominated_by in self.hive_members
            )
        ])

        if not teammate_noms:
            return None
        else:
            return random.choice(list(teammate_noms)).nomination

    def learn_hive_member(self, sanitized_player: "SanitizedPlayer"):
        self.world_model.map(sanitized_player, type(self.role))
    
    def __make_attr_decision(
        self,
        attr: float,
        decider: Callable[[], float]=random.random
    ) -> bool:
        """
        Where `attr` is a value in the range [0, 1] and `decider` returns a
        value in the same range, this function returns True when `decider`
        returns a value in the range [0, attr]. The distribution can be
        controlled by passing a different `decider` function.
        """
        return decider() <= attr

    def __is_player_credible(self, player: "SanitizedPlayer") -> bool:
        # Very simple for now
        return self.world_model.query_player(player) is not Werewolf

    def __is_nomination_accepted(self, nomination: "Nomination") -> bool:
        last_turn_of_note = self.__turn_count - self.nomination_recency.recency
        recent_turns = self.nomination_recency.get_recent_turns_nomination_made(
            nomination.nominated_by
        )
        # Aggressive players will be seen as too pushy and, hence, less
        # credible.
        return not (
            min(recent_turns) >= last_turn_of_note and
            not self.__make_attr_decision(self.suggestibility)
        ) and self.__is_player_credible(nomination.nominated_by)

    def daytime_behavior(self, nominations: Sequence["Nomination"]) -> Optional["SanitizedPlayer"]:
        self.__turn_count += 1

        if self.nominated_this_turn is not None:
            conviction_vote = self.nominated_this_turn
            self.nominated_this_turn = None
            return conviction_vote

        if self.__make_attr_decision(self.hive_affinity) and self.hive_members:
            return self.__pick_from_hive_suggestion(nominations)
        
        # Filter out nominations first based on how aggressive the nominators
        # are, coupled with how suggestible this player is.
        considered_nominations: List[SanitizedPlayer] = []
        for nom in nominations:
            self.nomination_recency.notemination(
                nom.nominated_by, self.__turn_count
            )

            if self.__is_nomination_accepted(nom):
                considered_nominations.append(nom.nomination)

        # If you are persecuted, might as well abstain. In a final show of
        # defiance, you might want to vote someone else just for the heck of it.
        # But ultimately, it is meaningless since everyone else might just
        # choose you. So we won't waste instruction cycles on your admirable yet
        # all the same pointless act.
        if not self.__is_persecuted(considered_nominations):
            return self._pick_not_me(
                considered_nominations,
                self.role.daytime_behavior,
                SanitizedPlayer.is_the_same_player
            )
        return None

    def ask_lynch_nomination(self, players: Sequence["SanitizedPlayer"]) -> Optional["Nomination"]:
        """
        Given the players still alive in the game, get a nomination from this
        player on who to lynch.
        """
        if self.__make_attr_decision(self.aggression):
            pick: Optional[SanitizedPlayer] = self._pick_not_me(
                players,
                self.role.daytime_behavior,
                SanitizedPlayer.is_the_same_player
            )
            if pick:
                self.nominated_this_turn = pick
                return Nomination(pick, SanitizedPlayer.sanitize(self))

        return None

    def accept_night_suggestion(
        self,
        voted_for: "SanitizedPlayer",
        suggested_by: "SanitizedPlayer"
    ) -> bool:
        """
        Use this for consensus calls during the night.
        """
        return (
            SanitizedPlayer.is_the_same_player(self, suggested_by) or
            self.__make_attr_decision(self.suggestibility)
        )

    def react_to_lynch_result(
        self,
        final_nominations: NominationMap,
        victim: "Player",
        final_vote_table: VoteTable
    ) -> None:
        """
        At the end of the day, the result of the lynching vote is broadcasted to
        all remaining players. They can react/adjust their world models based on
        the result of this vote.
        """
        victim_sanitized = SanitizedPlayer.sanitize(victim)
        if type(victim.role) is not Werewolf:
            for nominator in final_nominations:
                if final_nominations[nominator] is victim_sanitized:
                    self.world_model.map(nominator, Werewolf)

            for voter in final_vote_table:
                if final_vote_table[voter] is victim_sanitized:
                    self.world_model.map(voter, Werewolf)

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
    __create_key = object()

    def __init__(self, create_key: Any, player: Player):
        """
        NOTE: DO NOT USE THIS CONSTRUCTOR! This class "caches" SanitizedPlayers
        for speed and tracking and it's messy to do that in the constructor. To
        sanitize players, use the `sanitize` static method instead.
        """
        if create_key is not SanitizedPlayer.__create_key:
            raise Exception("Please use SanitizedPlayer.sanitize to create SanitizedPlayers.")
        self.name: str = player.name
        self.aggression: float = player.aggression
        self.persuasiveness : float = player.persuasiveness

    @classmethod
    def sanitize(cls, player: Player) -> "SanitizedPlayer":
        # FIXME later when we allow role swapping effects, we also have to check
        # if __PLAYER_MEMORY still corresponds to the actual roles in the game.
        # Consider also that this makes a coupling between this class and the
        # game state.
        exists: Optional[SanitizedPlayer] = SanitizedPlayer.__SANITATION_CACHE.get(player)

        if exists:
            return exists
        else:
            sanitized: SanitizedPlayer = SanitizedPlayer(cls.__create_key, player)
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

    def __str__(self) -> str:
        return "(%s -nominated-> %s)" % (self.nominated_by, self.nomination)


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

    @override
    @property
    def prerequisites(self) -> Set[Type["GameCharacter"]]:
        return set()

    def night_action(self, players: Sequence[SanitizedPlayer]) -> Optional[SanitizedPlayer]:
        return random.choice(players)

    def daytime_behavior(self, players: Sequence[SanitizedPlayer]) -> Optional[SanitizedPlayer]:
        return random.choice(players)

    def __str__(self) -> str:
        return "Werewolf"


class Villager(GameCharacter):

    @override
    @property
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
    A Hive represents a group of players who need to decide collectively at
    various points of the game. The Hive should ensure that collective decisions
    have reached consensus.
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

    def __configure_logger(self, _cfg: Optional[Dict]=None) -> None:
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
    def alive_players(self) -> Set[Player]:
        return set(self.players) - self.dead_players

    @property
    def consensus(self) -> int:
        """
        For this Hive (implementation), how many hive members must agree before
        we call a consensus?
        """
        alive_player_count = len(self.alive_players)
        if alive_player_count == 1:
            return 1
        else:
            return int(alive_player_count / 2)

    def has_reached_consensus(self, votes: int) -> bool:
        """
        Override this method to implement other majority decision schemes.
        """
        if votes > len(self.alive_players):
            raise InvalidGameStateError("Asked for consensus on more votes than possible for this hive. (votes: %s, alive players: %s)" % (votes, len(self.alive_players)))
        return votes >= self.consensus

    @abstractmethod
    def night_consensus(self, players: Sequence[SanitizedPlayer]) -> Optional[SanitizedPlayer]:
        """
        Given a group of players (such as might be achieved from a nomination
        process), this hive must decide on their night action for this turn.
        """
        pass

    @abstractmethod
    def day_consensus(self, players: Sequence[SanitizedPlayer]) -> Tuple[NominationMap, VoteTable]:
        """
        Given a group of players (such as might be achieved from a nomincation
        process), this hive must decide on their day action for this turn.

        (FIXME It seems that only the WholeGameHive would really use this.)
        """
        raise NotImplementedError("This faction will not reveal itself!")


class WholeGameHive(Hive):
    """
    This is a special hive that should contain all players. The purpose is for
    arriving at a consensus during the day. Hence, the night_consensus is not
    implemented.
    """

    MAX_LOOP_ITERS = 100

    def night_consensus(self, players: Sequence[SanitizedPlayer]) -> Optional[SanitizedPlayer]:
        raise NotImplementedError("WholeGameHive is for lynching decisions only.")

    def __gather_votes(self, nominations: Sequence[Nomination]) -> VoteTable:
        candidates = [nom.nomination for nom in nominations]
        vote_counter: Counter = ValueTieCounter()
        vote_table: VoteTable = {}
        deadlock_counter = 0

        # Force these players to vote!
        while len(vote_counter.most_common(1)) == 0:
            if deadlock_counter >= WholeGameHive.MAX_LOOP_ITERS:
                raise GameDeadLockError("Can't gather enough votes. %s" % vote_counter)

            for player in self.alive_players:
                voted_for: Optional[SanitizedPlayer] = player.daytime_behavior(nominations)
                vote_table[SanitizedPlayer.sanitize(player)] = voted_for
                if voted_for is not None:
                    self.logger.info("%s voted to lynch %s." % (player.name, voted_for))
                    vote_counter[SanitizedPlayer.recover_player_identity(voted_for)] += 1
            deadlock_counter += 1

        return vote_table

    def __gather_nominations(self, players: Sequence[SanitizedPlayer]) -> Sequence[Nomination]:
        aggressive_players: Tuple[Player, ...] = self._get_most_aggressive()
        candidates: Set[Nomination] = set()
        for ap in aggressive_players:
            candidate: Optional[Nomination] = ap.ask_lynch_nomination(players)
            if candidate is not None:
                self.logger.info("%s nominated %s for lynching." % (candidate.nominated_by, candidate.nomination))
                candidates.add(candidate)
        return list(candidates)

    def __count_votes(self, vote_table: VoteTable) -> List[SanitizedPlayer]:
        vote_counter = ValueTieCounter()
        
        for voter in vote_table:
            if vote_table[voter] is not None:
                vote_counter[vote_table[voter]] += 1

        if self.has_reached_consensus(vote_counter.total()):
            return [t[0] for t in vote_counter.most_common(1)]
        else:
            return []

    def day_consensus(self, players: Sequence[SanitizedPlayer]) -> Tuple[NominationMap, VoteTable]:
        vote_table: VoteTable = {}
        nomination_map: NominationMap = {}

        while not self.__count_votes(vote_table): 
            candidates: Sequence[Nomination] = self.__gather_nominations(players)
            nomination_fishing_count = 0

            while not candidates:
                if nomination_fishing_count >= WholeGameHive.MAX_LOOP_ITERS:
                    raise GameDeadLockError("No one wants to nominate anyone else! Such pacifists!")

                candidates = self.__gather_nominations(players)
                nomination_fishing_count += 1

            nomination_map = {
                nom.nomination: nom.nominated_by for nom in candidates
            }
            self.logger.info("The nominations for lynching are %s" % " ".join((str(_) for _ in candidates)))

            vote_table = self.__gather_votes(candidates)

        return (nomination_map, vote_table)


class WerewolfHive(Hive):

    def __init__(self) -> None:
        super().__init__()

    @property
    def can_members_know_each_other(self) -> bool:
        return True

    def night_consensus(self, players: Sequence[SanitizedPlayer]) -> Optional[SanitizedPlayer]:
        consensus_count: int = 0
        suggestion: Optional[SanitizedPlayer] = None

        while not self.has_reached_consensus(consensus_count):
            nominant: Player = random.choice(self._get_most_aggressive())
            suggestion = nominant.night_action(players)
            self.logger.info("%s suggested to kill %s" % (nominant, suggestion))
            # This is the part where hive members discuss amongst themselves if
            # the nominated villager is killed.
            for hive_member in self.players:
                if suggestion is not None:
                    consensus_count += (
                        1 if hive_member.accept_night_suggestion(suggestion, SanitizedPlayer.sanitize(nominant)) else 0
                    )

            if self.has_reached_consensus(consensus_count):
                self.logger.info("WEREWOLVES Suggestion accepted")
                break
            else:
                self._publish_event("CONSENSUS_NOT_REACHED", "werewolves")
                self.logger.info("WEREWOLVES Suggestion not accepted (votes: %s)." % consensus_count)
                consensus_count = 0

        return suggestion

    def day_consensus(self, players: Sequence[SanitizedPlayer]) -> Tuple[NominationMap, VoteTable]:
        return ({}, {})


class VillagerHive(Hive):

    def night_consensus(self, players: Sequence[SanitizedPlayer]) -> Optional[SanitizedPlayer]:
        return None

    def day_consensus(self, players: Sequence[SanitizedPlayer]) -> Tuple[NominationMap, VoteTable]:
        return ({}, {})


CHARACTER_HIVE_MAPPING: Dict[Type["GameCharacter"], Type["Hive"]] = {
    Werewolf: WerewolfHive,
    Villager: VillagerHive
}
