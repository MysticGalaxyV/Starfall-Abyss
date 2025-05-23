import discord
import random
from typing import Dict, List, Any

# Game constants
STARTER_CLASSES = {
    "Spirit Striker": {
        "role": "Balanced",
        "stats": {
            "power": 15,
            "defense": 10,
            "speed": 8,
            "hp": 100
        },
        "abilities": {
            "active": "Cursed Combo",
            "passive": "Power Scaling"
        }
    },
    "Domain Tactician": {
        "role": "Tank",
        "stats": {
            "power": 10,
            "defense": 20,
            "speed": 6,
            "hp": 120
        },
        "abilities": {
            "active": "Barrier Pulse",
            "passive": "Damage Resistance"
        }
    },
    "Flash Rogue": {
        "role": "Assassin",
        "stats": {
            "power": 18,
            "defense": 6,
            "speed": 15,
            "hp": 90
        },
        "abilities": {
            "active": "Shadowstep",
            "passive": "First Strike"
        }
    }
}

# Advanced classes unlockable through progression
ADVANCED_CLASSES = {
    "Archmage": {
        "role": "Mage+",
        "stats": {
            "power": 30,
            "defense": 12,
            "speed": 15,
            "hp": 110
        },
        "abilities": {
            "active": "Arcane Mastery",
            "passive": "Mana Efficiency"
        },
        "requirements": {
            "level": 50
        }
    },
    "Cursed Specialist": {
        "role": "Balanced+",
        "stats": {
            "power": 20,
            "defense": 15,
            "speed": 12,
            "hp": 120
        },
        "abilities": {
            "active": "Reversed Curse",
            "passive": "Cursed Adaptation"
        },
        "requirements": {
            "base_class": "Spirit Striker",
            "level": 10
        }
    },
    "Domain Master": {
        "role": "Tank+",
        "stats": {
            "power": 15,
            "defense": 25,
            "speed": 8,
            "hp": 150
        },
        "abilities": {
            "active": "Domain Expansion",
            "passive": "Perfect Territory"
        },
        "requirements": {
            "base_class": "Domain Tactician",
            "level": 10
        }
    },
    "Shadow Assassin": {
        "role": "Assassin+",
        "stats": {
            "power": 22,
            "defense": 10,
            "speed": 20,
            "hp": 110
        },
        "abilities": {
            "active": "Phantom Rush",
            "passive": "Critical Strikes"
        },
        "requirements": {
            "base_class": "Flash Rogue",
            "level": 10
        }
    },
    "Limitless Sorcerer": {
        "role": "Special",
        "stats": {
            "power": 25,
            "defense": 18,
            "speed": 18,
            "hp": 130
        },
        "abilities": {
            "active": "Infinity",
            "passive": "Six-Eyes"
        },
        "requirements": {
            "level": 20,
            "dungeon_clears": 5
        }
    }
}

# Merge starter and advanced classes for easy access
GAME_CLASSES = {**STARTER_CLASSES, **ADVANCED_CLASSES}

