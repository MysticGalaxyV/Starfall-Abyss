import discord
from discord.ui import Button, View, Select
import datetime
import random
from typing import Dict, List, Any, Optional, Tuple

from data_models import PlayerData, DataManager, Achievement

# Achievement definitions with requirements, rewards, and badges
ACHIEVEMENTS = {
    # Leveling achievements
    "first_steps": {
        "name": "First Steps",
        "description": "Reach level 5",
        "category": "leveling",
        "requirement": {"type": "level", "value": 5},
        "reward": {"exp": 100, "gold": 100},
        "badge": "🥉",
        "points": 10
    },
    "apprentice_adventurer": {
        "name": "Apprentice Adventurer",
        "description": "Reach level 15",
        "category": "leveling",
        "requirement": {"type": "level", "value": 15},
        "reward": {"exp": 300, "gold": 300},
        "badge": "🥈",
        "points": 20
    },
    "skilled_explorer": {
        "name": "Skilled Explorer",
        "description": "Reach level 30",
        "category": "leveling",
        "requirement": {"type": "level", "value": 30},
        "reward": {"exp": 500, "gold": 500},
        "badge": "🥇",
        "points": 30
    },
    "master_adventurer": {
        "name": "Master Adventurer",
        "description": "Reach level 50",
        "category": "leveling",
        "requirement": {"type": "level", "value": 50},
        "reward": {"exp": 1000, "gold": 1000},
        "badge": "🏆",
        "points": 50
    },
    "legendary_hero": {
        "name": "Legendary Hero",
        "description": "Reach level 100",
        "category": "leveling",
        "requirement": {"type": "level", "value": 100},
        "reward": {"exp": 5000, "gold": 5000},
        "badge": "👑",
        "points": 100
    },

    # Battle achievements
    "battle_novice": {
        "name": "Battle Novice",
        "description": "Win 10 battles",
        "category": "combat",
        "requirement": {"type": "wins", "value": 10},
        "reward": {"exp": 100, "gold": 100},
        "badge": "⚔️",
        "points": 10
    },
    "combat_expert": {
        "name": "Combat Expert",
        "description": "Win 50 battles",
        "category": "combat",
        "requirement": {"type": "wins", "value": 50},
        "reward": {"exp": 300, "gold": 300},
        "badge": "⚔️⚔️",
        "points": 20
    },
    "battle_master": {
        "name": "Battle Master",
        "description": "Win 200 battles",
        "category": "combat",
        "requirement": {"type": "wins", "value": 200},
        "reward": {"exp": 500, "gold": 500},
        "badge": "⚔️⚔️⚔️",
        "points": 30
    },
    "monster_slayer": {
        "name": "Monster Slayer",
        "description": "Defeat 500 enemies",
        "category": "combat",
        "requirement": {"type": "wins", "value": 500},
        "reward": {"exp": 1000, "gold": 1000},
        "badge": "☠️",
        "points": 50
    },
    "pvp_novice": {
        "name": "PVP Novice",
        "description": "Win 5 PVP battles",
        "category": "combat",
        "requirement": {"type": "pvp_wins", "value": 5},
        "reward": {"exp": 200, "gold": 200},
        "badge": "🎯",
        "points": 20
    },
    "pvp_master": {
        "name": "PVP Master",
        "description": "Win 25 PVP battles",
        "category": "combat",
        "requirement": {"type": "pvp_wins", "value": 25},
        "reward": {"exp": 500, "gold": 500},
        "badge": "🎯🎯",
        "points": 40
    },

    # Dungeon achievements
    "dungeon_crawler": {
        "name": "Dungeon Crawler",
        "description": "Complete 5 dungeons",
        "category": "exploration",
        "requirement": {"type": "dungeons_completed", "value": 5},
        "reward": {"exp": 200, "gold": 200},
        "badge": "🔍",
        "points": 15
    },
    "dungeon_master": {
        "name": "Dungeon Master",
        "description": "Complete 20 dungeons",
        "category": "exploration",
        "requirement": {"type": "dungeons_completed", "value": 20},
        "reward": {"exp": 400, "gold": 400},
        "badge": "🔍🔍",
        "points": 30
    },
    "legendary_explorer": {
        "name": "Legendary Explorer",
        "description": "Complete 50 dungeons",
        "category": "exploration",
        "requirement": {"type": "dungeons_completed", "value": 50},
        "reward": {"exp": 1000, "gold": 1000},
        "badge": "🔍🔍🔍",
        "points": 50
    },
    "boss_hunter": {
        "name": "Boss Hunter",
        "description": "Defeat 10 dungeon bosses",
        "category": "exploration",
        "requirement": {"type": "bosses_defeated", "value": 10},
        "reward": {"exp": 500, "gold": 500},
        "badge": "👹",
        "points": 30
    },

    # Wealth achievements
    "small_fortune": {
        "name": "Small Fortune",
        "description": "Accumulate 1,000 gold",
        "category": "wealth",
        "requirement": {"type": "gold_earned", "value": 1000},
        "reward": {"exp": 100},
        "badge": "💰",
        "points": 10
    },
    "treasure_hunter": {
        "name": "Treasure Hunter",
        "description": "Accumulate 10,000 gold",
        "category": "wealth",
        "requirement": {"type": "gold_earned", "value": 10000},
        "reward": {"exp": 300},
        "badge": "💰💰",
        "points": 20
    },
    "gold_hoarder": {
        "name": "Gold Hoarder",
        "description": "Accumulate 100,000 gold",
        "category": "wealth",
        "requirement": {"type": "gold_earned", "value": 100000},
        "reward": {"exp": 1000},
        "badge": "💰💰💰",
        "points": 50
    },
    "big_spender": {
        "name": "Big Spender",
        "description": "Spend 50,000 gold",
        "category": "wealth",
        "requirement": {"type": "gold_spent", "value": 50000},
        "reward": {"exp": 500},
        "badge": "🛍️",
        "points": 30
    },

    # Collection achievements
    "item_collector": {
        "name": "Item Collector",
        "description": "Collect 20 unique items",
        "category": "collection",
        "requirement": {"type": "unique_items", "value": 20},
        "reward": {"exp": 200, "gold": 200},
        "badge": "🎒",
        "points": 15
    },
    "weapon_master": {
        "name": "Weapon Master",
        "description": "Collect 10 unique weapons",
        "category": "collection",
        "requirement": {"type": "unique_weapons", "value": 10},
        "reward": {"exp": 300, "gold": 300},
        "badge": "🗡️",
        "points": 20
    },
    "armor_collector": {
        "name": "Armor Collector",
        "description": "Collect 10 unique armor pieces",
        "category": "collection",
        "requirement": {"type": "unique_armor", "value": 10},
        "reward": {"exp": 300, "gold": 300},
        "badge": "🛡️",
        "points": 20
    },
    "accessory_enthusiast": {
        "name": "Accessory Enthusiast",
        "description": "Collect 10 unique accessories",
        "category": "collection",
        "requirement": {"type": "unique_accessories", "value": 10},
        "reward": {"exp": 300, "gold": 300},
        "badge": "💍",
        "points": 20
    },
    "rare_collector": {
        "name": "Rare Collector",
        "description": "Collect 5 rare or higher items",
        "category": "collection",
        "requirement": {"type": "rare_items", "value": 5},
        "reward": {"exp": 300, "gold": 300},
        "badge": "🔷",
        "points": 20
    },
    "epic_collector": {
        "name": "Epic Collector",
        "description": "Collect 3 epic or higher items",
        "category": "collection",
        "requirement": {"type": "epic_items", "value": 3},
        "reward": {"exp": 500, "gold": 500},
        "badge": "🔶",
        "points": 30
    },
    "legendary_collector": {
        "name": "Legendary Collector",
        "description": "Collect 1 legendary item",
        "category": "collection",
        "requirement": {"type": "legendary_items", "value": 1},
        "reward": {"exp": 1000, "gold": 1000},
        "badge": "✨",
        "points": 50
    },

    # Training achievements
    "training_novice": {
        "name": "Training Novice",
        "description": "Complete 10 training sessions",
        "category": "training",
        "requirement": {"type": "training_completed", "value": 10},
        "reward": {"exp": 100, "gold": 100},
        "badge": "🏋️",
        "points": 10
    },
    "training_enthusiast": {
        "name": "Training Enthusiast",
        "description": "Complete 50 training sessions",
        "category": "training",
        "requirement": {"type": "training_completed", "value": 50},
        "reward": {"exp": 300, "gold": 300},
        "badge": "🏋️🏋️",
        "points": 20
    },
    "training_master": {
        "name": "Training Master",
        "description": "Complete 200 training sessions",
        "category": "training",
        "requirement": {"type": "training_completed", "value": 200},
        "reward": {"exp": 500, "gold": 500},
        "badge": "🏋️🏋️🏋️",
        "points": 30
    },
    "advanced_training_specialist": {
        "name": "Advanced Training Specialist",
        "description": "Complete 20 advanced training sessions",
        "category": "training",
        "requirement": {"type": "advanced_training_completed", "value": 20},
        "reward": {"exp": 400, "gold": 400},
        "badge": "🏆",
        "points": 25
    },

    # Guild achievements
    "guild_member": {
        "name": "Guild Member",
        "description": "Join a guild",
        "category": "guild",
        "requirement": {"type": "join_guild", "value": 1},
        "reward": {"exp": 100, "gold": 100},
        "badge": "🏰",
        "points": 10
    },
    "guild_contributor": {
        "name": "Guild Contributor",
        "description": "Contribute 1,000 gold to your guild",
        "category": "guild",
        "requirement": {"type": "guild_contributions", "value": 1000},
        "reward": {"exp": 200, "gold": 100},
        "badge": "🤝",
        "points": 15
    },
    "guild_explorer": {
        "name": "Guild Explorer",
        "description": "Complete 10 guild dungeons",
        "category": "guild",
        "requirement": {"type": "guild_dungeons", "value": 10},
        "reward": {"exp": 300, "gold": 300},
        "badge": "👥",
        "points": 20
    },
    "guild_elite": {
        "name": "Guild Elite",
        "description": "Reach guild rank of officer",
        "category": "guild",
        "requirement": {"type": "guild_officer", "value": 1},
        "reward": {"exp": 500, "gold": 500},
        "badge": "👮",
        "points": 30
    },
    "guild_leader": {
        "name": "Guild Leader",
        "description": "Become a guild leader",
        "category": "guild",
        "requirement": {"type": "guild_leader", "value": 1},
        "reward": {"exp": 1000, "gold": 1000},
        "badge": "👑",
        "points": 50
    },

    # Special achievements
    "class_master": {
        "name": "Class Master",
        "description": "Change class 3 times",
        "category": "special",
        "requirement": {"type": "class_changes", "value": 3},
        "reward": {"exp": 500, "gold": 500},
        "badge": "🧙",
        "points": 30
    },
    "daily_login": {
        "name": "Dedicated Player",
        "description": "Claim daily rewards 30 times",
        "category": "special",
        "requirement": {"type": "daily_claims", "value": 30},
        "reward": {"exp": 500, "gold": 500},
        "badge": "📅",
        "points": 20
    },
    "completionist": {
        "name": "Completionist",
        "description": "Complete 50 quests",
        "category": "quests",
        "requirement": {"type": "quests_completed", "value": 50},
        "reward": {"exp": 1000, "gold": 1000},
        "badge": "📜",
        "points": 40
    },
    "achievement_hunter": {
        "name": "Achievement Hunter",
        "description": "Earn 20 achievements",
        "category": "meta",
        "requirement": {"type": "achievements_earned", "value": 20},
        "reward": {"exp": 1000, "gold": 1000, "special_item": "Achievement Hunter's Badge"},
        "badge": "🎯",
        "points": 50
    },
    "server_role": {
        "name": "Elite Status",
        "description": "Earn 500 achievement points to unlock the Elite Role",
        "category": "meta",
        "requirement": {"type": "achievement_points", "value": 500},
        "reward": {"exp": 2000, "gold": 2000, "server_role": "Elite Adventurer"},
        "badge": "🌟",
        "points": 100
    }
}

