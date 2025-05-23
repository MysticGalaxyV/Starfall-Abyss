import json
import os
import datetime
from typing import Dict, List, Optional, Any, Union


class Item:

    def __init__(self, item_id: str, name: str, description: str,
                 item_type: str, rarity: str, stats: Dict[str, int],
                 level_req: int, value: int):
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
        return cls(item_id=data["item_id"],
                   name=data["name"],
                   description=data["description"],
                   item_type=data["item_type"],
                   rarity=data["rarity"],
                   stats=data["stats"],
                   level_req=data["level_req"],
                   value=data["value"])


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
        return cls(item=Item.from_dict(data["item"]),
                   quantity=data["quantity"],
                   equipped=data["equipped"])


class Skill:

    def __init__(self, skill_id: str, name: str, description: str,
                 level_req: int, damage_multiplier: float, energy_cost: int,
                 cooldown: int):
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
        return cls(skill_id=data["skill_id"],
                   name=data["name"],
                   description=data["description"],
                   level_req=data["level_req"],
                   damage_multiplier=data["damage_multiplier"],
                   energy_cost=data["energy_cost"],
                   cooldown=data["cooldown"])


class PlayerClass:

    def __init__(self,
                 name: str,
                 role: str,
                 base_stats: Dict[str, int],
                 abilities: Dict[str, str],
                 skills: Optional[List[Skill]] = None):
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
        skills = [
            Skill.from_dict(skill_data)
            for skill_data in data.get("skills", [])
        ]
        return cls(name=data["name"],
                   role=data["role"],
                   base_stats=data["base_stats"],
                   abilities=data["abilities"],
                   skills=skills)


