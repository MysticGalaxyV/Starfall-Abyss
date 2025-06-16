#!/usr/bin/env python3
"""
Test script to verify skill tree integration is working properly
"""

from data_models import PlayerData, DataManager
import json

def test_skill_tree_integration():
    """Test that skill tree bonuses are properly applied to player stats"""
    
    # Create a test player
    player = PlayerData(user_id=12345)
    player.class_name = "Warrior"
    player.class_level = 10
    
    # Add some skill points and allocate them to the strength tree
    player.skill_points = 15
    player.skill_tree = {
        "strength": {
            "Power Strike": 5,     # Max level for +25 power
            "Brute Force": 3,      # +9 power
            "Weapon Mastery": 2    # +8 power
        },
        "vitality": {
            "Iron Skin": 4,        # +20 defense
            "Endurance": 3         # +60 hp
        }
    }
    
    # Test class data
    class_data = {
        "Warrior": {
            "stats": {"power": 50, "defense": 30, "speed": 20, "hp": 150}
        }
    }
    
    # Calculate stats without skills (manually)
    base_stats = {"power": 50, "defense": 30, "speed": 20, "hp": 150}
    print("Base class stats:", base_stats)
    
    # Calculate bonuses from skills
    bonuses = player.calculate_skill_tree_bonuses()
    print("Skill tree bonuses:", bonuses)
    
    # Get total stats with skills
    total_stats = player.get_stats(class_data)
    print("Total stats with skills:", total_stats)
    
    # Verify the calculations
    expected_power = 50 + (5*5) + (3*3) + (2*4)  # base + Power Strike + Brute Force + Weapon Mastery
    expected_defense = 30 + (4*5)  # base + Iron Skin
    expected_hp = 150 + (3*20)  # base + Endurance
    
    print(f"\nExpected power: {expected_power}, Actual: {total_stats['power']}")
    print(f"Expected defense: {expected_defense}, Actual: {total_stats['defense']}")
    print(f"Expected HP: {expected_hp}, Actual: {total_stats['hp']}")
    
    # Check if the bonuses are applied correctly
    assert total_stats['power'] == expected_power, f"Power calculation incorrect: expected {expected_power}, got {total_stats['power']}"
    assert total_stats['defense'] == expected_defense, f"Defense calculation incorrect: expected {expected_defense}, got {total_stats['defense']}"
    assert total_stats['hp'] == expected_hp, f"HP calculation incorrect: expected {expected_hp}, got {total_stats['hp']}"
    
    print("\n✅ All skill tree calculations are correct!")
    
    # Test skill level retrieval
    from battle_system import BattleEntity
    battle_entity = BattleEntity("Test Player", total_stats, is_player=True, player_data=player)
    
    power_strike_level = battle_entity.get_skill_level("Power Strike")
    brute_force_level = battle_entity.get_skill_level("Brute Force")
    nonexistent_skill = battle_entity.get_skill_level("Nonexistent Skill")
    
    print(f"\nSkill level tests:")
    print(f"Power Strike level: {power_strike_level} (expected: 5)")
    print(f"Brute Force level: {brute_force_level} (expected: 3)")
    print(f"Nonexistent skill level: {nonexistent_skill} (expected: 0)")
    
    assert power_strike_level == 5, f"Power Strike level incorrect: expected 5, got {power_strike_level}"
    assert brute_force_level == 3, f"Brute Force level incorrect: expected 3, got {brute_force_level}"
    assert nonexistent_skill == 0, f"Nonexistent skill level should be 0, got {nonexistent_skill}"
    
    print("✅ Skill level retrieval working correctly!")

if __name__ == "__main__":
    test_skill_tree_integration()
    print("\n🎉 All skill tree integration tests passed!")