# Game skills and abilities
GAME_SKILLS = {
    "basic_attack": {
        "name": "Basic Attack",
        "description": "A simple attack with minimal energy cost",
        "damage_multiplier": 1.0,
        "energy_cost": 5,
        "level_req": 1,
        "cooldown": 0,
        "class": None,
        "universal": True
    },
    "power_strike": {
        "name": "Power Strike",
        "description": "A powerful strike with increased damage",
        "damage_multiplier": 1.5,
        "energy_cost": 10,
        "level_req": 2,
        "cooldown": 0,
        "class": "Spirit Striker"
    },
    "barrier_pulse": {
        "name": "Barrier Pulse",
        "description": "Create a defensive barrier that reduces incoming damage",
        "damage_multiplier": 0.8,
        "energy_cost": 10,
        "level_req": 2,
        "cooldown": 2,
        "effect": "defense_boost",
        "class": "Domain Tactician"
    },
    "shadowstep": {
        "name": "Shadowstep",
        "description": "Quick strike with a chance to dodge the next attack",
        "damage_multiplier": 1.2,
        "energy_cost": 10,
        "level_req": 2,
        "cooldown": 1,
        "effect": "dodge_next",
        "class": "Flash Rogue"
    },
    "cursed_combo": {
        "name": "Cursed Combo",
        "description": "A series of cursed energy infused strikes",
        "damage_multiplier": 1.8,
        "energy_cost": 15,
        "level_req": 5,
        "cooldown": 1,
        "class": "Spirit Striker"
    },
    "domain_expansion": {
        "name": "Domain Expansion",
        "description": "Expand your domain to gain significant defensive power",
        "damage_multiplier": 1.0,
        "energy_cost": 20,
        "level_req": 10,
        "cooldown": 3,
        "effect": "major_defense_boost",
        "class": "Domain Master"
    },
    "phantom_rush": {
        "name": "Phantom Rush",
        "description": "A lightning-fast series of attacks that's hard to defend against",
        "damage_multiplier": 2.0,
        "energy_cost": 18,
        "level_req": 10,
        "cooldown": 2,
        "class": "Shadow Assassin"
    },
    "infinity": {
        "name": "Infinity",
        "description": "Tap into limitless cursed energy for a devastating attack",
        "damage_multiplier": 2.5,
        "energy_cost": 25,
        "level_req": 20,
        "cooldown": 4,
        "class": "Limitless Sorcerer"
    },
    "reversed_curse": {
        "name": "Reversed Curse",
        "description": "Turn your opponent's energy against them",
        "damage_multiplier": 1.7,
        "energy_cost": 15,
        "level_req": 10,
        "effect": "energy_drain",
        "cooldown": 2,
        "class": "Cursed Specialist"
    },
    "arcane_mastery": {
        "name": "Arcane Mastery",
        "description": "Channel arcane energy for a powerful magical attack",
        "damage_multiplier": 2.2,
        "energy_cost": 20,
        "level_req": 15,
        "cooldown": 2,
        "class": "Archmage"
    },
    "heavenly_restriction": {
        "name": "Heavenly Restriction",
        "description": "Unlock your full physical potential with this ultimate technique",
        "damage_multiplier": 3.0,
        "energy_cost": 30,
        "level_req": 25,
        "cooldown": 5,
        "class": "Spirit Striker"
    },
    "black_flash": {
        "name": "Black Flash",
        "description": "The pinnacle of cursed energy manipulation",
        "damage_multiplier": 3.5,
        "energy_cost": 35,
        "level_req": 30,
        "cooldown": 6,
        "class": None,
        "universal": True
    },
    "hollow_purple": {
        "name": "Hollow Purple",
        "description": "The ultimate technique combining opposing forces",
        "damage_multiplier": 4.0,
        "energy_cost": 40,
        "level_req": 40,
        "cooldown": 8,
        "class": "Limitless Sorcerer"
    },
    "malevolent_shrine": {
        "name": "Malevolent Shrine",
        "description": "The most powerful domain expansion technique",
        "damage_multiplier": 5.0,
        "energy_cost": 50,
        "level_req": 50,
        "cooldown": 10,
        "class": "Domain Master"
    },
    "final_technique": {
        "name": "Final Technique",
        "description": "The ultimate attack that consumes all your energy",
        "damage_multiplier": 10.0,
        "energy_cost": 100,
        "level_req": 100,
        "cooldown": 20,
        "class": None,
        "universal": True
    }
}

# Enemy encounter pools for different zones
ENEMY_POOLS = {
    "Forest": [
        {"name": "Cursed Wolf", "min_level": 1, "max_level": 3},
        {"name": "Forest Specter", "min_level": 2, "max_level": 4},
        {"name": "Ancient Treefolk", "min_level": 3, "max_level": 5}
    ],
    "Cave": [
        {"name": "Cave Crawler", "min_level": 3, "max_level": 5},
        {"name": "Armored Golem", "min_level": 4, "max_level": 6},
        {"name": "Crystal Spider", "min_level": 5, "max_level": 7}
    ],
    "Shrine": [
        {"name": "Shrine Guardian", "min_level": 5, "max_level": 7},
        {"name": "Cursed Monk", "min_level": 6, "max_level": 8},
        {"name": "Vengeful Spirit", "min_level": 7, "max_level": 9}
    ],
    "Abyss": [
        {"name": "Deep One", "min_level": 8, "max_level": 10},
        {"name": "Abyssal Hunter", "min_level": 9, "max_level": 11},
        {"name": "Giant Squid", "min_level": 10, "max_level": 12}
    ],
    "Citadel": [
        {"name": "Flame Knight", "min_level": 11, "max_level": 13},
        {"name": "Lava Golem", "min_level": 12, "max_level": 14},
        {"name": "Fire Drake", "min_level": 13, "max_level": 15}
    ]
}

