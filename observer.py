#! /usr/bin/env python

"""
Quick and dirty Observer pattern style in Python. Custom-built for wherwholf.

Wherwholf usage:
    - A GameEnvironment will observe the villagers.
    - Villagers will notify the game environment with a certain command.
    - Where does the hive figure in all this? Command structure?

OR
    - GameEnvironment AND Hives observe the villagers. Of course, Hives will
      only observe the villagers under them.

Customizations for wherewholf:
 - Sometimes, we only want to 
"""

class Observer(object):
    
    def update(self, observable, command):
        pass

class Observable(object):
    
    def __init__(self):
        self.__observer_list = []

    def add_observer(self, observer):
        self.__observer_list.insert(0, observer)

    def notify_observer(self, comma):
        pass
