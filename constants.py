import random
from typing import Dict, List, Any, Optional
import discord

# Bot settings
ACTIVITY_STATUS = "!help | Jujutsu RPG"
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# Cooldowns (seconds)
BATTLE_COOLDOWN = 300  # 5 minutes
DUNGEON_COOLDOWN = 600  # 10 minutes
SKILLS_COOLDOWN = 300  # 5 minutes

# Battle constants
CRITICAL_MULTIPLIER = 1.5
ABILITY_COSTS = {
    "Cursed Combo": 20,
    "Barrier Pulse": 15,
    "Shadowstep": 25,
    "Special Attack": 15
}

# Classes
STARTER_CLASSES = {
    "Spirit Striker": {
        "role": "Balanced",
        "stats": {
            "power": 15,
            "defense": 10,
            "speed": 8,
            "hp": 100,
            "max_hp": 100
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
            "hp": 120,
            "max_hp": 120
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
            "hp": 90,
            "max_hp": 90
        },
        "abilities": {
            "active": "Shadowstep",
            "passive": "First Strike"
        }
    }
}

# Advanced classes (unlockable later)
ADVANCED_CLASSES = {
    "Cursed Swordsman": {
        "role": "DPS",
        "stats": {
            "power": 22,
            "defense": 12,
            "speed": 10,
            "hp": 110,
            "max_hp": 110
        },
        "abilities": {
            "active": "Blade Storm",
            "passive": "Critical Focus"
        },
        "requirements": {
            "level": 15,
            "class": ["Spirit Striker"]
        }
    },
    "Barrier Specialist": {
        "role": "Tank/Support",
        "stats": {
            "power": 12,
            "defense": 25,
            "speed": 8,
            "hp": 140,
            "max_hp": 140
        },
        "abilities": {
            "active": "Domain Expansion",
            "passive": "Resilience"
        },
        "requirements": {
            "level": 15,
            "class": ["Domain Tactician"]
        }
    },
    "Shadow Assassin": {
        "role": "Assassin",
        "stats": {
            "power": 20,
            "defense": 8,
            "speed": 22,
            "hp": 95,
            "max_hp": 95
        },
        "abilities": {
            "active": "Shadow Dance",
            "passive": "Evasion"
        },
        "requirements": {
            "level": 15,
            "class": ["Flash Rogue"]
        }
    },
    "Cursed Healer": {
        "role": "Support",
        "stats": {
            "power": 14,
            "defense": 15,
            "speed": 12,
            "hp": 115,
            "max_hp": 115
        },
        "abilities": {
            "active": "Reverse Technique",
            "passive": "Energy Surge"
        },
        "requirements": {
            "level": 20,
            "class": ["Domain Tactician", "Spirit Striker"]
        }
    }
}

# All classes combined
CLASSES = {**STARTER_CLASSES, **ADVANCED_CLASSES}

# Dungeons
DUNGEONS = {
    "Training Grounds": {
        "difficulty": "Easy",
        "level_req": 1,
        "floors": 3,
        "exp": 50,
        "min_rewards": 30,
        "max_rewards": 50,
        "rare_drop": 5,  # 5% chance
        "style": discord.ButtonStyle.primary
    },
    "Cursed Forest": {
        "difficulty": "Normal",
        "level_req": 5,
        "floors": 5,
        "exp": 100,
        "min_rewards": 60,
        "max_rewards": 100,
        "rare_drop": 8,  # 8% chance
        "style": discord.ButtonStyle.success
    },
    "Abandoned Temple": {
        "difficulty": "Hard",
        "level_req": 10,
        "floors": 7,
        "exp": 180,
        "min_rewards": 120,
        "max_rewards": 180,
        "rare_drop": 12,  # 12% chance
        "style": discord.ButtonStyle.danger
    },
    "Cursed Abyss": {
        "difficulty": "Very Hard",
        "level_req": 15,
        "floors": 10,
        "exp": 300,
        "min_rewards": 200,
        "max_rewards": 300,
        "rare_drop": 15,  # 15% chance
        "style": discord.ButtonStyle.danger
    },
    "Domain of Shadows": {
        "difficulty": "Extreme",
        "level_req": 20,
        "floors": 12,
        "exp": 450,
        "min_rewards": 300,
        "max_rewards": 500,
        "rare_drop": 20,  # 20% chance
        "style": discord.ButtonStyle.danger
    }
}