# Boss encounters
BOSSES = {
    "Forest": {"name": "Elder Treant", "level_offset": 3},
    "Cave": {"name": "Cave Warden", "level_offset": 3},
    "Shrine": {"name": "Shrine Deity", "level_offset": 3},
    "Abyss": {"name": "Kraken Lord", "level_offset": 4},
    "Citadel": {"name": "Infernal Overlord", "level_offset": 5}
}

# Experience calculations
def calculate_exp_for_level(level: int) -> int:
    """Calculate experience required for the next level"""
    return int(100 * (level ** 1.5))

def calculate_battle_exp(enemy_level: int, player_level: int) -> int:
    """Calculate experience reward from a battle"""
    base_exp = 15 + (enemy_level * 5)

    # Adjust based on level difference
    level_diff = enemy_level - player_level
    if level_diff > 0:
        # More exp for defeating higher level enemies
        exp_modifier = 1.0 + (level_diff * 0.2)
    elif level_diff < 0:
        # Less exp for defeating lower level enemies
        exp_modifier = max(0.3, 1.0 + (level_diff * 0.1))
    else:
        # Same level
        exp_modifier = 1.0

    return int(base_exp * exp_modifier)

def format_time_until(time_seconds: int) -> str:
    """Format seconds into a human-readable time string"""
    if time_seconds < 60:
        return f"{time_seconds} seconds"
    elif time_seconds < 3600:
        minutes = time_seconds // 60
        seconds = time_seconds % 60
        return f"{minutes}m {seconds}s"
    else:
        hours = time_seconds // 3600
        minutes = (time_seconds % 3600) // 60
        return f"{hours}h {minutes}m"

def get_rarity_color(rarity: str) -> discord.Color:
    """Get Discord color for item rarity"""
    rarity_colors = {
        "common": discord.Color.light_grey(),
        "uncommon": discord.Color.green(),
        "rare": discord.Color.blue(),
        "epic": discord.Color.purple(),
        "legendary": discord.Color.gold()
    }
    return rarity_colors.get(rarity.lower(), discord.Color.default())

def get_random_enemy(zone: str, player_level: int) -> Dict[str, Any]:
    """Get a random enemy appropriate for the player's level from a zone"""
    # Filter enemies by level
    suitable_enemies = [
        enemy for enemy in ENEMY_POOLS[zone] 
        if enemy["min_level"] <= player_level + 2 and enemy["max_level"] >= player_level - 2
    ]

    # If no suitable enemies, get closest ones
    if not suitable_enemies:
        suitable_enemies = ENEMY_POOLS[zone]

    # Select random enemy
    enemy = random.choice(suitable_enemies)

    # Determine enemy level
    min_level = max(1, player_level - 2)
    max_level = player_level + 2

    # Keep within enemy's level range
    min_level = max(min_level, enemy["min_level"])
    max_level = min(max_level, enemy["max_level"])

    level = random.randint(min_level, max_level)

    return {
        "name": enemy["name"],
        "level": level
    }

def get_zone_boss(zone: str, player_level: int) -> Dict[str, Any]:
    """Get a zone's boss with appropriate level for the player"""
    boss = BOSSES[zone]
    boss_level = player_level + boss["level_offset"]

    return {
        "name": boss["name"],
        "level": boss_level
    }

def get_appropriate_zone(player_level: int) -> str:
    """Get an appropriate zone for the player's level"""
    if player_level <= 3:
        return "Forest"
    elif player_level <= 6:
        return "Cave"
    elif player_level <= 9:
        return "Shrine"
    elif player_level <= 12:
        return "Abyss"
    else:
        return "Citadel"

# Utility function to create progress bars
def create_progress_bar(current: int, maximum: int, length: int = 10) -> str:
    """Create a text-based progress bar"""
    filled = int((current / maximum) * length)
    bar = "█" * filled + "░" * (length - filled)
    return bar

# Discord message utility functions
def create_embed(title: str, description: str, color: discord.Color = discord.Color.blue()) -> discord.Embed:
    """Create a standardized Discord embed"""
    embed = discord.Embed(
        title=title,
        description=description,
        color=color
    )
    embed.set_footer(text="Cursed RPG • Type !help for commands")
    return embed
