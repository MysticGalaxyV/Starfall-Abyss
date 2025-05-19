"""
Battle System Enhancements to improve energy scaling and potion usage

This module contains improvements to the battle system including:
1. Energy scaling with player level and training
2. Improved potion detection and usage during battles
3. Enhanced battle display to show dynamic energy limits
"""

from typing import Optional, Dict, Any, List, Tuple
import random
import discord
from discord.ui import Button, View
import asyncio
from data_models import PlayerData

# Enhanced BattleEntity class to replace the initialization method
def enhanced_battle_entity_init(self, name: str, stats: Dict[str, int], moves=None, 
                          is_player: bool = False, player_data: Optional[PlayerData] = None):
    """Enhanced initialization for BattleEntity that uses the dynamic energy maximum"""
    self.name = name
    self.stats = stats.copy()
    self.current_hp = stats["hp"]
    
    # Use the player's dynamic max energy calculation if player is present
    if player_data and is_player and hasattr(player_data, "get_max_battle_energy"):
        self.max_energy = player_data.get_max_battle_energy()
        self.current_energy = min(player_data.battle_energy, self.max_energy)
    else:
        self.max_energy = stats.get("energy", 100)
        self.current_energy = self.max_energy
        
    self.moves = moves or []
    self.is_player = is_player
    self.player_data = player_data
    self.status_effects = {}  # Effect name -> (turns remaining, effect strength)
    
    # Process active effects from special items
    if is_player and player_data and hasattr(player_data, "active_effects"):
        # Apply any HP boosts from active effects
        for effect_name, effect_data in player_data.active_effects.items():
            if effect_data.get("effect") == "hp_boost":
                boost_amount = effect_data.get("boost_amount", 0)
                self.stats["hp"] += boost_amount
                self.current_hp += boost_amount
            elif effect_data.get("effect") == "all_stats_boost":
                boost_amount = effect_data.get("boost_amount", 0)
                for stat in ["power", "defense", "speed", "hp"]:
                    if stat in self.stats:
                        self.stats[stat] += boost_amount
                        if stat == "hp":
                            self.current_hp += boost_amount

# Enhanced function to update player energy after battle
def update_player_energy_after_battle(player_data: PlayerData, battle_entity):
    """Update the player's energy after battle with their current battle energy"""
    if player_data and hasattr(player_data, "battle_energy"):
        player_data.battle_energy = min(battle_entity.current_energy, 
                                       player_data.get_max_battle_energy())

# Function to create battle status text
def create_battle_stats_text(player, enemy, player_status_msg="", enemy_status_msg=""):
    """Create formatted battle stats text with dynamic energy maximum"""
    battle_stats = (
        f"Your HP: {player.current_hp}/{player.stats['hp']} ❤️ | "
        f"Energy: {player.current_energy}/{player.max_energy} ⚡\n"
        f"{enemy.name}'s HP: {enemy.current_hp}/{enemy.stats['hp']} ❤️ | "
        f"Energy: {enemy.current_energy}/{enemy.max_energy} ⚡"
        f"{player_status_msg}{enemy_status_msg}"
    )
    return battle_stats

# Enhanced function for energy replenishment
def enemy_energy_replenish(enemy, amount=30):
    """Replenish enemy energy up to their maximum"""
    enemy.current_energy = min(enemy.max_energy, enemy.current_energy + amount)
    return enemy.current_energy

# Find potions in player inventory
def find_potions_in_inventory(player_data: PlayerData):
    """Find all potion items in the player's inventory"""
    potions = []
    if not player_data or not hasattr(player_data, "inventory"):
        return potions
    
    for inv_item in player_data.inventory:
        if not inv_item or not hasattr(inv_item, "item"):
            continue
            
        item = inv_item.item
        # Check if it's a potion or usable item (health or energy effects)
        if (hasattr(item, "item_type") and item.item_type and item.item_type.lower() == "potion" or 
            hasattr(item, "name") and ("potion" in item.name.lower() or "elixir" in item.name.lower())):
            
            # Default to "energy" effect if we can't determine the type
            effect_type = "energy"
            
            # Try to determine the effect type from description
            if hasattr(item, "description") and item.description:
                if "heal" in item.description.lower() or "health" in item.description.lower():
                    effect_type = "healing"
                elif "energy" in item.description.lower():
                    effect_type = "energy"
            
            # Add the potion to our list
            potions.append({
                "name": item.name if hasattr(item, "name") else "Potion",
                "effect": effect_type,
                "item": item,
                "inventory_item": inv_item
            })
    
    return potions