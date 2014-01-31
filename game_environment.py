#! /usr/bin/env python

from exceptions import GamePrivilegeError, VillageClosedError

class NotedVillagers:
    """
    The official role strings used for this game.
    """
    WEREWOLF = "werewolf"
    SEER = "seer"
    WITCH = "witch"

# FIXME I need a sort of "hive mind" for the whole village. Otherwise, voting
# for a killer may appear nonsensical.
class GameEnvironment(object):
    
    def __init__(self):
        self.villager_set = set()
        self.villager_names = set()
        self.werewolf_kill_vote = {}
        self.village_kill_vote = {}
        # Will hold the reasoning of players on who to kill
        self.kill_reasons = []

        self._werewolf_count = 0
        self._village_open = True

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
            self.villager_set.add(villager)
            self.villager_names.add(villager.name)
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
    assigned to a villager.
    """

    CAN_KILL_INDEX = 0
    CAN_CHECK_INDEX = 1
    CAN_GUARD_INDEX = 2
    PRIVILEGE_TABLE = {}
    PRIVILEGE_TABLE[NotedVillagers.WEREWOLF] = (True, False, False)
    PRIVILEGE_TABLE[NotedVillagers.SEER] = (False, True, False)
    PRIVILEGE_TABLE[NotedVillagers.WITCH] = (True, False, True)

    def __init__(self):
        self.__character_map = {}

    def can_kill(rolestring):
        return IdentityMapper.PRIVILEGE_TABLE[rolestring][NotedVillagers.CAN_KILL_INDEX]

    def can_check(rolestring):
        return IdentityMapper.PRIVILEGE_TABLE[rolestring][NotedVillagers.CAN_CHECK_INDEX]
    
    def can_guard(rolestring):
        return IdentityMapper.PRIVILEGE_TABLE[rolestring][NotedVillagers.CAN_GUARD_INDEX]

class GameMaster(object):
    """
    Villagers should not interact directly with the GameEnvironment. All
    interactions with the GameEnvironment should go through the GameMaster.
    """
    
    def __init__(self, game_environment):
        self.__game_environment = game_environment
    
    # FIXME Still not very foolproof. As an implementation, I can hold an instance
    # of a villager that has the privileges I want.
    # Solution idea: Decouple villager identity from function. GameMaster will map
    # the privileges of every villager.
    # Idea! Makes for a good game character. "Hostage taker" or something...
    def kill_villager(self, killer, victim):
        """
        If killer has the sufficient permission, kill the victim. Otherwise, will
        raise a GamePrivilegeError.
        """
        if NotedVillagers.can_kill(killer.role):
            self.__game_environment.kill_villager(victim)
        else:
            raise GamePrivilegeError(killer)
    
    def check_villager(self, checker, victim):
        """
        If checker has the sufficient permission, return the role string of
        victim. Otherwise, will raise a GamePrivilegeError.
        """
        if NotedVillagers.can_kill(checker.role):
            return victim.role
        else:
            raise GamePrivilegeError(checker)

    def guard_villager(self, guardian, taker):
        """
        If guardian has the sufficient permission, set taker's health_guard
        to true. Otherwise, will raise a GamePrivilegeError.
        """
        if NotedVillagers.can_guard(guardian.role):
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
