#! /usr/bin/env python3

from game_environment import NotedVillagers

import unittest

class CharacterPrivileges(unittest.TestCase):
    
    def test_privileges(self):
        # Werewolf tests
        self.assertTrue(NotedVillagers.can_kill(NotedVillagers.WEREWOLF))
        self.assertFalse(NotedVillagers.can_check(NotedVillagers.WEREWOLF))
        self.assertFalse(NotedVillagers.can_guard(NotedVillagers.WEREWOLF))
        
        # Seer tests
        self.assertFalse(NotedVillagers.can_kill(NotedVillagers.SEER))
        self.assertTrue(NotedVillagers.can_check(NotedVillagers.SEER))
        self.assertFalse(NotedVillagers.can_guard(NotedVillagers.SEER))
        
        #Witch tests
        self.assertTrue(NotedVillagers.can_kill(NotedVillagers.WITCH))
        self.assertFalse(NotedVillagers.can_check(NotedVillagers.WITCH))
        self.assertTrue(NotedVillagers.can_guard(NotedVillagers.WITCH))

if __name__ == "__main__":
    unittest.main()