# Daily quests - these reset daily
DAILY_QUESTS = [
    {
        "id": "daily_battles",
        "name": "Daily Battles",
        "description": "Win {value} battles today",
        "type": "daily_wins",
        "min_value": 3,
        "max_value": 10,
        "reward": {"exp": lambda v: v * 50, "gold": lambda v: v * 50}
    },
    {
        "id": "daily_dungeons",
        "name": "Daily Expedition",
        "description": "Complete {value} dungeon today",
        "type": "daily_dungeons",
        "min_value": 1,
        "max_value": 3,
        "reward": {"exp": lambda v: v * 100, "gold": lambda v: v * 100}
    },
    {
        "id": "daily_training",
        "name": "Daily Training",
        "description": "Complete {value} training sessions today",
        "type": "daily_training",
        "min_value": 1,
        "max_value": 5,
        "reward": {"exp": lambda v: v * 30, "gold": lambda v: v * 30}
    },
    {
        "id": "daily_gold",
        "name": "Gold Hunter",
        "description": "Earn {value} gold today",
        "type": "daily_gold",
        "min_value": 100,
        "max_value": 1000,
        "reward": {"exp": lambda v: int(v * 0.2)}
    },
    {
        "id": "daily_items",
        "name": "Item Collector",
        "description": "Find {value} new items today",
        "type": "daily_items",
        "min_value": 1,
        "max_value": 5,
        "reward": {"exp": lambda v: v * 80, "gold": lambda v: v * 40}
    },
    {
        "id": "daily_pvp",
        "name": "PVP Daily",
        "description": "Win {value} PVP battles today",
        "type": "daily_pvp",
        "min_value": 1,
        "max_value": 3,
        "reward": {"exp": lambda v: v * 100, "gold": lambda v: v * 100}
    }
]

# Weekly quests - these reset weekly
WEEKLY_QUESTS = [
    {
        "id": "weekly_bosses",
        "name": "Boss Hunter",
        "description": "Defeat {value} bosses this week",
        "type": "weekly_bosses",
        "min_value": 2,
        "max_value": 7,
        "reward": {"exp": lambda v: v * 200, "gold": lambda v: v * 200}
    },
    {
        "id": "weekly_pvp",
        "name": "PVP Champion",
        "description": "Win {value} PVP battles this week",
        "type": "weekly_pvp",
        "min_value": 3,
        "max_value": 10,
        "reward": {"exp": lambda v: v * 150, "gold": lambda v: v * 150}
    },
    {
        "id": "weekly_guild",
        "name": "Guild Activity",
        "description": "Contribute {value} gold to your guild this week",
        "type": "weekly_guild_contribution",
        "min_value": 500,
        "max_value": 2000,
        "reward": {"exp": lambda v: int(v * 0.3)}
    },
    {
        "id": "weekly_training",
        "name": "Advanced Training",
        "description": "Complete {value} advanced training sessions this week",
        "type": "weekly_advanced_training",
        "min_value": 2,
        "max_value": 7,
        "reward": {"exp": lambda v: v * 120, "gold": lambda v: v * 120}
    },
    {
        "id": "weekly_dungeons",
        "name": "Weekly Explorer",
        "description": "Complete {value} dungeons this week",
        "type": "weekly_dungeons",
        "min_value": 3,
        "max_value": 10,
        "reward": {"exp": lambda v: v * 150, "gold": lambda v: v * 150}
    },
    {
        "id": "weekly_wins",
        "name": "Weekly Warrior",
        "description": "Win {value} battles this week",
        "type": "weekly_wins",
        "min_value": 10,
        "max_value": 25,
        "reward": {"exp": lambda v: v * 100, "gold": lambda v: v * 100}
    }
]

# Long-term quests - these don't reset
LONG_TERM_QUESTS = [
    {
        "id": "level_milestone_30",
        "name": "Veteran Adventurer",
        "description": "Reach level 30",
        "type": "reach_level",
        "value": 30,
        "reward": {"exp": 2000, "gold": 2000, "special_item": "Veteran's Medal"}
    },
    {
        "id": "dungeon_milestone_50",
        "name": "Dungeon Expert",
        "description": "Complete 50 dungeons",
        "type": "total_dungeons",
        "value": 50,
        "reward": {"exp": 3000, "gold": 3000, "special_item": "Dungeon Map Fragment"}
    },
    {
        "id": "battle_milestone_500",
        "name": "Battlemaster",
        "description": "Win 500 battles",
        "type": "total_wins",
        "value": 500,
        "reward": {"exp": 5000, "gold": 5000, "special_item": "Battlemaster's Insignia"}
    },
    {
        "id": "elite_equipment",
        "name": "Elite Equipment",
        "description": "Collect 5 legendary items",
        "type": "legendary_items",
        "value": 5,
        "reward": {"exp": 10000, "gold": 10000, "special_item": "Legendary Equipment Box"}
    },
    {
        "id": "guild_legend",
        "name": "Guild Legend",
        "description": "Reach level 10 with your guild",
        "type": "guild_level",
        "value": 10,
        "reward": {"exp": 5000, "gold": 5000, "special_item": "Guild Banner"}
    },
    {
        "id": "training_master",
        "name": "Training Master",
        "description": "Complete 100 training sessions",
        "type": "total_training",
        "value": 100,
        "reward": {"exp": 3000, "gold": 3000, "special_item": "Master Trainer's Certificate"}
    },
    {
        "id": "level_milestone_50",
        "name": "Elite Adventurer",
        "description": "Reach level 50",
        "type": "reach_level",
        "value": 50,
        "reward": {"exp": 5000, "gold": 5000, "special_item": "Elite Adventurer's Crown"}
    }
]