# Dungeon enemies
DUNGEON_ENEMIES = [
    {
        "name": "Cursed Spirit (Minor)",
        "level": 1,
        "hp": 40,
        "power": 8,
        "defense": 5
    },
    {
        "name": "Cursed Spirit (Normal)",
        "level": 3,
        "hp": 60,
        "power": 12,
        "defense": 8
    },
    {
        "name": "Cursed Spirit (Strong)",
        "level": 5,
        "hp": 80,
        "power": 15,
        "defense": 10
    },
    {
        "name": "Cursed Puppet",
        "level": 7,
        "hp": 100,
        "power": 18,
        "defense": 12
    },
    {
        "name": "Vengeful Shade",
        "level": 9,
        "hp": 120,
        "power": 20,
        "defense": 15
    },
    {
        "name": "Cursed Swordsman",
        "level": 12,
        "hp": 150,
        "power": 25,
        "defense": 18
    },
    {
        "name": "Barrier Spirit",
        "level": 15,
        "hp": 180,
        "power": 22,
        "defense": 25
    },
    {
        "name": "Shadow Assassin",
        "level": 18,
        "hp": 160,
        "power": 28,
        "defense": 15
    },
    {
        "name": "Domain Spectre",
        "level": 20,
        "hp": 200,
        "power": 30,
        "defense": 20
    },
    {
        "name": "Cursed King",
        "level": 25,
        "hp": 300,
        "power": 35,
        "defense": 25
    }
]

# Item rarity indicators
ITEM_RARITY = {
    "common": "⚪",
    "uncommon": "🟢",
    "rare": "🔵",
    "epic": "🟣",
    "legendary": "🟠",
    "mythic": "🔴"
}

