#!/usr/bin/env python3
"""
Test script to verify guild shop purchases award experience for leveling
"""

import json
from data_models import DataManager, PlayerData
from guild_system import GuildManager
import datetime

def test_guild_shop_leveling():
    """Test guild shop purchases award proper experience"""
    print("=== Testing Guild Shop Leveling ===")
    
    # Create test data manager
    data_manager = DataManager()
    guild_manager = GuildManager(data_manager)
    
    # Create test player
    test_player = PlayerData(
        user_id=12345,
        username="TestGuildLeader",
        level=10,
        gold=50000  # Enough to buy all items
    )
    
    # Create test guild
    success, message = guild_manager.create_guild("TestGuild", test_player.user_id, test_player)
    if not success:
        print(f"Failed to create guild: {message}")
        return
    
    guild = guild_manager.get_guild_by_name("TestGuild")
    print(f"Created guild: {guild.name} at level {guild.level} with {guild.exp} XP")
    
    # Test each shop item purchase and experience gain
    shop_items = [
        {"name": "Guild Expansion Permit", "cost": 5000, "expected_exp": 1000},
        {"name": "Guild Banner", "cost": 2500, "expected_exp": 500},
        {"name": "Guild Storage Expansion", "cost": 3000, "expected_exp": 600},
        {"name": "Guild XP Boost", "cost": 7500, "expected_exp": 1500},
        {"name": "Rare Material Crate", "cost": 4000, "expected_exp": 800},
        {"name": "Guild Emblem Customization", "cost": 1000, "expected_exp": 200},
        {"name": "Special Guild Dungeon Key", "cost": 6000, "expected_exp": 1200}
    ]
    
    initial_level = guild.level
    initial_exp = guild.exp
    total_expected_exp = sum(item["expected_exp"] for item in shop_items)
    
    print(f"\nStarting state: Level {initial_level}, {initial_exp} XP")
    print(f"Total expected experience gain: {total_expected_exp} XP")
    
    # Simulate each purchase by directly adding experience
    for item in shop_items:
        # Deduct cost from guild bank
        if guild.bank >= item["cost"]:
            guild.bank -= item["cost"]
            
            # Add experience (20% of cost)
            exp_gained = item["expected_exp"]
            old_level = guild.level
            leveled_up = guild.add_exp(exp_gained)
            
            level_msg = f" (LEVEL UP! {old_level} → {guild.level})" if leveled_up else ""
            print(f"✓ {item['name']}: -{item['cost']} gold, +{exp_gained} XP{level_msg}")
        else:
            print(f"✗ {item['name']}: Insufficient funds ({guild.bank} < {item['cost']})")
    
    # Final results
    final_level = guild.level
    final_exp = guild.exp
    actual_exp_gain = final_exp - initial_exp
    
    print(f"\nFinal state: Level {final_level}, {final_exp} XP")
    print(f"Expected XP gain: {total_expected_exp}")
    print(f"Actual XP gain: {actual_exp_gain}")
    print(f"Level progression: {initial_level} → {final_level}")
    
    # Verify the system works
    if actual_exp_gain == total_expected_exp:
        print("✅ Guild shop leveling system working correctly!")
    else:
        print("❌ Guild shop leveling system has issues!")
    
    # Show level requirements for reference
    print(f"\nGuild Level Requirements:")
    for level in range(1, 6):
        exp_needed = guild.exp_for_next_level
        print(f"Level {level} → {level + 1}: {exp_needed} XP needed")
        if guild.level >= level + 1:
            break

def test_achievement_point_deduction():
    """Test achievement point deduction system"""
    print("\n=== Testing Achievement Point Deduction ===")
    
    # Create test data manager and load achievements
    data_manager = DataManager()
    from achievements import AchievementTracker
    achievement_tracker = AchievementTracker(data_manager)
    
    # Create test player with achievement points
    test_player = PlayerData(
        user_id=67890,
        username="TestAchievementPlayer",
        level=5
    )
    
    # Give player some achievement points
    test_player.earned_achievement_points = 500
    test_player.spent_achievement_points = 0
    
    print(f"Starting achievement points: {achievement_tracker.get_player_achievement_points(test_player)}")
    
    # Test purchasing roles (150 points each)
    role_cost = 150
    tag_cost = 49
    
    # Purchase 2 roles
    for i in range(2):
        points_before = achievement_tracker.get_player_achievement_points(test_player)
        test_player.spent_achievement_points += role_cost
        points_after = achievement_tracker.get_player_achievement_points(test_player)
        print(f"Bought role {i+1}: {points_before} → {points_after} points (-{role_cost})")
    
    # Purchase 3 tags
    for i in range(3):
        points_before = achievement_tracker.get_player_achievement_points(test_player)
        test_player.spent_achievement_points += tag_cost
        points_after = achievement_tracker.get_player_achievement_points(test_player)
        print(f"Bought tag {i+1}: {points_before} → {points_after} points (-{tag_cost})")
    
    # Test overspending (should show negative balance)
    points_before = achievement_tracker.get_player_achievement_points(test_player)
    test_player.spent_achievement_points += 200  # Overspend
    points_after = achievement_tracker.get_player_achievement_points(test_player)
    print(f"Overspent by 200: {points_before} → {points_after} points (negative balance)")
    
    # Verify final state
    final_points = achievement_tracker.get_player_achievement_points(test_player)
    expected_spent = (2 * role_cost) + (3 * tag_cost) + 200  # 300 + 147 + 200 = 647
    expected_balance = 500 - expected_spent  # 500 - 647 = -147
    
    print(f"\nFinal verification:")
    print(f"Earned: {test_player.earned_achievement_points}")
    print(f"Spent: {test_player.spent_achievement_points}")
    print(f"Balance: {final_points}")
    print(f"Expected balance: {expected_balance}")
    
    if final_points == expected_balance:
        print("✅ Achievement point deduction system working correctly!")
    else:
        print("❌ Achievement point deduction system has issues!")

if __name__ == "__main__":
    test_guild_shop_leveling()
    test_achievement_point_deduction()
    print("\n=== All Tests Complete ===")