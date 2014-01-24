#! /usr/bin/env python

class NotedVillagers:
    """
    The official role strings used for this game.
    """
    WEREWOLF = "werewolf"
    SEER = "seer"
    WITCH = "witch"

# FIXME Ensure that rogue villager implementations cannot just kill off
# random villagers. Maybe, implement a privileges table that will list the
# privileges (kill, check, etc) of various noted villagers.

# FIXME I need a sort of "hive mind" for the whole village. Otherwise, voting
# for 
class GameEnvironment(object):
    
    def __init__(self):
        self.villager_set = set()
        self.villager_names = set()
        self.werewolf_kill_vote = {}
        self.village_kill_vote = {}
        # Will hold the reasoning of players on who to kill
        self.kill_reasons = []
    
    @property
    def villager_list(self):
        return self.villager_set.iterkeys()

    def register_villager(self, villager):
        self.villager_set.add(villager)
        self.villager_names[villager] = villager.name
        self.werewolf_kill_vote[villager] = 0

    def kill_villager(self, villager):
        if not villager.health_guard:
            self.villager_set.remove(villager)
            villager.health_guard = False

    def clean_slate(self):
        for villager in villager_list:
            self.werewolf_kill_vote[villager] = 0
            self.village_kill_vote[villager] = 0

class GameMaster(object):
    
    def __init__(self, game_environment):
        self.__game_environment = game_environment