# Shop items
SHOP_ITEMS = [
    # Weapons
    {
        "name": "Steel Sword",
        "description": "A basic but reliable blade.",
        "type": "equipment",
        "slot": "weapon",
        "level_req": 1,
        "rarity": "common",
        "price": 100,
        "stats_boost": {
            "power": 3
        }
    },
    {
        "name": "Heavy Mace",
        "description": "Slow but powerful crushing weapon.",
        "type": "equipment",
        "slot": "weapon",
        "level_req": 3,
        "rarity": "common",
        "price": 150,
        "stats_boost": {
            "power": 5,
            "speed": -1
        }
    },
    {
        "name": "Cursed Dagger",
        "description": "Fast blade that channels cursed energy.",
        "type": "equipment",
        "slot": "weapon",
        "level_req": 5,
        "rarity": "uncommon",
        "price": 300,
        "stats_boost": {
            "power": 4,
            "speed": 2
        }
    },
    {
        "name": "Spirit Blade",
        "description": "A sword forged with cursed energy.",
        "type": "equipment",
        "slot": "weapon",
        "level_req": 10,
        "rarity": "rare",
        "price": 600,
        "stats_boost": {
            "power": 8,
            "speed": 1
        }
    },
    {
        "name": "Shadow Cutter",
        "description": "A blade that phases through defenses.",
        "type": "equipment",
        "slot": "weapon",
        "level_req": 15,
        "rarity": "epic",
        "price": 1200,
        "stats_boost": {
            "power": 12,
            "speed": 3
        }
    },
    
    # Armor
    {
        "name": "Padded Vest",
        "description": "Basic protection for novice curse users.",
        "type": "equipment",
        "slot": "armor",
        "level_req": 1,
        "rarity": "common",
        "price": 100,
        "stats_boost": {
            "defense": 3,
            "hp": 10
        }
    },
    {
        "name": "Reinforced Robes",
        "description": "Enchanted fabric that disperses curses.",
        "type": "equipment",
        "slot": "armor",
        "level_req": 3,
        "rarity": "common",
        "price": 200,
        "stats_boost": {
            "defense": 5,
            "hp": 15
        }
    },
    {
        "name": "Barrier Coat",
        "description": "Infused with minor barrier techniques.",
        "type": "equipment",
        "slot": "armor",
        "level_req": 7,
        "rarity": "uncommon",
        "price": 400,
        "stats_boost": {
            "defense": 8,
            "hp": 20
        }
    },
    {
        "name": "Domain Armor",
        "description": "Imbued with powers from a domain.",
        "type": "equipment",
        "slot": "armor",
        "level_req": 12,
        "rarity": "rare",
        "price": 800,
        "stats_boost": {
            "defense": 12,
            "hp": 30,
            "power": 2
        }
    },
    {
        "name": "Cursed Technique Armor",
        "description": "Armor created using an advanced cursed technique.",
        "type": "equipment",
        "slot": "armor",
        "level_req": 18,
        "rarity": "epic",
        "price": 1500,
        "stats_boost": {
            "defense": 18,
            "hp": 50,
            "power": 3
        }
    },
    
    # Accessories
    {
        "name": "Lucky Charm",
        "description": "A simple charm that brings minor luck.",
        "type": "equipment",
        "slot": "accessory",
        "level_req": 1,
        "rarity": "common",
        "price": 50,
        "stats_boost": {
            "speed": 1,
            "power": 1
        }
    },
    {
        "name": "Cursed Ring",
        "description": "Enhances the wearer's cursed energy.",
        "type": "equipment",
        "slot": "accessory",
        "level_req": 4,
        "rarity": "uncommon",
        "price": 250,
        "stats_boost": {
            "power": 3,
            "speed": 1
        }
    },
    {
        "name": "Shadow Band",
        "description": "Forged from shadows, enhances speed and evasion.",
        "type": "equipment",
        "slot": "accessory",
        "level_req": 8,
        "rarity": "rare",
        "price": 500,
        "stats_boost": {
            "speed": 5,
            "defense": 2
        }
    },
    {
        "name": "Domain Fragment",
        "description": "A fragment of a powerful domain, granting its wearer enhanced abilities.",
        "type": "equipment",
        "slot": "accessory",
        "level_req": 15,
        "rarity": "epic",
        "price": 1000,
        "stats_boost": {
            "power": 5,
            "defense": 3,
            "speed": 3
        }
    },
    
    # Talismans
    {
        "name": "Cursed Talisman",
        "description": "A basic talisman that enhances cursed energy.",
        "type": "equipment",
        "slot": "talisman",
        "level_req": 2,
        "rarity": "common",
        "price": 150,
        "stats_boost": {
            "power": 2,
            "hp": 5
        }
    },
    {
        "name": "Barrier Talisman",
        "description": "Enhances defensive capabilities.",
        "type": "equipment",
        "slot": "talisman",
        "level_req": 5,
        "rarity": "uncommon",
        "price": 300,
        "stats_boost": {
            "defense": 4,
            "hp": 10
        }
    },
    {
        "name": "Technique Amplifier",
        "description": "Amplifies the power of cursed techniques.",
        "type": "equipment",
        "slot": "talisman",
        "level_req": 10,
        "rarity": "rare",
        "price": 700,
        "stats_boost": {
            "power": 6,
            "speed": 2
        }
    },
    {
        "name": "Ancient Seal",
        "description": "A powerful seal containing ancient cursed techniques.",
        "type": "equipment",
        "slot": "talisman",
        "level_req": 18,
        "rarity": "epic",
        "price": 1400,
        "stats_boost": {
            "power": 8,
            "defense": 4,
            "hp": 15
        }
    },
    
    # Consumables
    {
        "name": "Minor Healing Potion",
        "description": "Restores a small amount of health.",
        "type": "consumable",
        "level_req": 1,
        "rarity": "common",
        "price": 30,
        "heal": 20
    },
    {
        "name": "Healing Potion",
        "description": "Restores a moderate amount of health.",
        "type": "consumable",
        "level_req": 5,
        "rarity": "uncommon",
        "price": 60,
        "heal": 50
    },
    {
        "name": "Major Healing Potion",
        "description": "Restores a large amount of health.",
        "type": "consumable",
        "level_req": 10,
        "rarity": "rare",
        "price": 120,
        "heal": 100
    },
    {
        "name": "Cursed Energy Vial",
        "description": "Restores a small amount of cursed energy.",
        "type": "consumable",
        "level_req": 1,
        "rarity": "common",
        "price": 30,
        "energy": 20
    },
    {
        "name": "Cursed Energy Flask",
        "description": "Restores a moderate amount of cursed energy.",
        "type": "consumable",
        "level_req": 5,
        "rarity": "uncommon",
        "price": 60,
        "energy": 50
    },
    {
        "name": "Cursed Energy Crystal",
        "description": "Restores a large amount of cursed energy.",
        "type": "consumable",
        "level_req": 10,
        "rarity": "rare",
        "price": 120,
        "energy": 100
    },
    {
        "name": "Strength Elixir",
        "description": "Temporarily boosts power.",
        "type": "consumable",
        "level_req": 3,
        "rarity": "uncommon",
        "price": 75,
        "effect": "strength",
        "buff_amount": 5
    },
    {
        "name": "Recovery Pack",
        "description": "Restores both health and cursed energy.",
        "type": "consumable",
        "level_req": 7,
        "rarity": "rare",
        "price": 100,
        "heal": 30,
        "energy": 30
    }
]

