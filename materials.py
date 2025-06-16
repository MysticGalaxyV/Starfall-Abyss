import discord
from discord.ui import Button, View, Select
import random
from typing import Dict, List, Optional, Any, Union
from data_models import DataManager, PlayerData, Item, InventoryItem
from user_restrictions import RestrictedView

# Materials rarity levels
MATERIAL_RARITIES = {
    "Common": {
        "color": discord.Color.light_gray(),
        "drop_rate": 0.6,
        "value_multiplier": 1
    },
    "Uncommon": {
        "color": discord.Color.green(),
        "drop_rate": 0.3,
        "value_multiplier": 2
    },
    "Rare": {
        "color": discord.Color.blue(),
        "drop_rate": 0.1,
        "value_multiplier": 5
    },
    "Epic": {
        "color": discord.Color.purple(),
        "drop_rate": 0.05,
        "value_multiplier": 15
    },
    "Legendary": {
        "color": discord.Color.gold(),
        "drop_rate": 0.01,
        "value_multiplier": 50
    },
    "Mythic": {
        "color": discord.Color.red(),
        "drop_rate": 0.005,
        "value_multiplier": 200
    },
    "Divine": {
        "color": 0xf2d7b4,
        "drop_rate": 0.001,
        "value_multiplier": 1000
    },  # Light gold/divine color
    "Transcendent": {
        "color": 0xb5f0f2,
        "drop_rate": 0.0005,
        "value_multiplier": 5000
    },  # Ethereal blue
    "Primordial": {
        "color": 0x660066,
        "drop_rate": 0.0001,
        "value_multiplier": 25000
    },  # Deep purple
}

# Material categories and types

