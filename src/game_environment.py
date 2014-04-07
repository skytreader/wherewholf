#! /usr/bin/env python

from errors import GamePrivilegeError, RegistrationError, VillageClosedError
from observer import Observer
from villagers import HiveVillager, WerewolfHive
from gameplayer import NotedPlayers

# FIXME I need a sort of "hive mind" for the whole village. Otherwise, voting
# for a killer may appear nonsensical.

# TODO Observer's update method
class GameEnvironment(Observer):
    """
    The `GameEnvironment` is responsible for noting the variables involved in a
    game. By itself, no game play happens. The GameEnvironment is oblivious to
    the rules of the game. It just knows what game resources are available.

    For game play to happen, we need a `GameMaster` (as below).
    """

    # TODO Clarify mechanics regarding the properties of this class.
    
    def __init__(self):
        self.villager_set = set()
        self.villager_names = set()
        self.id_mapper = IdentityMapper()
        self.werewolf_kill_vote = {}
        self.village_kill_vote = {}
        # Will hold the reasoning of players on who to kill
        self.kill_reasons = []

        self._werewolf_count = 0
        self._village_open = True

        self._default_hive = HiveVillager("village hive")
        self._werewolf_hive = WerewolfHive()
    
    @property
    def default_hive(self):
        """
        The hive to which all villagers should belong.
        """
        return self._default_hive

    @property
    def village_open(self):
        return self._village_open

    @village_open.setter
    def village_open(self, is_open):
        """
        You can only mess with the village's status if it is open. Once you
        close it, there is no turning back.
        """
        if self._village_open:  
            self._village_open = is_open
        else:
            raise VillageClosedError("trying to re-open a closed village")
    
    @property
    def villager_list(self):
        return self.villager_set.iterkeys()

    def register_villager(self, villager):
        if self.village_open:
            # Register in IdentityMapper first to save some constant time
            self.id_mapper.register_identity(villager)
            self.villager_set.add(villager)
            self.villager_names.add(villager.name)
            self.default_hive.add_member(villager)
            self.werewolf_kill_vote[villager] = 0
        else:
            raise VillageClosedError("new players are trying to get in a closed village")

    def kill_villager(self, villager):
        if not villager.health_guard:
            self.villager_set.remove(villager)
            villager.health_guard = False

    def clean_slate(self):
        for villager in villager_list:
            self.werewolf_kill_vote[villager] = 0
            self.village_kill_vote[villager] = 0

class IdentityMapper(object):
    """
    Given a villager's role + name, this class takes note of the privileges
    Assumptions:
        - For all villager instances that will be involved in the game, the
        combination name + rolestring is unique.
        - No rolestring or villager name will have the record separator
        character (ascii code 30).
    """

    CAN_KILL_INDEX = 0
    CAN_CHECK_INDEX = 1
    CAN_GUARD_INDEX = 2
    PRIVILEGE_TABLE = {}
    PRIVILEGE_TABLE[NotedPlayers.WEREWOLF] = (True, False, False)
    PRIVILEGE_TABLE[NotedPlayers.SEER] = (False, True, False)
    PRIVILEGE_TABLE[NotedPlayers.WITCH] = (True, False, True)

    RECORD_SEPARATOR = chr(30)

    def __init__(self):
        self.__character_map = {}

    def __compute_registry_key(self, villager):
        """
        A villager's registry key is made up of the following:
            - The villager's name
            - The villager's role
        """
        return "".join((villager.name, IdentityMapper.RECORD_SEPARATOR, villager.role))

    def register_identity(self, villager):
        if IdentityMapper.RECORD_SEPARATOR in villager.name or \
          IdentityMapper.RECORD_SEPARATOR in villager.role:
            raise RegistrationError(villager)

        registry_key = self.__compute_registry_key(villager)

        if self.__character_map.get(registry_key) is not None:
            raise RegistrationError(villager)
        # FIXME If the villager's role string is not mapped, this will throw an
        # exception. Maybe, catch it and throw a RegistrationError?
        self.__character_map[registry_key] = IdentityMapper.PRIVILEGE_TABLE[villager.role]

    def get_identity(self, villager):
        # FIXME What is this for? This seems redundant.
        registry_key = self.__compute_registry_key(villager)
        return self.__character_map[registry_key]
    
    # As opposed to can_{kill, check, guard} methods below
    def verify_kill(self, villager):
        """
        Given a villager, verify whether that villager can kill another villager.
        """
        identity = self.get_identity(villager)
        return identity[IdentityMapper.CAN_KILL_INDEX]

    def verify_check(self, villager):
        """
        Given a villager, verify whether that villager can check the role of
        another villager.
        """
        identity = self.get_identity(villager)
        return identity[IdentityMapper.CAN_CHECK_INDEX]

    def verify_guard(self, villager):
        """
        Given a villager, verify whether a villager can guard another villager.
        """
        identity = self.get_identity(villager)
        return identity[IdentityMapper.CAN_GUARD_INDEX]

    @staticmethod
    def can_kill(rolestring):
        return IdentityMapper.PRIVILEGE_TABLE[rolestring][IdentityMapper.CAN_KILL_INDEX]

    @staticmethod
    def can_check(rolestring):
        return IdentityMapper.PRIVILEGE_TABLE[rolestring][IdentityMapper.CAN_CHECK_INDEX]
    
    @staticmethod
    def can_guard(rolestring):
        return IdentityMapper.PRIVILEGE_TABLE[rolestring][IdentityMapper.CAN_GUARD_INDEX]

class GameMaster(object):
    """
    The `GameMaster` is responsible for managing the current game session. The
    `GameMaster` enforces the rules of the game. Utilization of game resources
    may vary depending on the `GameMaster` implementation that manages a game
    session.

    Villagers should not interact directly with the GameEnvironment. All
    interactions with the `GameEnvironment` should go through the `GameMaster`.
    Because of this, `GameMaster` will have a lot of "pass-through" properties
    to `GameEnvironment`.
    """

    # TODO Will the Observer pattern usage render this class obsolete? The only
    # function that might remain relevant is `play()`.
    
    def __init__(self, game_environment):
        self.__game_environment = game_environment

    # Pass-through properties

    @property
    def villager_list(self):
        return self.__game_environment.villager_list

    @property
    def werewolf_kill_vote(self):
        return self.__game_environment.werewolf_kill_vote
    
    def kill_villager(self, killer, victim):
        """
        If killer has the sufficient permission, kill the victim. Otherwise, will
        raise a GamePrivilegeError.
        """
        if NotedPlayers.can_kill(killer.role):
            self.__game_environment.kill_villager(victim)
        else:
            raise GamePrivilegeError(killer)
    
    def check_villager(self, checker, victim):
        """
        If checker has the sufficient permission, return the role string of
        victim. Otherwise, will raise a GamePrivilegeError.
        """
        if NotedPlayers.can_kill(checker.role):
            return victim.role
        else:
            raise GamePrivilegeError(checker)

    def guard_villager(self, guardian, taker):
        """
        If guardian has the sufficient permission, set taker's health_guard
        to true. Otherwise, will raise a GamePrivilegeError.
        """
        if NotedPlayers.can_guard(guardian.role):
            taker.health_guard = True
        else:
            raise GamePrivilegeError(guardian)
    
    def register_villagers(self, villager):
        # Pass through function
        self.__game_environment.register_villager(villager)
    
    def play(self):
        """
        GameMaster will continue interacting with the GameEnvironment and the
        Villagers until we reach end game.
        """
        pass