# Special server events
SPECIAL_EVENTS = [
    {
        "id": "double_exp",
        "name": "Double XP Weekend",
        "description": "Earn double XP from all sources!",
        "effect": {"type": "exp_multiplier", "value": 2.0},
        "duration": 2  # days
    },
    {
        "id": "gold_rush",
        "name": "Gold Rush",
        "description": "Earn 50% more gold from all sources!",
        "effect": {"type": "gold_multiplier", "value": 1.5},
        "duration": 1  # days
    },
    # Dragon Bosses
    {
        "id": "special_boss_fire_dragon",
        "name": "World Boss: Infernus the Fire Dragon",
        "description": "A powerful fire dragon has appeared! Work together to defeat it for special fire-based rewards!",
        "effect": {"type": "world_boss", "boss_name": "Infernus the Fire Dragon", "boss_level": lambda avg_lvl: avg_lvl + 20},
        "duration": 0.5  # days (12 hours)
    },
    {
        "id": "special_boss_ice_dragon",
        "name": "World Boss: Glacius the Ice Dragon",
        "description": "A fearsome ice dragon has appeared! Defeat it to claim rare frost items!",
        "effect": {"type": "world_boss", "boss_name": "Glacius the Ice Dragon", "boss_level": lambda avg_lvl: avg_lvl + 22},
        "duration": 0.5  # days (12 hours)
    },
    {
        "id": "special_boss_storm_dragon",
        "name": "World Boss: Tempestus the Storm Dragon",
        "description": "A mighty storm dragon brings thunder and lightning! Defeat it for storm-infused rewards!",
        "effect": {"type": "world_boss", "boss_name": "Tempestus the Storm Dragon", "boss_level": lambda avg_lvl: avg_lvl + 25},
        "duration": 0.5  # days (12 hours)
    },

    # Elemental Lords
    {
        "id": "special_boss_fire_lord",
        "name": "World Boss: Ignius the Fire Lord",
        "description": "The lord of fire has emerged from the volcano! Battle this blazing enemy for fire-imbued rewards!",
        "effect": {"type": "world_boss", "boss_name": "Ignius the Fire Lord", "boss_level": lambda avg_lvl: avg_lvl + 18},
        "duration": 0.5  # days (12 hours)
    },
    {
        "id": "special_boss_water_lord",
        "name": "World Boss: Aquarius the Water Lord",
        "description": "The ruler of the deep seas has risen! Defeat this watery foe for aquatic treasures!",
        "effect": {"type": "world_boss", "boss_name": "Aquarius the Water Lord", "boss_level": lambda avg_lvl: avg_lvl + 19},
        "duration": 0.5  # days (12 hours)
    },

    # Mythic Creatures
    {
        "id": "special_boss_phoenix",
        "name": "World Boss: Eternus the Phoenix",
        "description": "The immortal phoenix spreads its fiery wings! Defeat it before it can be reborn!",
        "effect": {"type": "world_boss", "boss_name": "Eternus the Phoenix", "boss_level": lambda avg_lvl: avg_lvl + 23},
        "duration": 0.5  # days (12 hours)
    },
    {
        "id": "special_boss_kraken",
        "name": "World Boss: Tentalus the Kraken",
        "description": "The legendary sea monster attacks! Battle its many tentacles for deep-sea treasures!",
        "effect": {"type": "world_boss", "boss_name": "Tentalus the Kraken", "boss_level": lambda avg_lvl: avg_lvl + 24},
        "duration": 0.5  # days (12 hours)
    },

    # Undead Lords
    {
        "id": "special_boss_lich_king",
        "name": "World Boss: Mortus the Lich King",
        "description": "The dreaded Lich King commands his undead army! Destroy this necromancer for dark artifacts!",
        "effect": {"type": "world_boss", "boss_name": "Mortus the Lich King", "boss_level": lambda avg_lvl: avg_lvl + 26},
        "duration": 0.5  # days (12 hours)
    },

    # Generic Boss (fallback)
    {
        "id": "special_boss",
        "name": "World Boss: Ancient Behemoth",
        "description": "A powerful world boss has appeared! Work together to defeat it for special rewards!",
        "effect": {"type": "world_boss", "boss_name": "Ancient Behemoth", "boss_level": lambda avg_lvl: avg_lvl + 20},
        "duration": 0.5  # days (12 hours)
    },
    {
        "id": "item_boost",
        "name": "Lucky Loot",
        "description": "Increased chance of rare items from all sources!",
        "effect": {"type": "item_rarity_boost", "value": 1.5},
        "duration": 1  # days
    },
    {
        "id": "training_boost",
        "name": "Training Frenzy",
        "description": "All training now gives double stat bonuses!",
        "effect": {"type": "training_multiplier", "value": 2.0},
        "duration": 1  # days
    },
    {
        "id": "fortune_event",
        "name": "Fortune Event",
        "description": "A mystical fortune event has occurred! Increased gold drops by 75%!",
        "effect": {"type": "gold_multiplier", "value": 1.75},
        "duration": 1  # days
    },
    {
        "id": "gold_rush",
        "name": "Gold Rush Event",
        "description": "The legendary Gold Rush is here! All gold rewards are doubled!",
        "effect": {"type": "gold_multiplier", "value": 2.0},
        "duration": 1  # days
    }
]

