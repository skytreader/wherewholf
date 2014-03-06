#! /usr/bin/env python

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
   observers with a filter field but adn require them to check this field if
   the given command is for them. But implementations which will not respect
   this will be able to cheat on the game!
"""

class Observer(object):
    
    def update(self, observable, command):
        pass

class Observable(object):
    
    def __init__(self):
        self.__observer_list = []

    def add_observer(self, observer):
        self.__observer_list.insert(0, observer)

    def notify_observer(self, command):
        pass
