#! /usr/bin/env python

from errors import RegistrationError, VillageClosedError
from game_environment import NotedVillagers, GameEnvironment, IdentityMapper
from villagers import HiveVillager, Villager, WerewolfAI, SeerAI, WitchAI

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

class HiveTest(unittest.TestCase):
    
    def setUp(self):
        self.beehive = HiveVillager("bee")
        self.sample_victims = (Villager("Homer"), Villager("Lenny"),
          Villager("Karl"), Villager("Barney"))
    
    def test_rolelabel(self):
        self.assertEqual(self.beehive.label, self.beehive.role)

    def test_get_leading(self):
        self.assertEqual(self.beehive.get_leading(), None)

        # Let Homer lead
        self.beehive.vote(self.sample_victims[0])
        self.beehive.vote(self.sample_victims[0])

        self.assertEqual(self.beehive.get_leading(), self.sample_victims[0])
        
        # A few more votes and Homer shall still lead
        self.beehive.vote(self.sample_victims[2])
        self.beehive.vote(self.sample_victims[3])

        self.assertEqual(self.beehive.get_leading(), self.sample_victims[0])

        # Make a tie and a vote for Lenny
        self.beehive.vote(self.sample_victims[1])
        self.beehive.vote(self.sample_victims[2])
        self.beehive.vote(self.sample_victims[3])

        self.assertTrue(self.beehive.get_leading() in (self.sample_victims[0],
          self.sample_victims[2], self.sample_victims[3]))

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
        # You shall not pass (the registration, throw exception)!
        dirty_name = "sauron" + IdentityMapper.RECORD_SEPARATOR
        dirty_name_villager = Villager(dirty_name)

        self.assertRaises(RegistrationError, self.id_accountant.register_identity,\
          dirty_name_villager)

        dirty_job = IdentityMapper.RECORD_SEPARATOR + "balrog"
        dirty_job_villager = Villager("sauron", dirty_job)

        self.assertRaises(RegistrationError, self.id_accountant.register_identity,\
          dirty_job_villager)

        # Ordinary cases
        # Test registration of all roles and ensure that they get the proper privileges
        normal_werewolf = WerewolfAI("fenrir")
        self.id_accountant.register_identity(normal_werewolf)
        self.assertEqual(self.id_accountant.get_identity(normal_werewolf), \
          IdentityMapper.PRIVILEGE_TABLE[NotedVillagers.WEREWOLF])

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