class Achievement:

    def __init__(self,
                 achievement_id: str,
                 name: str,
                 description: str,
                 reward: Dict[str, int],
                 completed_at: Optional[datetime.datetime] = None):
        self.achievement_id = achievement_id
        self.name = name
        self.description = description
        self.reward = reward
        self.completed_at = completed_at

    def to_dict(self) -> Dict[str, Any]:
        return {
            "achievement_id":
            self.achievement_id,
            "name":
            self.name,
            "description":
            self.description,
            "reward":
            self.reward,
            "completed_at":
            self.completed_at.isoformat() if self.completed_at else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Achievement':
        completed_at = None
        if data.get("completed_at"):
            try:
                completed_at = datetime.datetime.fromisoformat(
                    data["completed_at"])
            except (ValueError, TypeError):
                pass

        return cls(achievement_id=data["achievement_id"],
                   name=data["name"],
                   description=data["description"],
                   reward=data["reward"],
                   completed_at=completed_at)


class PlayerData:

    def __init__(self, user_id: int):
        self.user_id = user_id
        self.class_name = None
        self.class_level = 1
        self.class_exp = 0
        self.user_level = 1
        self.user_exp = 0
        self.gold = 100  # Currency (changed from cursed_energy)
        self.max_gold = 1000000  # Very high maximum as there's no cap on currency
        self.cursed_energy = 0  # Legacy field - we now use gold consistently as currency
        self.battle_energy = 100  # Battle resource
        self.max_battle_energy = 100  # Base max battle resource
        self.energy_training = 0  # Additional energy from specialized training
        self.unlocked_classes = []
        self.inventory = []  # List[InventoryItem]
        self.equipped_items = {
            "weapon": None,
            "armor": None,
            "accessory": None
        }
        # Gathering tools equipment slots
        self.equipped_gathering_tools = {
            "Mining": None,
            "Foraging": None,
            "Herbs": None,
            "Hunting": None,
            "Magical": None
        }
        self.achievements = []  # List[Achievement]
        self.special_abilities = {}  # Dict[str, Dict[str, Any]]
        self.active_effects = {}  # Dict[str, Dict[str, Any]]
        self.training_cooldowns = {
        }  # Dict[str, str] (training_name: iso_datetime)
        self.skill_points = 0
        self.allocated_stats = {"power": 0, "defense": 0, "speed": 0, "hp": 0}
        self.skill_tree = {
        }  # Dict[str, Dict[str, int]] (tree_name: {node_name: level})
        self.skill_points_spent = {
        }  # Dict[str, int] (tree_name: points_spent)
        self.wins = 0
        self.losses = 0
        self.last_daily = None
        self.daily_streak = 0
        self.last_train = None
        self.dungeon_clears = {}  # Map of dungeon name to count of clears
        self.skill_cooldowns = {
        }  # Map of skill_id to next available timestamp
        self.technique_grade = "Grade 3"  # Jujutsu rank/grade
        self.domain_expansion = None  # Special ultimate technique
        self.pvp_history = []  # List of PvP battle history
        self.pvp_wins = 0
        self.pvp_losses = 0
        self.last_pvp_battle = None
        self.earned_roles = []  # Server roles earned through achievements
        self.level = 1  # Alias for user_level to fix compatibility issues
        self.current_hp = 100  # Current health points
        self.dungeon_damage = 0  # Accumulated damage in dungeons
        self.equipped_gathering_tools = {
        }  # Map of category to equipped tool name
        # Additional attributes for achievements
        self.dungeons_completed = 0
        self.bosses_defeated = 0
        self.gold_earned = 0
        self.gold_spent = 0
        self.training_completed = 0
        self.advanced_training_completed = 0
        self.guild_contributions = 0
        self.guild_dungeons = 0
        self.class_changes = 0
        self.daily_claims = 0
        self.quests_completed = 0
        # Quest tracking
        self.daily_quests = {}
        self.weekly_quests = {}
        self.long_term_quests = []
        self.achievement_progress = {}
        self.last_pvp_battle = None  # Timestamp of last PvP battle

    def get_max_battle_energy(self) -> int:
        """
        Calculate the player's maximum battle energy based on level and training.

        IMPORTANT: Battle Energy is the resource used for combat abilities and skills.
        It is completely separate from Gold, which is the game's currency.

        Battle Energy scales with player level (5 per level) and is permanently increased
        through Energy Cultivation specialized training.
        """
        # Base energy from max_battle_energy attribute
        base_energy = self.max_battle_energy

        # Battle Energy bonus from player level (5 per level after level 1)
        level_bonus = (self.class_level - 1) * 5

        # Battle Energy bonus from Energy Cultivation specialized training
        training_bonus = self.energy_training

        # Calculate total max battle energy
        total_max_energy = base_energy + level_bonus + training_bonus

        return total_max_energy

    def get_battle_energy(self) -> int:
        """
        Get the player's current battle energy, ensuring it never returns a negative value.
        This method should be used whenever displaying battle energy to the user.
        """
        return max(0, self.battle_energy)

    def get_max_hp(self, class_data: Dict[str, Any] = None) -> int:
        """
        Get the player's maximum HP based on their stats
        If class_data is not provided, will return a default max HP of 100
        """
        if class_data is None:
            # Return default HP if no class data available
            return 100

        stats = self.get_stats(class_data)
        return stats.get('hp', 100)

    def regenerate_health_and_energy(self,
                                     class_data: Dict[str, Any],
                                     percent: float = 1.0) -> None:
        """
        Regenerate the player's health and energy by the specified percentage
        percent: 1.0 = full regeneration, 0.5 = half regeneration, etc.
        """
        # Regenerate HP
        max_hp = self.get_max_hp(class_data)
        self.current_hp = max(int(max_hp * percent), 1)  # Ensure at least 1 HP

        # Regenerate Energy - battles should always restore to full energy
        # Regardless of percent parameter, energy is always fully restored
        max_energy = self.get_max_battle_energy()
        self.battle_energy = max_energy  # Always ensure full energy regeneration

    def add_dungeon_damage(self, damage: int, class_data: Dict[str,
                                                               Any]) -> None:
        """
        Add accumulated damage from a dungeon encounter
        """
        self.dungeon_damage += damage

        # Reduce current HP by the damage amount
        self.current_hp = max(self.current_hp - damage,
                              1)  # Ensure player always has at least 1 HP

    def reset_dungeon_damage(self,
                             class_data: Dict[str, Any],
                             full_heal: bool = True) -> None:
        """
        Reset accumulated dungeon damage and regenerate health
        full_heal: If True, fully restore HP; if False, keep current HP
        """
        self.dungeon_damage = 0

        if full_heal:
            # Fully restore HP
            self.current_hp = self.get_max_hp(class_data)

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
            if inv_item.equipped and hasattr(inv_item.item, 'stats'):
                for stat, value in inv_item.item.stats.items():
                    if stat in base_stats:
                        base_stats[stat] += value

        return base_stats

    def add_gold(self, amount: int) -> int:
        """Add gold with no maximum limit. Returns the amount added."""
        if amount <= 0:
            return 0

        # Simply add the amount (no limit)
        self.gold += amount
        # Track for achievements
        self.gold_earned += amount
        return amount

    def remove_gold(self, amount: int) -> bool:
        """Remove gold if available. Returns True if successful."""
        if amount <= 0:
            return True

        if self.gold >= amount:
            self.gold -= amount
            # Track for achievements
            self.gold_spent += amount
            return True
        return False

    # Legacy method for backward compatibility
    def add_cursed_energy(self, amount: int) -> int:
        """Legacy method that calls add_gold"""
        return self.add_gold(amount)

    # Legacy method for backward compatibility
    def remove_cursed_energy(self, amount: int) -> bool:
        """Legacy method that calls remove_gold"""
        return self.remove_gold(amount)

    def add_battle_energy(self, amount: int) -> int:
        """Add battle energy up to maximum limit. Returns the actual amount added."""
        if amount <= 0:
            return 0

        old_value = self.battle_energy
        self.battle_energy = min(self.max_battle_energy,
                                 self.battle_energy + amount)
        return self.battle_energy - old_value

    def calculate_xp_for_level(self, level: int) -> int:
        """
        Calculate XP needed to level up from a specific level
        This is the canonical XP formula that should be used throughout the game
        """
        # Updated to match the easier progression formula in level_validation.py
        base_xp = 75  # Reduced from 100 to make progression easier
        level_exponent = 1.35  # Reduced from 1.5 to flatten the curve for high levels
        return int(base_xp * (level**level_exponent))

    def xp_to_next_level(self) -> int:
        """Calculate XP needed for the next level."""
        # Use the standard formula
        return self.calculate_xp_for_level(self.class_level)

    def remove_battle_energy(self, amount: int) -> bool:
        """Remove battle energy if available. Returns True if successful."""
        if amount <= 0:
            return True

        if self.battle_energy >= amount:
            self.battle_energy -= amount
            return True
        return False

    def add_exp(self, exp_amount: int) -> bool:
        """Add experience points and handle level ups. Returns True if leveled up."""
        leveled_up = False

        # Reduce the XP penalty for higher levels to make progression easier
        level_penalty = max(
            0.95,
            1.0 - (self.class_level *
                   0.002))  # 0.2% reduction per level, min 95% of original XP
        adjusted_exp = int(exp_amount * level_penalty)

        self.class_exp += adjusted_exp

        # Calculate the required XP for the current level
        MAX_LEVEL = 1000  # Maximum level cap
        leveled_up = False

        if self.class_level >= MAX_LEVEL:
            return False

        # Calculate XP needed for next level using the standard formula
        xp_needed = self.calculate_xp_for_level(self.class_level)

        # Level up while player has enough XP
        while self.class_exp >= xp_needed and self.class_level < MAX_LEVEL:
            self.class_exp -= xp_needed
            self.class_level += 1
            leveled_up = True

            # Increase rewards at level-up
            self.skill_points += 3
            self.max_gold += 200
            self.gold = min(self.gold + 150, self.max_gold)

            # Increase max battle energy on level up
            battle_energy_increase = 5 + (self.class_level // 10)
            self.max_battle_energy += battle_energy_increase
            # Refill battle energy on level up
            self.battle_energy = self.max_battle_energy

            # Set a flag to check achievements after the whole leveling process

            # Calculate XP needed for the next level if not at max level
            if self.class_level < MAX_LEVEL:
                xp_needed = self.calculate_xp_for_level(self.class_level)

        # The leveled_up flag will be returned
        # When handling this in the calling code, make sure to check achievements
        # Since the PlayerData instance doesn't have direct access to the DataManager,
        # achievement checking needs to happen in code that has access to both

        return leveled_up

    def to_dict(self) -> Dict[str, Any]:
        return {
            "class_name":
            self.class_name,
            "class_level":
            self.class_level,
            "class_exp":
            self.class_exp,
            "user_level":
            self.user_level,
            "user_exp":
            self.user_exp,
            "gold":
            self.gold,
            "max_gold":
            self.max_gold,
            "cursed_energy":
            self.cursed_energy,  # Store actual cursed energy
            "max_cursed_energy":
            self.max_gold,  # For backward compatibility
            "unlocked_classes":
            self.unlocked_classes,
            "inventory": [item.to_dict() for item in self.inventory],
            "equipped_items":
            self.equipped_items,
            "achievements":
            [achievement.to_dict() for achievement in self.achievements],
            "skill_points":
            self.skill_points,
            "allocated_stats":
            self.allocated_stats,
            "skill_tree":
            self.skill_tree,
            "skill_points_spent":
            self.skill_points_spent,
            "wins":
            self.wins,
            "losses":
            self.losses,
            "last_daily":
            self.last_daily.isoformat() if self.last_daily else None,
            "daily_streak":
            self.daily_streak,
            "last_train":
            self.last_train.isoformat() if self.last_train else None,
            "dungeon_clears":
            self.dungeon_clears,
            "skill_cooldowns": {
                k: v.isoformat()
                for k, v in self.skill_cooldowns.items()
            } if self.skill_cooldowns else {},
            "special_abilities":
            self.special_abilities,
            "active_effects":
            self.active_effects,
            "training_cooldowns":
            self.training_cooldowns,
            "battle_energy":
            self.battle_energy,
            "max_battle_energy":
            self.max_battle_energy,
            "technique_grade":
            self.technique_grade,
            "domain_expansion":
            self.domain_expansion,
            "pvp_history":
            self.pvp_history,
            "pvp_wins":
            self.pvp_wins,
            "pvp_losses":
            self.pvp_losses,
            "last_pvp_battle":
            self.last_pvp_battle.isoformat() if self.last_pvp_battle else None,
            "equipped_gathering_tools":
            self.equipped_gathering_tools
        }

    @classmethod
    def from_dict(cls, user_id: int, data: Dict[str, Any]) -> 'PlayerData':
        player = cls(user_id)

        # Handle currency conversion (from cursed_energy to gold)
        if "gold" in data:
            player.gold = data["gold"]
        elif "cursed_energy" in data:
            # Convert old cursed_energy to gold
            player.gold = data["cursed_energy"]

        # Load actual cursed energy (used for special abilities)
        if "cursed_energy" in data:
            player.cursed_energy = data["cursed_energy"]

        # Handle maximum currency
        if "max_gold" in data:
            player.max_gold = data["max_gold"]
        elif "max_cursed_energy" in data:
            # Convert old max_cursed_energy to max_gold
            player.max_gold = data["max_cursed_energy"]

        # Set simple attributes
        for attr in [
                "class_name",
                "class_level",
                "class_exp",
                "user_level",
                "user_exp",
                "battle_energy",
                "max_battle_energy",
                "technique_grade",
                "domain_expansion",
                "unlocked_classes",
                "equipped_items",
                "skill_points",
                "allocated_stats",
                "skill_tree",
                "skill_points_spent",
                "wins",
                "losses",
                "daily_streak",
                "dungeon_clears",
                "special_abilities",
                "active_effects",
                "training_cooldowns",
                "pvp_history",
                "pvp_wins",
                "pvp_losses",
                "energy_training",
                "equipped_gathering_tools"  # Make sure we load equipped tools
        ]:
            if attr in data:
                setattr(player, attr, data[attr])

        # Convert inventory
        if "inventory" in data:
            player.inventory = [
                InventoryItem.from_dict(item_data)
                for item_data in data["inventory"]
            ]

        # Convert achievements
        if "achievements" in data:
            player.achievements = [
                Achievement.from_dict(achievement_data)
                for achievement_data in data["achievements"]
            ]

        # Convert datetime objects
        for dt_attr in ["last_daily", "last_train", "last_pvp_battle"]:
            if dt_attr in data and data[dt_attr]:
                try:
                    setattr(player, dt_attr,
                            datetime.datetime.fromisoformat(data[dt_attr]))
                except (ValueError, TypeError):
                    setattr(player, dt_attr, None)

        # Convert skill cooldowns
        if "skill_cooldowns" in data:
            player.skill_cooldowns = {}
            for skill_id, timestamp in data["skill_cooldowns"].items():
                try:
                    player.skill_cooldowns[
                        skill_id] = datetime.datetime.fromisoformat(timestamp)
                except (ValueError, TypeError):
                    continue

        return player


class DataManager:

    def __init__(self):
        self.players: Dict[int, PlayerData] = {}
        self.dungeons = {}  # Will be populated with dungeon data
        self.active_events = {}  # Active server events
        self.member_guild_map = {}  # Maps member IDs to guild IDs
        self.guild_data = {}  # Guild data storage
        self.player_data = {}  # For compatibility with existing code
        self.achievement_tracker = None  # Will be initialized after imports

        if not os.path.exists('player_data.json'):
            with open('player_data.json', 'w') as f:
                json.dump({}, f)
        self.load_data()
        self.load_dungeons()

    def save_data(self):
        try:
            # Save player data
            player_data = {}
            for user_id, player in self.players.items():
                player_data[str(user_id)] = player.to_dict()

            # Create complete data object with both player and guild data
            complete_data = {
                "players": player_data,
                "guilds": self.guild_data,
                "member_guild_map": self.member_guild_map
            }

            with open('player_data.json', 'w') as f:
                json.dump(complete_data, f, indent=4)

            print("Successfully saved player and guild data")
        except Exception as e:
            print(f"Error saving data: {e}")

    def load_data(self):
        try:
            with open('player_data.json', 'r') as f:
                data = json.load(f)

            # Check if we have the new format with separate players and guilds
            if isinstance(data, dict) and "players" in data:
                # New format
                player_data = data.get("players", {})
                self.guild_data = data.get("guilds", {})
                self.member_guild_map = data.get("member_guild_map", {})

                # Convert string keys to int for member_guild_map
                if self.member_guild_map:
                    self.member_guild_map = {
                        int(k): v
                        for k, v in self.member_guild_map.items()
                    }

                for user_id, p_data in player_data.items():
                    self.players[int(user_id)] = PlayerData.from_dict(
                        int(user_id), p_data)
            else:
                # Old format - only player data
                for user_id, player_data in data.items():
                    self.players[int(user_id)] = PlayerData.from_dict(
                        int(user_id), player_data)

            print(
                f"Loaded {len(self.players)} players and {len(self.guild_data)} guilds"
            )
        except Exception as e:
            print(f"Error loading data: {e}")

    def get_player(self, user_id: int) -> PlayerData:
        """Get a player or create a new one if not exists"""
        if user_id not in self.players:
            self.players[user_id] = PlayerData(user_id)
            self.save_data()
        return self.players[user_id]

    def check_player_achievements(self, player: PlayerData) -> List[Dict[str, Any]]:
        """Check for new achievements and return any that were earned

        This method should be called after any action that might
        trigger an achievement (leveling up, winning battles, etc.)
        """
        # We need to import here to avoid circular imports
        if self.achievement_tracker is None:
            from achievements import AchievementTracker
            self.achievement_tracker = AchievementTracker(self)

        # Check for new achievements
        new_achievements = self.achievement_tracker.check_achievements(player)

        # If any achievements were earned, save the data
        if new_achievements:
            self.save_data()

        return new_achievements

    def load_dungeons(self):
        """Load dungeon data from the DUNGEONS dictionary in dungeons.py"""
        from dungeons import DUNGEONS
        self.dungeons = DUNGEONS.copy()
