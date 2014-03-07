#! /usr/bin/env python

from observer import Observable

class GamePlayer(Observable):
    
    def __init__(self, name, role):
        super(GamePlayer, self).__init__()
        self._name = name
        self._role = role

    @property
    def name(self):
        return self._name

    @property
    def role(self):
        return self._role

class NotedVillagers:
    """
    The official role strings used for this game.
    """
    WEREWOLF = "werewolf"
    SEER = "seer"
    WITCH = "witch"
