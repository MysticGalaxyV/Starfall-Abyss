import json
import os
import datetime
from typing import Dict, Optional, List, Any
import logging

logger = logging.getLogger('jujutsu_rpg')

class PlayerData:
    """Class to store individual player data"""
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.class_name = None
        self.class_level = 1
        self.class_exp = 0
        self.user_level = 1
        self.user_exp = 0
        self.cursed_energy = 100
        self.max_cursed_energy = 100
        self.unlocked_classes = []
        self.inventory = []
        self.equipped_items = {
            "weapon": None,
            "armor": None,
            "accessory": None,
            "talisman": None
        }
        self.base_stats = {
            "power": 10,
            "defense": 10,
            "speed": 10,
            "hp": 100,
            "max_hp": 100
        }
        # Stats including equipment bonuses
        self.current_stats = self.base_stats.copy()
        self.skill_points = 0
        self.abilities = []
        self.achievements = []
        self.wins = 0
        self.losses = 0
        self.dungeons_completed = {}
        self.last_daily = None
        self.daily_streak = 0
        self.last_battle = None
        self.last_train = None
        self.currency = 0  # In-game currency
        
    @property
    def level_requirement(self) -> int:
        """Calculate XP needed for next level"""
        return int(100 * (self.class_level * 1.5))
    
    def add_exp(self, amount: int) -> bool:
        """Add experience and handle level-ups. Returns True if level-up occurred."""
        self.class_exp += amount
        level_up = False
        
        while self.class_exp >= self.level_requirement:
            self.class_exp -= self.level_requirement
            self.class_level += 1
            self.skill_points += 3  # Award skill points on level up
            level_up = True
            
            # Increase base stats on level up
            self.base_stats["power"] += 2
            self.base_stats["defense"] += 2
            self.base_stats["speed"] += 1
            self.base_stats["hp"] += 10
            self.base_stats["max_hp"] += 10
            self.max_cursed_energy += 10
            
            # Recalculate current stats
            self.update_stats()
            
        return level_up
    
    def update_stats(self):
        """Update current stats based on base stats + equipment bonuses"""
        self.current_stats = self.base_stats.copy()
        
        # Apply equipment bonuses
        for slot, item in self.equipped_items.items():
            if item:
                for stat, value in item.get("stats_boost", {}).items():
                    if stat in self.current_stats:
                        self.current_stats[stat] += value
        
        # Ensure HP and CE don't exceed maximum
        if self.current_stats["hp"] > self.current_stats["max_hp"]:
            self.current_stats["hp"] = self.current_stats["max_hp"]
        if self.cursed_energy > self.max_cursed_energy:
            self.cursed_energy = self.max_cursed_energy

    def can_equip_item(self, item: Dict[str, Any]) -> bool:
        """Check if the player meets requirements to equip an item"""
        return self.class_level >= item.get("level_req", 1)
    
    def equip_item(self, item_name: str) -> bool:
        """
        Equip an item from the player's inventory.
        Returns True if successful, False otherwise.
        """
        # Find the item in inventory
        item = None
        for inv_item in self.inventory:
            if inv_item["name"].lower() == item_name.lower():
                item = inv_item
                break
        
        if not item:
            return False
        
        # Check requirements
        if not self.can_equip_item(item):
            return False
        
        # Unequip current item in that slot
        slot = item.get("slot", "accessory")
        if self.equipped_items.get(slot):
            # Put the currently equipped item back in inventory
            old_item = self.equipped_items[slot]
            
            # If we're equipping the same item, no change needed
            if old_item["name"] == item["name"]:
                return True
        
        # Equip the new item
        self.equipped_items[slot] = item
        
        # Remove from inventory
        self.inventory.remove(item)
        
        # Update stats
        self.update_stats()
        return True
    
    def unequip_item(self, slot: str) -> bool:
        """
        Unequip an item from the specified slot.
        Returns True if successful, False otherwise.
        """
        if slot not in self.equipped_items or not self.equipped_items[slot]:
            return False
        
        # Add the item back to inventory
        self.inventory.append(self.equipped_items[slot])
        
        # Clear the slot
        self.equipped_items[slot] = None
        
        # Update stats
        self.update_stats()
        return True
        
    def add_to_inventory(self, item: Dict[str, Any]):
        """Add an item to the player's inventory"""
        self.inventory.append(item)
    
    def remove_from_inventory(self, item_name: str) -> bool:
        """Remove an item from inventory by name. Returns True if successful."""
        for i, item in enumerate(self.inventory):
            if item["name"].lower() == item_name.lower():
                self.inventory.pop(i)
                return True
        return False
    
    def heal(self, amount: int):
        """Heal the player by the specified amount"""
        self.current_stats["hp"] = min(
            self.current_stats["hp"] + amount,
            self.current_stats["max_hp"]
        )
    
    def restore_energy(self, amount: int):
        """Restore cursed energy by the specified amount"""
        self.cursed_energy = min(
            self.cursed_energy + amount,
            self.max_cursed_energy
        )
    
    def full_restore(self):
        """Fully restore HP and cursed energy"""
        self.current_stats["hp"] = self.current_stats["max_hp"]
        self.cursed_energy = self.max_cursed_energy
    
    def allocate_skill_point(self, stat: str) -> bool:
        """
        Allocate a skill point to increase a base stat.
        Returns True if successful, False if no skill points available.
        """
        if self.skill_points <= 0:
            return False
        
        if stat not in self.base_stats:
            return False
            
        # Allocate the point
        self.skill_points -= 1
        
        # Increase the stat
        if stat == "hp" or stat == "max_hp":
            self.base_stats["hp"] += 5
            self.base_stats["max_hp"] += 5
        else:
            self.base_stats[stat] += 1
            
        # Update current stats
        self.update_stats()
        return True