# Define gathering tool categories, types, and efficiency tiers
GATHERING_TOOLS = {
    "Mining": {
        "Tool Types": ["Pickaxe", "Drill", "Excavator"],
        "Tiers": [{
            "name": "Copper",
            "level_req": 1,
            "efficiency": 1.2
        }, {
            "name": "Iron",
            "level_req": 10,
            "efficiency": 1.5
        }, {
            "name": "Steel",
            "level_req": 20,
            "efficiency": 1.8
        }, {
            "name": "Titanium",
            "level_req": 30,
            "efficiency": 2.2
        }, {
            "name": "Enchanted",
            "level_req": 40,
            "efficiency": 2.5
        }, {
            "name": "Divine",
            "level_req": 50,
            "efficiency": 3.0
        }]
    },
    "Foraging": {
        "Tool Types": ["Axe", "Saw", "Harvester"],
        "Tiers": [{
            "name": "Copper",
            "level_req": 1,
            "efficiency": 1.2
        }, {
            "name": "Iron",
            "level_req": 10,
            "efficiency": 1.5
        }, {
            "name": "Steel",
            "level_req": 20,
            "efficiency": 1.8
        }, {
            "name": "Reinforced",
            "level_req": 30,
            "efficiency": 2.2
        }, {
            "name": "Enchanted",
            "level_req": 40,
            "efficiency": 2.5
        }, {
            "name": "Divine",
            "level_req": 50,
            "efficiency": 3.0
        }]
    },
    "Herbs": {
        "Tool Types": ["Sickle", "Shears", "Cultivator"],
        "Tiers": [{
            "name": "Copper",
            "level_req": 1,
            "efficiency": 1.2
        }, {
            "name": "Silver",
            "level_req": 10,
            "efficiency": 1.5
        }, {
            "name": "Gold",
            "level_req": 20,
            "efficiency": 1.8
        }, {
            "name": "Refined",
            "level_req": 30,
            "efficiency": 2.2
        }, {
            "name": "Enchanted",
            "level_req": 40,
            "efficiency": 2.5
        }, {
            "name": "Divine",
            "level_req": 50,
            "efficiency": 3.0
        }]
    },
    "Hunting": {
        "Tool Types": ["Knife", "Bow", "Trap"],
        "Tiers": [{
            "name": "Copper",
            "level_req": 1,
            "efficiency": 1.2
        }, {
            "name": "Iron",
            "level_req": 10,
            "efficiency": 1.5
        }, {
            "name": "Steel",
            "level_req": 20,
            "efficiency": 1.8
        }, {
            "name": "Composite",
            "level_req": 30,
            "efficiency": 2.2
        }, {
            "name": "Enchanted",
            "level_req": 40,
            "efficiency": 2.5
        }, {
            "name": "Divine",
            "level_req": 50,
            "efficiency": 3.0
        }]
    },
    "Magical": {
        "Tool Types": ["Wand", "Staff", "Crystal"],
        "Tiers": [{
            "name": "Novice",
            "level_req": 1,
            "efficiency": 1.2
        }, {
            "name": "Adept",
            "level_req": 10,
            "efficiency": 1.5
        }, {
            "name": "Expert",
            "level_req": 20,
            "efficiency": 1.8
        }, {
            "name": "Master",
            "level_req": 30,
            "efficiency": 2.2
        }, {
            "name": "Arcane",
            "level_req": 40,
            "efficiency": 2.5
        }, {
            "name": "Divine",
            "level_req": 50,
            "efficiency": 3.0
        }]
    }
}
MATERIAL_CATEGORIES = {
    "Mining": {
        "description":
        "Materials obtained from mining ores and stones",
        "types": [
            "Stone", "Coal", "Copper Ore", "Tin Ore", "Iron Ore", "Silver Ore",
            "Gold Ore", "Platinum Ore", "Mithril Ore", "Adamantite Ore",
            "Runite Ore", "Dragonite Ore", "Orichalcum", "Elementium",
            "Vibrainium", "Celestial Ore", "Void Matter", "Chronostone",
            "Ethereal Ore", "Cosmic Crystal"
        ],
        "level_ranges": [(1, 10), (5, 20), (10, 30), (15, 40), (20, 50),
                         (30, 60), (40, 70), (50, 80), (60, 90), (70, 100),
                         (80, 110), (90, 120), (100, 150), (150, 200),
                         (200, 300), (300, 500), (500, 700), (700, 850),
                         (850, 950), (950, 1000)],
        "base_values": [
            5, 10, 15, 25, 40, 75, 120, 200, 350, 550, 800, 1200, 2000, 5000,
            15000, 50000, 150000, 500000, 1500000, 5000000
        ]
    },
    "Foraging": {
        "description":
        "Materials gathered from forests and nature",
        "types": [
            "Timber", "Oak Wood", "Maple Wood", "Yew Wood", "Magic Wood",
            "Elder Wood", "Ancient Wood", "Petrified Wood", "Spirit Wood",
            "Fey Wood", "Treant Wood", "Dryad Essence", "World Tree Bark",
            "Living Wood", "Whispering Bark", "Timeless Wood", "Astral Timber",
            "Void-touched Wood", "Cosmic Heartwood", "Genesis Wood"
        ],
        "level_ranges": [(1, 10), (5, 20), (10, 30), (15, 40), (20, 50),
                         (30, 60), (40, 70), (50, 80), (60, 90), (70, 100),
                         (80, 110), (90, 120), (100, 150), (150, 200),
                         (200, 300), (300, 500), (500, 700), (700, 850),
                         (850, 950), (950, 1000)],
        "base_values": [
            5, 10, 15, 25, 40, 75, 120, 200, 350, 550, 800, 1200, 2000, 5000,
            15000, 50000, 150000, 500000, 1500000, 5000000
        ]
    },
    "Herbs": {
        "description":
        "Magical and medicinal plants",
        "types": [
            "Mint Leaf", "Lavender", "Sage", "Rosemary", "Mandrake",
            "Nightshade", "Dreamleaf", "Golden Lotus", "Ghost Mushroom",
            "Dragon's Breath Plant", "Celestial Herb", "Starflower",
            "Phoenix Bloom", "Lunar Petal", "Void Sprout", "Ethereal Seed",
            "Timeblossom", "Cosmic Sprout", "Astral Blossom", "God Flower"
        ],
        "level_ranges": [(1, 10), (5, 20), (10, 30), (15, 40), (20, 50),
                         (30, 60), (40, 70), (50, 80), (60, 90), (70, 100),
                         (80, 110), (90, 120), (100, 150), (150, 200),
                         (200, 300), (300, 500), (500, 700), (700, 850),
                         (850, 950), (950, 1000)],
        "base_values": [
            8, 15, 25, 40, 70, 120, 180, 300, 500, 800, 1200, 1800, 3000, 8000,
            25000, 80000, 250000, 750000, 2000000, 7500000
        ]
    },
    "Monster Parts": {
        "description":
        "Parts obtained from slain monsters",
        "types": [
            "Wolf Fang", "Bear Claw", "Spider Silk", "Snake Venom",
            "Troll Blood", "Dragon Scale", "Griffin Feather", "Phoenix Ash",
            "Basilisk Eye", "Kraken Tentacle", "Unicorn Horn", "Demon Heart",
            "Angel Feather", "Titan's Bone", "Behemoth Hide",
            "Leviathan Scale", "World Serpent Skin", "Cosmic Beast Essence",
            "Void Dragon Heart", "God Beast Relic"
        ],
        "level_ranges": [(1, 10), (5, 20), (10, 30), (15, 40), (20, 50),
                         (30, 60), (40, 70), (50, 80), (60, 90), (70, 100),
                         (80, 110), (90, 120), (100, 150), (150, 200),
                         (200, 300), (300, 500), (500, 700), (700, 850),
                         (850, 950), (950, 1000)],
        "base_values": [
            10, 20, 35, 60, 100, 180, 300, 500, 800, 1300, 2000, 3500, 6000,
            15000, 50000, 150000, 500000, 1500000, 5000000, 20000000
        ]
    },
    "Fabrics": {
        "description":
        "Materials for crafting clothing and armor",
        "types": [
            "Cotton", "Wool", "Silk", "Velvet", "Runecloth", "Mooncloth",
            "Netherweave", "Frostweave", "Embersilk", "Celestial Cloth",
            "Dreamweave", "Ethereal Fabric", "Astral Silk", "Time-Woven Cloth",
            "Dimensional Fabric", "Cosmic Weave", "Void Fabric",
            "God-Touched Cloth", "Destiny Cloth", "Creation Weave"
        ],
        "level_ranges": [(1, 10), (5, 20), (10, 30), (15, 40), (20, 50),
                         (30, 60), (40, 70), (50, 80), (60, 90), (70, 100),
                         (80, 110), (90, 120), (100, 150), (150, 200),
                         (200, 300), (300, 500), (500, 700), (700, 850),
                         (850, 950), (950, 1000)],
        "base_values": [
            7, 12, 20, 35, 60, 100, 150, 250, 400, 700, 1100, 1600, 2500, 6000,
            20000, 60000, 200000, 600000, 2000000, 6000000
        ]
    },
    "Magical": {
        "description":
        "Rare magical essences and components",
        "types": [
            "Minor Magic Essence", "Lesser Magic Essence", "Magic Essence",
            "Greater Magic Essence", "Superior Magic Essence", "Arcane Dust",
            "Soul Shard", "Void Crystal", "Cosmic Essence", "Planar Essence",
            "Time Fragment", "Elemental Core", "Divine Spark",
            "Ethereal Essence", "Astral Fragment", "Cosmic Shard",
            "Reality Shard", "Creation Essence", "God Spark",
            "Universe Fragment"
        ],
        "level_ranges": [(1, 10), (5, 20), (10, 30), (15, 40), (20, 50),
                         (30, 60), (40, 70), (50, 80), (60, 90), (70, 100),
                         (80, 110), (90, 120), (100, 150), (150, 200),
                         (200, 300), (300, 500), (500, 700), (700, 850),
                         (850, 950), (950, 1000)],
        "base_values": [
            20, 40, 70, 120, 200, 350, 600, 1000, 1800, 3000, 5000, 8000,
            15000, 40000, 100000, 300000, 1000000, 3000000, 10000000, 50000000
        ]
    },
    "Gems": {
        "description":
        "Precious and magical gemstones",
        "types": [
            "Quartz", "Amethyst", "Jade", "Amber", "Topaz", "Sapphire", "Ruby",
            "Emerald", "Diamond", "Opal", "Black Diamond", "Star Ruby",
            "Dragon's Eye Gem", "Heartstone", "Void Gem", "Soul Prism",
            "Time Crystal", "Eternity Diamond", "Cosmic Jewel", "God's Eye"
        ],
        "level_ranges": [(1, 10), (5, 20), (10, 30), (15, 40), (20, 50),
                         (30, 60), (40, 70), (50, 80), (60, 90), (70, 100),
                         (80, 110), (90, 120), (100, 150), (150, 200),
                         (200, 300), (300, 500), (500, 700), (700, 850),
                         (850, 950), (950, 1000)],
        "base_values": [
            15, 30, 50, 80, 150, 250, 400, 700, 1200, 2000, 3500, 6000, 10000,
            25000, 75000, 250000, 750000, 2500000, 7500000, 30000000
        ]
    },
    "Elemental": {
        "description":
        "Pure elemental materials from primordial planes",
        "types": [
            "Dust of Earth", "Water Droplet", "Spark of Fire", "Air Wisp",
            "Lightning Shard", "Ice Sliver", "Nature Essence",
            "Shadow Fragment", "Holy Light", "Void Essence", "Pure Earth",
            "Pure Water", "Pure Fire", "Pure Air", "Elemental Core",
            "Planar Essence", "Cosmic Element", "Creation Element",
            "Divine Element", "Primordial Element"
        ],
        "level_ranges": [(1, 10), (5, 20), (10, 30), (15, 40), (20, 50),
                         (30, 60), (40, 70), (50, 80), (60, 90), (70, 100),
                         (80, 110), (90, 120), (100, 150), (150, 200),
                         (200, 300), (300, 500), (500, 700), (700, 850),
                         (850, 950), (950, 1000)],
        "base_values": [
            25, 50, 90, 150, 250, 400, 700, 1200, 2000, 3500, 6000, 10000,
            18000, 50000, 150000, 500000, 1500000, 5000000, 15000000, 75000000
        ]
    }
}

