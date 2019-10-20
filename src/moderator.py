from .game_characters import CHARACTER_HIVE_MAPPING, GameCharacter, Hive, Player, SanitizedPlayer, Werewolf, WholeGameHive, Villager
from typing import Dict, Iterable, Optional, Sequence, Set, Type


class Moderator(object):

    def __init__(self, players: Set[Player]):
        self.players: Set[Player] = players
        self.player_memory: Dict[SanitizedPlayer, Player] = {}
        self.sanitation_manager: Dict[Player, SanitizedPlayer] = {}
        self.classes: Dict[Type[GameCharacter], Set[Player]] = {}

        for player in players:
            sanitized: SanitizedPlayer = SanitizedPlayer(player)
            self.player_memory[sanitized] = player
            self.sanitation_manager[player] = sanitized
            if type(player.role) in self.classes:
                self.classes[type(player.role)].add(player)
            else:
                self.classes[type(player.role)] = set((player,))
        
        self.werewolf_count: int = len(self.classes.get(Werewolf, []))
        self.villager_count: int = len(self.classes.get(Villager, []))
        self.whole_game_hive: WholeGameHive = WholeGameHive()
        self.whole_game_hive.add_players(self.players)

    def __kill_player(self, player: Player) -> None:
        self.players.remove(player)
        self.whole_game_hive.players -= set((player,))

    def __game_on(self):
        return self.villager_count > self.werewolf_count and self.werewolf_count > 0

    def __batch_sanitize(self, players: Iterable[Player]) -> Sequence[SanitizedPlayer]:
        return [self.sanitation_manager[player] for player in players]

    def __filter_members(self, char_class: Type[GameCharacter]) -> Set[Player]:
        """
        Return the list of players with those belonging to the specified class
        _removed_.
        """
        return self.players - self.classes[char_class]
    
    def is_me(self, player: Player, splayer: SanitizedPlayer) -> bool:
        return self.player_memory[splayer] == player

    def play(self) -> None:
        # Ideally we want this to topo-sort the included characters and then
        # play them based on that but right now we only have Werewolves and
        # Villagers, so f*ck that fancy algorithmic shit.
        while self.__game_on():
            print("The village goes to sleep...")
            print("Werewolves wake up!")
            spam: Hive = CHARACTER_HIVE_MAPPING[Werewolf]()
            spam.add_players(self.classes[Werewolf])
            dead_by_wolf: Optional[SanitizedPlayer] = spam.night_consensus(self.__batch_sanitize(self.__filter_members(Werewolf)))

            if dead_by_wolf is not None:
                role_of_the_dead = self.player_memory[dead_by_wolf].role
                print("Night has ended and the village awakes...")
                print("The werewolves killed %s, a %s!" % (
                    dead_by_wolf.name, role_of_the_dead
                ))
                
                if type(role_of_the_dead) == Villager:
                    self.villager_count -= 1
                else:
                    self.werewolf_count -= 1
                self.__kill_player(self.player_memory[dead_by_wolf])

                if self.villager_count < self.werewolf_count:
                    break

                print("Vote now who to lynch...")
                lynched: SanitizedPlayer = self.whole_game_hive.day_consensus(self.__batch_sanitize(self.players))
                role_of_the_lynched = self.player_memory[lynched].role

                print("You chose to lynch %s, a %s!" % (lynched.name, role_of_the_lynched))

                if type(role_of_the_lynched) == Villager:
                    self.villager_count -= 1
                else:
                    self.werewolf_count -= 1
                self.__kill_player(self.player_memory[lynched])

        if self.villager_count < self.werewolf_count:
            print("The werewolves won!")
        elif self.werewolf_count == 0:
            print("The villagers won!")