class DataManager:
    """Manages saving and loading player data"""
    def __init__(self):
        self.players: Dict[int, PlayerData] = {}
        self.data_file = 'player_data.json'
        
        # Create data file if it doesn't exist
        if not os.path.exists(self.data_file):
            with open(self.data_file, 'w') as f:
                json.dump({}, f)
                
        self.load_data()
        
    def get_player(self, user_id: int) -> PlayerData:
        """Get a player's data, creating it if it doesn't exist"""
        if user_id not in self.players:
            self.players[user_id] = PlayerData(user_id)
        return self.players[user_id]
    
    def save_data(self):
        """Save all player data to file"""
        try:
            data = {}
            for user_id, player in self.players.items():
                data[str(user_id)] = {
                    "class_name": player.class_name,
                    "class_level": player.class_level,
                    "class_exp": player.class_exp,
                    "user_level": player.user_level,
                    "user_exp": player.user_exp,
                    "cursed_energy": player.cursed_energy,
                    "max_cursed_energy": player.max_cursed_energy,
                    "unlocked_classes": player.unlocked_classes,
                    "inventory": player.inventory,
                    "equipped_items": player.equipped_items,
                    "base_stats": player.base_stats,
                    "current_stats": player.current_stats,
                    "skill_points": player.skill_points,
                    "abilities": player.abilities,
                    "achievements": player.achievements,
                    "wins": player.wins,
                    "losses": player.losses,
                    "dungeons_completed": player.dungeons_completed,
                    "last_daily": player.last_daily.isoformat() if player.last_daily else None,
                    "daily_streak": player.daily_streak,
                    "last_battle": player.last_battle.isoformat() if player.last_battle else None,
                    "last_train": player.last_train.isoformat() if player.last_train else None,
                    "currency": player.currency
                }
            
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=4)
                
            logger.info(f"Saved data for {len(self.players)} players")
            
        except Exception as e:
            logger.error(f"Error saving data: {e}", exc_info=True)
    
    def load_data(self):
        """Load player data from file"""
        try:
            with open(self.data_file, 'r') as f:
                data = json.load(f)
                
            for user_id, player_data in data.items():
                player = PlayerData(int(user_id))
                
                # Load basic attributes
                for attr, value in player_data.items():
                    if attr not in ["last_daily", "last_battle", "last_train"]:
                        setattr(player, attr, value)
                
                # Handle datetime fields
                try:
                    last_daily = player_data.get("last_daily")
                    player.last_daily = datetime.datetime.fromisoformat(last_daily) if last_daily else None
                    
                    last_battle = player_data.get("last_battle")
                    player.last_battle = datetime.datetime.fromisoformat(last_battle) if last_battle else None
                    
                    last_train = player_data.get("last_train")
                    player.last_train = datetime.datetime.fromisoformat(last_train) if last_train else None
                except (TypeError, ValueError) as e:
                    logger.error(f"Error parsing datetime for user {user_id}: {e}")
                    player.last_daily = None
                    player.last_battle = None
                    player.last_train = None
                
                # Add to players dictionary
                self.players[int(user_id)] = player
                
            logger.info(f"Loaded data for {len(self.players)} players")
            
        except Exception as e:
            logger.error(f"Error loading data: {e}", exc_info=True)
            # If we can't load the data, start with an empty dictionary
            self.players = {}