# Tools for gathering materials
GATHERING_TOOLS = {
    "Mining": {
        "Tool Types": ["Pickaxe", "Drill", "Excavator"],
        "Tiers": [{
            "name": "Copper",
            "level_req": 1,
            "efficiency": 1.0,
            "durability": 50,
            "value": 100
        }, {
            "name": "Iron",
            "level_req": 20,
            "efficiency": 1.2,
            "durability": 100,
            "value": 500
        }, {
            "name": "Steel",
            "level_req": 40,
            "efficiency": 1.5,
            "durability": 200,
            "value": 2000
        }, {
            "name": "Mithril",
            "level_req": 60,
            "efficiency": 1.8,
            "durability": 300,
            "value": 8000
        }, {
            "name": "Adamantite",
            "level_req": 80,
            "efficiency": 2.1,
            "durability": 500,
            "value": 25000
        }, {
            "name": "Runite",
            "level_req": 100,
            "efficiency": 2.5,
            "durability": 800,
            "value": 100000
        }, {
            "name": "Dragon",
            "level_req": 150,
            "efficiency": 3.0,
            "durability": 1200,
            "value": 300000
        }, {
            "name": "Crystal",
            "level_req": 250,
            "efficiency": 3.5,
            "durability": 1500,
            "value": 1000000
        }, {
            "name": "Celestial",
            "level_req": 400,
            "efficiency": 4.0,
            "durability": 2000,
            "value": 5000000
        }, {
            "name": "Ethereal",
            "level_req": 600,
            "efficiency": 5.0,
            "durability": 3000,
            "value": 20000000
        }, {
            "name": "Void",
            "level_req": 800,
            "efficiency": 7.0,
            "durability": 5000,
            "value": 75000000
        }, {
            "name": "Divine",
            "level_req": 950,
            "efficiency": 10.0,
            "durability": 10000,
            "value": 300000000
        }]
    },
    "Foraging": {
        "Tool Types": ["Axe", "Saw", "Harvester"],
        "Tiers": [{
            "name": "Copper",
            "level_req": 1,
            "efficiency": 1.0,
            "durability": 50,
            "value": 100
        }, {
            "name": "Iron",
            "level_req": 20,
            "efficiency": 1.2,
            "durability": 100,
            "value": 500
        }, {
            "name": "Steel",
            "level_req": 40,
            "efficiency": 1.5,
            "durability": 200,
            "value": 2000
        }, {
            "name": "Mithril",
            "level_req": 60,
            "efficiency": 1.8,
            "durability": 300,
            "value": 8000
        }, {
            "name": "Adamantite",
            "level_req": 80,
            "efficiency": 2.1,
            "durability": 500,
            "value": 25000
        }, {
            "name": "Runite",
            "level_req": 100,
            "efficiency": 2.5,
            "durability": 800,
            "value": 100000
        }, {
            "name": "Dragon",
            "level_req": 150,
            "efficiency": 3.0,
            "durability": 1200,
            "value": 300000
        }, {
            "name": "Crystal",
            "level_req": 250,
            "efficiency": 3.5,
            "durability": 1500,
            "value": 1000000
        }, {
            "name": "Celestial",
            "level_req": 400,
            "efficiency": 4.0,
            "durability": 2000,
            "value": 5000000
        }, {
            "name": "Ethereal",
            "level_req": 600,
            "efficiency": 5.0,
            "durability": 3000,
            "value": 20000000
        }, {
            "name": "Void",
            "level_req": 800,
            "efficiency": 7.0,
            "durability": 5000,
            "value": 75000000
        }, {
            "name": "Divine",
            "level_req": 950,
            "efficiency": 10.0,
            "durability": 10000,
            "value": 300000000
        }]
    },
    "Herbs": {
        "Tool Types": ["Sickle", "Herb Cutter", "Botanist Set"],
        "Tiers": [{
            "name": "Copper",
            "level_req": 1,
            "efficiency": 1.0,
            "durability": 50,
            "value": 100
        }, {
            "name": "Iron",
            "level_req": 20,
            "efficiency": 1.2,
            "durability": 100,
            "value": 500
        }, {
            "name": "Steel",
            "level_req": 40,
            "efficiency": 1.5,
            "durability": 200,
            "value": 2000
        }, {
            "name": "Mithril",
            "level_req": 60,
            "efficiency": 1.8,
            "durability": 300,
            "value": 8000
        }, {
            "name": "Enchanted",
            "level_req": 80,
            "efficiency": 2.1,
            "durability": 500,
            "value": 25000
        }, {
            "name": "Runic",
            "level_req": 100,
            "efficiency": 2.5,
            "durability": 800,
            "value": 100000
        }, {
            "name": "Dragonscale",
            "level_req": 150,
            "efficiency": 3.0,
            "durability": 1200,
            "value": 300000
        }, {
            "name": "Crystal",
            "level_req": 250,
            "efficiency": 3.5,
            "durability": 1500,
            "value": 1000000
        }, {
            "name": "Celestial",
            "level_req": 400,
            "efficiency": 4.0,
            "durability": 2000,
            "value": 5000000
        }, {
            "name": "Ethereal",
            "level_req": 600,
            "efficiency": 5.0,
            "durability": 3000,
            "value": 20000000
        }, {
            "name": "Void",
            "level_req": 800,
            "efficiency": 7.0,
            "durability": 5000,
            "value": 75000000
        }, {
            "name": "Divine",
            "level_req": 950,
            "efficiency": 10.0,
            "durability": 10000,
            "value": 300000000
        }]
    },
    "Hunting": {
        "Tool Types": ["Knife", "Skinning Set", "Beast Hunter Kit"],
        "Tiers": [{
            "name": "Copper",
            "level_req": 1,
            "efficiency": 1.0,
            "durability": 50,
            "value": 100
        }, {
            "name": "Iron",
            "level_req": 20,
            "efficiency": 1.2,
            "durability": 100,
            "value": 500
        }, {
            "name": "Steel",
            "level_req": 40,
            "efficiency": 1.5,
            "durability": 200,
            "value": 2000
        }, {
            "name": "Mithril",
            "level_req": 60,
            "efficiency": 1.8,
            "durability": 300,
            "value": 8000
        }, {
            "name": "Adamantite",
            "level_req": 80,
            "efficiency": 2.1,
            "durability": 500,
            "value": 25000
        }, {
            "name": "Runite",
            "level_req": 100,
            "efficiency": 2.5,
            "durability": 800,
            "value": 100000
        }, {
            "name": "Dragon",
            "level_req": 150,
            "efficiency": 3.0,
            "durability": 1200,
            "value": 300000
        }, {
            "name": "Crystal",
            "level_req": 250,
            "efficiency": 3.5,
            "durability": 1500,
            "value": 1000000
        }, {
            "name": "Celestial",
            "level_req": 400,
            "efficiency": 4.0,
            "durability": 2000,
            "value": 5000000
        }, {
            "name": "Ethereal",
            "level_req": 600,
            "efficiency": 5.0,
            "durability": 3000,
            "value": 20000000
        }, {
            "name": "Void",
            "level_req": 800,
            "efficiency": 7.0,
            "durability": 5000,
            "value": 75000000
        }, {
            "name": "Divine",
            "level_req": 950,
            "efficiency": 10.0,
            "durability": 10000,
            "value": 300000000
        }]
    },
    "Magical": {
        "Tool Types": ["Wand", "Essence Gatherer", "Arcane Extractor"],
        "Tiers": [{
            "name": "Apprentice",
            "level_req": 1,
            "efficiency": 1.0,
            "durability": 50,
            "value": 100
        }, {
            "name": "Journeyman",
            "level_req": 20,
            "efficiency": 1.2,
            "durability": 100,
            "value": 500
        }, {
            "name": "Adept",
            "level_req": 40,
            "efficiency": 1.5,
            "durability": 200,
            "value": 2000
        }, {
            "name": "Master",
            "level_req": 60,
            "efficiency": 1.8,
            "durability": 300,
            "value": 8000
        }, {
            "name": "Archmagus",
            "level_req": 80,
            "efficiency": 2.1,
            "durability": 500,
            "value": 25000
        }, {
            "name": "Runic",
            "level_req": 100,
            "efficiency": 2.5,
            "durability": 800,
            "value": 100000
        }, {
            "name": "Dragon",
            "level_req": 150,
            "efficiency": 3.0,
            "durability": 1200,
            "value": 300000
        }, {
            "name": "Crystal",
            "level_req": 250,
            "efficiency": 3.5,
            "durability": 1500,
            "value": 1000000
        }, {
            "name": "Celestial",
            "level_req": 400,
            "efficiency": 4.0,
            "durability": 2000,
            "value": 5000000
        }, {
            "name": "Ethereal",
            "level_req": 600,
            "efficiency": 5.0,
            "durability": 3000,
            "value": 20000000
        }, {
            "name": "Void",
            "level_req": 800,
            "efficiency": 7.0,
            "durability": 5000,
            "value": 75000000
        }, {
            "name": "Divine",
            "level_req": 950,
            "efficiency": 10.0,
            "durability": 10000,
            "value": 300000000
        }]
    }
}


