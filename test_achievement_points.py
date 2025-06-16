#!/usr/bin/env python3
"""
Test script to verify achievement points deduction system
"""

import json
from data_models import PlayerData, DataManager
from achievements import AchievementTracker

def test_achievement_points():
    # Create test data manager
    data_manager = DataManager()
    
    # Create test player with some achievement points
    test_player = PlayerData(user_id=12345)
    test_player.achievements = ["first_steps", "battle_novice", "dungeon_crawler"]  # Should give 35 points total (10+10+15)
    
    # Initialize achievement tracker
    achievement_tracker = AchievementTracker(data_manager)
    
    print("=== Achievement Points Test ===")
    
    # Check initial points
    initial_points = achievement_tracker.get_player_achievement_points(test_player)
    print(f"Initial achievement points: {initial_points}")
    
    # Check spent points
    spent_points = getattr(test_player, 'spent_achievement_points', 0)
    print(f"Initially spent points: {spent_points}")
    
    # Simulate spending 50 points
    test_player.spent_achievement_points = spent_points + 50
    
    # Check points after spending
    remaining_points = achievement_tracker.get_player_achievement_points(test_player)
    print(f"Points after spending 50: {remaining_points}")
    print(f"Spent points after purchase: {test_player.spent_achievement_points}")
    
    # Verify calculation
    expected_remaining = initial_points - 50
    if remaining_points == expected_remaining:
        print("✅ Achievement points deduction working correctly!")
    else:
        print(f"❌ Issue found! Expected {expected_remaining}, got {remaining_points}")
    
    return remaining_points == expected_remaining

if __name__ == "__main__":
    success = test_achievement_points()
    if not success:
        print("\n=== Debugging Info ===")
        # Additional debug info can go here
        exit(1)
    else:
        print("\n✅ All tests passed!")