# Help command pages
HELP_PAGES = {
    "Basic": {
        "Start": {
            "description": "Begin your journey and select your class",
            "usage": "!start"
        },
        "Profile": {
            "description": "View your stats and progress",
            "usage": "!profile [user]"
        },
        "Help": {
            "description": "Show this help message",
            "usage": "!help [category]"
        },
        "Status": {
            "description": "View your current battle status and cooldowns",
            "usage": "!status"
        },
        "Daily": {
            "description": "Claim your daily rewards",
            "usage": "!daily"
        }
    },
    "Battle": {
        "Battle": {
            "description": "Battle another player or an NPC",
            "usage": "!battle [@player]"
        },
        "Train": {
            "description": "Train to improve your stats and earn XP",
            "usage": "!train"
        },
        "Skills": {
            "description": "Allocate skill points to increase stats",
            "usage": "!skills"
        },
        "Heal": {
            "description": "Heal your character for a cost",
            "usage": "!heal"
        }
    },
    "Equipment": {
        "Inventory": {
            "description": "View your inventory",
            "usage": "!inventory"
        },
        "Equipment": {
            "description": "View your equipped items",
            "usage": "!equipment"
        },
        "Equip": {
            "description": "Equip an item from your inventory",
            "usage": "!equip [item_name]"
        },
        "Unequip": {
            "description": "Unequip an item",
            "usage": "!unequip [slot]"
        },
        "Use": {
            "description": "Use a consumable item",
            "usage": "!use [item_name]"
        }
    },
    "Economy": {
        "Shop": {
            "description": "Browse and buy items",
            "usage": "!shop"
        },
        "Gift": {
            "description": "Gift currency to another player",
            "usage": "!gift @player [amount]"
        }
    },
    "Dungeons": {
        "Dungeon": {
            "description": "Enter a dungeon",
            "usage": "!dungeon [name]"
        },
        "Rewards": {
            "description": "View possible dungeon rewards",
            "usage": "!rewards"
        }
    },
    "Social": {
        "Leaderboard": {
            "description": "View the server leaderboard",
            "usage": "!leaderboard [category]"
        }
    }
}

