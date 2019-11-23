from .game_characters import CHARACTER_HIVE_MAPPING, GameCharacter, Hive, Player, SanitizedPlayer, Werewolf, WholeGameHive, Villager
from typing import Dict, Iterable, List, Optional, Sequence, Set, Type

import logging


class Moderator(object):

    def __init__(self, players: Set[Player]):
        self.players: Set[Player] = players
        self.classes: Dict[Type[GameCharacter], Set[Player]] = {}

        for player in players:
            if type(player.role) in self.classes:
                self.classes[type(player.role)].add(player)
            else:
                self.classes[type(player.role)] = set((player,))
        
        self.werewolf_count: int = len(self.classes.get(Werewolf, []))
        self.villager_count: int = len(self.classes.get(Villager, []))
        self.whole_game_hive: WholeGameHive = WholeGameHive()
        self.whole_game_hive.add_players(self.players)
        self.logger: logging.Logger = logging.getLogger("moderator")
        self.__configure_logger()

        self.hives: List[Hive] = [self.whole_game_hive]

    def __configure_logger(self, _cfg=None):
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

    def __game_on(self):
        return self.villager_count > self.werewolf_count and self.werewolf_count > 0

    def __batch_sanitize(self, players: Iterable[Player]) -> Sequence[SanitizedPlayer]:
        return [SanitizedPlayer.sanitize(player) for player in players]

    def __filter_members(self, char_class: Type[GameCharacter]) -> Set[Player]:
        """
        Return the list of players with those belonging to the specified class
        _removed_.
        """
        return self.players - self.classes[char_class]

    def play(self) -> None:
        # Ideally we want this to topo-sort the included characters and then
        # play them based on that but right now we only have Werewolves and
        # Villagers, so f*ck that fancy algorithmic shit.
        ww_hive: Hive = CHARACTER_HIVE_MAPPING[Werewolf]()
        ww_hive.add_players(self.classes[Werewolf])

        self.hives.append(ww_hive)
        while self.__game_on():
            self.logger.info("The village goes to sleep...")
            self.logger.info("Werewolves wake up!")
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

                if self.villager_count < self.werewolf_count:
                    break

                self.logger.info("Vote now who to lynch...")
                lynched: Optional[SanitizedPlayer] = self.whole_game_hive.day_consensus(self.__batch_sanitize(self.players))
                assert lynched is not None
                role_of_the_lynched = SanitizedPlayer.recover_player_identity(lynched).role

                self.logger.info("You chose to lynch %s, a %s!" % (lynched.name, role_of_the_lynched))

                if type(role_of_the_lynched) == Villager:
                    self.villager_count -= 1
                else:
                    self.werewolf_count -= 1
                self.__kill_player(SanitizedPlayer.recover_player_identity(lynched))

        if self.villager_count < self.werewolf_count:
            self.logger.info("The werewolves won!")
        elif self.werewolf_count == 0:
            self.logger.info("The villagers won!")
