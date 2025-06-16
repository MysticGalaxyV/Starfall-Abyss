#!/usr/bin/env python3
"""
Test script to debug achievement display issues
"""

import json
from data_models import DataManager, PlayerData
from achievements import AchievementTracker, ACHIEVEMENTS

def main():
    # Load player data
    data_manager = DataManager()
    
    # Load and check player data
    data_manager.load_data()
    
    if not data_manager.players:
        print("No player data found!")
        return
    
    print(f"Found {len(data_manager.players)} players")
    print(f"Player IDs: {list(data_manager.players.keys())}")
    
    # Get the player from the screenshot (user ID: 759434349069860945)
    target_player_id = 759434349069860945
    if target_player_id in data_manager.players:
        player = data_manager.players[target_player_id]
        player_id = target_player_id
    else:
        # Get first player as fallback
        player_id = list(data_manager.players.keys())[0]
        player = data_manager.players[player_id]
    
    print(f"Testing achievements for player: {player_id}")
    print(f"Player level: {player.class_level}")
    print(f"Player stats: Level {player.class_level}, {getattr(player, 'wins', 0)} wins")
    print()
    
    # Check raw achievements data
    print("=== RAW ACHIEVEMENTS DATA ===")
    if hasattr(player, 'achievements'):
        print(f"Player achievements attribute exists: {len(player.achievements)} items")
        for i, ach in enumerate(player.achievements):
            if isinstance(ach, str):
                print(f"  {i}: String ID = '{ach}'")
            elif hasattr(ach, 'achievement_id'):
                print(f"  {i}: Achievement object, ID = '{ach.achievement_id}', Name = '{ach.name}'")
            else:
                print(f"  {i}: Unknown type = {type(ach)}")
    else:
        print("Player has no achievements attribute")
    print()
    
    # Test achievement tracker
    achievement_tracker = AchievementTracker(data_manager)
    
    print("=== COMPLETED ACHIEVEMENTS ===")
    completed = achievement_tracker.get_player_achievements(player)
    print(f"Found {len(completed)} completed achievements:")
    for ach in completed:
        print(f"  - {ach['name']} ({ach['id']}) - {ach['points']} points")
    print()
    
    print("=== ACHIEVEMENT POINTS ===")
    total_points = achievement_tracker.get_player_achievement_points(player)
    print(f"Total points: {total_points}")
    print()
    
    print("=== AVAILABLE ACHIEVEMENTS ===")
    available = achievement_tracker.get_player_available_achievements(player)
    print(f"Found {len(available)} available achievements:")
    for ach in available[:5]:  # Show first 5
        req_type = ach['requirement']['type']
        req_value = ach['requirement']['value']
        print(f"  - {ach['name']}: Need {req_type} >= {req_value}")
    print()
    
    # Test specific achievement completion
    print("=== MANUAL ACHIEVEMENT CHECKS ===")
    first_steps = ACHIEVEMENTS['first_steps']
    is_completed = achievement_tracker.check_achievement_completion(player, first_steps)
    print(f"First Steps (level 5): Player level {player.class_level} >= 5? {is_completed}")
    
    if hasattr(player, 'wins'):
        battle_novice = ACHIEVEMENTS['battle_novice']
        is_completed = achievement_tracker.check_achievement_completion(player, battle_novice)
        print(f"Battle Novice (10 wins): Player wins {player.wins} >= 10? {is_completed}")

if __name__ == "__main__":
    main()