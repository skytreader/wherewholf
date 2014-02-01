#! /usr/bin/env python

from errors import RegistrationError, VillageClosedError
from game_environment import NotedVillagers, GameEnvironment, IdentityMapper
from villagers import Villager, WerewolfAI, SeerAI, WitchAI

import unittest

class CharacterPrivileges(unittest.TestCase):
    
    def test_privileges(self):
        # Werewolf tests
        self.assertTrue(IdentityMapper.can_kill(NotedVillagers.WEREWOLF))
        self.assertFalse(IdentityMapper.can_check(NotedVillagers.WEREWOLF))
        self.assertFalse(IdentityMapper.can_guard(NotedVillagers.WEREWOLF))
        
        # Seer tests
        self.assertFalse(IdentityMapper.can_kill(NotedVillagers.SEER))
        self.assertTrue(IdentityMapper.can_check(NotedVillagers.SEER))
        self.assertFalse(IdentityMapper.can_guard(NotedVillagers.SEER))
        
        #Witch tests
        self.assertTrue(IdentityMapper.can_kill(NotedVillagers.WITCH))
        self.assertFalse(IdentityMapper.can_check(NotedVillagers.WITCH))
        self.assertTrue(IdentityMapper.can_guard(NotedVillagers.WITCH))

class IdentityMapperTests(unittest.TestCase):

    def setUp(self):
        self.id_accountant = IdentityMapper()
    
    def test_villager_equality(self):
        """
        No matter what happens, two different villager instances (even with the
        same name and role), should not hash to the same dictionary slot for the
        Python implementation on which this code will run.
        """
        jango = WerewolfAI("Jango")
        clone_trooper = WerewolfAI("Jango")

        dummy_map = {}
        dummy_map[jango] = "Clone"
        dummy_map[clone_trooper] = "Trooper"

        self.assertNotEqual(dummy_map[jango], dummy_map[clone_trooper])

    def test_registration(self):
        dirty_name = "sauron" + IdentityMapper.CHARACTER_SEPARATOR
        dirty_name_villager = Villager(dirty_name)

        self.assertRaises(RegistrationError, self.id_accountant.register_identity,\
          dirty_name_villager)

        dirty_job = IdentityMapper.CHARACTER_SEPARATOR + "balrog"
        dirty_job_villager = Villager("sauron", dirty_job)

        self.assertRaises(RegistrationError, self.id_accountant.register_identity,\
          dirty_job_villager)

class GameEnvironmentTests(unittest.TestCase):
    
    def setUp(self):
        self.lupin = WerewolfAI("Lupin")
        self.trelawney = SeerAI("Trelawney")
        self.bellatrix = SeerAI("Bellatrix")

    def test_game_states(self):
        # Create a GameEnvironment
        test_village = GameEnvironment()
        test_crew = (self.lupin, self.trelawney, self.bellatrix)

        for crew in test_crew:
            test_village.register_villager(crew)

        test_village.village_open = False

        # Test that we can't open it again
        with self.assertRaises(VillageClosedError):
            test_village.village_open = True

        # Test that we can't add any other character
        self.assertRaises(VillageClosedError, test_village.register_villager, SeerAI("Cassandra"))

if __name__ == "__main__":
    unittest.main()
