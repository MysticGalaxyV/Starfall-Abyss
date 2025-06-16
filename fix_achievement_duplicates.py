#!/usr/bin/env python3
"""
Fix duplicate achievements in player data
"""

import json
from data_models import DataManager

def main():
    # Load player data
    data_manager = DataManager()
    
    # Get your player (user ID: 759434349069860945)
    player_id = 759434349069860945
    if player_id not in data_manager.players:
        print(f"Player {player_id} not found!")
        return
    
    player = data_manager.players[player_id]
    
    print(f"Player {player_id} has {len(player.achievements)} achievement entries")
    
    # Remove duplicates by keeping track of seen achievement IDs
    seen_ids = set()
    unique_achievements = []
    
    for achievement in player.achievements:
        if hasattr(achievement, 'achievement_id'):
            ach_id = achievement.achievement_id
            if ach_id not in seen_ids:
                seen_ids.add(ach_id)
                unique_achievements.append(achievement)
                print(f"Keeping: {ach_id} - {achievement.name}")
            else:
                print(f"Removing duplicate: {ach_id} - {achievement.name}")
    
    # Update player achievements
    player.achievements = unique_achievements
    
    print(f"Reduced from {len(player.achievements) + len(unique_achievements)} to {len(unique_achievements)} unique achievements")
    
    # Save the cleaned data
    data_manager.save_data()
    print("Saved cleaned achievement data")

if __name__ == "__main__":
    main()