# Generate a complete material based on level and category
def generate_material(level: int, category: str = None) -> Item:
    """Generate a random material based on player level and optional category"""
    # Pick a random category if none specified
    if not category or category not in MATERIAL_CATEGORIES:
        category = random.choice(list(MATERIAL_CATEGORIES.keys()))

    category_data = MATERIAL_CATEGORIES[category]

    # Determine which tier of material the player can find based on level
    available_tiers = [
        i for i, level_range in enumerate(category_data["level_ranges"])
        if level >= level_range[0] and level <= level_range[1]
    ]

    if not available_tiers:
        # Default to the first tier if no matches
        tier_idx = 0
    else:
        # Weighted selection favors lower tiers
        weights = [1 / (i + 1) for i in range(len(available_tiers))]
        tier_idx = random.choices(available_tiers, weights=weights, k=1)[0]

    # Select material type and base value from the chosen tier
    material_type = category_data["types"][tier_idx]
    base_value = category_data["base_values"][tier_idx]
    level_req = category_data["level_ranges"][tier_idx][0]

    # Determine rarity with weighted randomization
    rarities = list(MATERIAL_RARITIES.keys())
    rarity_weights = [
        MATERIAL_RARITIES[rarity]["drop_rate"] for rarity in rarities
    ]
    rarity = random.choices(rarities, weights=rarity_weights, k=1)[0]

    # Calculate final value based on rarity
    value = int(base_value * MATERIAL_RARITIES[rarity]["value_multiplier"])

    # Generate item_id
    import uuid
    item_id = str(uuid.uuid4())

    # Create the material item
    material = Item(
        item_id=item_id,
        name=f"{rarity} {material_type}",
        description=
        f"A {rarity.lower()} quality {material_type.lower()} used in crafting.",
        item_type=f"Material:{category}",
        rarity=rarity,
        stats={},  # Materials don't have stats directly
        level_req=level_req,
        value=value)

    return material


