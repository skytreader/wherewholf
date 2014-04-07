#! /usr/bin/env python

from commands import PassThroughCommander

"""
Quick and dirty Observer pattern style in Python. Custom-built for wherewholf.

Wherwholf usage:
    - A GameEnvironment will observe the villagers.
    - Villagers will notify the game environment with a certain command.
    - Where does the hive figure in all this? Command structure?

OR
    - GameEnvironment AND Hives observe the villagers. Of course, Hives will
      only observe the villagers under them.

Customizations for wherewholf:
 - Sometimes, we only want to notify a certain subset of observers. We need to
   make sure that only this subset is notified. We could issue a command to all
   observers with a filter field but and require them to check this field if
   the given command is for them. But implementations which will not respect
   this will be able to cheat on the game!

   - Nope. The burden of filtering falls on the Observables. For that, we will
     give them an accept_command method.
"""

class Observer(object):
    
    def update(self, observable, command):
        pass

class Observable(object):
    
    def __init__(self, cmd_manager = None):
        self.__observer_list = []
        if cmd_manager:
            self.__cmd_manager = cmd_manager
        else:
            self.__cmd_manager = PassThroughCommander()

    def add_observer(self, observer):
        self.__observer_list.insert(0, observer)

    def _can_accept_command(self, command, observer):
        """
        Return true if the given observer may receive the intended command. This
        implies that Observables have a certain assumption about their
        Observers. The command is given as a Python map.

        This is how we filter the command to Observers. Implementing classes
        must override this. Returns False by default.
        """
        return False

    def notify_observer(self, command):
        """
        Observables need to implement this method for the wherewholf
        modification on this pattern: observables may choose the observers to
        whom they will broadcast their signals.
        """
        for observer in self.__observer_list:
            if self._can_accept_command(command, observer):
                observer.update(self, command) 
