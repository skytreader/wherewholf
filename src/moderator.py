from .game_characters import GameCharacter, Hive, Player, Werewolf, WholeGameHive, Villager
from typing import Dict, Iterable, Set, Type


class Moderator(object):

    def __init__(self, players: Set[Player]):
        self.players: Set[Player] = players
        self.classes: Dict[Type[GameCharacter], Set[Player]] = {}

        for player in players:
            if player.role in self.classes:
                self.classes[type(player.role)].add(player)
            else:
                self.classes[type(player.role)] = set((player,))
        
        self.werewolf_count: int = len(self.classes.get(Werewolf, []))
        self.villager_count: int = len(self.classes.get(Villager, []))
        self.whole_game_hive: WholeGameHive = WholeGameHive()
        self.whole_game_hive.add_players(self.players)

    def __kill_player(self, player) -> None:
        self.players.remove(player)

    def play(self) -> None:
        # Ideally we want this to topo-sort the included characters and then
        # play them based on that but right now we only have Werewolves and
        # Villagers, so f*ck that fancy algorithmic shit.
        while self.villager_count > self.werewolf_count or self.werewolf_count > 0:
            print("The village goes to sleep...")
            print("Werewolves wake up!")
            spam: Hive = Werewolf.hive()()
            spam.add_players(self.classes[Werewolf])
            print(self.players)
            dead_by_wolf = spam.night_consensus(list(self.players))

            if dead_by_wolf is not None:
                print("Night has ended and the village awakes...")
                print("The werewolves killed %s, a %s!" % (
                    dead_by_wolf.name, dead_by_wolf.role
                ))
                
                if dead_by_wolf.role == Villager:
                    self.villager_count -= 1
                else:
                    self.werewolf_count -= 1
                self.players.remove(dead_by_wolf)

                print("Vote now who to lynch...")
                lynched = self.whole_game_hive.day_consensus(list(self.players))

                print("You chose to lynch %s, a %s!" % (lynched.name, lynched.role))

                if lynched.role == Villager:
                    self.villager_count -= 1
                else:
                    self.werewolf_count -= 1
                self.players.remove(lynched)
