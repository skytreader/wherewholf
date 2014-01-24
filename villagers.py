#! /usr/bin/env python

from game_environment import NotedVillagers, GameEnvironment

import random

class Villager(object):
    
    def __init__(self, name, role):
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

    def ability(self, game_environment):
        """
        Apply this villager's ability to another villager's. Some villagers may
        not have any ability at all (common villagers).

        The argument is the game_environment. (TODO Define game_environment).
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
        Nominate a villager for killing. This should never return None.
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

class WerewolfAI(Villager):
    """
    Dumb artificial intelligence for a werewolf character.

    Hahaha, werewolf characters should have some kind of "hive thinking". Cool
    for something so simple.
    """
    
    def __init__(self, name):
        # Atta mean killing machine!
        super(Villager, self).__init__(name, NotedVillagers.WEREWOLF)
    
    def ability(self, game_environment):
        """
        A werewolf's ability is to choose a villager and vote for its death.
        There should be at least two werewolves in the game.
        """
        # What if werewolf wants to offer self in the name of deception?
        villager = self.selfless_select(game_environment.villager_list)

        game_environment.werewolf_kill_vote[villager] += 1

class SeerAI(Villager):
    def __init__(self, name):
        super(Villager, self).__init__(name, NotedVillagers.SEER)
        self.__villager_perception = {}

    def ability(self, game_environment):
        """
        A seer can peek into a villager's role and use that information for
        votation later.
        """
        villager = self.selfless_select(game_environment.villager_list)
        self.__villager_perception[villager.name] = villager.role

class WitchAI(Villager):
    
    def __init__(self, name):
        super(Villager, self).__init__(name, NotedVillagers.WITCH)
        # The following variables hold _True_ if the potions can still be used.
        self.can_poison = True
        self.can_potion = True

    def ability(self, game_environment):
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
                suspect = self.selfless_select(game_environment.villager_list)
                game_environment.kill_villager(suspect)
                self.can_poison = False
            elif self.can_potion:
                lucky_villager = random.choice(game_environment.villager_list)
                lucky_villager.health_guard = True
                self.can_potion = False