# Get materials for a specific gathering action based on player level and tool
def gather_materials(player: PlayerData,
                     category: str,
                     tool_efficiency: float = 1.0) -> List[Item]:
    """Gather materials from a specific category using a gathering tool"""
    # Base number of items (1-3) affected by tool efficiency
    base_count = max(1, min(5, int(random.randint(1, 3) * tool_efficiency)))

    # Chance for bonus items based on player level
    bonus_chance = min(0.5,
                       player.class_level / 200)  # Max 50% chance at level 100
    if random.random() < bonus_chance:
        base_count += random.randint(1, 2)

    # Generate the materials
    materials = []
    for _ in range(base_count):
        material = generate_material(player.class_level, category)
        materials.append(material)

    return materials


class MaterialsView(View):

    def __init__(self, player_data: PlayerData, data_manager: DataManager):
        super().__init__(timeout=60)
        self.player = player_data
        self.data_manager = data_manager
        self.category = None
        self.page = 0
        self.items_per_page = 10

        # Add category selector
        self.add_category_select()

        # Add navigation buttons
        self.add_navigation_buttons()

    def add_category_select(self):
        """Add dropdown for material categories"""
        select = Select(placeholder="Select Material Category",
                        options=[
                            discord.SelectOption(
                                label=category,
                                description=data["description"][:100])
                            for category, data in MATERIAL_CATEGORIES.items()
                        ],
                        custom_id="category_select")
        select.callback = self.category_callback
        self.add_item(select)

    def add_navigation_buttons(self):
        """Add navigation buttons for pagination"""
        prev_button = Button(label="◀️ Previous",
                             custom_id="prev_page",
                             style=discord.ButtonStyle.gray)
        prev_button.callback = self.prev_page_callback

        next_button = Button(label="Next ▶️",
                             custom_id="next_page",
                             style=discord.ButtonStyle.gray)
        next_button.callback = self.next_page_callback

        self.add_item(prev_button)
        self.add_item(next_button)

    async def category_callback(self, interaction: discord.Interaction):
        """Handle category selection"""
        self.category = interaction.data["values"][0]
        self.page = 0

        embed = self.create_materials_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    async def prev_page_callback(self, interaction: discord.Interaction):
        """Handle previous page button"""
        if self.page > 0:
            self.page -= 1

        embed = self.create_materials_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    async def next_page_callback(self, interaction: discord.Interaction):
        """Handle next page button"""
        if self.category:
            category_data = MATERIAL_CATEGORIES[self.category]
            max_pages = (len(category_data["types"]) + self.items_per_page -
                         1) // self.items_per_page

            if self.page < max_pages - 1:
                self.page += 1

        embed = self.create_materials_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    def create_materials_embed(self) -> discord.Embed:
        """Create the materials display embed"""
        if not self.category:
            # General materials information if no category selected
            embed = discord.Embed(
                title="📦 Material Encyclopedia",
                description=
                "Browse different types of materials used in crafting. Select a category to see available materials.",
                color=discord.Color.blue())

            for category, data in MATERIAL_CATEGORIES.items():
                embed.add_field(name=category,
                                value=data["description"],
                                inline=False)

            # Add total count of materials to footer
            total_count = sum(
                len(data["types"]) for data in MATERIAL_CATEGORIES.values())
            embed.set_footer(
                text=
                f"Total Materials: {total_count} | Select a category to view details"
            )

        else:
            # Show materials for the selected category
            category_data = MATERIAL_CATEGORIES[self.category]
            embed = discord.Embed(title=f"📦 {self.category} Materials",
                                  description=category_data["description"],
                                  color=discord.Color.blue())

            # Calculate start and end indices for pagination
            start_idx = self.page * self.items_per_page
            end_idx = min(start_idx + self.items_per_page,
                          len(category_data["types"]))

            for i in range(start_idx, end_idx):
                material_type = category_data["types"][i]
                level_range = category_data["level_ranges"][i]
                base_value = category_data["base_values"][i]

                # Create value text showing ranges for different rarities
                rarities_text = []
                for rarity, data in MATERIAL_RARITIES.items():
                    value = int(base_value * data["value_multiplier"])
                    rarities_text.append(f"{rarity}: {value} gold")

                value_text = "\n".join(
                    rarities_text[:3])  # Show top 3 rarities
                if len(rarities_text) > 3:
                    value_text += "\n..."

                embed.add_field(
                    name=
                    f"{material_type} (Level {level_range[0]}-{level_range[1]})",
                    value=
                    f"**Base Value:** {base_value} gold\n**Rarity Values:**\n{value_text}",
                    inline=True)

            # Add pagination info to footer
            total_pages = (len(category_data["types"]) + self.items_per_page -
                           1) // self.items_per_page
            embed.set_footer(
                text=
                f"Page {self.page + 1}/{total_pages} | {len(category_data['types'])} materials total"
            )

        return embed


