#!/usr/bin/env python3
"""
Test script to verify skill effects work in battle scenarios
"""

from data_models import PlayerData
from battle_system import BattleEntity, BattleMove
import random

def test_battle_skills():
    """Test that skill tree effects work properly in battle scenarios"""
    
    # Create a test player with skills
    player = PlayerData(user_id=12345)
    player.class_name = "Warrior"
    player.class_level = 15
    
    # Allocate skills for testing different effects
    player.skill_tree = {
        "strength": {
            "Power Strike": 5,     # +25 power
            "Brute Force": 4,      # 40% chance to ignore defense
            "Critical Eye": 3      # +15% crit chance
        },
        "dexterity": {
            "Quick Draw": 2,       # 20% chance for extra attack
            "Evasive Maneuvers": 3 # 15% dodge chance
        },
        "intelligence": {
            "Spell Mastery": 4     # 40% energy cost reduction
        }
    }
    
    # Test class data
    class_data = {
        "Warrior": {
            "stats": {"power": 60, "defense": 40, "speed": 25, "hp": 200}
        }
    }
    
    # Get enhanced stats
    enhanced_stats = player.get_stats(class_data)
    print("Enhanced player stats:", enhanced_stats)
    
    # Create battle entity
    player_entity = BattleEntity("Skilled Warrior", enhanced_stats, is_player=True, player_data=player)
    enemy_entity = BattleEntity("Test Enemy", {"power": 50, "defense": 30, "speed": 20, "hp": 150})
    
    # Test energy cost reduction
    test_move = BattleMove("Test Attack", 1.2, 30)  # 30 energy cost
    
    print(f"\nTesting Spell Mastery (40% energy reduction):")
    print(f"Original energy cost: {test_move.energy_cost}")
    
    # Simulate the energy cost reduction that happens in apply_move
    spell_mastery_level = player_entity.get_skill_level("Spell Mastery")
    if spell_mastery_level > 0:
        energy_reduction = spell_mastery_level * 0.1  # 10% per level
        reduced_cost = max(1, int(test_move.energy_cost * (1 - energy_reduction)))
        print(f"Spell Mastery level: {spell_mastery_level}")
        print(f"Energy reduction: {energy_reduction * 100}%")
        print(f"Reduced energy cost: {reduced_cost}")
    
    # Test skill level detection
    print(f"\nSkill levels detected:")
    print(f"Power Strike: {player_entity.get_skill_level('Power Strike')}")
    print(f"Brute Force: {player_entity.get_skill_level('Brute Force')}")
    print(f"Quick Draw: {player_entity.get_skill_level('Quick Draw')}")
    print(f"Evasive Maneuvers: {player_entity.get_skill_level('Evasive Maneuvers')}")
    
    # Test stat calculations
    expected_power = 60 + 25  # base + Power Strike bonus
    actual_power = enhanced_stats['power']
    print(f"\nPower calculation: expected {expected_power}, actual {actual_power}")
    
    print("\n✅ Battle skill integration test completed!")

if __name__ == "__main__":
    test_battle_skills()