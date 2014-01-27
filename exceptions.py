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