class GatheringView(View):

    def __init__(self, player_data, data_manager):
        super().__init__(timeout=120)
        self.player = player_data
        self.data_manager = data_manager
        self.selected_category = None

        # Add category select
        self.add_category_select()

        # Add gather button (initially disabled)
        self.gather_button = Button(label="Gather Materials",
                                    custom_id="gather",
                                    style=discord.ButtonStyle.green,
                                    disabled=True)
        self.gather_button.callback = self.gather_callback
        self.add_item(self.gather_button)

    def add_category_select(self):
        """Add dropdown for gathering categories"""
        select = Select(
            placeholder="Select Gathering Type",
            options=[
                discord.SelectOption(
                    label=category,
                    description=f"Gather {category.lower()} materials")
                for category in MATERIAL_CATEGORIES.keys()
            ],
            custom_id="category_select")
        select.callback = self.category_callback
        self.add_item(select)

    async def category_callback(self, interaction: discord.Interaction):
        """Handle category selection"""
        self.selected_category = interaction.data["values"][0]

        # Enable gather button once category is selected
        self.gather_button.disabled = False

        # Find player's best tool for this category
        best_tool = self.get_best_tool(self.selected_category)

        # Create and send embed
        embed = discord.Embed(
            title=f"🧰 {self.selected_category} Gathering",
            description=
            f"You are about to gather {self.selected_category.lower()} materials.",
            color=discord.Color.green())

        if best_tool:
            tool_name, efficiency = best_tool
            embed.add_field(
                name="🧰 Tool Equipped",
                value=f"**{tool_name}**\nEfficiency Bonus: {efficiency:.1f}x\n✅ Ready to gather!",
                inline=False)
        else:
            embed.add_field(
                name="⚠️ No Tool Equipped",
                value="You don't have any tools equipped for this gathering type.\nUse `!tools` to equip tools for better results!",
                inline=False)

        await interaction.response.edit_message(embed=embed, view=self)

    def get_best_tool(self, category: str) -> Optional[tuple]:
        """Find the player's best tool for a category"""
        # Check if the player has an equipped gathering tool for this category
        equipped_tool_name = self.player.equipped_gathering_tools.get(category)

        if equipped_tool_name:
            # Find the equipped tool in the player's inventory
            for inv_item in self.player.inventory:
                if hasattr(inv_item, 'item') and hasattr(inv_item.item, 'name') and inv_item.item.name == equipped_tool_name:
                    # Use the simplified efficiency calculation from GatheringToolsView
                    efficiency = self.get_tool_efficiency_simple(equipped_tool_name, category)
                    if efficiency > 1.0:  # Only return if we found a valid efficiency
                        return (inv_item.item.name, efficiency)

        # If no equipped tool found or if efficiency couldn't be determined, return None
        return None

    def get_tool_efficiency_simple(self, tool_name: str, category: str) -> float:
        """Get efficiency for a tool using simplified logic"""
        # Check all gathering categories to find the tool
        for cat_name, cat_data in GATHERING_TOOLS.items():
            # Check if this tool matches any tool type in this category
            for tool_type in cat_data.get("Tool Types", []):
                if tool_type in tool_name:
                    # Extract tier name by removing the tool type
                    tier_name = tool_name.replace(f" {tool_type}", "").replace(f"{tool_type} ", "")
                    
                    # Find efficiency for this tier
                    for tier in cat_data.get("Tiers", []):
                        if tier["name"] == tier_name:
                            return tier["efficiency"]
        
        # If no match found, return default efficiency
        return 1.0

    async def gather_callback(self, interaction: discord.Interaction):
        """Handle gather button click"""
        if not self.selected_category:
            await interaction.response.send_message(
                "Please select a gathering type first.", ephemeral=True)
            return

        # Get player's tool and efficiency
        best_tool = self.get_best_tool(self.selected_category)
        efficiency = 1.0  # Default with no tool
        if best_tool:
            _, efficiency = best_tool

        # Gather materials
        materials = gather_materials(self.player, self.selected_category,
                                     efficiency)

        # Add materials to player inventory
        for material in materials:
            # Check if player already has this material (by name)
            found = False
            for inv_item in self.player.inventory:
                if inv_item.item.name == material.name:
                    inv_item.quantity += 1
                    found = True
                    break

            if not found:
                # Add new material to inventory
                self.player.inventory.append(
                    InventoryItem(material, quantity=1, equipped=False))

        # Save player data
        self.data_manager.save_data()

        # Create result embed with tool information
        embed = discord.Embed(
            title=f"🔍 Gathering Results: {self.selected_category}",
            description=f"You gathered {len(materials)} materials!",
            color=discord.Color.green())

        # Add tool information to results
        if best_tool:
            tool_name, tool_efficiency = best_tool
            embed.add_field(
                name="🧰 Tool Used",
                value=f"{tool_name}\nEfficiency Bonus: {tool_efficiency:.1f}x",
                inline=False
            )
        else:
            embed.add_field(
                name="🧰 Tool Used",
                value="No tool equipped\nConsider equipping a tool for better results!",
                inline=False
            )

        # Group materials by name, tracking counts and actual values
        material_data = {}
        for material in materials:
            if material.name in material_data:
                material_data[material.name]["count"] += 1
                material_data[material.name]["total_value"] += material.value
            else:
                material_data[material.name] = {
                    "count": 1,
                    "total_value": material.value,
                    "value_per_unit": material.value
                }

        # Add each material to the embed
        for name, data in material_data.items():
            embed.add_field(name=f"{name} x{data['count']}",
                            value=f"Value: {data['total_value']} gold",
                            inline=True)

        # Also give some experience for gathering
        base_xp = 10 + (self.player.class_level // 5
                        )  # Use class_level instead of level
        total_xp = base_xp * len(materials)
        exp_result = self.player.add_exp(total_xp, data_manager=self.data_manager)

        # Create XP display with event multipliers
        xp_display = f"+{total_xp} XP"
        if exp_result["event_multiplier"] > 1.0:
            adjusted_xp = exp_result["adjusted_exp"]
            event_name = exp_result["event_name"]
            xp_display = f"{total_xp} → {adjusted_xp} XP (🎉 {event_name} {exp_result['event_multiplier']}x!)"

        embed.add_field(name="Experience Gained",
                        value=xp_display +
                        (" (Level Up!)" if exp_result["leveled_up"] else ""),
                        inline=False)

        # Send the result without replacing the view to avoid errors
        await interaction.response.edit_message(embed=embed, view=None)

        # Create a fresh gathering view for continued use
        fresh_embed = discord.Embed(
            title="🔍 Gathering Materials",
            description="Select a gathering type to begin collecting materials for crafting.",
            color=discord.Color.green())

        new_view = GatheringView(self.player, self.data_manager)
        await interaction.followup.send(embed=fresh_embed, view=new_view)


async def materials_command(ctx, data_manager: DataManager):
    """View the materials encyclopedia"""
    player = data_manager.get_player(ctx.author.id)

    view = MaterialsView(player, data_manager)
    embed = view.create_materials_embed()

    await ctx.send(embed=embed, view=view)


