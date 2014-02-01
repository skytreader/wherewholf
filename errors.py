#! /usr/bin/env python

class GamePrivilegeError(Exception):
    """
    This error is thrown if a game character attempts an action for which the
    character has no sufficient privilege.
    """

    def __init__(self, character):
        self.character = character

    def __str__(self):
        return repr(self.character) + " does not have sufficient privileges for that action."

class VillageClosedError(Exception):
    """
    This error is thrown if a set-up change is attempted on a game in-progress.
    Example of possible set-up changes are:
        - A new villager is introduced,
        - ...more
    """

    def __init__(self, change):
        """
        change is a string specifying the change that triggered this exception.
        """
        self.change = change

    def __str__(self):
        return "Invalid state-change: " + self.change
