#!/usr/bin/env python3
"""
Comprehensive script to convert all cursed energy references to gold throughout the game
"""

import json
from data_models import DataManager

def main():
    print("Converting all cursed energy to gold throughout the game...")
    
    # Load player data
    data_manager = DataManager()
    
    # Convert existing player data
    total_converted = 0
    for player_id, player in data_manager.players.items():
        # If player has cursed_energy attribute, convert it to additional gold
        if hasattr(player, 'cursed_energy') and player.cursed_energy > 0:
            old_cursed_energy = player.cursed_energy
            player.gold += old_cursed_energy
            player.cursed_energy = 0  # Clear the old field
            print(f"Player {player_id}: Converted {old_cursed_energy} cursed energy to gold (now has {player.gold} gold)")
            total_converted += old_cursed_energy
    
    # Save the updated data
    data_manager.save_data()
    print(f"Conversion complete! Total cursed energy converted to gold: {total_converted}")
    print("All players now use gold as the single currency.")

if __name__ == "__main__":
    main()