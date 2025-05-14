import json
import os
import datetime
from typing import Dict, List, Optional, Any, Union

class Item:
    def __init__(self, item_id: str, name: str, description: str, item_type: str, 
                 rarity: str, stats: Dict[str, int], level_req: int, value: int):
        self.item_id = item_id
        self.name = name
        self.description = description
        self.item_type = item_type  # weapon, armor, accessory, consumable
        self.rarity = rarity  # common, uncommon, rare, epic, legendary
        self.stats = stats  # power, defense, speed, hp etc.
        self.level_req = level_req
        self.value = value
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            "item_id": self.item_id,
            "name": self.name,
            "description": self.description,
            "item_type": self.item_type,
            "rarity": self.rarity,
            "stats": self.stats,
            "level_req": self.level_req,
            "value": self.value
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Item':
        return cls(
            item_id=data["item_id"],
            name=data["name"],
            description=data["description"],
            item_type=data["item_type"],
            rarity=data["rarity"],
            stats=data["stats"],
            level_req=data["level_req"],
            value=data["value"]
        )

class InventoryItem:
    def __init__(self, item: Item, quantity: int = 1, equipped: bool = False):
        self.item = item
        self.quantity = quantity
        self.equipped = equipped
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            "item": self.item.to_dict(),
            "quantity": self.quantity,
            "equipped": self.equipped
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'InventoryItem':
        return cls(
            item=Item.from_dict(data["item"]),
            quantity=data["quantity"],
            equipped=data["equipped"]
        )

class Skill:
    def __init__(self, skill_id: str, name: str, description: str, level_req: int, 
                 damage_multiplier: float, energy_cost: int, cooldown: int):
        self.skill_id = skill_id
        self.name = name
        self.description = description
        self.level_req = level_req
        self.damage_multiplier = damage_multiplier
        self.energy_cost = energy_cost
        self.cooldown = cooldown
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "name": self.name,
            "description": self.description,
            "level_req": self.level_req,
            "damage_multiplier": self.damage_multiplier,
            "energy_cost": self.energy_cost,
            "cooldown": self.cooldown
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Skill':
        return cls(
            skill_id=data["skill_id"],
            name=data["name"],
            description=data["description"],
            level_req=data["level_req"],
            damage_multiplier=data["damage_multiplier"],
            energy_cost=data["energy_cost"],
            cooldown=data["cooldown"]
        )

class PlayerClass:
    def __init__(self, name: str, role: str, base_stats: Dict[str, int], 
                 abilities: Dict[str, str], skills: Optional[List[Skill]] = None):
        self.name = name
        self.role = role
        self.base_stats = base_stats
        self.abilities = abilities
        self.skills = skills or []
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "role": self.role,
            "base_stats": self.base_stats,
            "abilities": self.abilities,
            "skills": [skill.to_dict() for skill in self.skills]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PlayerClass':
        skills = [Skill.from_dict(skill_data) for skill_data in data.get("skills", [])]
        return cls(
            name=data["name"],
            role=data["role"],
            base_stats=data["base_stats"],
            abilities=data["abilities"],
            skills=skills
        )

class Achievement:
    def __init__(self, achievement_id: str, name: str, description: str, 
                 reward: Dict[str, int], completed_at: Optional[datetime.datetime] = None):
        self.achievement_id = achievement_id
        self.name = name
        self.description = description
        self.reward = reward
        self.completed_at = completed_at
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            "achievement_id": self.achievement_id,
            "name": self.name,
            "description": self.description,
            "reward": self.reward,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Achievement':
        completed_at = None
        if data.get("completed_at"):
            try:
                completed_at = datetime.datetime.fromisoformat(data["completed_at"])
            except (ValueError, TypeError):
                pass
                
        return cls(
            achievement_id=data["achievement_id"],
            name=data["name"],
            description=data["description"],
            reward=data["reward"],
            completed_at=completed_at
        )

