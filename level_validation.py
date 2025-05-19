"""
Level validation system to ensure players are at the correct level based on their XP
"""

from typing import Dict, Any, Tuple
from data_models import PlayerData, DataManager

# Consistent XP formula to use throughout the game
def calculate_xp_for_level(level: int) -> int:
    """Calculate XP needed to reach a specific level using the standard formula"""
    base_xp = 75  # Reduced from 100 to make progression easier
    level_exponent = 1.35  # Reduced from 1.5 to flatten the curve for high levels
    return int(base_xp * (level ** level_exponent))

def validate_player_level(player: PlayerData) -> Tuple[bool, int, int]:
    """
    Validates and corrects a player's level based on their current XP
    
    Returns:
        Tuple of (was_correction_needed, old_level, new_level)
    """
    old_level = player.class_level
    total_xp = calculate_total_xp(player)
    
    # Determine the correct level based on total XP
    new_level, remaining_xp = calculate_level_from_xp(total_xp)
    
    # Set correct values if needed
    if old_level != new_level or player.class_exp != remaining_xp:
        player.class_level = new_level
        player.class_exp = remaining_xp
        return True, old_level, new_level
    
    return False, old_level, new_level

def calculate_total_xp(player: PlayerData) -> int:
    """
    Calculate the total XP a player has accumulated throughout their progression
    This includes XP already "spent" on levels plus their current XP
    """
    total_xp = player.class_exp
    
    # Add XP from all previous levels
    for level in range(1, player.class_level):
        total_xp += calculate_xp_for_level(level)
    
    return total_xp

def calculate_level_from_xp(total_xp: int) -> Tuple[int, int]:
    """
    Calculate the correct level and remaining XP based on total accumulated XP
    
    Returns:
        Tuple of (level, remaining_xp)
    """
    level = 1
    remaining_xp = total_xp
    
    # Keep leveling up until we can't anymore
    while True:
        xp_needed = calculate_xp_for_level(level)
        
        if remaining_xp >= xp_needed:
            remaining_xp -= xp_needed
            level += 1
        else:
            break
            
    # Enforce maximum level cap if needed
    MAX_LEVEL = 1000  # Match the cap in the rest of the game
    if level > MAX_LEVEL:
        level = MAX_LEVEL
        remaining_xp = 0
    
    return level, remaining_xp

def validate_all_players(data_manager: DataManager) -> Dict[int, Tuple[int, int]]:
    """
    Validate all players in the system and correct any level inconsistencies
    
    Returns:
        Dictionary mapping player IDs to tuples of (old_level, new_level) for players whose levels were corrected
    """
    corrections = {}
    
    for user_id, player in data_manager.players.items():
        was_corrected, old_level, new_level = validate_player_level(player)
        
        if was_corrected:
            corrections[user_id] = (old_level, new_level)
    
    # Save changes if any corrections were made
    if corrections:
        data_manager.save_data()
        
    return corrections

def auto_correct_player_level(player: PlayerData) -> bool:
    """
    Automatically corrects a player's level based on their XP.
    Returns True if a correction was made.
    """
    was_corrected, _, _ = validate_player_level(player)
    return was_corrected