class AchievementTracker:
    def __init__(self, data_manager: DataManager):
        self.data_manager = data_manager

    def get_player_achievements(self, player: PlayerData) -> List[Dict[str, Any]]:
        """Get a list of player's completed achievements"""
        if not hasattr(player, "achievements"):
            player.achievements = []

        completed_achievements = []
        for achievement in player.achievements:
            # Handle both string IDs and Achievement objects
            if isinstance(achievement, str):
                achievement_id = achievement
            elif hasattr(achievement, 'achievement_id'):
                achievement_id = achievement.achievement_id
            else:
                continue
                
            if achievement_id in ACHIEVEMENTS:
                completed_achievements.append({
                    "id": achievement_id,
                    **ACHIEVEMENTS[achievement_id]
                })

        return completed_achievements

    def get_player_achievement_points(self, player: PlayerData) -> int:
        """Get available achievement points for player (earned minus spent)"""
        total_earned = 0

        if not hasattr(player, "achievements"):
            player.achievements = []

        for achievement in player.achievements:
            # Handle both string IDs and Achievement objects
            if isinstance(achievement, str):
                achievement_id = achievement
            elif hasattr(achievement, 'achievement_id'):
                achievement_id = achievement.achievement_id
            else:
                continue
                
            if achievement_id in ACHIEVEMENTS:
                total_earned += ACHIEVEMENTS[achievement_id].get("points", 0)

        # Initialize spent_achievement_points if it doesn't exist
        if not hasattr(player, "spent_achievement_points"):
            player.spent_achievement_points = 0

        # Return available points (earned minus spent)
        return total_earned - player.spent_achievement_points

    def get_player_available_achievements(self, player: PlayerData) -> List[Dict[str, Any]]:
        """Get a list of player's available (not yet completed) achievements"""
        if not hasattr(player, "achievements"):
            player.achievements = []

        # Get list of completed achievement IDs
        completed_ids = []
        for achievement in player.achievements:
            if isinstance(achievement, str):
                completed_ids.append(achievement)
            elif hasattr(achievement, 'achievement_id'):
                completed_ids.append(achievement.achievement_id)

        available_achievements = []
        for achievement_id, achievement in ACHIEVEMENTS.items():
            if achievement_id not in completed_ids:
                available_achievements.append({
                    "id": achievement_id,
                    **achievement
                })

        return available_achievements

    def check_achievements(self, player: PlayerData) -> List[Dict[str, Any]]:
        """Check and apply any newly completed achievements"""
        if not hasattr(player, "achievements"):
            player.achievements = []

        if not hasattr(player, "achievement_progress"):
            player.achievement_progress = {}

        newly_earned = []

        # Get available achievements
        available_achievements = self.get_player_available_achievements(player)

        for achievement in available_achievements:
            # Skip already earned - check both string IDs and Achievement objects
            earned_ids = []
            for ach in player.achievements:
                if hasattr(ach, 'achievement_id'):
                    earned_ids.append(ach.achievement_id)
                elif isinstance(ach, str):
                    earned_ids.append(ach)
            
            if achievement["id"] in earned_ids:
                continue

            # Check if achievement is completed
            completed = self.check_achievement_completion(player, achievement)

            if completed:
                # Create Achievement object and add to player
                achievement_obj = Achievement(
                    achievement_id=achievement["id"],
                    name=achievement["name"],
                    description=achievement["description"],
                    reward=achievement.get("reward", {}),
                    completed_at=datetime.datetime.now()
                )
                player.achievements.append(achievement_obj)

                # Award rewards
                self.award_achievement_rewards(player, achievement)

                # Add to newly earned list
                newly_earned.append(achievement)

                # Check for meta achievements (like earning X achievements)
                if achievement["category"] == "meta":
                    # Recheck achievements since we just earned one
                    return newly_earned + self.check_achievements(player)

        return newly_earned

    def check_achievement_completion(self, player: PlayerData, achievement: Dict[str, Any]) -> bool:
        """Check if an achievement is completed"""
        req_type = achievement["requirement"]["type"]
        req_value = achievement["requirement"]["value"]

        # Check based on requirement type
        if req_type == "level":
            return player.class_level >= req_value

        elif req_type == "wins":
            return hasattr(player, "wins") and player.wins >= req_value

        elif req_type == "pvp_wins":
            return hasattr(player, "pvp_wins") and player.pvp_wins >= req_value

        elif req_type == "dungeons_completed":
            return hasattr(player, "dungeons_completed") and player.dungeons_completed >= req_value

        elif req_type == "bosses_defeated":
            return hasattr(player, "bosses_defeated") and player.bosses_defeated >= req_value

        elif req_type == "gold_earned":
            return hasattr(player, "gold_earned") and player.gold_earned >= req_value

        elif req_type == "gold_spent":
            return hasattr(player, "gold_spent") and player.gold_spent >= req_value

        elif req_type == "unique_items":
            return hasattr(player, "inventory") and len(self.get_unique_items(player)) >= req_value

        elif req_type == "unique_weapons":
            return hasattr(player, "inventory") and len(self.get_unique_items_by_type(player, "weapon")) >= req_value

        elif req_type == "unique_armor":
            return hasattr(player, "inventory") and len(self.get_unique_items_by_type(player, "armor")) >= req_value

        elif req_type == "unique_accessories":
            return hasattr(player, "inventory") and len(self.get_unique_items_by_type(player, "accessory")) >= req_value

        elif req_type == "rare_items":
            return hasattr(player, "inventory") and len(self.get_items_by_rarity(player, ["rare", "epic", "legendary", "mythic"])) >= req_value

        elif req_type == "epic_items":
            return hasattr(player, "inventory") and len(self.get_items_by_rarity(player, ["epic", "legendary", "mythic"])) >= req_value

        elif req_type == "legendary_items":
            return hasattr(player, "inventory") and len(self.get_items_by_rarity(player, ["legendary", "mythic"])) >= req_value

        elif req_type == "training_completed":
            return hasattr(player, "training_completed") and player.training_completed >= req_value

        elif req_type == "advanced_training_completed":
            return hasattr(player, "advanced_training_completed") and player.advanced_training_completed >= req_value

        elif req_type == "join_guild":
            # Check if player is in a guild
            if hasattr(self.data_manager, "member_guild_map"):
                return player.user_id in self.data_manager.member_guild_map
            return False

        elif req_type == "guild_contributions":
            return hasattr(player, "guild_contributions") and player.guild_contributions >= req_value

        elif req_type == "guild_dungeons":
            return hasattr(player, "guild_dungeons") and player.guild_dungeons >= req_value

        elif req_type == "guild_officer":
            # Check if player is a guild officer
            if hasattr(self.data_manager, "member_guild_map") and player.user_id in self.data_manager.member_guild_map:
                guild_name = self.data_manager.member_guild_map[player.user_id]
                if guild_name in self.data_manager.guild_data:
                    guild_data = self.data_manager.guild_data[guild_name]
                    return player.user_id in guild_data.get("officers", [])
            return False

        elif req_type == "guild_leader":
            # Check if player is a guild leader
            if hasattr(self.data_manager, "member_guild_map") and player.user_id in self.data_manager.member_guild_map:
                guild_name = self.data_manager.member_guild_map[player.user_id]
                if guild_name in self.data_manager.guild_data:
                    guild_data = self.data_manager.guild_data[guild_name]
                    return player.user_id == guild_data.get("leader_id")
            return False

        elif req_type == "class_changes":
            return hasattr(player, "class_changes") and player.class_changes >= req_value

        elif req_type == "daily_claims":
            return hasattr(player, "daily_claims") and player.daily_claims >= req_value

        elif req_type == "quests_completed":
            return hasattr(player, "quests_completed") and player.quests_completed >= req_value

        elif req_type == "achievements_earned":
            return len(player.achievements) >= req_value

        elif req_type == "achievement_points":
            return self.get_player_achievement_points(player) >= req_value

        return False

    def get_achievement_progress(self, player: PlayerData, achievement: Dict[str, Any]) -> Dict[str, Any]:
        """Get current progress for an achievement"""
        req_type = achievement["requirement"]["type"]
        req_value = achievement["requirement"]["value"]
        current_value = 0
        
        # Get current value based on requirement type
        if req_type == "level":
            current_value = player.class_level
            
        elif req_type == "wins":
            current_value = getattr(player, "wins", 0)
            
        elif req_type == "pvp_wins":
            current_value = getattr(player, "pvp_wins", 0)
            
        elif req_type == "dungeons_completed":
            current_value = getattr(player, "dungeons_completed", 0)
            
        elif req_type == "bosses_defeated":
            current_value = getattr(player, "bosses_defeated", 0)
            
        elif req_type == "gold_earned":
            current_value = getattr(player, "gold_earned", 0)
            
        elif req_type == "gold_spent":
            current_value = getattr(player, "gold_spent", 0)
            
        elif req_type == "unique_items":
            current_value = len(self.get_unique_items(player)) if hasattr(player, "inventory") else 0
            
        elif req_type == "unique_weapons":
            current_value = len(self.get_unique_items_by_type(player, "weapon")) if hasattr(player, "inventory") else 0
            
        elif req_type == "unique_armor":
            current_value = len(self.get_unique_items_by_type(player, "armor")) if hasattr(player, "inventory") else 0
            
        elif req_type == "unique_accessories":
            current_value = len(self.get_unique_items_by_type(player, "accessory")) if hasattr(player, "inventory") else 0
            
        elif req_type == "rare_items":
            current_value = len(self.get_items_by_rarity(player, ["rare", "epic", "legendary", "mythic"])) if hasattr(player, "inventory") else 0
            
        elif req_type == "epic_items":
            current_value = len(self.get_items_by_rarity(player, ["epic", "legendary", "mythic"])) if hasattr(player, "inventory") else 0
            
        elif req_type == "legendary_items":
            current_value = len(self.get_items_by_rarity(player, ["legendary", "mythic"])) if hasattr(player, "inventory") else 0
            
        elif req_type == "training_completed":
            current_value = getattr(player, "training_completed", 0)
            
        elif req_type == "advanced_training_completed":
            current_value = getattr(player, "advanced_training_completed", 0)
            
        elif req_type == "join_guild":
            # Binary achievement - either in guild (1) or not (0)
            if hasattr(self.data_manager, "member_guild_map"):
                current_value = 1 if player.user_id in self.data_manager.member_guild_map else 0
            req_value = 1
            
        elif req_type == "guild_contributions":
            current_value = getattr(player, "guild_contributions", 0)
            
        elif req_type == "guild_dungeons":
            current_value = getattr(player, "guild_dungeons", 0)
            
        elif req_type == "guild_officer":
            # Binary achievement - either officer (1) or not (0)
            current_value = 0
            if hasattr(self.data_manager, "member_guild_map") and player.user_id in self.data_manager.member_guild_map:
                guild_name = self.data_manager.member_guild_map[player.user_id]
                if guild_name in self.data_manager.guild_data:
                    guild_data = self.data_manager.guild_data[guild_name]
                    current_value = 1 if player.user_id in guild_data.get("officers", []) else 0
            req_value = 1
            
        elif req_type == "guild_leader":
            # Binary achievement - either leader (1) or not (0)
            current_value = 0
            if hasattr(self.data_manager, "member_guild_map") and player.user_id in self.data_manager.member_guild_map:
                guild_name = self.data_manager.member_guild_map[player.user_id]
                if guild_name in self.data_manager.guild_data:
                    guild_data = self.data_manager.guild_data[guild_name]
                    current_value = 1 if player.user_id == guild_data.get("leader_id") else 0
            req_value = 1
            
        elif req_type == "class_changes":
            current_value = getattr(player, "class_changes", 0)
            
        elif req_type == "daily_claims":
            current_value = getattr(player, "daily_claims", 0)
            
        elif req_type == "quests_completed":
            current_value = getattr(player, "quests_completed", 0)
            
        elif req_type == "achievements_earned":
            current_value = len(player.achievements) if hasattr(player, "achievements") else 0
            
        elif req_type == "achievement_points":
            current_value = self.get_player_achievement_points(player)
        
        # Calculate percentage and create progress bar
        percentage = min(100, (current_value / req_value) * 100) if req_value > 0 else 100
        progress_bar = self.create_progress_bar(current_value, req_value)
        
        return {
            "current": current_value,
            "required": req_value,
            "percentage": percentage,
            "progress_bar": progress_bar,
            "completed": current_value >= req_value
        }

    def create_progress_bar(self, current: int, maximum: int, length: int = 10) -> str:
        """Create a text progress bar"""
        if maximum <= 0:
            return "█" * length
            
        filled = int((current / maximum) * length) if maximum > 0 else 0
        filled = min(filled, length)
        empty = length - filled
        
        return "█" * filled + "░" * empty

    def get_unique_items(self, player: PlayerData) -> List[str]:
        """Get list of unique item names in player inventory"""
        if not hasattr(player, "inventory"):
            return []

        unique_items = set()
        for inv_item in player.inventory:
            unique_items.add(inv_item.item.name)

        return list(unique_items)

    def get_unique_items_by_type(self, player: PlayerData, item_type: str) -> List[str]:
        """Get list of unique items of a specific type"""
        if not hasattr(player, "inventory"):
            return []

        unique_items = set()
        for inv_item in player.inventory:
            if inv_item.item.item_type == item_type:
                unique_items.add(inv_item.item.name)

        return list(unique_items)

    def get_items_by_rarity(self, player: PlayerData, rarities: List[str]) -> List[str]:
        """Get list of items with specified rarities"""
        if not hasattr(player, "inventory"):
            return []

        matching_items = []
        for inv_item in player.inventory:
            if inv_item.item.rarity in rarities:
                matching_items.append(inv_item.item.name)

        return matching_items

    def award_achievement_rewards(self, player: PlayerData, achievement: Dict[str, Any]):
        """Award rewards for completing an achievement"""
        if "reward" not in achievement:
            return

        reward = achievement["reward"]

        # Award XP
        if "exp" in reward:
            player.add_exp(reward["exp"], data_manager=self.data_manager)

        # Award gold
        if "gold" in reward:
            if not hasattr(player, "gold"):
                player.gold = 0
            player.gold += reward["gold"]

        # Award special item if any
        if "special_item" in reward:
            # Import here to avoid circular imports
            from special_items import create_special_reward_item
            from equipment import add_item_to_inventory

            # Create the special reward item
            special_item = create_special_reward_item(reward["special_item"], achievement["name"])

            # Add to inventory
            if special_item:
                add_item_to_inventory(player, special_item)

        # Handle server role reward if any
        if "server_role" in reward:
            # Store that the player has earned this role
            if not hasattr(player, "earned_roles"):
                player.earned_roles = []

            if reward["server_role"] not in player.earned_roles:
                player.earned_roles.append(reward["server_role"])

        # Save player data
        self.data_manager.save_data()

