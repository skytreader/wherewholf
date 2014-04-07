#! /usr/bin/env python

from observer import Observable
from commands import PassThroughCommander

class GamePlayer(Observable):
    
    def __init__(self, name, role, cmd_manager = PassThroughCommander()):
        super(GamePlayer, self).__init__()
        self._name = name
        self._role = role
        self._cmd_manager = cmd_manager

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