def generate_shop_items(player_level: int) -> List[Dict]:
    """Generate a list of shop items appropriate for player level"""
    # Filter items by level requirement
    available_items = [item for item in SHOP_ITEMS if item.get("level_req", 1) <= player_level + 3]
    
    # Always include some basic consumables
    consumables = [item for item in available_items if item.get("type") == "consumable"]
    equipment = [item for item in available_items if item.get("type") == "equipment"]
    
    # Select random items, ensuring we have some of each type
    selected_consumables = random.sample(consumables, min(3, len(consumables)))
    selected_equipment = random.sample(equipment, min(5, len(equipment)))
    
    return selected_consumables + selected_equipment

def generate_npc_opponent(player_level: int) -> Any:
    """Generate an NPC opponent for battle based on player level"""
    from data_manager import PlayerData
    
    # Create a dummy player object for the NPC
    npc = PlayerData(0)  # ID 0 for NPCs
    
    # Choose a random class
    npc.class_name = random.choice(list(CLASSES.keys()))
    
    # Set level close to player's level (±1)
    npc.class_level = max(1, player_level + random.randint(-1, 1))
    
    # Set stats based on class and level
    base_stats = CLASSES[npc.class_name]["stats"].copy()
    
    # Scale stats based on level
    level_scale = 1.0 + ((npc.class_level - 1) * 0.1)  # 10% increase per level
    for stat in base_stats:
        base_stats[stat] = int(base_stats[stat] * level_scale)
    
    npc.base_stats = base_stats
    npc.current_stats = base_stats.copy()
    
    # Generate a name
    prefixes = ["Dark", "Shadow", "Cursed", "Spirit", "Vengeful", "Deadly", "Ancient", "Phantom"]
    suffixes = ["Hunter", "Slayer", "Warrior", "Guardian", "Assassin", "Knight", "Sorcerer", "Ghost"]
    
    npc_name = f"{random.choice(prefixes)} {random.choice(suffixes)}"
    npc.user_name = npc_name  # Not a real property, but we'll use it for display
    
    # Set abilities based on class
    npc.abilities = [
        CLASSES[npc.class_name]["abilities"]["active"],
        CLASSES[npc.class_name]["abilities"]["passive"]
    ]
    
    # Set cursed energy
    npc.cursed_energy = 100
    npc.max_cursed_energy = 100
    
    return npc