class QuestManager:
    def __init__(self, data_manager: DataManager):
        self.data_manager = data_manager

        # Initialize event system if not already
        if not hasattr(self.data_manager, "active_events"):
            self.data_manager.active_events = {}

        # Check for event expiration
        self.check_expired_events()

    def get_daily_quests(self, player: PlayerData) -> List[Dict[str, Any]]:
        """Get player's active daily quests"""
        today = datetime.datetime.now().strftime("%Y-%m-%d")

        # Initialize player quest data if needed
        if not hasattr(player, "daily_quests"):
            player.daily_quests = {}

        # Check if we need to generate new daily quests
        if today not in player.daily_quests:
            # Generate new daily quests
            player.daily_quests[today] = self.generate_daily_quests(player)
            self.data_manager.save_data()

        return player.daily_quests[today]

    def generate_daily_quests(self, player: PlayerData) -> List[Dict[str, Any]]:
        """Generate a set of daily quests for a player"""
        # Select 3 random daily quests
        selected_quests = random.sample(DAILY_QUESTS, min(3, len(DAILY_QUESTS)))

        # Customize values based on player level
        daily_quests = []
        for quest_template in selected_quests:
            # Generate appropriate value based on level
            level_factor = min(1.0, player.class_level / 50)  # Cap at level 50
            value_range = quest_template["max_value"] - quest_template["min_value"]
            quest_value = quest_template["min_value"] + int(value_range * level_factor)

            # Calculate rewards
            rewards = {}
            for reward_type, reward_calc in quest_template["reward"].items():
                rewards[reward_type] = reward_calc(quest_value)

            # Create the quest
            quest = {
                "id": quest_template["id"],
                "name": quest_template["name"],
                "description": quest_template["description"].format(value=quest_value),
                "type": quest_template["type"],
                "value": quest_value,
                "progress": 0,
                "completed": False,
                "reward": rewards
            }

            daily_quests.append(quest)

        return daily_quests

    def get_weekly_quests(self, player: PlayerData) -> List[Dict[str, Any]]:
        """Get player's active weekly quests"""
        # Get current week (ISO week number)
        today = datetime.datetime.now()
        current_week = f"{today.year}-W{today.isocalendar()[1]}"

        # Initialize player quest data if needed
        if not hasattr(player, "weekly_quests"):
            player.weekly_quests = {}

        # Check if we need to generate new weekly quests
        if current_week not in player.weekly_quests:
            # Generate new weekly quests
            player.weekly_quests[current_week] = self.generate_weekly_quests(player)
            self.data_manager.save_data()

        return player.weekly_quests[current_week]

    def generate_weekly_quests(self, player: PlayerData) -> List[Dict[str, Any]]:
        """Generate a set of weekly quests for a player"""
        # Select 2 random weekly quests
        selected_quests = random.sample(WEEKLY_QUESTS, min(2, len(WEEKLY_QUESTS)))

        # Customize values based on player level
        weekly_quests = []
        for quest_template in selected_quests:
            # Generate appropriate value based on level
            level_factor = min(1.0, player.class_level / 50)  # Cap at level 50
            value_range = quest_template["max_value"] - quest_template["min_value"]
            quest_value = quest_template["min_value"] + int(value_range * level_factor)

            # Calculate rewards
            rewards = {}
            for reward_type, reward_calc in quest_template["reward"].items():
                rewards[reward_type] = reward_calc(quest_value)

            # Create the quest
            quest = {
                "id": quest_template["id"],
                "name": quest_template["name"],
                "description": quest_template["description"].format(value=quest_value),
                "type": quest_template["type"],
                "value": quest_value,
                "progress": 0,
                "completed": False,
                "reward": rewards
            }

            weekly_quests.append(quest)

        return weekly_quests

    def get_long_term_quests(self, player: PlayerData) -> List[Dict[str, Any]]:
        """Get player's long-term quests"""
        # Initialize player quest data if needed
        if not hasattr(player, "long_term_quests"):
            # Generate all long-term quests
            player.long_term_quests = self.generate_long_term_quests()
            self.data_manager.save_data()

        return player.long_term_quests

    def generate_long_term_quests(self) -> List[Dict[str, Any]]:
        """Generate all long-term quests"""
        long_term_quests = []

        for quest_template in LONG_TERM_QUESTS:
            # Create the quest
            quest = {
                "id": quest_template["id"],
                "name": quest_template["name"],
                "description": quest_template["description"],
                "type": quest_template["type"],
                "value": quest_template["value"],
                "progress": 0,
                "completed": False,
                "reward": quest_template["reward"]
            }

            long_term_quests.append(quest)

        return long_term_quests

    def update_quest_progress(self, player: PlayerData, quest_type: str, amount: int = 1) -> List[Dict[str, Any]]:
        """Update progress for all quests of a specific type and return completed quests"""
        completed_quests = []

        # Check daily quests
        daily_quests = self.get_daily_quests(player)
        for quest in daily_quests:
            if quest["type"] == quest_type and not quest["completed"]:
                quest["progress"] += amount
                if quest["progress"] >= quest["value"]:
                    quest["completed"] = True
                    completed_quests.append(quest)

        # Check weekly quests
        weekly_quests = self.get_weekly_quests(player)
        for quest in weekly_quests:
            if quest["type"] == quest_type and not quest["completed"]:
                quest["progress"] += amount
                if quest["progress"] >= quest["value"]:
                    quest["completed"] = True
                    completed_quests.append(quest)

        # Check long-term quests
        long_term_quests = self.get_long_term_quests(player)
        for quest in long_term_quests:
            if quest["type"] == quest_type and not quest["completed"]:
                quest["progress"] += amount
                if quest["progress"] >= quest["value"]:
                    quest["completed"] = True
                    completed_quests.append(quest)

        # Award rewards for completed quests
        for quest in completed_quests:
            self.award_quest_rewards(player, quest)

        # Update quest completion count for achievements
        if not hasattr(player, "quests_completed"):
            player.quests_completed = 0
        player.quests_completed += len(completed_quests)

        # Save data
        self.data_manager.save_data()

        return completed_quests

    def create_quest_completion_message(self, quest: Dict[str, Any]) -> str:
        """Create a formatted message for quest completion"""
        quest_type_emoji = {
            "daily_wins": "⚔️",
            "weekly_wins": "🏆", 
            "daily_training": "🏋️",
            "weekly_training": "💪",
            "daily_dungeons": "🏴‍☠️",
            "weekly_dungeons": "🗡️",
            "daily_gold": "💰",
            "daily_items": "🎁",
            "weekly_bosses": "👹",
            "weekly_pvp": "⚔️",
            "weekly_guild_contribution": "🏰",
            "total_wins": "🥇",
            "total_training": "🎯",
            "total_dungeons": "🗡️"
        }
        
        emoji = quest_type_emoji.get(quest["type"], "✅")
        
        # Create reward text
        reward_text = ""
        if "reward" in quest:
            reward = quest["reward"]
            reward_parts = []
            
            if "exp" in reward:
                reward_parts.append(f"+{reward['exp']} EXP")
            if "gold" in reward:
                reward_parts.append(f"+{reward['gold']} Gold")
            if "special_item" in reward:
                reward_parts.append(f"Special Item: {reward['special_item']}")
                
            if reward_parts:
                reward_text = f"\n**Rewards:** {', '.join(reward_parts)}"
        
        return f"{emoji} **Quest Complete!** {quest['name']}{reward_text}"

    def award_quest_rewards(self, player: PlayerData, quest: Dict[str, Any]):
        """Award rewards for completing a quest"""
        if "reward" not in quest:
            return

        reward = quest["reward"]

        # Award XP with event multiplier
        if "exp" in reward:
            exp_amount = reward["exp"]
            # Use the proper event-aware XP method
            player.add_exp(exp_amount, data_manager=self.data_manager)

        # Award gold with event multiplier
        if "gold" in reward:
            gold_amount = reward["gold"]

            # Apply event multipliers if any
            if "active_events" in self.data_manager.__dict__:
                for event_id, event_data in self.data_manager.active_events.items():
                    if event_data["effect"]["type"] == "gold_multiplier":
                        gold_amount = int(gold_amount * event_data["effect"]["value"])

            # Add to player's gold (the main currency)
            player.add_gold(gold_amount)

        # Award special item if any
        if "special_item" in reward:
            # Import here to avoid circular imports
            from special_items import create_special_reward_item
            from equipment import add_item_to_inventory

            # Create the special reward item
            special_item = create_special_reward_item(reward["special_item"], quest["name"])

            # Add to inventory
            if special_item:
                add_item_to_inventory(player, special_item)

    def start_special_event(self, event_id: str, duration_override: float = None) -> Dict[str, Any]:
        """Start a special server event"""
        # Find the event template
        event_template = None
        for evt in SPECIAL_EVENTS:
            if evt["id"] == event_id:
                event_template = evt
                break

        if not event_template:
            return None

        # Create the event instance
        now = datetime.datetime.now()

        # Set duration
        duration = duration_override if duration_override is not None else event_template["duration"]
        end_time = now + datetime.timedelta(days=duration)

        # Create event data
        if event_id == "special_boss":
            # Get average player level for boss scaling
            avg_level = self.get_average_player_level()
            # Expanded boss list with even more epic options
            boss_name = random.choice([
                # Original bosses
                "Abyssal Warlord", "Corrupted Dragon", "Elemental Titan", "Shadow Empress",
                # New elemental bosses
                "Inferno Overlord", "Tsunami Serpent", "Gale Ravager", "Earth Colossus", "Void Harbinger",
                "Magma Lord", "Blizzard King", "Lightning Archon", "Venomous Hydra", "Crystal Emperor",
                # New mythical creatures
                "Ancient Behemoth", "Celestial Phoenix", "Frost Wyrm", "Thundering Leviathan", "Plague Monstrosity",
                "Chimera Alpha", "Golden Sphinx", "Void Kraken", "Verdant Manticore", "Cerberus the Devourer",
                # New unique bosses
                "Chronos the Timeless", "Nyx the Night Terror", "Gorgon Queen", "Molten Giant", "Death's Executioner",
                "Ares the Warlord", "Poseidon the Storm Bringer", "Hades the Soul Collector", "Atlas the Mountain", "Hermes the Swift Death",
                # New legendary bosses
                "The World Eater", "Nightmare King", "Star Devourer", "King of the Abyss", "Ancient God of Chaos",
                "Ragnarok Harbinger", "Oblivion Walker", "Cosmic Destroyer", "The Dark Sovereign", "The Great Devourer",
                # Celestial bosses
                "Eclipse Lord", "Solaris the Sun Tyrant", "Lunar Empress", "Astral Annihilator", "Comet Rider",
                # Ancient beings
                "First One", "Elder Entity", "The Forgotten", "The Nameless", "Ancestor of Madness",
                # Tech bosses
                "Mech Overlord", "Armageddon Engine", "Neural Network Prime", "The Eradicator", "Rogue Colossus"
            ])

            event_data = {
                "id": event_id,
                "name": event_template["name"].format(boss_name=boss_name),
                "description": event_template["description"].format(boss_name=boss_name),
                "effect": {
                    "type": "world_boss",
                    "boss_name": boss_name,
                    "boss_level": event_template["effect"]["boss_level"](avg_level)
                },
                "start_time": now.isoformat(),
                "end_time": end_time.isoformat()
            }
        else:
            event_data = {
                "id": event_id,
                "name": event_template["name"],
                "description": event_template["description"],
                "effect": event_template["effect"],
                "start_time": now.isoformat(),
                "end_time": end_time.isoformat()
            }

        # Add to active events
        self.data_manager.active_events[event_id] = event_data
        self.data_manager.save_data()

        return event_data

    def get_active_events(self) -> List[Dict[str, Any]]:
        """Get list of currently active events"""
        if not hasattr(self.data_manager, "active_events"):
            self.data_manager.active_events = {}
            return []

        # Check for expired events
        self.check_expired_events()

        # Return active events
        return list(self.data_manager.active_events.values())

    def check_expired_events(self):
        """Check and remove expired events"""
        if not hasattr(self.data_manager, "active_events"):
            self.data_manager.active_events = {}
            return

        now = datetime.datetime.now()
        expired_events = []

        for event_id, event_data in self.data_manager.active_events.items():
            end_time = datetime.datetime.fromisoformat(event_data["end_time"])
            if now > end_time:
                expired_events.append(event_id)

        # Remove expired events
        for event_id in expired_events:
            del self.data_manager.active_events[event_id]

        # Save if any were removed
        if expired_events:
            self.data_manager.save_data()

    def get_average_player_level(self) -> int:
        """Get average level of all players"""
        total_level = 0
        player_count = 0

        for player_id, player_data in self.data_manager.player_data.items():
            total_level += player_data.class_level
            player_count += 1

        if player_count == 0:
            return 10  # Default if no players

        return max(1, int(total_level / player_count))