class GatheringToolsView(View):

    def __init__(self, player_data: PlayerData, data_manager: DataManager):
        super().__init__(timeout=120)
        self.player = player_data
        self.data_manager = data_manager
        self.selected_category = None

        # Add category selection
        self.add_category_select()

        # Add back button
        back_button = Button(label="Back",
                             style=discord.ButtonStyle.secondary,
                             emoji="↩️")
        back_button.callback = self.back_callback
        self.add_item(back_button)

        # Tool selection will be added after category is selected
        self.tool_select = None

    def add_category_select(self):
        """Add dropdown for gathering tool categories"""
        select = Select(
            placeholder="Select Tool Category",
            options=[
                discord.SelectOption(
                    label=category,
                    description=f"Equip tools for {category.lower()}",
                    emoji=self.get_category_emoji(category))
                for category in GATHERING_TOOLS.keys()
            ])
        select.callback = self.category_callback
        self.add_item(select)

    def get_category_emoji(self, category: str) -> str:
        """Get emoji for gathering category"""
        emojis = {
            "Mining": "⛏️",
            "Foraging": "🪓",
            "Herbs": "🌿",
            "Hunting": "🔪",
            "Magical": "✨"
        }
        return emojis.get(category, "🧰")

    async def category_callback(self, interaction: discord.Interaction):
        """Handle category selection"""
        self.selected_category = interaction.data["values"][0]

        # Clear old tool selection if it exists
        if self.tool_select:
            self.remove_item(self.tool_select)
            self.tool_select = None

        # Get player's tools for this category
        tools = self.get_player_tools(self.selected_category)

        if not tools:
            embed = discord.Embed(
                title=
                f"{self.get_category_emoji(self.selected_category)} {self.selected_category} Tools",
                description=
                f"You don't have any {self.selected_category.lower()} tools in your inventory. Visit the shop or craft some tools first!",
                color=discord.Color.orange())
            await interaction.response.edit_message(embed=embed, view=self)
            return

        # Create tool options with unique values
        tool_options = []
        seen_tools = set()
        
        # Add unique tools to options
        for tool_name, efficiency in tools:
            if tool_name not in seen_tools:
                seen_tools.add(tool_name)
                tool_options.append(discord.SelectOption(
                    label=tool_name,
                    description=f"Efficiency: {efficiency:.1f}x",
                    value=tool_name,
                    default=tool_name == self.player.equipped_gathering_tools.get(self.selected_category)
                ))
        
        # Add "None" option to unequip
        tool_options.append(discord.SelectOption(
            label="None (Unequip)",
            description="Gather without a tool",
            value="none",
            default=self.player.equipped_gathering_tools.get(self.selected_category) is None
        ))

        # Create the dropdown with unique options
        self.tool_select = Select(
            placeholder=f"Select a {self.selected_category} Tool to Equip",
            options=tool_options
        )
        self.tool_select.callback = self.tool_callback
        self.add_item(self.tool_select)

        # Show current equipment status
        embed = discord.Embed(
            title=
            f"{self.get_category_emoji(self.selected_category)} {self.selected_category} Tools",
            description=
            f"Select a tool to equip for {self.selected_category.lower()} activities.",
            color=discord.Color.blue())

        # Add currently equipped tool info
        currently_equipped = self.player.equipped_gathering_tools.get(
            self.selected_category)
        if currently_equipped:
            embed.add_field(name="Currently Equipped",
                            value=f"{currently_equipped}",
                            inline=False)
        else:
            embed.add_field(name="Currently Equipped",
                            value="None",
                            inline=False)

        await interaction.response.edit_message(embed=embed, view=self)

    def get_player_tools(self, category: str) -> List[tuple]:
        """Get all player's tools for a category with their efficiencies"""
        tools = []

        for inv_item in self.player.inventory:
            # Skip if not an item
            if not hasattr(inv_item, 'item') or not hasattr(inv_item.item, 'name'):
                continue

            tool_name = inv_item.item.name
            item_type = getattr(inv_item.item, 'item_type', '')
            
            # Check if this is a tool by item_type or name patterns
            is_tool = False
            efficiency = 1.0
            level_req = 1
            
            # Check if item_type indicates it's a tool
            if item_type == 'tool':
                is_tool = True
                efficiency = self.get_tool_efficiency_simple(tool_name, category)
                level_req = getattr(inv_item.item, 'level_req', 1)
            else:
                # Check name patterns for tools
                tool_keywords = {
                    "Mining": ["Pickaxe", "Drill", "Excavator", "Mining"],
                    "Foraging": ["Axe", "Saw", "Harvester", "Logging"],
                    "Herbs": ["Sickle", "Herb", "Botanist"],
                    "Hunting": ["Bow", "Trap", "Snare", "Hunter"],
                    "Magical": ["Wand", "Essence", "Arcane", "Staff"]
                }
                
                keywords = tool_keywords.get(category, [])
                if any(keyword in tool_name for keyword in keywords):
                    is_tool = True
                    efficiency = self.get_tool_efficiency_simple(tool_name, category)
                    level_req = getattr(inv_item.item, 'level_req', 1)
            
            # Add tool if it's valid and player meets requirements
            if is_tool and efficiency > 1.0 and self.player.class_level >= level_req:
                tools.append((tool_name, efficiency))

        # Sort by efficiency (highest first)
        return sorted(tools, key=lambda x: x[1], reverse=True)

    def get_tool_efficiency_simple(self, tool_name: str, category: str) -> float:
        """Get efficiency for a tool using simplified logic"""
        # Tier mapping based on common material names
        tier_efficiency = {
            "Copper": 1.2, "Iron": 1.5, "Steel": 1.8, "Mithril": 2.1,
            "Adamantite": 2.5, "Runite": 3.0, "Dragon": 3.5, "Crystal": 4.0,
            "Divine": 5.0, "Apprentice": 1.2, "Journeyman": 1.5, "Adept": 1.8,
            "Master": 2.1, "Archmagus": 2.5, "Basic": 1.1, "Reinforced": 2.2,
            "Enchanted": 2.5, "Titanium": 2.2, "Celestial": 4.0, "Ethereal": 5.0,
            "Void": 7.0
        }
        
        # Check for tier keywords in tool name
        for tier, efficiency in tier_efficiency.items():
            if tier in tool_name:
                return efficiency
        
        # Default efficiency for any tool
        return 1.2

    def get_tool_efficiency(self, tool_name: str, category: str) -> float:
        """Get the efficiency for a specific tool"""
        # First check standard tool patterns (e.g., "Copper Pickaxe")
        for tool_type in GATHERING_TOOLS.get(category, {}).get("Tool Types", []):
            if tool_type in tool_name:
                # Extract the tier name (e.g., "Copper" from "Copper Pickaxe")
                tier_name = tool_name.replace(f" {tool_type}", "")
                
                # Find the efficiency for this tier
                for tier in GATHERING_TOOLS.get(category, {}).get("Tiers", []):
                    if tier["name"] == tier_name:
                        return tier.get("efficiency", 1.0)
        
        # Check crafting system tool patterns (e.g., "Iron Mining Kit", "Steel Excavator")
        from crafting_system import CRAFTING_CATEGORIES
        if "Tools" in CRAFTING_CATEGORIES:
            tools_category = CRAFTING_CATEGORIES["Tools"]["types"]
            
            # Map category to crafting tool type
            category_mapping = {
                "Mining": "Mining Tools",
                "Foraging": "Foraging Tools", 
                "Herbs": "Herb Tools",
                "Hunting": "Hunting Tools",
                "Magical": "Magical Tools"
            }
            
            craft_type = category_mapping.get(category)
            if craft_type and craft_type in tools_category:
                products = tools_category[craft_type].get("products", [])
                for i, product in enumerate(products):
                    if product in tool_name:
                        # Calculate efficiency based on tier (higher index = better tool)
                        base_efficiency = 1.0 + (i * 0.3)  # Each tier adds 30% efficiency
                        return base_efficiency
        
        return 1.0  # Default efficiency if not found

    def get_tool_level_requirement(self, tool_name: str, category: str) -> int:
        """Get the level requirement for a specific tool"""
        # First check standard tool patterns
        for tool_type in GATHERING_TOOLS.get(category, {}).get("Tool Types", []):
            if tool_type in tool_name:
                # Extract the tier name (e.g., "Copper" from "Copper Pickaxe")
                tier_name = tool_name.replace(f" {tool_type}", "")
                
                # Find the level requirement for this tier
                for tier in GATHERING_TOOLS.get(category, {}).get("Tiers", []):
                    if tier["name"] == tier_name:
                        return tier.get("level_req", 1)
        
        # Check crafting system tool patterns
        from crafting_system import CRAFTING_CATEGORIES
        if "Tools" in CRAFTING_CATEGORIES:
            tools_category = CRAFTING_CATEGORIES["Tools"]["types"]
            
            # Map category to crafting tool type
            category_mapping = {
                "Mining": "Mining Tools",
                "Foraging": "Foraging Tools",
                "Herbs": "Herb Tools", 
                "Hunting": "Hunting Tools",
                "Magical": "Magical Tools"
            }
            
            craft_type = category_mapping.get(category)
            if craft_type and craft_type in tools_category:
                products = tools_category[craft_type].get("products", [])
                level_ranges = tools_category[craft_type].get("level_ranges", [])
                
                for i, product in enumerate(products):
                    if product in tool_name:
                        if i < len(level_ranges):
                            return level_ranges[i][0]  # Return minimum level for this tier
        
        return 1  # Default to level 1 if not found

    async def tool_callback(self, interaction: discord.Interaction):
        """Handle tool selection"""
        if not interaction.data or "values" not in interaction.data:
            await interaction.response.send_message("❌ Invalid selection.", ephemeral=True)
            return
            
        selected_tool = interaction.data["values"][0]

        # Handle unequip option
        if selected_tool == "none":
            if self.selected_category:
                self.player.equipped_gathering_tools[self.selected_category] = None

                embed = discord.Embed(
                    title=
                    f"{self.get_category_emoji(self.selected_category)} Tool Unequipped",
                    description=
                    f"You have unequipped your {self.selected_category.lower()} tool.",
                    color=discord.Color.green())
        else:
            # Check if player meets level requirement for this tool
            level_req = self.get_tool_level_requirement(selected_tool, self.selected_category or "")
            if level_req > self.player.class_level:
                await interaction.response.send_message(
                    f"❌ You need to be level {level_req} to equip {selected_tool}. "
                    f"You are currently level {self.player.class_level}.", 
                    ephemeral=True)
                return

            # Equip the selected tool
            if self.selected_category:
                self.player.equipped_gathering_tools[self.selected_category] = selected_tool

                # Get tool efficiency for display
                efficiency = 1.0
                for tool_name, eff in self.get_player_tools(self.selected_category):
                    if tool_name == selected_tool:
                        efficiency = eff
                        break

                embed = discord.Embed(
                    title=
                    f"{self.get_category_emoji(self.selected_category)} Tool Equipped",
                    description=
                    f"You have equipped **{selected_tool}** (Efficiency: {efficiency:.1f}x)",
                    color=discord.Color.green())
            else:
                embed = discord.Embed(
                    title="❌ Error",
                    description="No category selected.",
                    color=discord.Color.red())

        # Save player data
        self.data_manager.save_data()

        # Update UI
        await interaction.response.edit_message(embed=embed, view=self)

    async def back_callback(self, interaction: discord.Interaction):
        """Handle back button"""
        embed = discord.Embed(
            title="🧰 Gathering Tools",
            description="Here are your currently equipped gathering tools:",
            color=discord.Color.blue())

        # List all equipped tools
        for category, tool_name in self.player.equipped_gathering_tools.items(
        ):
            if tool_name:
                embed.add_field(
                    name=f"{self.get_category_emoji(category)} {category}",
                    value=tool_name,
                    inline=True)
            else:
                embed.add_field(
                    name=f"{self.get_category_emoji(category)} {category}",
                    value="None",
                    inline=True)

        await interaction.response.edit_message(embed=embed, view=None)
        self.stop()


