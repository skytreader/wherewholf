#! /usr/bin/env python 
from errors import RegistrationError, VillageClosedError
from game_environment import NotedPlayers, GameEnvironment, IdentityMapper
from villagers import HiveVillager, Villager, WerewolfAI, SeerAI, WitchAI

import unittest

"""
Get the game resources you need from here.
"""
STOCKPILE = GameEnvironment()

class CharacterPrivileges(unittest.TestCase):
    
    def test_privileges(self):
        # Werewolf tests
        self.assertTrue(IdentityMapper.can_kill(NotedPlayers.WEREWOLF))
        self.assertFalse(IdentityMapper.can_check(NotedPlayers.WEREWOLF))
        self.assertFalse(IdentityMapper.can_guard(NotedPlayers.WEREWOLF))
        
        # Seer tests
        self.assertFalse(IdentityMapper.can_kill(NotedPlayers.SEER))
        self.assertTrue(IdentityMapper.can_check(NotedPlayers.SEER))
        self.assertFalse(IdentityMapper.can_guard(NotedPlayers.SEER))
        
        #Witch tests
        self.assertTrue(IdentityMapper.can_kill(NotedPlayers.WITCH))
        self.assertFalse(IdentityMapper.can_check(NotedPlayers.WITCH))
        self.assertTrue(IdentityMapper.can_guard(NotedPlayers.WITCH))

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
          IdentityMapper.PRIVILEGE_TABLE[NotedPlayers.WEREWOLF])

class GameEnvironmentTests(unittest.TestCase):
    
    def setUp(self):
        self.lupin = WerewolfAI("Lupin")
        self.trelawney = SeerAI("Trelawney")
        self.bellatrix = SeerAI("Bellatrix")

        self.test_village = GameEnvironment()
        self.test_crew = (self.lupin, self.trelawney, self.bellatrix)

    def test_game_states(self):
        # Create a GameEnvironment

        for crew in self.test_crew:
            self.test_village.register_villager(crew)

        self.test_village.village_open = False

        # Test that we can't open it again
        with self.assertRaises(VillageClosedError):
            self.test_village.village_open = True

        # Test that we can't add any other character
        self.assertRaises(VillageClosedError, self.test_village.register_villager, SeerAI("Cassandra"))

    def test_deep_duplicates(self):
        """
        Registering deep duplicates (same name and role but different objects,
        i.e., "deep copies") shall not pass. Throw a RegistrationError.
        """
        self.test_village.register_villager(self.lupin)
        self.lupin_clone = WerewolfAI("Lupin")

        self.assertRaises(RegistrationError, self.test_village.register_villager, self.lupin_clone)

if __name__ == "__main__":
    unittest.main()
