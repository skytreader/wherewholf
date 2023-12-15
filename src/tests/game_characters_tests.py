import random
import unittest

from typing import List, Tuple

from ..game_characters import (
    GameCharacter, Hive, Nomination, Player, SanitizedPlayer, Villager, Werewolf,
    WerewolfHive, WholeGameHive
)
from typing import Dict, Optional, Sequence, Set


class DummyHive(Hive):
    """
    Stand in for the Hive class so we can test the default methods.
    """

    def night_consensus(self, players: Sequence[SanitizedPlayer]) -> Optional[SanitizedPlayer]:
        print("Just a dummy hive...")
        return None

    def day_consensus(self, players: Sequence[SanitizedPlayer]) -> Optional[SanitizedPlayer]:
        print("Just a dummy hive...")
        return None


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


def make_singleton_hive(hive: Hive) -> Hive:
    hive.players = set([Player("simba", Villager())])
    return hive


class PlayerTest(unittest.TestCase):

    def setUp(self) -> None:
        self.me: Player = Player("Chad", Villager())
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

    def test_pick_not_me_solo(self) -> None:
        no_choice: Sequence[SanitizedPlayer] = [SanitizedPlayer.sanitize(self.me)]
        chosen = self.me._pick_not_me(
            no_choice,
            random.choice,
            SanitizedPlayer.is_the_same_player
        )
        self.assertIsNone(chosen)

    def test_pick_not_me(self) -> None:
        REF_SANITIZED_PLAYERS: Sequence[SanitizedPlayer] = [
            SanitizedPlayer.sanitize(_p) for _p in self.players
        ]
        sanitized_players: Sequence[SanitizedPlayer] = [
            SanitizedPlayer.sanitize(_p) for _p in self.players
        ]

        for i in range(100):
            chosen = self.me._pick_not_me(
                sanitized_players, random.choice, SanitizedPlayer.is_the_same_player
            )

            self.assertEqual(REF_SANITIZED_PLAYERS, sanitized_players)
            self.assertIsNotNone(chosen)
            self.assertFalse(SanitizedPlayer.is_the_same_player(self.me,
                chosen)) # type: ignore

    def test_daytime_behavior(self) -> None:
        for _ in range(100):
            lynch: Optional[SanitizedPlayer] = self.me.daytime_behavior(self.nominations)
            if lynch is not None:
                self.assertFalse(SanitizedPlayer.is_the_same_player(self.me, lynch))

    def test_hive_affinity(self) -> None:
        mark: Player = Player("Mark", Werewolf(), hive_affinity=1.0)
        self.werewolf_hive.add_player(mark)
        for player in self.werewolf_hive.players:
            mark.learn_hive_member(SanitizedPlayer.sanitize(player))

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

    def test_aggression_deterrent(self) -> None:
        """
        A player that has no tolerance for aggression should not have patience
        with aggressive players.
        """
        gandhi = Player(
            "Mahatma", Villager(), suggestibility=0, nomination_recency=1
        )
        duterte = Player("Rodrigo", Werewolf(), aggression=1)
        delacruz = Player("Juan", Villager())
        robredo = Player("Leni", Villager())

        the_impossible = SanitizedPlayer.sanitize(duterte)

        # Do this only for the side-effect that it increments the internal
        # turn counter, as well as duterte's tally.
        gandhi.daytime_behavior(
            [
                Nomination(
                    SanitizedPlayer.sanitize(delacruz),
                    the_impossible
                )
            ]
        )
        gandhi_choice = gandhi.daytime_behavior(
            (
                Nomination(
                    SanitizedPlayer.sanitize(delacruz),
                    the_impossible
                ),
                Nomination(
                    the_impossible,
                    SanitizedPlayer.sanitize(robredo)
                )
            )
        )
        self.assertTrue(
            gandhi_choice is the_impossible or
            gandhi_choice is None
        )


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

    def test_singleton_consensus(self):
        SINGLETON_HIVES_CONSENSUS: List[Tuple[Hive, int]] = [
            (
                make_singleton_hive(_hive), 0
            ) for _hive in (DummyHive(), WerewolfHive(), WholeGameHive())
        ]
        for singleton_hive, singleton_consensus in SINGLETON_HIVES_CONSENSUS:
            self.assertEqual(singleton_hive.consensus, singleton_consensus)
            self.assertTrue(singleton_hive.has_reached_consensus(singleton_consensus))


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
