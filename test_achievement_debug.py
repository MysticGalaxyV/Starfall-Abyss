#!/usr/bin/env python3
"""
Test script to debug achievement system issues
"""

import json
from data_models import DataManager, PlayerData
from achievements import AchievementTracker

def main():
    # Load player data
    data_manager = DataManager()
    
    # Find the player with 46 wins
    player_id = "759434349069860945"  # From the JSON grep
    
    if player_id in data_manager.players:
        player = data_manager.players[player_id]
        
        print(f"Testing achievement system for player:")
        print(f"  Class: {player.class_name}")
        print(f"  Level: {player.class_level}")
        print(f"  Wins: {player.wins}")
        print(f"  Current achievements: {len(player.achievements)}")
        
        # Create achievement tracker
        achievement_tracker = AchievementTracker(data_manager)
        
        # Check available achievements
        available = achievement_tracker.get_player_available_achievements(player)
        print(f"  Available achievements: {len(available)}")
        
        for ach in available[:5]:  # Show first 5
            print(f"    - {ach['name']}: {ach['requirement']}")
        
        # Test achievement completion check
        new_achievements = achievement_tracker.check_achievements(player)
        print(f"  New achievements found: {len(new_achievements)}")
        
        for ach in new_achievements:
            print(f"    ✓ {ach['name']}: {ach['description']}")
            
        if new_achievements:
            print(f"  Player achievements after check: {len(player.achievements)}")
            data_manager.save_data()
            print("  Data saved!")
        else:
            print("  No new achievements earned.")
            
            # Debug specific achievement
            first_win_ach = {
                "id": "first_win",
                "name": "First Victory",
                "description": "Win your first battle",
                "requirement": {"type": "wins", "value": 1},
                "reward": {"gold": 50, "cursed_energy": 25},
                "category": "combat"
            }
            
            completed = achievement_tracker.check_achievement_completion(player, first_win_ach)
            print(f"  Manual check 'First Victory' achievement: {completed}")
            print(f"  Player wins attribute exists: {hasattr(player, 'wins')}")
            print(f"  Player wins value: {getattr(player, 'wins', 'NOT_FOUND')}")
            
    else:
        print(f"Player {player_id} not found")

if __name__ == "__main__":
    main()