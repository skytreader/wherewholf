import random
import unittest

from ..game_characters import (
    GameCharacter, Hive, Nomination, Player, SanitizedPlayer, Villager, Werewolf,
    WerewolfHive, WholeGameHive
)
from typing import Dict, Optional, Sequence, Set


class InspectablePlayer(Player):

    def __init__(
        self,
        name: str,
        role: GameCharacter,
        aggression: float=0.3,
        suggestibility: float=0.4,
        persuasiveness: float=0.5
    ) -> None:
        super().__init__(name, role, aggression, suggestibility, persuasiveness)
        self.was_asked_for_daytime = False

    def daytime_behavior(self, players: Sequence[Nomination]) -> Optional[SanitizedPlayer]:
        self.was_asked_for_daytime = True
        return super().daytime_behavior(players)


class DummyHive(Hive):

    def night_consensus(self, players: Sequence[SanitizedPlayer]) -> Optional[SanitizedPlayer]:
        print("Just a dummy hive...")
        return None

    def day_consensus(self, players: Sequence[SanitizedPlayer]) -> Optional[SanitizedPlayer]:
        print("Just a dummy hive...")
        return None


class PlayerTest(unittest.TestCase):

    def setUp(self) -> None:
        self.me = Player("Chad", Villager())
        self.players: Set[Player] = set()
        self.players.add(Player("Christine", Werewolf()))
        self.players.add(Player("Shara", Werewolf()))
        self.players.add(self.me)
        self.players.add(Player("JE", Villager()))
        self.players.add(Player("Gab", Villager()))
        self.player_map: Dict[str, Player] = {p.name:p for p in self.players}
        self.werewolf_hive: WerewolfHive = WerewolfHive()
        self.werewolf_hive.add_player(self.player_map["Christine"])
        self.werewolf_hive.add_player(self.player_map["Shara"])

        self.nominations = [
            Nomination(
                SanitizedPlayer.sanitize(p),
                _pick_nominator(SanitizedPlayer.sanitize(p), list(self.players))
            ) for p in self.players
        ]

    def test_daytime_behavior(self) -> None:
        for _ in range(100):
            lynch: Optional[SanitizedPlayer] = self.me.daytime_behavior(self.nominations)
            if lynch is not None:
                self.assertFalse(SanitizedPlayer.is_the_same_player(self.me, lynch))

    def test_hive_affinity(self) -> None:
        mark: Player = Player("Mark", Werewolf(), hive_affinity=1.0)
        self.werewolf_hive.add_player(mark)
        mark.hive_members = self.werewolf_hive.players
        nominations = [
            Nomination(
                SanitizedPlayer.sanitize(self.player_map["Chad"]),
                SanitizedPlayer.sanitize(self.player_map["Shara"])
            ),
            Nomination(
                SanitizedPlayer.sanitize(self.player_map["Gab"]),
                SanitizedPlayer.sanitize(self.player_map["Chad"])
            ),
            Nomination(
                SanitizedPlayer.sanitize(self.player_map["JE"]),
                SanitizedPlayer.sanitize(self.player_map["Gab"])
            )
        ]
        self.assertEqual(
            SanitizedPlayer.sanitize(self.player_map["Chad"]),
            mark.daytime_behavior(nominations)
        )

    def test_aggression(self) -> None:
        """
        Recall: aggression is the factor which determines how likely a player
        will suggest others for lynching.
        """
        aunt_zee: Player = Player("Zelda", Villager(), aggression=1.0)
        aunt_hilda: Player = Player("Hilda", Villager(), aggression=0.0)

        sanitizeds = [SanitizedPlayer.sanitize(p) for p in self.players]
        self.assertIsNone(aunt_hilda.ask_lynch_nomination(sanitizeds))
        self.assertIsNotNone(aunt_zee.ask_lynch_nomination(sanitizeds))

class HiveTest(unittest.TestCase):

    def setUp(self) -> None:
        self.some_hive: Hive = DummyHive()
        self.christine = Player("Christine", Werewolf(), aggression=0.9)
        self.chad = Player("Chad", Villager(), aggression=0.7)
        self.josh = Player("Josh", Werewolf(), aggression=0.65)

        self.some_hive.add_player(self.christine)
        self.some_hive.add_player(self.chad)
        self.some_hive.add_player(self.josh)
        self.some_hive.add_player(Player("JE", Villager()))
        self.some_hive.add_player(Player("Alvin", Villager(), aggression=0.1))
    
    def test_get_most_aggressive(self) -> None:
        expected_top_aggressors = (
            self.christine, self.chad, self.josh
        )
        actual_aggressors = self.some_hive._get_most_aggressive(3)
        self.assertEqual(expected_top_aggressors, actual_aggressors)
    
    def test_dead_is_not_aggressive(self) -> None:
        # was not invited and will be dead
        charles: Player = Player("Charles", Villager(), aggression=1)
        self.some_hive.add_player(charles)
        aggressors = self.some_hive._get_most_aggressive(3)
        expected_top_aggressors = (
            charles, self.christine, self.chad
        )
        self.assertEqual(expected_top_aggressors, aggressors)

        # Goodbye Charles
        self.some_hive.notify_player_death(charles)
        aggressors = self.some_hive._get_most_aggressive(3)
        expected_top_aggressors = (
            self.christine, self.chad, self.josh
        )
        self.assertEqual(expected_top_aggressors, aggressors)


class WholeGameHiveTest(unittest.TestCase):

    def setUp(self) -> None:
        self.me = InspectablePlayer("Chad", Villager())
        self.players: Set[Player] = set()
        self.players.add(Player("Christine", Werewolf()))
        self.players.add(Player("Shara", Werewolf()))
        self.players.add(self.me)
        self.players.add(Player("JE", Villager()))
        self.players.add(Player("Gab", Villager()))

        self.whole_game_hive: WholeGameHive = WholeGameHive()
        self.whole_game_hive.add_players(self.players)

    def test_player_death(self) -> None:
        # Betrayed by my so-called "friends", let's say
        self.whole_game_hive.notify_player_death(self.me)
        sanitized = [SanitizedPlayer.sanitize(p) for p in self.players]
        for _ in range(100):
            self.whole_game_hive.day_consensus(sanitized)
            self.assertFalse(self.me.was_asked_for_daytime)

def _pick_nominator(nomination: SanitizedPlayer, players: Sequence[Player]):
    nominator: Player = random.choice(players)

    while SanitizedPlayer.is_the_same_player(nominator, nomination):
        nominator = random.choice(players)

    return nominator