def generate_random_item(player_level: int, quality_bonus: int = 0) -> Dict:
    """Generate a random item appropriate for the player's level"""
    # Determine item type
    item_type = random.choices(
        ["equipment", "consumable"],
        weights=[0.7, 0.3],
        k=1
    )[0]
    
    if item_type == "equipment":
        # Determine equipment slot
        slot = random.choices(
            ["weapon", "armor", "accessory", "talisman"],
            weights=[0.3, 0.3, 0.2, 0.2],
            k=1
        )[0]
        
        # Determine rarity based on player level and quality bonus
        rarity_choices = ["common", "uncommon", "rare", "epic", "legendary", "mythic"]
        rarity_weights = [0.4, 0.3, 0.15, 0.1, 0.04, 0.01]  # Base weights
        
        # Adjust weights based on level and quality bonus
        level_factor = min(1.0, player_level / 20)  # Scale up to level 20
        quality_factor = 0.1 * quality_bonus  # Each quality point shifts by 10%
        
        # Shift weights toward better rarities
        for i in range(len(rarity_weights) - 1):
            shift = (level_factor * 0.3) + quality_factor
            if shift > 0:
                transfer = rarity_weights[i] * shift
                rarity_weights[i] -= transfer
                rarity_weights[i+1] += transfer
        
        rarity = random.choices(rarity_choices, weights=rarity_weights, k=1)[0]
        
        # Determine stat boosts based on level and rarity
        rarity_multiplier = {
            "common": 1.0,
            "uncommon": 1.5,
            "rare": 2.0,
            "epic": 2.5,
            "legendary": 3.0,
            "mythic": 4.0
        }
        
        base_stat_value = 1 + (player_level // 3)
        stat_value = int(base_stat_value * rarity_multiplier[rarity])
        
        # Choose which stats to boost based on slot
        stats_boost = {}
        if slot == "weapon":
            stats_boost["power"] = stat_value
            if random.random() < 0.3:
                stats_boost["speed"] = max(1, stat_value // 2)
        elif slot == "armor":
            stats_boost["defense"] = stat_value
            stats_boost["hp"] = stat_value * 5
        elif slot == "accessory":
            primary = random.choice(["power", "speed"])
            secondary = random.choice(["defense", "hp"])
            stats_boost[primary] = stat_value
            stats_boost[secondary] = max(1, stat_value // 2) if secondary != "hp" else stat_value * 3
        elif slot == "talisman":
            primary = random.choice(["power", "defense"])
            stats_boost[primary] = stat_value
            if random.random() < 0.5:
                stats_boost["hp"] = stat_value * 3
        
        # Generate name
        prefixes = {
            "common": ["Basic", "Simple", "Standard", "Sturdy"],
            "uncommon": ["Quality", "Enhanced", "Improved", "Reinforced"],
            "rare": ["Superior", "Exceptional", "Refined", "Empowered"],
            "epic": ["Magnificent", "Extraordinary", "Formidable", "Dominant"],
            "legendary": ["Legendary", "Ancient", "Mythical", "Divine"],
            "mythic": ["Supreme", "Transcendent", "Ethereal", "Godly"]
        }
        
        suffixes = {
            "weapon": ["Blade", "Sword", "Dagger", "Scythe", "Katana"],
            "armor": ["Armor", "Garb", "Robes", "Suit", "Vestment"],
            "accessory": ["Ring", "Amulet", "Charm", "Band", "Bracelet"],
            "talisman": ["Talisman", "Emblem", "Seal", "Rune", "Totem"]
        }
        
        modifiers = {
            "power": ["Strength", "Power", "Might", "Force", "Vigor"],
            "defense": ["Protection", "Defense", "Warding", "Guard", "Shield"],
            "speed": ["Quickness", "Speed", "Agility", "Swiftness", "Haste"],
            "hp": ["Health", "Vitality", "Life", "Endurance", "Resilience"]
        }
        
        # Choose a key stat for the name
        key_stat = max(stats_boost.items(), key=lambda x: x[1])[0]
        
        name = f"{random.choice(prefixes[rarity])} {random.choice(modifiers[key_stat])} {random.choice(suffixes[slot])}"
        
        # Generate description
        descriptions = {
            "common": [
                "A basic item with minor enhancements.",
                "A serviceable item for beginners.",
                "Provides basic protection/offense.",
                "A common item found throughout the world."
            ],
            "uncommon": [
                "An item with minor cursed energy infusion.",
                "Better than standard equipment.",
                "Shows signs of quality craftsmanship.",
                "Enhanced with basic cursed techniques."
            ],
            "rare": [
                "A powerful item imbued with cursed energy.",
                "Expertly crafted using rare materials.",
                "Contains trace elements of a curse user's power.",
                "A valuable find with potent properties."
            ],
            "epic": [
                "An exceptional item radiating with cursed energy.",
                "Created by a master craftsman for elite users.",
                "Contains considerable power from its previous owner.",
                "Few curse users possess such fine equipment."
            ],
            "legendary": [
                "A legendary artifact of immense power.",
                "Said to have been wielded by a famous curse user.",
                "Emanates tremendous cursed energy even at rest.",
                "One of the finest examples of its kind in existence."
            ],
            "mythic": [
                "A mythical relic of unparalleled power.",
                "Belongs in the realm of legends and myths.",
                "Radiates cursed energy beyond comprehension.",
                "Its very existence defies the natural order."
            ]
        }
        
        description = random.choice(descriptions[rarity])
        
        # Add stat-specific descriptions
        stat_desc = []
        for stat, value in stats_boost.items():
            if stat == "power":
                stat_desc.append(f"Enhances striking power")
            elif stat == "defense":
                stat_desc.append(f"Reinforces defensive capabilities")
            elif stat == "speed":
                stat_desc.append(f"Increases movement and reaction speed")
            elif stat == "hp":
                stat_desc.append(f"Bolsters vitality and resilience")
        
        if stat_desc:
            description += f" {random.choice(['It', 'This item', 'When equipped, it'])} {' and '.join(stat_desc)}."
        
        # Level requirement based on rarity and player level
        level_req = max(1, player_level - random.randint(2, 4))
        if rarity in ["rare", "epic", "legendary", "mythic"]:
            level_req = max(level_req, {
                "rare": 5,
                "epic": 10,
                "legendary": 15,
                "mythic": 20
            }[rarity])
        
        return {
            "name": name,
            "description": description,
            "type": "equipment",
            "slot": slot,
            "rarity": rarity,
            "level_req": level_req,
            "stats_boost": stats_boost
        }
    
    else:  # consumable
        # Determine consumable type
        consumable_type = random.choices(
            ["healing", "energy", "dual", "buff"],
            weights=[0.4, 0.3, 0.2, 0.1],
            k=1
        )[0]
        
        # Determine potency based on player level
        base_potency = 10 + (player_level * 5)
        
        # Determine rarity
        rarity_choices = ["common", "uncommon", "rare", "epic"]
        rarity_weights = [0.5, 0.3, 0.15, 0.05]
        
        # Adjust weights based on level and quality bonus
        level_factor = min(1.0, player_level / 20)
        quality_factor = 0.1 * quality_bonus
        
        for i in range(len(rarity_weights) - 1):
            shift = (level_factor * 0.3) + quality_factor
            if shift > 0:
                transfer = rarity_weights[i] * shift
                rarity_weights[i] -= transfer
                rarity_weights[i+1] += transfer
        
        rarity = random.choices(rarity_choices, weights=rarity_weights, k=1)[0]
        
        # Rarity multiplier
        rarity_multiplier = {
            "common": 1.0,
            "uncommon": 1.5,
            "rare": 2.0,
            "epic": 2.5
        }
        
        potency = int(base_potency * rarity_multiplier[rarity])
        
        # Create the item based on type
        item = {
            "type": "consumable",
            "rarity": rarity
        }
        
        if consumable_type == "healing":
            item["name"] = f"{rarity.title()} Healing Potion"
            item["description"] = f"Restores {potency} health points."
            item["heal"] = potency
        
        elif consumable_type == "energy":
            item["name"] = f"{rarity.title()} Cursed Energy Vial"
            item["description"] = f"Restores {potency} cursed energy."
            item["energy"] = potency
        
        elif consumable_type == "dual":
            dual_potency = int(potency * 0.7)  # Slightly less potent than single-effect items
            item["name"] = f"{rarity.title()} Recovery Essence"
            item["description"] = f"Restores {dual_potency} health and {dual_potency} cursed energy."
            item["heal"] = dual_potency
            item["energy"] = dual_potency
        
        elif consumable_type == "buff":
            buff_amount = max(3, player_level // 2)
            if rarity != "common":
                buff_amount += {"uncommon": 1, "rare": 2, "epic": 3}[rarity]
            
            buff_type = random.choice(["strength", "defense", "speed"])
            
            item["name"] = f"{rarity.title()} {buff_type.title()} Elixir"
            item["description"] = f"Temporarily increases {buff_type} by {buff_amount}."
            item["effect"] = buff_type
            item["buff_amount"] = buff_amount
        
        return item

def generate_rare_item(player_level: int, dungeon_name: str) -> Dict:
    """Generate a rare item specific to a dungeon"""
    # Each dungeon has specific themed rare items
    dungeon_items = {
        "Training Grounds": [
            {
                "name": "Instructor's Guidance",
                "description": "A special talisman imbued with knowledge from skilled instructors.",
                "type": "equipment",
                "slot": "talisman",
                "rarity": "rare",
                "level_req": max(1, player_level - 2),
                "stats_boost": {
                    "power": 3,
                    "defense": 3,
                    "speed": 3
                }
            },
            {
                "name": "Training Weights",
                "description": "Special weights that enhance your power when removed in battle.",
                "type": "equipment",
                "slot": "accessory",
                "rarity": "rare",
                "level_req": max(1, player_level - 2),
                "stats_boost": {
                    "power": 6,
                    "speed": -1
                }
            }
        ],
        "Cursed Forest": [
            {
                "name": "Woodland Spirit Blade",
                "description": "A blade forged with the essence of forest spirits.",
                "type": "equipment",
                "slot": "weapon",
                "rarity": "rare",
                "level_req": max(5, player_level - 1),
                "stats_boost": {
                    "power": 8,
                    "speed": 2
                }
            },
            {
                "name": "Forest Guardian's Armor",
                "description": "Armor infused with the protective essence of the forest.",
                "type": "equipment",
                "slot": "armor",
                "rarity": "rare",
                "level_req": max(5, player_level - 1),
                "stats_boost": {
                    "defense": 7,
                    "hp": 25
                }
            }
        ],
        "Abandoned Temple": [
            {
                "name": "Temple Elder's Staff",
                "description": "An ancient weapon used by the temple's former guardians.",
                "type": "equipment",
                "slot": "weapon",
                "rarity": "epic",
                "level_req": max(10, player_level - 1),
                "stats_boost": {
                    "power": 10,
                    "defense": 5
                }
            },
            {
                "name": "Sacred Temple Robes",
                "description": "Ceremonial robes with powerful defensive enchantments.",
                "type": "equipment",
                "slot": "armor",
                "rarity": "epic",
                "level_req": max(10, player_level - 1),
                "stats_boost": {
                    "defense": 12,
                    "hp": 35
                }
            }
        ],
        "Cursed Abyss": [
            {
                "name": "Abyssal Claw",
                "description": "A weapon formed from the hardened claws of an abyss creature.",
                "type": "equipment",
                "slot": "weapon",
                "rarity": "epic",
                "level_req": max(15, player_level - 1),
                "stats_boost": {
                    "power": 15,
                    "speed": 5
                }
            },
            {
                "name": "Void-Touched Amulet",
                "description": "An amulet that absorbed the power of the abyss.",
                "type": "equipment",
                "slot": "accessory",
                "rarity": "legendary",
                "level_req": max(15, player_level),
                "stats_boost": {
                    "power": 8,
                    "defense": 8,
                    "hp": 20
                }
            }
        ],
        "Domain of Shadows": [
            {
                "name": "Shadow King's Blade",
                "description": "The personal weapon of the Shadow King, radiating with dark power.",
                "type": "equipment",
                "slot": "weapon",
                "rarity": "legendary",
                "level_req": max(20, player_level),
                "stats_boost": {
                    "power": 18,
                    "speed": 8
                }
            },
            {
                "name": "Crown of Shadows",
                "description": "A crown that grants its wearer dominion over shadows.",
                "type": "equipment",
                "slot": "talisman",
                "rarity": "legendary",
                "level_req": max(20, player_level),
                "stats_boost": {
                    "power": 10,
                    "defense": 10,
                    "speed": 5,
                    "hp": 30
                }
            },
            {
                "name": "Shadow Domain Fragment",
                "description": "A rare fragment containing a portion of the Shadow Domain's power.",
                "type": "equipment",
                "slot": "accessory",
                "rarity": "mythic",
                "level_req": max(20, player_level),
                "stats_boost": {
                    "power": 12,
                    "defense": 8,
                    "speed": 8,
                    "hp": 25
                }
            }
        ]
    }
    
    # Fallback to default dungeon if the provided one doesn't exist
    if dungeon_name not in dungeon_items:
        dungeon_name = "Training Grounds"
    
    # Select a random item from the dungeon's rare items
    return random.choice(dungeon_items[dungeon_name])
