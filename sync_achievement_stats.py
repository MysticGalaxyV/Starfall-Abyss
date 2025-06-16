#!/usr/bin/env python3
"""
Synchronization script to fix achievement stats for existing players
This script updates missing achievement-related fields from existing game data
"""

from data_models import DataManager

def sync_player_achievement_stats():
    """Synchronize achievement stats for all existing players"""
    print("Loading player data...")
    data_manager = DataManager()
    
    players_updated = 0
    
    for player_id, player in data_manager.players.items():
        print(f"\nProcessing player {player_id} ({player.class_name})...")
        
        updated = False
        
        # Sync dungeons_completed from dungeon_clears
        if hasattr(player, 'dungeon_clears') and player.dungeon_clears:
            total_dungeons = sum(player.dungeon_clears.values())
            if not hasattr(player, 'dungeons_completed') or player.dungeons_completed != total_dungeons:
                player.dungeons_completed = total_dungeons
                print(f"  Updated dungeons_completed: {total_dungeons}")
                updated = True
        else:
            if not hasattr(player, 'dungeons_completed'):
                player.dungeons_completed = 0
                
        # Sync bosses_defeated (assume 1 boss per dungeon completion)
        if hasattr(player, 'dungeons_completed'):
            if not hasattr(player, 'bosses_defeated') or player.bosses_defeated != player.dungeons_completed:
                player.bosses_defeated = player.dungeons_completed
                print(f"  Updated bosses_defeated: {player.dungeons_completed}")
                updated = True
        else:
            if not hasattr(player, 'bosses_defeated'):
                player.bosses_defeated = 0
                
        # Initialize gold_earned if missing (can't calculate from current gold)
        if not hasattr(player, 'gold_earned'):
            # Estimate based on current level and wins (conservative estimate)
            estimated_gold = (player.wins * 50) + (player.class_level * 100)
            player.gold_earned = estimated_gold
            print(f"  Initialized gold_earned: {estimated_gold} (estimated)")
            updated = True
            
        # Initialize gold_spent if missing
        if not hasattr(player, 'gold_spent'):
            player.gold_spent = 0
            
        # Initialize training stats if missing
        if not hasattr(player, 'training_completed'):
            player.training_completed = 0
            
        if not hasattr(player, 'advanced_training_completed'):
            player.advanced_training_completed = 0
            
        # Initialize other missing stats
        if not hasattr(player, 'guild_contributions'):
            player.guild_contributions = 0
            
        if not hasattr(player, 'guild_dungeons'):
            player.guild_dungeons = 0
            
        if not hasattr(player, 'class_changes'):
            player.class_changes = len(player.unlocked_classes) - 1  # Minus starting class
            if updated:
                print(f"  Initialized class_changes: {player.class_changes}")
            
        if not hasattr(player, 'daily_claims'):
            player.daily_claims = player.daily_streak  # Use current streak as estimate
            
        if not hasattr(player, 'quests_completed'):
            player.quests_completed = 0
            
        if updated:
            players_updated += 1
            print(f"  Player data updated!")
        else:
            print(f"  No updates needed")
    
    if players_updated > 0:
        print(f"\nSaving data for {players_updated} updated players...")
        data_manager.save_data()
        print("✓ Achievement stats synchronized successfully!")
    else:
        print("\n✓ All player stats are already synchronized")
    
    return players_updated

if __name__ == "__main__":
    sync_player_achievement_stats()