class AchievementsView(View):
    def __init__(self, player_data: PlayerData, achievement_tracker: AchievementTracker):
        super().__init__(timeout=60)
        self.player_data = player_data
        self.achievement_tracker = achievement_tracker
        self.current_category = "all"
        self.show_progress_details = False

        # Add category selection
        self.add_category_select()
        self.add_progress_toggle_button()

    def add_category_select(self):
        """Add dropdown for achievement category filtering"""
        categories = [
            discord.SelectOption(label="All Achievements", value="all", emoji="🏆"),
            discord.SelectOption(label="Leveling", value="leveling", emoji="📊"),
            discord.SelectOption(label="Combat", value="combat", emoji="⚔️"),
            discord.SelectOption(label="Exploration", value="exploration", emoji="🔍"),
            discord.SelectOption(label="Wealth", value="wealth", emoji="💰"),
            discord.SelectOption(label="Collection", value="collection", emoji="🎒"),
            discord.SelectOption(label="Training", value="training", emoji="🏋️"),
            discord.SelectOption(label="Guild", value="guild", emoji="🏰"),
            discord.SelectOption(label="Special", value="special", emoji="✨")
        ]

        category_select = Select(
            placeholder="Filter by category",
            options=categories,
            min_values=1,
            max_values=1
        )
        category_select.callback = self.category_callback
        self.add_item(category_select)

    def add_progress_toggle_button(self):
        """Add button to toggle detailed progress view"""
        toggle_button = Button(
            label="Show Progress Details" if not self.show_progress_details else "Hide Progress Details",
            style=discord.ButtonStyle.secondary,
            emoji="📊"
        )
        toggle_button.callback = self.progress_toggle_callback
        self.add_item(toggle_button)

    async def progress_toggle_callback(self, interaction: discord.Interaction):
        """Handle progress toggle button"""
        self.show_progress_details = not self.show_progress_details
        
        # Update button label
        for item in self.children:
            if isinstance(item, Button) and item.emoji and item.emoji.name == "📊":
                item.label = "Show Progress Details" if not self.show_progress_details else "Hide Progress Details"
                break
        
        # Create updated embed
        embed = self.create_achievements_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    async def category_callback(self, interaction: discord.Interaction):
        """Handle category selection"""
        values = interaction.data.get("values", [])
        if values:
            self.current_category = values[0]
        else:
            # Default to "All" if no selection was made
            self.current_category = "All"

        # Create updated embed
        embed = self.create_achievements_embed()

        await interaction.response.edit_message(embed=embed, view=self)

    def create_achievements_embed(self) -> discord.Embed:
        """Create the achievements embed"""
        # Get player's achievements
        completed_achievements = self.achievement_tracker.get_player_achievements(self.player_data)
        available_achievements = self.achievement_tracker.get_player_available_achievements(self.player_data)

        # Get total achievement points
        total_points = self.achievement_tracker.get_player_achievement_points(self.player_data)

        # Create embed
        embed = discord.Embed(
            title=f"Achievements",
            description=f"Total Achievement Points: **{total_points}**\n"
                       f"Achievements Earned: **{len(completed_achievements)}/{len(ACHIEVEMENTS)}**",
            color=discord.Color.gold()
        )

        # Filter by category if not "all"
        if self.current_category != "all":
            completed_achievements = [a for a in completed_achievements if a["category"] == self.current_category]
            available_achievements = [a for a in available_achievements if a["category"] == self.current_category]

        # Add completed achievements
        if completed_achievements:
            completed_text = ""
            for achievement in completed_achievements[:10]:  # Limit to first 10
                badge = achievement.get("badge", "🏆")
                points = achievement.get("points", 0)
                completed_text += f"{badge} **{achievement['name']}** ({points} pts)\n"
                completed_text += f"*{achievement['description']}*\n\n"

            if len(completed_achievements) > 10:
                completed_text += f"*And {len(completed_achievements) - 10} more...*"

            embed.add_field(
                name=f"✅ Completed Achievements ({len(completed_achievements)})",
                value=completed_text or "None",
                inline=False
            )

        # Add available achievements with progress tracking
        if available_achievements:
            available_text = ""
            for achievement in available_achievements[:5]:  # Limit to first 5
                badge = achievement.get("badge", "🏆")
                points = achievement.get("points", 0)
                
                # Get progress for this achievement
                progress = self.achievement_tracker.get_achievement_progress(self.player_data, achievement)
                
                available_text += f"{badge} **{achievement['name']}** ({points} pts)\n"
                available_text += f"*{achievement['description']}*\n"
                
                # Add progress bar and current/required values
                available_text += f"Progress: {progress['progress_bar']} {progress['current']}/{progress['required']} ({progress['percentage']:.0f}%)\n\n"

            if len(available_achievements) > 5:
                available_text += f"*And {len(available_achievements) - 5} more...*"

            embed.add_field(
                name=f"📋 Available Achievements ({len(available_achievements)})",
                value=available_text or "None",
                inline=False
            )

        # Add achievement badges to user profile
        if completed_achievements:
            badges = []
            for category in ["leveling", "combat", "exploration", "collection", "wealth", "guild", "special"]:
                # Get highest badge in each category
                category_achievements = [a for a in completed_achievements if a["category"] == category]
                if category_achievements:
                    # Sort by points (highest first)
                    category_achievements.sort(key=lambda a: a.get("points", 0), reverse=True)
                    badges.append(category_achievements[0].get("badge", ""))

            if badges:
                embed.add_field(
                    name="Your Achievement Badges",
                    value=" ".join(badges[:5]),  # Limit to 5 badges
                    inline=False
                )

        return embed

