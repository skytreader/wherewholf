#! /usr/bin/env python

import json

"""
Contains functionality to create commands to be issued to the Observers.
Commands are abstractly structured as hash maps.
"""

class Commander(object):
    """
    This class defines all the commands available to Observables in creating
    the command they will issue to their observers. Observables need not bother
    with how the command is actually encoded; through this class they just need
    to use native Python hash maps.

    All this, in case we ever make Players out of other clients (Scheme/Lua,
    anyone?)
    """

    def create_command(self, command_map):
        """
        Creates a command with the information as contained in command_map.
        """
        raise NotImplementedError("Command structure not yet implemented.")

    def parse_command(self, command):
        """
        Parses the given command into Python's native dictionary structure.
        """
        raise NotImplementedError("Unable to parse command yet.")

class PassThroughCommander(Commander):
    
    def create_command(self, command_map):
        return command_map

    def parse_command(self, command):
        return command

class JSONCommander(Commander):
    """
    Just show it off.
    """

    def create_command(self, command_map):
        return json.dumps(command_map)

    def parse_command(self, command):
        return json.loads(command)
