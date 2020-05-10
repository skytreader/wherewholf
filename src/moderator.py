from enum import Enum
from .game_characters import CHARACTER_HIVE_MAPPING, GameCharacter, Hive, Player, SanitizedPlayer, Werewolf, WholeGameHive, Villager
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Type

import logging

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

    def __configure_logger(self, _cfg: Dict=None) -> None:
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
        return self.villager_count >= self.werewolf_count and self.werewolf_count > 0 and not self.__is_standoff()

    def __batch_sanitize(self, players: Iterable[Player]) -> Sequence[SanitizedPlayer]:
        return [SanitizedPlayer.sanitize(player) for player in players]

    def __filter_members(self, char_class: Type[GameCharacter]) -> Set[Player]:
        """
        Return the list of players with those belonging to the specified class
        _removed_.
        """
        return self.players - self.hives_map[char_class].players

    def __is_standoff(self) -> bool:
        return self.villager_count == 1 and self.werewolf_count == 1

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
                werewolf.hive_members = ww_hive.players
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

                if self.villager_count < self.werewolf_count or self.__is_standoff():
                    break

                self.logger.info("Vote now who to lynch...")
                lynched: Optional[SanitizedPlayer] = self.whole_game_hive.day_consensus(self.__batch_sanitize(self.players))
                assert lynched is not None
                assert type(lynched) is SanitizedPlayer
                role_of_the_lynched = SanitizedPlayer.recover_player_identity(lynched).role

                self.logger.info("You chose to lynch %s, a %s!" % (lynched.name, role_of_the_lynched))

                if type(role_of_the_lynched) == Villager:
                    self.villager_count -= 1
                else:
                    self.werewolf_count -= 1
                self.__kill_player(SanitizedPlayer.recover_player_identity(lynched))

        if self.villager_count < self.werewolf_count:
            self.logger.info("The werewolves won!")
            return EndGameState.WEREWOLVES_WON
        elif self.werewolf_count == 0:
            self.logger.info("The villagers won!")
            return EndGameState.VILLAGERS_WON
        elif self.__is_standoff():
            self.logger.info("It's a draw!")
            return EndGameState.DRAW
        else:
            self.logger.error("Unknown endgame condition. Status: villagers=%s, werewolves=%s." % (self.villager_count, self.werewolf_count))
            return EndGameState.UNKNOWN_CONDITION
