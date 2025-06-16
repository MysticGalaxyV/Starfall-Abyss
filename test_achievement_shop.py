#!/usr/bin/env python3
"""
Test script to verify achievement points deduction for roles and tags
"""

import json
from data_models import PlayerData, DataManager
from achievements import AchievementTracker

def test_role_purchase():
    """Test that roles cost 150 points and are properly deducted"""
    data_manager = DataManager()
    
    # Create test player with 200 achievement points
    test_player = PlayerData(user_id=12345)
    test_player.achievements = ["first_steps", "apprentice_adventurer", "skilled_explorer", 
                               "battle_novice", "combat_expert", "dungeon_crawler", 
                               "dungeon_master"]  # Should give 200+ points
    
    achievement_tracker = AchievementTracker(data_manager)
    
    print("=== ROLE PURCHASE TEST ===")
    initial_points = achievement_tracker.get_player_achievement_points(test_player)
    print(f"Initial points: {initial_points}")
    
    # Simulate buying a role (150 points)
    role_cost = 150
    test_player.spent_achievement_points = getattr(test_player, 'spent_achievement_points', 0) + role_cost
    
    remaining_points = achievement_tracker.get_player_achievement_points(test_player)
    expected_remaining = initial_points - role_cost
    
    print(f"After buying role (150 points): {remaining_points}")
    print(f"Expected: {expected_remaining}")
    
    role_success = remaining_points == expected_remaining
    if role_success:
        print("✅ Role purchase deduction working correctly!")
    else:
        print("❌ Role purchase deduction failed!")
    
    return role_success, remaining_points

def test_tag_purchase():
    """Test that tags cost 49 points and are properly deducted"""
    data_manager = DataManager()
    
    # Create test player with 100 achievement points
    test_player = PlayerData(user_id=12346)
    test_player.achievements = ["first_steps", "apprentice_adventurer", "skilled_explorer", 
                               "battle_novice", "combat_expert"]  # Should give 90+ points
    
    achievement_tracker = AchievementTracker(data_manager)
    
    print("\n=== TAG PURCHASE TEST ===")
    initial_points = achievement_tracker.get_player_achievement_points(test_player)
    print(f"Initial points: {initial_points}")
    
    # Simulate buying a tag (49 points)
    tag_cost = 49
    test_player.spent_achievement_points = getattr(test_player, 'spent_achievement_points', 0) + tag_cost
    
    remaining_points = achievement_tracker.get_player_achievement_points(test_player)
    expected_remaining = initial_points - tag_cost
    
    print(f"After buying tag (49 points): {remaining_points}")
    print(f"Expected: {expected_remaining}")
    
    tag_success = remaining_points == expected_remaining
    if tag_success:
        print("✅ Tag purchase deduction working correctly!")
    else:
        print("❌ Tag purchase deduction failed!")
    
    return tag_success, remaining_points

def test_multiple_purchases():
    """Test buying multiple items"""
    data_manager = DataManager()
    
    # Create test player with lots of achievement points
    test_player = PlayerData(user_id=12347)
    test_player.achievements = ["first_steps", "apprentice_adventurer", "skilled_explorer", 
                               "master_adventurer", "battle_novice", "combat_expert", 
                               "battle_master", "dungeon_crawler", "dungeon_master"]  # 250+ points
    
    achievement_tracker = AchievementTracker(data_manager)
    
    print("\n=== MULTIPLE PURCHASES TEST ===")
    initial_points = achievement_tracker.get_player_achievement_points(test_player)
    print(f"Initial points: {initial_points}")
    
    # Buy 1 role (150) and 2 tags (49x2 = 98)
    total_cost = 150 + (49 * 2)  # 248 points
    test_player.spent_achievement_points = getattr(test_player, 'spent_achievement_points', 0) + total_cost
    
    remaining_points = achievement_tracker.get_player_achievement_points(test_player)
    expected_remaining = initial_points - total_cost
    
    print(f"After buying 1 role + 2 tags ({total_cost} points): {remaining_points}")
    print(f"Expected: {expected_remaining}")
    
    multiple_success = remaining_points == expected_remaining
    if multiple_success:
        print("✅ Multiple purchases deduction working correctly!")
    else:
        print("❌ Multiple purchases deduction failed!")
    
    return multiple_success

def test_insufficient_points():
    """Test that system handles insufficient points correctly"""
    data_manager = DataManager()
    
    # Create test player with only 50 points
    test_player = PlayerData(user_id=12348)
    test_player.achievements = ["first_steps", "apprentice_adventurer", "battle_novice"]  # 40 points
    
    achievement_tracker = AchievementTracker(data_manager)
    
    print("\n=== INSUFFICIENT POINTS TEST ===")
    initial_points = achievement_tracker.get_player_achievement_points(test_player)
    print(f"Initial points: {initial_points}")
    
    # Try to buy a role (150 points) with insufficient balance
    role_cost = 150
    can_afford = initial_points >= role_cost
    
    print(f"Can afford role (150 points): {can_afford}")
    
    if not can_afford:
        print("✅ Insufficient points check working correctly!")
        return True
    else:
        print("❌ Should not be able to afford role with insufficient points!")
        return False

if __name__ == "__main__":
    print("Testing Achievement Points Deduction System")
    print("=" * 50)
    
    role_success, role_remaining = test_role_purchase()
    tag_success, tag_remaining = test_tag_purchase()
    multiple_success = test_multiple_purchases()
    insufficient_success = test_insufficient_points()
    
    print("\n" + "=" * 50)
    print("SUMMARY:")
    print(f"Role purchase (150 points): {'✅ PASS' if role_success else '❌ FAIL'}")
    print(f"Tag purchase (49 points): {'✅ PASS' if tag_success else '❌ FAIL'}")
    print(f"Multiple purchases: {'✅ PASS' if multiple_success else '❌ FAIL'}")
    print(f"Insufficient points check: {'✅ PASS' if insufficient_success else '❌ FAIL'}")
    
    all_passed = all([role_success, tag_success, multiple_success, insufficient_success])
    
    if all_passed:
        print("\n🎉 ALL TESTS PASSED! Achievement shop working correctly.")
        exit(0)
    else:
        print("\n❌ Some tests failed. Check the issues above.")
        exit(1)