from enum import Enum
from .game_characters import CHARACTER_HIVE_MAPPING, GameCharacter, Hive, NominationMap, Player, SanitizedPlayer, Werewolf, WholeGameHive, Villager, VoteTable
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Type
from .utils import ValueTieCounter

import logging
import math

class EndGameState(Enum):
    UNKNOWN_CONDITION = -1
    WEREWOLVES_WON = 1
    VILLAGERS_WON = 2
    DRAW = 3

class Moderator(object):

    def __init__(self, players: Set[Player], log_discriminant: Optional[str]=None):
        self.logger: logging.Logger = logging.getLogger(
            "moderator%s" % (log_discriminant if log_discriminant else "")
        )
        self.__configure_logger()
        self.players: Set[Player] = players
        self.whole_game_hive: WholeGameHive = WholeGameHive()
        self.whole_game_hive.add_players(self.players)
        self.hives_map: Dict[Type[GameCharacter], Hive] = {}
        self.hives: List[Hive] = [self.whole_game_hive]

        for player in players:
            _type: Type[GameCharacter] = type(player.role)
            if type(player.role) in self.hives_map:
                self.hives_map[_type].add_player(player)
            else:
                new_hive = CHARACTER_HIVE_MAPPING[_type]()
                self.hives.append(new_hive)
                self.hives_map[_type] = new_hive
                self.hives_map[_type].add_player(player)
        
        self.werewolf_count: int = len(self.hives_map[Werewolf].players)
        self.villager_count: int = len(self.players) - self.werewolf_count

    def __configure_logger(self, _cfg: Optional[Dict]=None) -> None:
        cfg = _cfg if _cfg is not None else {}
        log_level = cfg.get("logLevel", "INFO")
        self.logger.setLevel(logging.getLevelName(log_level))

        log_format = cfg.get("logFormat", "%(asctime)s - %(levelname)s - %(message)s")
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(log_format))
        self.logger.addHandler(handler)

    def __kill_player(self, player: Player) -> None:
        self.players.remove(player)
        for hive in self.hives:
            hive.notify_player_death(player)

    def __game_on(self) -> bool:
        return self.villager_count >= self.werewolf_count and self.werewolf_count > 0

    def __batch_sanitize(self, players: Iterable[Player]) -> Sequence[SanitizedPlayer]:
        return [SanitizedPlayer.sanitize(player) for player in players]

    def __filter_members(self, char_class: Type[GameCharacter]) -> Set[Player]:
        """
        Return the list of players with those belonging to the specified class
        _removed_.
        """
        return self.players - self.hives_map[char_class].players

    def __count_votes(self, vote_table: VoteTable) -> List[SanitizedPlayer]:
        vote_counter = ValueTieCounter()
        
        for voter in vote_table:
            if vote_table[voter] is not None:
                vote_counter[vote_table[voter]] += 1

        return [t[0] for t in vote_counter.most_common(1)]

    def play(self) -> "EndGameState":
        # Ideally we want this to topo-sort the included characters and then
        # play them based on that but right now we only have Werewolves and
        # Villagers, so f*ck that fancy algorithmic shit.
        ww_hive: Hive = self.hives_map[Werewolf]
        while self.__game_on():
            self.logger.info("The village goes to sleep...")
            self.logger.info("Werewolves wake up!")
            # Inform the werewolves of each others' identities.
            # In the future, in a more abstracted version of the game, use the
            # `can_members_know_each_other` property of Hives.
            for werewolf in ww_hive.players:
                for player in ww_hive.players:
                    werewolf.learn_hive_member(SanitizedPlayer.sanitize(player))
            dead_by_wolf: Optional[SanitizedPlayer] = ww_hive.night_consensus(self.__batch_sanitize(self.__filter_members(Werewolf)))

            if dead_by_wolf is not None:
                role_of_the_dead = SanitizedPlayer.recover_player_identity(dead_by_wolf).role
                self.logger.info("Night has ended and the village awakes...")
                self.logger.info("The werewolves killed %s, a %s!" % (
                    dead_by_wolf.name, role_of_the_dead
                ))
                
                if type(role_of_the_dead) == Villager:
                    self.villager_count -= 1
                else:
                    self.werewolf_count -= 1
                self.__kill_player(SanitizedPlayer.recover_player_identity(dead_by_wolf))

                if self.villager_count <= self.werewolf_count:
                    break

                self.logger.info("Vote now who to lynch...")
                nomination_map, vote_table = self.whole_game_hive.day_consensus(self.__batch_sanitize(self.players))
                consensus: List[SanitizedPlayer] = self.__count_votes(vote_table)

                while len(consensus) != 1:
                    self.logger.info("Tie among %s" % str(consensus))
                    nomination_map, vote_table = self.whole_game_hive.day_consensus(consensus)
                    consensus = self.__count_votes(vote_table)

                assert len(consensus) == 1
                lynched = consensus[0]
                assert lynched is None or type(lynched) is SanitizedPlayer
                original_player = SanitizedPlayer.recover_player_identity(lynched)
                role_of_the_lynched = original_player.role

                self.logger.info("You chose to lynch %s, a %s!" % (lynched.name, role_of_the_lynched))
                for player in self.players:
                    player.react_to_lynch_result(
                        nomination_map,
                        original_player,
                        vote_table
                    )

                if type(role_of_the_lynched) == Villager:
                    self.villager_count -= 1
                else:
                    self.werewolf_count -= 1
                self.__kill_player(original_player)

        if self.villager_count <= self.werewolf_count:
            self.logger.info("The werewolves won!")
            return EndGameState.WEREWOLVES_WON
        elif self.werewolf_count == 0:
            self.logger.info("The villagers won!")
            return EndGameState.VILLAGERS_WON
        else:
            self.logger.error("Unknown endgame condition. Status: villagers=%s, werewolves=%s." % (self.villager_count, self.werewolf_count))
            return EndGameState.UNKNOWN_CONDITION
