#! /usr/bin/env python3

from game_environment import NotedVillagers

import unittest

class CharacterPrivileges(unittest.TestCase):
    
    def test_privileges(self):
        # Werewolf tests
        self.assertTrue(NotedVillagers.can_kill(NotedVillagers.WEREWOLF))

if __name__ == "__main__":
    unittest.main()