class PlayerData:
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
        self.inventory = []  # List[InventoryItem]
        self.equipped_items = {"weapon": None, "armor": None, "accessory": None}
        self.achievements = []  # List[Achievement]
        self.special_abilities = {}  # Dict[str, Dict[str, Any]]
        self.active_effects = {}  # Dict[str, Dict[str, Any]]
        self.training_cooldowns = {}  # Dict[str, str] (training_name: iso_datetime)
        self.skill_points = 0
        self.allocated_stats = {"power": 0, "defense": 0, "speed": 0, "hp": 0}
        self.skill_tree = {}  # Dict[str, Dict[str, int]] (tree_name: {node_name: level})
        self.skill_points_spent = {}  # Dict[str, int] (tree_name: points_spent)
        self.wins = 0
        self.losses = 0
        self.last_daily = None
        self.daily_streak = 0
        self.last_train = None
        self.dungeon_clears = {}  # Map of dungeon name to count of clears
        self.skill_cooldowns = {}  # Map of skill_id to next available timestamp
        self.cursed_energy = 100
        self.max_cursed_energy = 100
        self.technique_grade = "Grade 3"  # Jujutsu rank/grade
        self.domain_expansion = None  # Special ultimate technique
        self.pvp_history = []  # List of PvP battle history
        self.pvp_wins = 0
        self.pvp_losses = 0
        self.last_pvp_battle = None  # Timestamp of last PvP battle
        
    def get_stats(self, class_data: Dict[str, Any]) -> Dict[str, int]:
        """Calculate total stats based on base class stats, allocated points and equipped items"""
        if not self.class_name or self.class_name not in class_data:
            # Return default stats if no class chosen or class not found
            base_stats = {"power": 10, "defense": 10, "speed": 10, "hp": 100}
        else:
            # Get base stats from class
            base_stats = class_data[self.class_name]["stats"].copy()
        
        # Add allocated stat points
        for stat, points in self.allocated_stats.items():
            if stat in base_stats:
                base_stats[stat] += points
        
        # Add stats from equipped items
        for inv_item in self.inventory:
            if inv_item.equipped:
                for stat, value in inv_item.item.stats.items():
                    if stat in base_stats:
                        base_stats[stat] += value
        
        return base_stats
    
    def add_cursed_energy(self, amount: int) -> int:
        """Add cursed energy up to the maximum limit. Returns the amount actually added."""
        if amount <= 0:
            return 0
            
        # Check if we're already at max
        if self.cursed_energy >= self.max_cursed_energy:
            return 0
            
        # Calculate how much we can add without exceeding max
        can_add = min(amount, self.max_cursed_energy - self.cursed_energy)
        self.cursed_energy += can_add
        return can_add
        
    def remove_cursed_energy(self, amount: int) -> bool:
        """Remove cursed energy if available. Returns True if successful."""
        if amount <= 0:
            return True
            
        if self.cursed_energy >= amount:
            self.cursed_energy -= amount
            return True
        return False
    
    def add_exp(self, exp_amount: int) -> bool:
        """Add experience points and handle level ups. Returns True if leveled up."""
        leveled_up = False
        self.class_exp += exp_amount
        
        # Max level set to 100 (changed from 1000)
        MAX_LEVEL = 100
        
        # If already at max level, just accumulate XP but don't level up
        if self.class_level >= MAX_LEVEL:
            return False
        
        # Calculate XP needed for next level using a much steeper curve: 100 * (current_level)^2.5
        # This makes each level significantly harder than the previous one
        xp_needed = int(300 * (self.class_level ** 2.5))
        
        # Check for level up
        while self.class_exp >= xp_needed and self.class_level < MAX_LEVEL:
            self.class_exp -= xp_needed
            self.class_level += 1
            self.skill_points += 2  # Reduced from 3 to slow down character progression
            
            # Increase max cursed energy on level up
            old_max = self.max_cursed_energy
            self.max_cursed_energy = 100 + (self.class_level * 50)  # Scales with level
            
            # Also increase current cursed energy by the same amount
            self.cursed_energy += (self.max_cursed_energy - old_max)
            
            leveled_up = True
            
            # Stop if reached max level
            if self.class_level >= MAX_LEVEL:
                break
                
            # Recalculate XP needed for next level
            xp_needed = int(300 * (self.class_level ** 2.5))
        
        return leveled_up
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "class_name": self.class_name,
            "class_level": self.class_level,
            "class_exp": self.class_exp,
            "user_level": self.user_level,
            "user_exp": self.user_exp,
            "cursed_energy": self.cursed_energy,
            "max_cursed_energy": self.max_cursed_energy,
            "unlocked_classes": self.unlocked_classes,
            "inventory": [item.to_dict() for item in self.inventory],
            "equipped_items": self.equipped_items,
            "achievements": [achievement.to_dict() for achievement in self.achievements],
            "skill_points": self.skill_points,
            "allocated_stats": self.allocated_stats,
            "skill_tree": self.skill_tree,
            "skill_points_spent": self.skill_points_spent,
            "wins": self.wins,
            "losses": self.losses,
            "last_daily": self.last_daily.isoformat() if self.last_daily else None,
            "daily_streak": self.daily_streak,
            "last_train": self.last_train.isoformat() if self.last_train else None,
            "dungeon_clears": self.dungeon_clears,
            "skill_cooldowns": {k: v.isoformat() for k, v in self.skill_cooldowns.items()} if self.skill_cooldowns else {},
            "special_abilities": self.special_abilities,
            "active_effects": self.active_effects,
            "training_cooldowns": self.training_cooldowns,
            "cursed_energy": self.cursed_energy,
            "technique_grade": self.technique_grade,
            "domain_expansion": self.domain_expansion,
            "pvp_history": self.pvp_history,
            "pvp_wins": self.pvp_wins,
            "pvp_losses": self.pvp_losses,
            "last_pvp_battle": self.last_pvp_battle.isoformat() if self.last_pvp_battle else None
        }
    
    @classmethod
    def from_dict(cls, user_id: int, data: Dict[str, Any]) -> 'PlayerData':
        player = cls(user_id)
        
        # Set simple attributes
        for attr in ["class_name", "class_level", "class_exp", "user_level", "user_exp", 
                     "cursed_energy", "technique_grade", "domain_expansion", "unlocked_classes", "equipped_items",
                     "skill_points", "allocated_stats", "skill_tree", "skill_points_spent", "wins", "losses", "daily_streak",
                     "dungeon_clears", "special_abilities", "active_effects", "training_cooldowns",
                     "pvp_history", "pvp_wins", "pvp_losses"]:
            if attr in data:
                setattr(player, attr, data[attr])
        
        # Convert inventory
        if "inventory" in data:
            player.inventory = [InventoryItem.from_dict(item_data) for item_data in data["inventory"]]
            
        # Convert achievements
        if "achievements" in data:
            player.achievements = [Achievement.from_dict(achievement_data) for achievement_data in data["achievements"]]
            
        # Convert datetime objects
        for dt_attr in ["last_daily", "last_train", "last_pvp_battle"]:
            if dt_attr in data and data[dt_attr]:
                try:
                    setattr(player, dt_attr, datetime.datetime.fromisoformat(data[dt_attr]))
                except (ValueError, TypeError):
                    setattr(player, dt_attr, None)
                    
        # Convert skill cooldowns
        if "skill_cooldowns" in data:
            player.skill_cooldowns = {}
            for skill_id, timestamp in data["skill_cooldowns"].items():
                try:
                    player.skill_cooldowns[skill_id] = datetime.datetime.fromisoformat(timestamp)
                except (ValueError, TypeError):
                    continue
                    
        return player

class DataManager:
    def __init__(self):
        self.players: Dict[int, PlayerData] = {}
        self.dungeons = {}  # Will be populated with dungeon data
        if not os.path.exists('player_data.json'):
            with open('player_data.json', 'w') as f:
                json.dump({}, f)
        self.load_data()
        self.load_dungeons()

    def save_data(self):
        try:
            data = {}
            for user_id, player in self.players.items():
                data[str(user_id)] = player.to_dict()
            with open('player_data.json', 'w') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"Error saving data: {e}")

    def load_data(self):
        try:
            with open('player_data.json', 'r') as f:
                data = json.load(f)
            for user_id, player_data in data.items():
                self.players[int(user_id)] = PlayerData.from_dict(int(user_id), player_data)
        except Exception as e:
            print(f"Error loading data: {e}")
            
    def get_player(self, user_id: int) -> PlayerData:
        """Get a player or create a new one if not exists"""
        if user_id not in self.players:
            self.players[user_id] = PlayerData(user_id)
            self.save_data()
        return self.players[user_id]
        
    def load_dungeons(self):
        """Load dungeon data from the DUNGEONS dictionary in dungeons.py"""
        from dungeons import DUNGEONS
        self.dungeons = DUNGEONS.copy()
