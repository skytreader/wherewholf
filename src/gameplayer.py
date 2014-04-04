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

class NotedPlayers:
    """
    The official role strings used for this game.
    """
    VILLAGE_HIVE = "village hive"

    WEREWOLF = "werewolf"
    WEREWOLF_HIVE = "werewolf hive"
    SEER = "seer"
    SEER_HIVE = "seer hive"
    WITCH = "witch"
    WITCH_HIVE = "witch hive"
