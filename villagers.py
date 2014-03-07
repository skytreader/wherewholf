#! /usr/bin/env python

from observer import Observable
from game_environment import NotedVillagers, GameEnvironment

import random

class Villager(Observable):
    """
    At this level, the notify_observer method for Observable is not yet
    implemented.
    """
    
    def __init__(self, name, role="villager"):
        """
        name - the name of this villager
        role - the role of this villager. By default villager is in the plain
          "villager" role.
        """
        self._name = name
        self._role = role
        self._is_alive = True

        self.health_guard = False

    @property
    def name(self):
        return self._name

    @property
    def role(self):
        return self._role

    @property
    def is_alive(self):
        return self._is_alive

    def selfless_select(self, villagers):
        """
        Select some other villager.
        """
        chosen = random.choice(villagers)

        while chosen == self:
            chosen = random.choice(villagers)

        return chosen

    def ability(self, game_master):
        """
        Apply this villager's ability to another villager's. Some villagers may
        not have any ability at all (common villagers).

        The argument is a game_master instance (usually, the game_master handling
        the game where this instance is involved.
        """
        pass
    
    def kickback(self, offender):
        """
        This is called whenever another villager uses an ability on this villager.
        The argument is the perpetrator of the attack.
        """
        pass

    def nominate_for_kill(self):
        """
        Nominate a villager for killing. This should always return a valid villager.
        """
        # TODO Specify the structure of a kill nomination
        raise NotImplementedError("All villagers must nominate someone for killing.")

    def _decide_for_kill(self, kill_reasons):
        """
        Given the collated kill_reasons from all villagers, give this villager
        time to decide who to vote for killing. Always call this before
        get_kill_vote .
        """
        raise NotImplementedError("This villager is not deciding who to kill.")

    def _kill_vote(self):
        """
        Always call decide_for_kill before calling get_kill_vote. Return the
        name of a villager.
        """
        raise NotImplementedError("This villager is undecided who to kill!")

    def kill_vote(self, kill_reasons):
        """
        GameMaster can just call this method to get a kill vote.
        """
        self._decide_for_kill(kill_reasons)
        return self._kill_vote()
    
    def request_kill(self, game_master, villager):
        game_master.kill_villager(self, villager)

class HiveVillager(Villager, Observer):
    """
    This is not actually a villager. This structure is meant to aggregate
    decisions from various villagers and enact that decision based on some
    metric (by default, simple majority voting).

    In place of a name, it will have a `hiverole` which is just the label for
    this hive. All hives will have a role "hive" and will _not_ belong to any
    village hive (i.e., it is set to None).
    """

    # TODO I need a way for hive members to contact their HiveVillager for a vote.
    # The hive will observe all its members. Members will signal to the hive
    # for a vote.

    HIVEROLE = "hive"

    def __init__(self, hiverole):
        super(HiveVillager, self).__init__(hiverole, HiveVillager.HIVEROLE)
        self.__members = []
        self.__votes = {}

    @property
    def label(self):
        return self.role

    def add_member(self, villager):
        """
        Add the given villager to this Hive. Implementing classes may want to 
        override this function to validate the identity of the given villager
        (i.e., so that ordinary villagers don't join the werewolf pack).
        """
        self.__members.insert(0, villager)
        villager.add_observer(self)

    def is_member(self, villager):
        return villager in self.__members
    
    def vote(self, villager):
        """
        Votes/nominates the given villager for the collective action of this
        hive.
        """
        if self.__votes.get(villager):
            self.__votes[villager] += 1
        else:
            self.__votes[villager] = 1

    def get_leading(self):
        """
        Get the villager who leads the most in votation. If there is no
        obvious consensus yet, return None.

        If there are several leading villagers, one will be chosen at random. 
        """
        max_villager = None
        # Valid since a villager in __votes will have at least one vote.
        max_count = 0

        for nominee in self.__votes.keys():
            if self.__votes[nominee] > max_count:
                max_count = self.__votes[nominee]
                max_villager = nominee

        return max_villager

# TODO Implementations
class PlainVillagerAI(Villager):
    """
    Werewolf food villager.
    """

    def __init__(self, name):
        super(PlainVillagerAI, self).__init__(name)

class WerewolfHive(HiveVillager):
    
    def __init__(self):
        super(WerewolfHive, self).__init__("werewolf hive")

class WerewolfAI(Villager):
    """
    Dumb artificial intelligence for a werewolf character.

    Hahaha, werewolf characters should have some kind of "hive thinking". Cool
    for something so simple.
    """
    
    def __init__(self, name):
        # Atta mean killing machine!
        super(WerewolfAI, self).__init__(name, NotedVillagers.WEREWOLF)
    
    def ability(self, game_master):
        """
        A werewolf's ability is to choose a villager and vote for its death.
        There should be at least two werewolves in the game.
        """
        # What if werewolf wants to offer self in the name of deception?
        villager = self.selfless_select(game_master.villager_list)
        
        # FIXME Nope. Notify your the werewolf Hive first.
        game_master.werewolf_kill_vote[villager] += 1
    
    def notify_observer(self, command):
        

class SeerAI(Villager):
    def __init__(self, name):
        super(SeerAI, self).__init__(name, NotedVillagers.SEER)
        self.__villager_perception = {}

    def ability(self, game_master):
        """
        A seer can peek into a villager's role and use that information for
        votation later.
        """
        villager = self.selfless_select(game_master.villager_list)
        self.__villager_perception[villager.name] = villager.role

class WitchAI(Villager):
    
    def __init__(self, name):
        super(WitchAI, self).__init__(name, NotedVillagers.WITCH)
        # The following variables hold _True_ if the potions can still be used.
        self.can_poison = True
        self.can_potion = True

    def ability(self, game_master):
        """
        The witch has a poison and a potion. At any turn, the witch may decide
        to use one of these. If the witch has used both, the witch passes on the
        turn.
        """
        # If-else game tree yay!
        use_potion = random.choice([True, False])

        if use_potion:
            use_poison = random.choice([True, False])
            
            if use_poison and self.can_poison:
                suspect = self.selfless_select(game_master.villager_list)
                game_master.kill_villager(suspect)
                self.can_poison = False
            elif self.can_potion:
                lucky_villager = random.choice(game_master.villager_list)
                lucky_villager.health_guard = True
                self.can_potion = False