class QuestsView(View):
    def __init__(self, player_data: PlayerData, quest_manager: QuestManager):
        super().__init__(timeout=60)
        self.player_data = player_data
        self.quest_manager = quest_manager
        self.current_tab = "daily"

        # Add tab selection buttons
        self.add_tab_buttons()

    def add_tab_buttons(self):
        """Add buttons for switching between quest types"""
        # Daily quests button
        daily_btn = Button(
            label="Daily Quests",
            style=discord.ButtonStyle.primary if self.current_tab == "daily" else discord.ButtonStyle.secondary,
            emoji="📅",
            custom_id="daily_tab"
        )
        daily_btn.callback = self.daily_tab_callback
        self.add_item(daily_btn)

        # Weekly quests button
        weekly_btn = Button(
            label="Weekly Quests",
            style=discord.ButtonStyle.primary if self.current_tab == "weekly" else discord.ButtonStyle.secondary,
            emoji="🗓️",
            custom_id="weekly_tab"
        )
        weekly_btn.callback = self.weekly_tab_callback
        self.add_item(weekly_btn)

        # Long-term quests button
        longterm_btn = Button(
            label="Long-term Quests",
            style=discord.ButtonStyle.primary if self.current_tab == "longterm" else discord.ButtonStyle.secondary,
            emoji="📜",
            custom_id="longterm_tab"
        )
        longterm_btn.callback = self.longterm_tab_callback
        self.add_item(longterm_btn)

    async def daily_tab_callback(self, interaction: discord.Interaction):
        """Show daily quests"""
        self.current_tab = "daily"
        self.clear_items()  # Clear existing buttons
        self.add_tab_buttons()  # Re-add buttons with updated states

        embed = self.create_quests_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    async def weekly_tab_callback(self, interaction: discord.Interaction):
        """Show weekly quests"""
        self.current_tab = "weekly"
        self.clear_items()  # Clear existing buttons
        self.add_tab_buttons()  # Re-add buttons with updated states

        embed = self.create_quests_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    async def longterm_tab_callback(self, interaction: discord.Interaction):
        """Show long-term quests"""
        self.current_tab = "longterm"
        self.clear_items()  # Clear existing buttons
        self.add_tab_buttons()  # Re-add buttons with updated states

        embed = self.create_quests_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    def create_quests_embed(self) -> discord.Embed:
        """Create the quests embed based on current tab"""
        if self.current_tab == "daily":
            # Get daily quests
            quests = self.quest_manager.get_daily_quests(self.player_data)

            embed = discord.Embed(
                title=f"Daily Quests",
                description="Complete these quests before the daily reset!",
                color=discord.Color.green()
            )

            # Add a reset time note
            today = datetime.datetime.now()
            tomorrow = today + datetime.timedelta(days=1)
            reset_time = datetime.datetime(tomorrow.year, tomorrow.month, tomorrow.day, 0, 0, 0)
            time_until_reset = reset_time - today
            hours, remainder = divmod(time_until_reset.seconds, 3600)
            minutes, _ = divmod(remainder, 60)

            embed.set_footer(text=f"Resets in {hours} hours and {minutes} minutes")

        elif self.current_tab == "weekly":
            # Get weekly quests
            quests = self.quest_manager.get_weekly_quests(self.player_data)

            embed = discord.Embed(
                title=f"Weekly Quests",
                description="Complete these quests before the weekly reset!",
                color=discord.Color.blue()
            )

            # Add a reset time note
            today = datetime.datetime.now()
            days_until_monday = (7 - today.weekday()) % 7
            next_monday = today + datetime.timedelta(days=days_until_monday)
            reset_time = datetime.datetime(next_monday.year, next_monday.month, next_monday.day, 0, 0, 0)
            time_until_reset = reset_time - today

            embed.set_footer(text=f"Resets in {time_until_reset.days} days and {time_until_reset.seconds // 3600} hours")

        else:  # long-term
            # Get long-term quests
            quests = self.quest_manager.get_long_term_quests(self.player_data)

            embed = discord.Embed(
                title=f"Long-term Quests",
                description="These challenging quests never expire!",
                color=discord.Color.purple()
            )

            embed.set_footer(text="Complete these quests for special rewards")

        # Add active quests
        active_quests = [q for q in quests if not q["completed"]]
        if active_quests:
            active_text = ""
            for quest in active_quests:
                progress = min(quest["progress"], quest["value"])
                progress_bar = self.create_progress_bar(progress, quest["value"])
                active_text += f"**{quest['name']}**\n"
                active_text += f"{quest['description']}\n"
                active_text += f"{progress_bar} ({progress}/{quest['value']})\n"

                # Add rewards
                rewards_text = []
                for reward_type, amount in quest["reward"].items():
                    if reward_type == "exp":
                        rewards_text.append(f"{amount} EXP")
                    elif reward_type == "gold":
                        rewards_text.append(f"{amount} Gold")
                    elif reward_type == "special_item":
                        rewards_text.append(f"Special Item: {amount}")

                active_text += f"**Rewards:** {', '.join(rewards_text)}\n\n"

            embed.add_field(
                name="📋 Active Quests",
                value=active_text or "No active quests",
                inline=False
            )
        else:
            embed.add_field(
                name="📋 Active Quests",
                value="No active quests",
                inline=False
            )

        # Add completed quests
        completed_quests = [q for q in quests if q["completed"]]
        if completed_quests:
            completed_text = ""
            for quest in completed_quests[:3]:  # Limit to 3 most recent
                completed_text += f"**{quest['name']}** ✅\n"
                completed_text += f"{quest['description']}\n\n"

            if len(completed_quests) > 3:
                completed_text += f"*And {len(completed_quests) - 3} more completed...*"

            embed.add_field(
                name="✅ Completed Quests",
                value=completed_text or "No completed quests",
                inline=False
            )

        # Add active events if any
        active_events = self.quest_manager.get_active_events()
        if active_events:
            events_text = ""
            for event in active_events:
                # Calculate time remaining
                end_time = datetime.datetime.fromisoformat(event["end_time"])
                now = datetime.datetime.now()
                time_left = end_time - now

                if time_left.days > 0:
                    time_str = f"{time_left.days}d {time_left.seconds // 3600}h remaining"
                else:
                    hours, remainder = divmod(time_left.seconds, 3600)
                    minutes, _ = divmod(remainder, 60)
                    time_str = f"{hours}h {minutes}m remaining"

                events_text += f"**{event['name']}**\n"
                events_text += f"{event['description']}\n"
                events_text += f"*{time_str}*\n\n"

            embed.add_field(
                name="🎉 Active Events",
                value=events_text,
                inline=False
            )

        return embed

    def create_progress_bar(self, current: int, maximum: int, length: int = 10) -> str:
        """Create a text progress bar"""
        if maximum <= 0:
            return "Error: Invalid maximum value"

        progress = min(1.0, current / maximum)
        filled_length = int(length * progress)

        bar = "█" * filled_length + "░" * (length - filled_length)

        return f"[{bar}]"

async def achievements_command(ctx, data_manager: DataManager):
    """View your achievements and badges"""
    player_data = data_manager.get_player(ctx.author.id)

    # Initialize achievement tracker
    achievement_tracker = AchievementTracker(data_manager)

    # Check for new achievements
    new_achievements = achievement_tracker.check_achievements(player_data)

    # Create view
    achievements_view = AchievementsView(player_data, achievement_tracker)
    achievements_embed = achievements_view.create_achievements_embed()

    # Send the embed
    await ctx.send(embed=achievements_embed, view=achievements_view)

    # If any new achievements were earned, announce them
    for achievement in new_achievements:
        new_achievement_embed = discord.Embed(
            title=f"🎉 New Achievement Unlocked!",
            description=f"**{achievement['name']}**\n{achievement['description']}",
            color=discord.Color.gold()
        )

        # Add rewards
        rewards_text = ""
        for reward_type, amount in achievement["reward"].items():
            if reward_type == "exp":
                rewards_text += f"EXP: +{amount}\n"
            elif reward_type == "gold":
                rewards_text += f"Gold: +{amount}\n"
            elif reward_type == "special_item":
                rewards_text += f"Special Item: {amount}\n"
            elif reward_type == "server_role":
                rewards_text += f"Server Role: {amount}\n"

        # Add achievement points to rewards
        if "points" in achievement:
            rewards_text += f"Achievement Points: +{achievement['points']}\n"

        if rewards_text:
            new_achievement_embed.add_field(
                name="Rewards",
                value=rewards_text,
                inline=False
            )

        # Add badge
        if "badge" in achievement:
            new_achievement_embed.add_field(
                name="Badge",
                value=achievement["badge"],
                inline=False
            )

        await ctx.send(embed=new_achievement_embed)

async def quests_command(ctx, data_manager: DataManager):
    """View your active quests"""
    player_data = data_manager.get_player(ctx.author.id)

    # Initialize quest manager
    quest_manager = QuestManager(data_manager)

    # Create view
    quests_view = QuestsView(player_data, quest_manager)
    quests_embed = quests_view.create_quests_embed()

    # Send the embed
    await ctx.send(embed=quests_embed, view=quests_view)