async def gather_command(ctx, data_manager: DataManager):
    """Gather materials for crafting"""
    player = data_manager.get_player(ctx.author.id)

    view = GatheringView(player, data_manager)

    embed = discord.Embed(
        title="🔍 Gathering Materials",
        description=
        "Select a gathering type to begin collecting materials for crafting.",
        color=discord.Color.green())

    await ctx.send(embed=embed, view=view)


async def tools_command(ctx, data_manager: DataManager):
    """Manage your gathering tools"""
    player = data_manager.get_player(ctx.author.id)

    # Check if player has started the game
    if not player.class_name:
        await ctx.send(
            "❌ You haven't started your adventure yet! Use `!start` to choose a class."
        )
        return

    # Create and send the tools view
    view = GatheringToolsView(player, data_manager)

    embed = discord.Embed(
        title="🧰 Gathering Tools",
        description=
        "Equip tools to improve your gathering efficiency.\nSelect a category to see your available tools.",
        color=discord.Color.blue())

    # Add information about currently equipped tools
    equipped_tools_text = ""
    for category, tool_name in player.equipped_gathering_tools.items():
        emoji = view.get_category_emoji(category)
        equipped_tools_text += f"{emoji} **{category}:** {tool_name or 'None'}\n"

    if equipped_tools_text:
        embed.add_field(name="Currently Equipped Tools",
                        value=equipped_tools_text,
                        inline=False)

    await ctx.send(embed=embed, view=view)