async def event_command(ctx, data_manager: DataManager, action: str = None, event_id: str = None, duration: float = None):
    """Admin command to manage server events"""
    # Check if user has admin permissions
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("You don't have permission to use this command.")
        return

    # Initialize quest manager
    quest_manager = QuestManager(data_manager)

    if action == "start":
        if not event_id:
            # List available events
            events_list = "\n".join([f"• `{event['id']}`: {event['name']}" for event in SPECIAL_EVENTS])

            await ctx.send(f"Available events to start:\n{events_list}\n\nUse `!event start <event_id> [duration]` to start an event.")
            return

        # Try to start the event
        event_data = quest_manager.start_special_event(event_id, duration)

        if event_data:
            # Calculate end time
            end_time = datetime.datetime.fromisoformat(event_data["end_time"])
            duration_str = f"{(end_time - datetime.datetime.now()).days} days and {((end_time - datetime.datetime.now()).seconds // 3600)} hours"

            event_embed = discord.Embed(
                title=f"🎉 Event Started: {event_data['name']}",
                description=event_data["description"],
                color=discord.Color.gold()
            )

            event_embed.add_field(
                name="Duration",
                value=f"Event will last for {duration_str}",
                inline=False
            )

            # Add effect details
            effect_text = ""
            if event_data["effect"]["type"] == "exp_multiplier":
                effect_text = f"XP gain is multiplied by {event_data['effect']['value']}x!"
            elif event_data["effect"]["type"] == "gold_multiplier":
                effect_text = f"Gold gain is multiplied by {event_data['effect']['value']}x!"
            elif event_data["effect"]["type"] == "item_rarity_boost":
                effect_text = f"Chance of rare items is multiplied by {event_data['effect']['value']}x!"
            elif event_data["effect"]["type"] == "training_multiplier":
                effect_text = f"Training stat gains are multiplied by {event_data['effect']['value']}x!"
            elif event_data["effect"]["type"] == "world_boss":
                effect_text = f"A world boss '{event_data['effect']['boss_name']}' (Level {event_data['effect']['boss_level']}) has appeared!"

            if effect_text:
                event_embed.add_field(
                    name="Effect",
                    value=effect_text,
                    inline=False
                )

            await ctx.send(embed=event_embed)
        else:
            await ctx.send(f"Error: Unknown event ID '{event_id}'")

    elif action == "list":
        # List active events
        active_events = quest_manager.get_active_events()

        if not active_events:
            await ctx.send("There are no active events.")
            return

        events_embed = discord.Embed(
            title="Active Server Events",
            description="Currently running special events",
            color=discord.Color.gold()
        )

        for event in active_events:
            # Calculate time remaining
            end_time = datetime.datetime.fromisoformat(event["end_time"])
            now = datetime.datetime.now()
            time_left = end_time - now

            if time_left.days > 0:
                time_str = f"{time_left.days}d {time_left.seconds // 3600}h remaining"
            else:
                hours, remainder = divmod(time_left.seconds, 3600)
                minutes, _ = divmod(remainder, 60)
                time_str = f"{hours}h {minutes}m remaining"

            events_embed.add_field(
                name=event["name"],
                value=f"{event['description']}\n*{time_str}*",
                inline=False
            )

        await ctx.send(embed=events_embed)

    elif action == "end":
        if not event_id:
            await ctx.send("Please specify an event ID to end.")
            return

        # Check if event exists
        if event_id in data_manager.active_events:
            # Remove the event
            del data_manager.active_events[event_id]
            data_manager.save_data()

            await ctx.send(f"Event '{event_id}' has been ended.")
        else:
            await ctx.send(f"Error: No active event with ID '{event_id}'")

    else:
        # Show help
        help_embed = discord.Embed(
            title="Event Command Help",
            description="Commands for managing server events",
            color=discord.Color.blue()
        )

        help_embed.add_field(
            name="Available Commands",
            value="• `!event start <event_id> [duration]` - Start a new event\n"
                  "• `!event list` - List all active events\n"
                  "• `!event end <event_id>` - End an active event",
            inline=False
        )

        # Create event buttons view
        class EventCommandView(discord.ui.View):
            def __init__(self, quest_manager, data_manager):
                super().__init__(timeout=60)
                self.quest_manager = quest_manager
                self.data_manager = data_manager

            @discord.ui.button(label="List Available Events", style=discord.ButtonStyle.primary)
            async def list_events_button(self, interaction: discord.Interaction, button: discord.ui.Button):
                events_list = "\n".join([f"• `{event['id']}`: {event['name']}" for event in SPECIAL_EVENTS])
                await interaction.response.send_message(f"Available events to start:\n{events_list}", ephemeral=True)

            @discord.ui.button(label="Start 1-Week Event", style=discord.ButtonStyle.success)
            async def start_event_button(self, interaction: discord.Interaction, button: discord.ui.Button):
                # Create a select menu to choose an event with validation
                options = []
                seen_values = set()
                seen_labels = set()
                
                for event in SPECIAL_EVENTS:
                    # Skip if we've already seen this value or label
                    if event["id"] in seen_values or event["name"] in seen_labels:
                        continue
                    
                    # Create option with truncated description if needed
                    description = f"Start a 1-week {event['id']} event"
                    if len(description) > 100:
                        description = description[:97] + "..."
                    
                    options.append(discord.SelectOption(
                        label=event["name"][:100],  # Ensure label fits Discord limits
                        value=event["id"][:100],    # Ensure value fits Discord limits
                        description=description
                    ))
                    
                    seen_values.add(event["id"])
                    seen_labels.add(event["name"])

                select = discord.ui.Select(placeholder="Choose an event to start", options=options)

                event_view = discord.ui.View(timeout=30)
                event_view.add_item(select)

                async def select_callback(select_interaction):
                    event_id = select.values[0]
                    # Start event for 7 days (1 week)
                    event_data = self.quest_manager.start_special_event(event_id, 7.0)

                    if event_data:
                        # Calculate end time
                        end_time = datetime.datetime.fromisoformat(event_data["end_time"])
                        duration_str = f"{(end_time - datetime.datetime.now()).days} days and {((end_time - datetime.datetime.now()).seconds // 3600)} hours"

                        event_embed = discord.Embed(
                            title=f"🎉 Event Started: {event_data['name']}",
                            description=event_data["description"],
                            color=discord.Color.gold()
                        )

                        event_embed.add_field(
                            name="Duration",
                            value=f"Event will last for {duration_str}",
                            inline=False
                        )

                        # Add effect details
                        effect_text = ""
                        if event_data["effect"]["type"] == "exp_multiplier":
                            effect_text = f"XP gain is multiplied by {event_data['effect']['value']}x!"
                        elif event_data["effect"]["type"] == "gold_multiplier":
                            effect_text = f"Gold gain is multiplied by {event_data['effect']['value']}x!"
                        elif event_data["effect"]["type"] == "item_rarity_boost":
                            effect_text = f"Chance of rare items is multiplied by {event_data['effect']['value']}x!"
                        elif event_data["effect"]["type"] == "training_multiplier":
                            effect_text = f"Training stat gains are multiplied by {event_data['effect']['value']}x!"
                        elif event_data["effect"]["type"] == "world_boss":
                            effect_text = f"A world boss '{event_data['effect']['boss_name']}' (Level {event_data['effect']['boss_level']}) has appeared!"

                        if effect_text:
                            event_embed.add_field(
                                name="Effect",
                                value=effect_text,
                                inline=False
                            )

                        await select_interaction.response.send_message(embed=event_embed)
                    else:
                        await select_interaction.response.send_message(f"Error: Unknown event ID '{event_id}'", ephemeral=True)

                select.callback = select_callback
                await interaction.response.send_message("Select an event to start for 1 week:", view=event_view, ephemeral=True)

            @discord.ui.button(label="End Active Event", style=discord.ButtonStyle.danger) 
            async def end_event_button(self, interaction: discord.Interaction, button: discord.ui.Button):
                # Get active events
                active_events = self.quest_manager.get_active_events()

                if not active_events:
                    await interaction.response.send_message("There are no active events to end.", ephemeral=True)
                    return

                # Create select menu with active events
                options = [discord.SelectOption(label=event["name"], value=event["id"], 
                          description=f"End this event") for event in active_events]

                select = discord.ui.Select(placeholder="Choose an event to end", options=options)
                end_view = discord.ui.View(timeout=30)
                end_view.add_item(select)

                async def end_callback(end_interaction):
                    event_id = select.values[0]

                    # End the selected event
                    if event_id in self.data_manager.active_events:
                        del self.data_manager.active_events[event_id]
                        self.data_manager.save_data()
                        await end_interaction.response.send_message(f"Event '{event_id}' has been ended.")
                    else:
                        await end_interaction.response.send_message(f"Error: No active event with ID '{event_id}'", ephemeral=True)

                select.callback = end_callback
                await interaction.response.send_message("Select an event to end:", view=end_view, ephemeral=True)

        # Send help embed with buttons
        await ctx.send(embed=help_embed, view=EventCommandView(quest_manager, data_manager))

# Command aliases
async def achieve_command(ctx, data_manager: DataManager):
    """Alias for achievements command"""
    await achievements_command(ctx, data_manager)

async def ach_command(ctx, data_manager: DataManager):
    """Shorter alias for achievements command"""
    await achievements_command(ctx, data_manager)

async def q_command(ctx, data_manager: DataManager):
    """Alias for quests command"""
    await quests_command(ctx, data_manager)