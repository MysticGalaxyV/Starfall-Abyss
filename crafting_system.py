import discord
from discord.ui import Button, View, Select
import random
import time
import asyncio
from typing import Dict, List, Optional, Any, Union, Tuple
from data_models import DataManager, PlayerData, Item, InventoryItem
from materials import MATERIAL_CATEGORIES, MATERIAL_RARITIES

# Crafting categories and patterns
CRAFTING_CATEGORIES = {
    "Weapons": {
        "description": "Craft weapons for combat",
        "types": {
            "Swords": {
                "materials": {
                    "Mining": 3,    # Requires 3 mining materials
                    "Foraging": 1,  # Requires 1 foraging material
                    "Monster Parts": 1  # Requires 1 monster part
                },
                "stat_focus": ["strength", "critical_chance"],
                "products": [
                    "Short Sword", "Long Sword", "Broadsword", "Claymore", "Great Sword", "Rune Blade", 
                    "Dragon Sword", "Crystal Sword", "Void Blade", "Ethereal Cleaver", "Divine Sword"
                ],
                "level_ranges": [
                    (1, 20), (15, 40), (35, 60), (55, 80), (75, 100), (95, 150), 
                    (140, 300), (280, 500), (480, 700), (680, 900), (880, 1000)
                ]
            },
            "Axes": {
                "materials": {
                    "Mining": 4,    # Requires 4 mining materials
                    "Foraging": 1,  # Requires 1 foraging material
                    "Monster Parts": 1  # Requires 1 monster part
                },
                "stat_focus": ["strength", "critical_damage"],
                "products": [
                    "Hand Axe", "Battle Axe", "War Axe", "Great Axe", "Double-Bladed Axe", "Runic Axe", 
                    "Dragon Axe", "Crystal Cleaver", "Void Axe", "Ethereal Hewer", "Divine Axe"
                ],
                "level_ranges": [
                    (1, 20), (15, 40), (35, 60), (55, 80), (75, 100), (95, 150), 
                    (140, 300), (280, 500), (480, 700), (680, 900), (880, 1000)
                ]
            },
            "Maces": {
                "materials": {
                    "Mining": 5,    # Requires 5 mining materials
                    "Monster Parts": 1  # Requires 1 monster part
                },
                "stat_focus": ["strength", "defense"],
                "products": [
                    "Club", "Mace", "Morning Star", "War Hammer", "Battle Hammer", "Runic Maul", 
                    "Dragon Mace", "Crystal Crusher", "Void Hammer", "Ethereal Mace", "Divine Hammer"
                ],
                "level_ranges": [
                    (1, 20), (15, 40), (35, 60), (55, 80), (75, 100), (95, 150), 
                    (140, 300), (280, 500), (480, 700), (680, 900), (880, 1000)
                ]
            },
            "Daggers": {
                "materials": {
                    "Mining": 2,    # Requires 2 mining materials
                    "Monster Parts": 1  # Requires 1 monster part
                },
                "stat_focus": ["dexterity", "critical_chance"],
                "products": [
                    "Dagger", "Dirk", "Stiletto", "Shadow Blade", "Assassin's Blade", "Runic Dagger", 
                    "Dragon Fang", "Crystal Dagger", "Void Shiv", "Ethereal Dagger", "Divine Stiletto"
                ],
                "level_ranges": [
                    (1, 20), (15, 40), (35, 60), (55, 80), (75, 100), (95, 150), 
                    (140, 300), (280, 500), (480, 700), (680, 900), (880, 1000)
                ]
            },
            "Bows": {
                "materials": {
                    "Foraging": 3,  # Requires 3 foraging materials
                    "Monster Parts": 2  # Requires 2 monster parts
                },
                "stat_focus": ["dexterity", "accuracy"],
                "products": [
                    "Short Bow", "Long Bow", "Recurve Bow", "Composite Bow", "Hunter's Bow", "Runic Bow", 
                    "Dragon Bow", "Crystal Arc", "Void Bow", "Ethereal Bow", "Divine Arc"
                ],
                "level_ranges": [
                    (1, 20), (15, 40), (35, 60), (55, 80), (75, 100), (95, 150), 
                    (140, 300), (280, 500), (480, 700), (680, 900), (880, 1000)
                ]
            },
            "Staves": {
                "materials": {
                    "Foraging": 2,  # Requires 2 foraging materials
                    "Magical": 3,   # Requires 3 magical materials
                    "Gems": 1       # Requires 1 gem
                },
                "stat_focus": ["intelligence", "magical_power"],
                "products": [
                    "Wooden Staff", "Apprentice Staff", "Wizard's Staff", "Mage Staff", "Archmage Staff", "Runic Staff", 
                    "Dragon Staff", "Crystal Staff", "Void Staff", "Ethereal Staff", "Divine Staff"
                ],
                "level_ranges": [
                    (1, 20), (15, 40), (35, 60), (55, 80), (75, 100), (95, 150), 
                    (140, 300), (280, 500), (480, 700), (680, 900), (880, 1000)
                ]
            }
        }
    },
    "Armor": {
        "description": "Craft protective armor and shields",
        "types": {
            "Helmets": {
                "materials": {
                    "Mining": 3,    # Requires 3 mining materials
                    "Monster Parts": 1  # Requires 1 monster part
                },
                "stat_focus": ["defense", "health"],
                "products": [
                    "Leather Cap", "Iron Helm", "Steel Helmet", "Mithril Helm", "Adamantite Helmet", "Rune Helmet", 
                    "Dragon Helm", "Crystal Crown", "Void Helmet", "Ethereal Helm", "Divine Crown"
                ],
                "level_ranges": [
                    (1, 20), (15, 40), (35, 60), (55, 80), (75, 100), (95, 150), 
                    (140, 300), (280, 500), (480, 700), (680, 900), (880, 1000)
                ]
            },
            "Chestplates": {
                "materials": {
                    "Mining": 5,    # Requires 5 mining materials
                    "Monster Parts": 2,  # Requires 2 monster parts
                    "Fabrics": 1    # Requires 1 fabric
                },
                "stat_focus": ["defense", "health"],
                "products": [
                    "Leather Tunic", "Iron Chestplate", "Steel Breastplate", "Mithril Plate", "Adamantite Armor", "Rune Chestplate", 
                    "Dragon Plate", "Crystal Breastplate", "Void Armor", "Ethereal Plate", "Divine Breastplate"
                ],
                "level_ranges": [
                    (1, 20), (15, 40), (35, 60), (55, 80), (75, 100), (95, 150), 
                    (140, 300), (280, 500), (480, 700), (680, 900), (880, 1000)
                ]
            },
            "Leggings": {
                "materials": {
                    "Mining": 4,    # Requires 4 mining materials
                    "Monster Parts": 1,  # Requires 1 monster part
                    "Fabrics": 1    # Requires 1 fabric
                },
                "stat_focus": ["defense", "speed"],
                "products": [
                    "Leather Pants", "Iron Greaves", "Steel Leggings", "Mithril Legs", "Adamantite Leggings", "Rune Greaves", 
                    "Dragon Legs", "Crystal Leggings", "Void Greaves", "Ethereal Leggings", "Divine Greaves"
                ],
                "level_ranges": [
                    (1, 20), (15, 40), (35, 60), (55, 80), (75, 100), (95, 150), 
                    (140, 300), (280, 500), (480, 700), (680, 900), (880, 1000)
                ]
            },
            "Boots": {
                "materials": {
                    "Mining": 2,    # Requires 2 mining materials
                    "Monster Parts": 1,  # Requires 1 monster part
                    "Fabrics": 1    # Requires 1 fabric
                },
                "stat_focus": ["speed", "defense"],
                "products": [
                    "Leather Boots", "Iron Boots", "Steel Sabatons", "Mithril Treads", "Adamantite Boots", "Rune Sabatons", 
                    "Dragon Treads", "Crystal Boots", "Void Sabatons", "Ethereal Boots", "Divine Treads"
                ],
                "level_ranges": [
                    (1, 20), (15, 40), (35, 60), (55, 80), (75, 100), (95, 150), 
                    (140, 300), (280, 500), (480, 700), (680, 900), (880, 1000)
                ]
            },
            "Shields": {
                "materials": {
                    "Mining": 4,    # Requires 4 mining materials
                    "Foraging": 1   # Requires 1 foraging material
                },
                "stat_focus": ["defense", "block_chance"],
                "products": [
                    "Wooden Shield", "Iron Buckler", "Steel Shield", "Mithril Ward", "Adamantite Shield", "Rune Defender", 
                    "Dragon Shield", "Crystal Bulwark", "Void Shield", "Ethereal Aegis", "Divine Protector"
                ],
                "level_ranges": [
                    (1, 20), (15, 40), (35, 60), (55, 80), (75, 100), (95, 150), 
                    (140, 300), (280, 500), (480, 700), (680, 900), (880, 1000)
                ]
            },
            "Robes": {
                "materials": {
                    "Fabrics": 4,    # Requires 4 fabric materials
                    "Magical": 2,    # Requires 2 magical materials
                    "Gems": 1        # Requires 1 gem
                },
                "stat_focus": ["magical_defense", "intelligence"],
                "products": [
                    "Apprentice Robe", "Magus Robe", "Enchanted Vestment", "Arcane Robe", "Astral Garment", "Runic Vestment", 
                    "Dragon Silk Robe", "Crystal Robe", "Void Garb", "Ethereal Robe", "Divine Vestment"
                ],
                "level_ranges": [
                    (1, 20), (15, 40), (35, 60), (55, 80), (75, 100), (95, 150), 
                    (140, 300), (280, 500), (480, 700), (680, 900), (880, 1000)
                ]
            }
        }
    },
    "Accessories": {
        "description": "Craft jewelry and magical trinkets",
        "types": {
            "Rings": {
                "materials": {
                    "Mining": 1,    # Requires 1 mining material
                    "Gems": 1,      # Requires 1 gem
                    "Magical": 1    # Requires 1 magical material
                },
                "stat_focus": ["magical_power", "critical_chance"],
                "products": [
                    "Copper Ring", "Silver Band", "Gold Ring", "Mithril Ring", "Enchanted Band", "Runic Ring", 
                    "Dragon Signet", "Crystal Loop", "Void Ring", "Ethereal Band", "Divine Ring"
                ],
                "level_ranges": [
                    (1, 20), (15, 40), (35, 60), (55, 80), (75, 100), (95, 150), 
                    (140, 300), (280, 500), (480, 700), (680, 900), (880, 1000)
                ]
            },
            "Necklaces": {
                "materials": {
                    "Mining": 1,    # Requires 1 mining material
                    "Gems": 2,      # Requires 2 gems
                    "Magical": 1    # Requires 1 magical material
                },
                "stat_focus": ["all_stats", "magical_resistance"],
                "products": [
                    "Copper Pendant", "Silver Amulet", "Gold Necklace", "Mithril Collar", "Enchanted Pendant", "Runic Amulet", 
                    "Dragon Torc", "Crystal Necklace", "Void Choker", "Ethereal Pendant", "Divine Amulet"
                ],
                "level_ranges": [
                    (1, 20), (15, 40), (35, 60), (55, 80), (75, 100), (95, 150), 
                    (140, 300), (280, 500), (480, 700), (680, 900), (880, 1000)
                ]
            },
            "Belts": {
                "materials": {
                    "Monster Parts": 2,  # Requires 2 monster parts
                    "Fabrics": 1,        # Requires 1 fabric
                    "Mining": 1          # Requires 1 mining material
                },
                "stat_focus": ["strength", "carry_capacity"],
                "products": [
                    "Leather Belt", "Reinforced Belt", "Warrior's Girdle", "Mithril Belt", "Power Sash", "Runic Belt", 
                    "Dragon Scale Belt", "Crystal Girdle", "Void Belt", "Ethereal Sash", "Divine Cincture"
                ],
                "level_ranges": [
                    (1, 20), (15, 40), (35, 60), (55, 80), (75, 100), (95, 150), 
                    (140, 300), (280, 500), (480, 700), (680, 900), (880, 1000)
                ]
            },
            "Earrings": {
                "materials": {
                    "Mining": 1,    # Requires 1 mining material
                    "Gems": 1,      # Requires 1 gem
                    "Magical": 1    # Requires 1 magical material
                },
                "stat_focus": ["intelligence", "magical_resistance"],
                "products": [
                    "Copper Studs", "Silver Earrings", "Gold Hoops", "Mithril Earrings", "Enchanted Studs", "Runic Earrings", 
                    "Dragon Ear Cuffs", "Crystal Danglers", "Void Earrings", "Ethereal Studs", "Divine Earrings"
                ],
                "level_ranges": [
                    (1, 20), (15, 40), (35, 60), (55, 80), (75, 100), (95, 150), 
                    (140, 300), (280, 500), (480, 700), (680, 900), (880, 1000)
                ]
            },
            "Bracelets": {
                "materials": {
                    "Mining": 2,    # Requires 2 mining materials
                    "Gems": 1,      # Requires 1 gem
                    "Magical": 1    # Requires 1 magical material
                },
                "stat_focus": ["dexterity", "magical_power"],
                "products": [
                    "Copper Bracelet", "Silver Wristband", "Gold Bangle", "Mithril Bracelet", "Enchanted Band", "Runic Bracelet", 
                    "Dragon Wristguard", "Crystal Bangle", "Void Bracelet", "Ethereal Wristband", "Divine Armlet"
                ],
                "level_ranges": [
                    (1, 20), (15, 40), (35, 60), (55, 80), (75, 100), (95, 150), 
                    (140, 300), (280, 500), (480, 700), (680, 900), (880, 1000)
                ]
            }
        }
    },
    "Potions": {
        "description": "Craft potions and elixirs",
        "types": {
            "Health Potions": {
                "materials": {
                    "Herbs": 3,          # Requires 3 herbs
                    "Monster Parts": 1   # Requires 1 monster part
                },
                "stat_focus": ["healing"],
                "products": [
                    "Minor Healing Potion", "Healing Potion", "Greater Healing Potion", "Superior Healing Potion", "Master Healing Potion", 
                    "Runic Health Elixir", "Dragon Blood Potion", "Crystal Vitality", "Void Restoration", "Ethereal Healing", "Divine Elixir"
                ],
                "level_ranges": [
                    (1, 20), (15, 40), (35, 60), (55, 80), (75, 100), (95, 150), 
                    (140, 300), (280, 500), (480, 700), (680, 900), (880, 1000)
                ]
            },
            "Mana Potions": {
                "materials": {
                    "Herbs": 2,         # Requires 2 herbs
                    "Magical": 2        # Requires 2 magical materials
                },
                "stat_focus": ["mana_restoration"],
                "products": [
                    "Minor Mana Potion", "Mana Potion", "Greater Mana Potion", "Superior Mana Potion", "Master Mana Potion", 
                    "Runic Mana Elixir", "Dragon Magic Potion", "Crystal Energy", "Void Essence", "Ethereal Mana", "Divine Mana"
                ],
                "level_ranges": [
                    (1, 20), (15, 40), (35, 60), (55, 80), (75, 100), (95, 150), 
                    (140, 300), (280, 500), (480, 700), (680, 900), (880, 1000)
                ]
            },
            "Stat Potions": {
                "materials": {
                    "Herbs": 2,         # Requires 2 herbs
                    "Monster Parts": 1,  # Requires 1 monster part
                    "Magical": 1        # Requires 1 magical material
                },
                "stat_focus": ["temporary_stats"],
                "products": [
                    "Minor Strength Potion", "Dexterity Potion", "Intelligence Potion", "Superior Attribute Elixir", "Master Stat Potion", 
                    "Runic Enhancement", "Dragon Might Potion", "Crystal Perfection", "Void Power", "Ethereal Enhancement", "Divine Blessing"
                ],
                "level_ranges": [
                    (1, 20), (15, 40), (35, 60), (55, 80), (75, 100), (95, 150), 
                    (140, 300), (280, 500), (480, 700), (680, 900), (880, 1000)
                ]
            },
            "Resistance Potions": {
                "materials": {
                    "Herbs": 2,         # Requires 2 herbs
                    "Elemental": 2      # Requires 2 elemental materials
                },
                "stat_focus": ["elemental_resistance"],
                "products": [
                    "Minor Fire Resist", "Frost Protection", "Lightning Ward", "Nature Shield", "Elemental Barrier", 
                    "Runic Resistance", "Dragon Scale Elixir", "Crystal Protection", "Void Shield", "Ethereal Warding", "Divine Protection"
                ],
                "level_ranges": [
                    (1, 20), (15, 40), (35, 60), (55, 80), (75, 100), (95, 150), 
                    (140, 300), (280, 500), (480, 700), (680, 900), (880, 1000)
                ]
            },
            "Utility Potions": {
                "materials": {
                    "Herbs": 2,         # Requires 2 herbs
                    "Magical": 1,       # Requires 1 magical material
                    "Gems": 1           # Requires 1 gem
                },
                "stat_focus": ["special_effects"],
                "products": [
                    "Minor Speed Potion", "Invisibility Elixir", "Water Breathing", "Feather Fall", "Night Vision", 
                    "Runic Utility", "Dragon Aspect", "Crystal Transformation", "Void Walking", "Ethereal Vision", "Divine Omnipotence"
                ],
                "level_ranges": [
                    (1, 20), (15, 40), (35, 60), (55, 80), (75, 100), (95, 150), 
                    (140, 300), (280, 500), (480, 700), (680, 900), (880, 1000)
                ]
            },
            "Battle Consumables": {
                "materials": {
                    "Monster Parts": 2,  # Requires 2 monster parts
                    "Magical": 2,        # Requires 2 magical materials
                    "Herbs": 1           # Requires 1 herb
                },
                "stat_focus": ["combat_effects"],
                "products": [
                    "Energy Boost", "Combat Stimulant", "Battle Focus", "Warrior's Vigor", "Champion's Elixir",
                    "Runic Combat Serum", "Dragon's Blood", "Crystal Battle Essence", "Void Combat Fluid", "Ethereal War Potion", "Divine Battle Elixir"
                ],
                "level_ranges": [
                    (1, 20), (15, 40), (35, 60), (55, 80), (75, 100), (95, 150), 
                    (140, 300), (280, 500), (480, 700), (680, 900), (880, 1000)
                ]
            },
            "Tactical Items": {
                "materials": {
                    "Monster Parts": 1,  # Requires 1 monster part
                    "Magical": 1,        # Requires 1 magical material
                    "Mining": 1,         # Requires 1 mining material
                    "Gems": 1            # Requires 1 gem
                },
                "stat_focus": ["battle_strategy"],
                "products": [
                    "Smoke Bomb", "Flash Grenade", "Caltrops", "Healing Orb", "Shield Generator",
                    "Runic Trap", "Dragon Scale Shield", "Crystal Barrier", "Void Anchor", "Ethereal Decoy", "Divine Sanctuary"
                ],
                "level_ranges": [
                    (1, 20), (15, 40), (35, 60), (55, 80), (75, 100), (95, 150), 
                    (140, 300), (280, 500), (480, 700), (680, 900), (880, 1000)
                ]
            }
        }
    },
    "Tools": {
        "description": "Craft utility and gathering tools",
        "types": {
            "Mining Tools": {
                "materials": {
                    "Mining": 3,       # Requires 3 mining materials
                    "Foraging": 1      # Requires 1 foraging material
                },
                "stat_focus": ["gathering_efficiency"],
                "products": [
                    "Copper Pickaxe", "Iron Mining Kit", "Steel Excavator", "Mithril Pickaxe", "Adamantite Mining Set", 
                    "Runic Excavator", "Dragon Pickaxe", "Crystal Mining Tools", "Void Extractor", "Ethereal Pickaxe", "Divine Excavator"
                ],
                "level_ranges": [
                    (1, 20), (15, 40), (35, 60), (55, 80), (75, 100), (95, 150), 
                    (140, 300), (280, 500), (480, 700), (680, 900), (880, 1000)
                ]
            },
            "Foraging Tools": {
                "materials": {
                    "Mining": 2,       # Requires 2 mining materials
                    "Foraging": 2      # Requires 2 foraging materials
                },
                "stat_focus": ["gathering_efficiency"],
                "products": [
                    "Copper Axe", "Iron Logging Kit", "Steel Foraging Set", "Mithril Axe", "Adamantite Harvester", 
                    "Runic Axe", "Dragon Logging Tools", "Crystal Harvester", "Void Axe", "Ethereal Logging Set", "Divine Harvester"
                ],
                "level_ranges": [
                    (1, 20), (15, 40), (35, 60), (55, 80), (75, 100), (95, 150), 
                    (140, 300), (280, 500), (480, 700), (680, 900), (880, 1000)
                ]
            },
            "Fishing Tools": {
                "materials": {
                    "Mining": 1,       # Requires 1 mining material
                    "Foraging": 2,     # Requires 2 foraging materials
                    "Fabrics": 1       # Requires 1 fabric
                },
                "stat_focus": ["gathering_luck"],
                "products": [
                    "Wooden Rod", "Iron Fishing Kit", "Steel Angler Set", "Mithril Rod", "Adamantite Fishing Set", 
                    "Runic Angler", "Dragon Fishing Rod", "Crystal Fishing Kit", "Void Fisher", "Ethereal Angler", "Divine Rod"
                ],
                "level_ranges": [
                    (1, 20), (15, 40), (35, 60), (55, 80), (75, 100), (95, 150), 
                    (140, 300), (280, 500), (480, 700), (680, 900), (880, 1000)
                ]
            },
            "Crafting Tools": {
                "materials": {
                    "Mining": 2,       # Requires 2 mining materials
                    "Foraging": 1,     # Requires 1 foraging material
                    "Fabrics": 1       # Requires 1 fabric
                },
                "stat_focus": ["crafting_quality"],
                "products": [
                    "Basic Toolkit", "Iron Crafting Set", "Steel Craftsman's Kit", "Mithril Tools", "Adamantite Artisan Set", 
                    "Runic Crafter", "Dragon Smith Tools", "Crystal Crafting Set", "Void Artisan Kit", "Ethereal Tools", "Divine Crafting Set"
                ],
                "level_ranges": [
                    (1, 20), (15, 40), (35, 60), (55, 80), (75, 100), (95, 150), 
                    (140, 300), (280, 500), (480, 700), (680, 900), (880, 1000)
                ]
            },
            "Magical Tools": {
                "materials": {
                    "Foraging": 1,     # Requires 1 foraging material
                    "Magical": 2,      # Requires 2 magical materials
                    "Gems": 1          # Requires 1 gem
                },
                "stat_focus": ["enchanting_power"],
                "products": [
                    "Apprentice Wand", "Enchanter's Staff", "Rune Carver", "Mithril Engraver", "Arcane Tools", 
                    "Runic Inscriber", "Dragon Magic Tools", "Crystal Enchanter", "Void Rune Tools", "Ethereal Enchanter", "Divine Runemaker"
                ],
                "level_ranges": [
                    (1, 20), (15, 40), (35, 60), (55, 80), (75, 100), (95, 150), 
                    (140, 300), (280, 500), (480, 700), (680, 900), (880, 1000)
                ]
            }
        }
    },
    "Special Items": {
        "description": "Craft unique and powerful items",
        "types": {
            "Guild Items": {
                "materials": {
                    "Mining": 5,      # Requires 5 mining materials
                    "Foraging": 5,    # Requires 5 foraging materials
                    "Gems": 3,        # Requires 3 gems
                    "Magical": 3      # Requires 3 magical materials
                },
                "stat_focus": ["guild_bonuses"],
                "products": [
                    "Guild Charter", "Guild Banner", "Guild Crest", "Guild Shrine", "Guild Artifact", 
                    "Runic Guild Seal", "Dragon Guild Standard", "Crystal Guild Monument", "Void Guild Relic", "Ethereal Guild Trophy", "Divine Guild Artifact"
                ],
                "level_ranges": [
                    (1, 20), (15, 40), (35, 60), (55, 80), (75, 100), (95, 150), 
                    (140, 300), (280, 500), (480, 700), (680, 900), (880, 1000)
                ]
            },
            "Class Items": {
                "materials": {
                    "Monster Parts": 5,  # Requires 5 monster parts
                    "Magical": 3,        # Requires 3 magical materials
                    "Gems": 1            # Requires 1 gem
                },
                "stat_focus": ["class_specific"],
                "products": [
                    "Novice Class Token", "Adept Class Emblem", "Expert Class Relic", "Master Class Token", "Grandmaster Emblem", 
                    "Runic Class Artifact", "Dragon Class Relic", "Crystal Class Token", "Void Class Emblem", "Ethereal Class Trophy", "Divine Class Relic"
                ],
                "level_ranges": [
                    (1, 20), (15, 40), (35, 60), (55, 80), (75, 100), (95, 150), 
                    (140, 300), (280, 500), (480, 700), (680, 900), (880, 1000)
                ]
            },
            "Quest Items": {
                "materials": {
                    "Monster Parts": 3,  # Requires 3 monster parts
                    "Magical": 3,        # Requires 3 magical materials
                    "Elemental": 2       # Requires 2 elemental materials
                },
                "stat_focus": ["quest_bonuses"],
                "products": [
                    "Quest Compass", "Explorer's Map", "Adventurer's Journal", "Hero's Chronicle", "Legend's Memoir", 
                    "Runic Quest Tome", "Dragon Quest Relic", "Crystal Pathfinder", "Void Explorer's Guide", "Ethereal Chronicle", "Divine Quest Artifact"
                ],
                "level_ranges": [
                    (1, 20), (15, 40), (35, 60), (55, 80), (75, 100), (95, 150), 
                    (140, 300), (280, 500), (480, 700), (680, 900), (880, 1000)
                ]
            },
            "Dungeon Keys": {
                "materials": {
                    "Mining": 2,        # Requires 2 mining materials
                    "Magical": 2,        # Requires 2 magical materials
                    "Elemental": 2       # Requires 2 elemental materials
                },
                "stat_focus": ["dungeon_access"],
                "products": [
                    "Ancient Forest Key", "Forgotten Cave Key", "Cursed Shrine Key", "Abyssal Depths Key", "Infernal Citadel Key", 
                    "Runic Dungeon Key", "Dragon's Lair Key", "Crystal Vault Key", "Void Gate Key", "Ethereal Realm Key", "Divine Domain Key"
                ],
                "level_ranges": [
                    (1, 20), (15, 40), (35, 60), (55, 80), (75, 100), (95, 150), 
                    (140, 300), (280, 500), (480, 700), (680, 900), (880, 1000)
                ]
            }
        }
    }
}

# Define crafting stations that affect crafting quality and success rate
CRAFTING_STATIONS = {
    "Basic Crafting Table": {
        "level_req": 1,
        "quality_bonus": 0,
        "success_bonus": 0,
        "description": "A simple crafting table for basic items."
    },
    "Apprentice's Workbench": {
        "level_req": 25,
        "quality_bonus": 5,
        "success_bonus": 5,
        "description": "A sturdy workbench with improved tools and space."
    },
    "Journeyman's Workshop": {
        "level_req": 50,
        "quality_bonus": 10,
        "success_bonus": 10,
        "description": "A well-equipped workshop with specialized tools."
    },
    "Master Craftsman's Forge": {
        "level_req": 75,
        "quality_bonus": 15,
        "success_bonus": 15,
        "description": "A professional forge with advanced equipment."
    },
    "Artisan's Atelier": {
        "level_req": 100,
        "quality_bonus": 20,
        "success_bonus": 20,
        "description": "An expert's workshop with rare tools and equipment."
    },
    "Runic Forge": {
        "level_req": 150,
        "quality_bonus": 25,
        "success_bonus": 25,
        "description": "A mystical forge infused with runic magic."
    },
    "Dragon's Smithy": {
        "level_req": 250,
        "quality_bonus": 30,
        "success_bonus": 30,
        "description": "A legendary smithy powered by dragon fire."
    },
    "Crystal Workshop": {
        "level_req": 400,
        "quality_bonus": 40,
        "success_bonus": 35,
        "description": "A workshop made of pure crystal that resonates with magic."
    },
    "Void Forge": {
        "level_req": 600,
        "quality_bonus": 50,
        "success_bonus": 40,
        "description": "A mystical forge drawing power from the void."
    },
    "Ethereal Crafting Chamber": {
        "level_req": 800,
        "quality_bonus": 60,
        "success_bonus": 50,
        "description": "A chamber that exists between planes of reality."
    },
    "Divine Creation Nexus": {
        "level_req": 950,
        "quality_bonus": 75,
        "success_bonus": 75,
        "description": "A nexus of creation energies rivaling the power of gods."
    }
}

# Class to track crafting skill progression
class CraftingSkill:
    def __init__(self, category: str = None, level: int = 1, exp: int = 0):
        self.category = category
        self.level = level
        self.exp = exp
        self.max_level = 1000

    def add_exp(self, amount: int) -> bool:
        """Add experience points and handle level ups. Returns True if leveled up."""
        old_level = self.level
        self.exp += amount

        # Calculate exp needed for next level (scales with level)
        while True:
            exp_needed = int(100 * (self.level ** 1.5))
            if self.exp >= exp_needed and self.level < self.max_level:
                self.exp -= exp_needed
                self.level += 1
            else:
                break

        return self.level > old_level

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            "category": self.category,
            "level": self.level,
            "exp": self.exp
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CraftingSkill':
        """Create from dictionary data"""
        return cls(
            category=data.get("category"),
            level=data.get("level", 1),
            exp=data.get("exp", 0)
        )

# Generate a crafted item based on player stats and materials
def generate_crafted_item(player: PlayerData, category: str, type_name: str, product_tier: int, 
                         material_quality: float, crafting_station: str) -> Item:
    """Generate a crafted item based on crafting parameters

    Args:
        player: Player data
        category: Crafting category (e.g., "Weapons")
        type_name: Specific type within category (e.g., "Swords")
        product_tier: Tier of product to craft (0-10 index)
        material_quality: Average quality score of materials (0.0-1.0)
        crafting_station: Name of crafting station used

    Returns:
        The crafted Item
    """
    # Get category and type data
    category_data = CRAFTING_CATEGORIES.get(category, {})
    type_data = category_data.get("types", {}).get(type_name, {})

    # Get product name and level requirement
    products = type_data.get("products", ["Generic Item"])
    level_ranges = type_data.get("level_ranges", [(1, 10)])

    product_name = products[product_tier] if product_tier < len(products) else products[-1]
    level_req = level_ranges[product_tier][0] if product_tier < len(level_ranges) else level_ranges[-1][0]

    # Calculate item value based on tier and quality
    base_value = 100 * (2 ** product_tier)  # Exponential value increase with tier
    quality_multiplier = 1 + material_quality

    # Apply station bonus if any
    station_data = CRAFTING_STATIONS.get(crafting_station, {})
    quality_bonus = station_data.get("quality_bonus", 0) / 100  # Convert percentage to decimal

    # Calculate final value
    value = int(base_value * quality_multiplier * (1 + quality_bonus))

    # Generate item stats based on type, tier, and quality
    stats = {}
    stat_focus = type_data.get("stat_focus", [])

    for stat in stat_focus:
        # Base stat value increases with tier
        base_stat = 5 + (product_tier * 3)

        # Apply quality modifier
        quality_mod = material_quality * 0.5

        # Apply crafting station bonus
        station_mod = quality_bonus

        # Calculate final stat value
        stat_value = int(base_stat * (1 + quality_mod + station_mod))
        stats[stat] = stat_value

    # Determine rarity based on quality
    rarity = "Common"
    if material_quality >= 0.99:
        rarity = "Divine"
    elif material_quality >= 0.95:
        rarity = "Primordial"
    elif material_quality >= 0.9:
        rarity = "Transcendent"
    elif material_quality >= 0.85:
        rarity = "Mythic"
    elif material_quality >= 0.75:
        rarity = "Legendary"
    elif material_quality >= 0.6:
        rarity = "Epic"
    elif material_quality >= 0.45:
        rarity = "Rare"
    elif material_quality >= 0.3:
        rarity = "Uncommon"

    # Generate a description based on item type and stats
    description = f"A {rarity.lower()} quality {product_name.lower()}. "

    if "weapon" in category.lower():
        description += f"Deals damage based on {', '.join(stat_focus)}."
    elif "armor" in category.lower():
        description += f"Provides protection and bonuses to {', '.join(stat_focus)}."
    elif "accessory" in category.lower():
        description += f"Enhances {', '.join(stat_focus)} when equipped."
    elif "potion" in category.lower():
        description += f"A consumable that affects {', '.join(stat_focus)}."
    elif "tool" in category.lower():
        description += f"Improves efficiency in {', '.join(stat_focus)}."
    else:
        description += f"Has special effects related to {', '.join(stat_focus)}."

    # Generate item_id
    import uuid
    item_id = str(uuid.uuid4())

    # Create the item
    item = Item(
        item_id=item_id,
        name=f"{rarity} {product_name}",
        description=description,
        item_type=f"{category}:{type_name}",
        rarity=rarity,
        stats=stats,
        level_req=level_req,
        value=value
    )

    return item

# Calculate success chance based on player level, material quality, and crafting station
def calculate_crafting_success(player_level: int, crafting_skill_level: int, 
                              item_level_req: int, crafting_station: str) -> float:
    """Calculate chance of successful crafting (0.0-1.0)"""
    # Base success chance depends on skill vs. item level
    base_chance = min(0.95, 0.5 + ((crafting_skill_level - item_level_req) / 100))

    # Apply minimum chance of 0.1 (10%)
    base_chance = max(0.1, base_chance)

    # Apply station bonus
    station_data = CRAFTING_STATIONS.get(crafting_station, {})
    success_bonus = station_data.get("success_bonus", 0) / 100  # Convert percentage to decimal

    # Calculate final success chance, capped at 0.99 (99%)
    success_chance = min(0.99, base_chance + success_bonus)

    return success_chance

class CraftingCategoryView(View):
    def __init__(self, player_data: PlayerData, data_manager: DataManager):
        super().__init__(timeout=60)
        self.player = player_data
        self.data_manager = data_manager

        # Add category selector
        self.add_category_select()

    def add_category_select(self):
        """Add dropdown for crafting categories"""
        select = Select(
            placeholder="Select Crafting Category",
            options=[
                discord.SelectOption(label=category, description=data["description"][:100])
                for category, data in CRAFTING_CATEGORIES.items()
            ],
            custom_id="category_select"
        )
        select.callback = self.category_callback
        self.add_item(select)

    async def category_callback(self, interaction: discord.Interaction):
        """Handle category selection"""
        category = interaction.data["values"][0]

        # Create a new view for the selected category
        type_view = CraftingTypeView(self.player, self.data_manager, category)

        # Create embed for the category
        embed = type_view.create_category_embed()

        await interaction.response.edit_message(embed=embed, view=type_view)

class CraftingTypeView(View):
    def __init__(self, player_data: PlayerData, data_manager: DataManager, category: str):
        super().__init__(timeout=60)
        self.player = player_data
        self.data_manager = data_manager
        self.category = category

        # Add type selector
        self.add_type_select()

        # Add back button
        back_button = Button(label="◀️ Back to Categories", custom_id="back", style=discord.ButtonStyle.gray)
        back_button.callback = self.back_callback
        self.add_item(back_button)

    def add_type_select(self):
        """Add dropdown for item types in this category"""
        select = Select(
            placeholder=f"Select {self.category} Type",
            options=[
                discord.SelectOption(label=type_name, description=f"Craft {type_name.lower()}")
                for type_name in CRAFTING_CATEGORIES.get(self.category, {}).get("types", {}).keys()
            ],
            custom_id="type_select"
        )
        select.callback = self.type_callback
        self.add_item(select)

    async def back_callback(self, interaction: discord.Interaction):
        """Handle back button click"""
        category_view = CraftingCategoryView(self.player, self.data_manager)

        embed = discord.Embed(
            title="⚒️ Crafting Workshop",
            description="Select a crafting category to begin creating items.",
            color=discord.Color.gold()
        )

        for category, data in CRAFTING_CATEGORIES.items():
            embed.add_field(
                name=category,
                value=data["description"],
                inline=True
            )

        await interaction.response.edit_message(embed=embed, view=category_view)

    async def type_callback(self, interaction: discord.Interaction):
        """Handle type selection"""
        type_name = interaction.data["values"][0]

        # Create a new view for crafting the selected type
        crafting_view = CraftingItemView(self.player, self.data_manager, self.category, type_name)

        # Create embed for the crafting type
        embed = crafting_view.create_crafting_embed()

        await interaction.response.edit_message(embed=embed, view=crafting_view)

    def create_category_embed(self) -> discord.Embed:
        """Create embed for the selected category"""
        category_data = CRAFTING_CATEGORIES.get(self.category, {})

        embed = discord.Embed(
            title=f"⚒️ {self.category} Crafting",
            description=category_data.get("description", "Craft various items in this category."),
            color=discord.Color.gold()
        )

        for type_name, type_data in category_data.get("types", {}).items():
            # Get information about the type
            products = type_data.get("products", [])
            materials = type_data.get("materials", {})
            level_ranges = type_data.get("level_ranges", [])

            # Only show a few examples of products
            product_examples = products[:3]
            if len(products) > 3:
                product_examples.append("...")
                product_examples.append(products[-1])

            # Show required materials
            material_text = "\n".join([f"• {count}x {mat}" for mat, count in materials.items()])

            # Show level ranges
            level_text = "Level Requirements:\n"
            level_text += f"• Tier 1: {level_ranges[0][0]}\n"
            if len(level_ranges) > 1:
                level_text += f"• Mid Tier: {level_ranges[len(level_ranges)//2][0]}\n"
            level_text += f"• Max Tier: {level_ranges[-1][0]}"

            embed.add_field(
                name=type_name,
                value=f"Examples: {', '.join(product_examples)}\n\nRequired Materials:\n{material_text}\n\n{level_text}",
                inline=False
            )

        return embed

class CraftingItemView(View):
    def __init__(self, player_data: PlayerData, data_manager: DataManager, category: str, type_name: str):
        super().__init__(timeout=180)
        self.player = player_data
        self.data_manager = data_manager
        self.category = category
        self.type_name = type_name
        self.selected_materials = {}
        self.selected_tier = 0
        self.selected_station = "Basic Crafting Table"

        # Find the highest tier the player can craft
        self.max_tier = self.get_max_available_tier()

        # Add tier selector
        self.add_tier_select()

        # Add station selector
        self.add_station_select()

        # Add craft button
        craft_button = Button(
            label="Craft Item", 
            emoji="⚒️", 
            custom_id="craft", 
            style=discord.ButtonStyle.success
        )
        craft_button.callback = self.craft_callback
        self.add_item(craft_button)

        # Add preview button
        preview_button = Button(
            label="Preview Item", 
            emoji="👁️", 
            custom_id="preview", 
            style=discord.ButtonStyle.primary
        )
        preview_button.callback = self.preview_callback
        self.add_item(preview_button)

        # Add back button
        back_button = Button(
            label="Back to Types", 
            emoji="◀️", 
            custom_id="back", 
            style=discord.ButtonStyle.secondary
        )
        back_button.callback = self.back_callback
        self.add_item(back_button)

    def get_max_available_tier(self) -> int:
        """Determine the maximum tier the player can craft based on level"""
        type_data = CRAFTING_CATEGORIES.get(self.category, {}).get("types", {}).get(self.type_name, {})
        level_ranges = type_data.get("level_ranges", [(1, 10)])

        # Find highest tier the player can craft
        max_tier = 0
        for i, (min_level, _) in enumerate(level_ranges):
            if self.player.level >= min_level:
                max_tier = i
            else:
                break

        return max_tier

    def add_tier_select(self):
        """Add dropdown for selecting item tier"""
        type_data = CRAFTING_CATEGORIES.get(self.category, {}).get("types", {}).get(self.type_name, {})
        products = type_data.get("products", ["Item"])
        level_ranges = type_data.get("level_ranges", [(1, 10)])

        # Only show tiers the player can craft
        options = []
        for i in range(min(len(products), self.max_tier + 1)):
            options.append(
                discord.SelectOption(
                    label=products[i],
                    description=f"Level {level_ranges[i][0]}-{level_ranges[i][1]}"
                )
            )

        if not options:
            # Add at least one option if player can't craft anything
            options.append(
                discord.SelectOption(
                    label=products[0],
                    description=f"Level {level_ranges[0][0]}-{level_ranges[0][1]} (Level too low)"
                )
            )

        select = Select(
            placeholder="Select Item Tier",
            options=options,
            custom_id="tier_select"
        )
        select.callback = self.tier_callback
        self.add_item(select)

    def add_station_select(self):
        """Add dropdown for selecting crafting station"""
        # Only show stations the player has access to
        options = []
        for station_name, station_data in CRAFTING_STATIONS.items():
            if self.player.level >= station_data.get("level_req", 1):
                options.append(
                    discord.SelectOption(
                        label=station_name,
                        description=f"+{station_data.get('quality_bonus', 0)}% Quality, +{station_data.get('success_bonus', 0)}% Success"
                    )
                )

        select = Select(
            placeholder="Select Crafting Station",
            options=options,
            custom_id="station_select"
        )
        select.callback = self.station_callback
        self.add_item(select)

    async def tier_callback(self, interaction: discord.Interaction):
        """Handle tier selection"""
        type_data = CRAFTING_CATEGORIES.get(self.category, {}).get("types", {}).get(self.type_name, {})
        products = type_data.get("products", ["Item"])

        selected_name = interaction.data["values"][0]
        self.selected_tier = products.index(selected_name)

        # Update the embed
        embed = self.create_crafting_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    async def station_callback(self, interaction: discord.Interaction):
        """Handle station selection"""
        self.selected_station = interaction.data["values"][0]

        # Update the embed
        embed = self.create_crafting_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    async def back_callback(self, interaction: discord.Interaction):
        """Handle back button click"""
        type_view = CraftingTypeView(self.player, self.data_manager, self.category)

        embed = type_view.create_category_embed()

        await interaction.response.edit_message(embed=embed, view=type_view)

    async def preview_callback(self, interaction: discord.Interaction):
        """Handle preview button click - shows what the crafted item might look like"""
        type_data = CRAFTING_CATEGORIES.get(self.category, {}).get("types", {}).get(self.type_name, {})
        products = type_data.get("products", ["Item"])
        level_ranges = type_data.get("level_ranges", [(1, 10)])
        stat_focus = type_data.get("stat_focus", ["strength"])

        # Check if player meets level requirement
        item_level_req = level_ranges[self.selected_tier][0]
        if self.player.level < item_level_req:
            await interaction.response.send_message(
                f"You need to be level {item_level_req} to see this item!",
                ephemeral=True
            )
            return

        # Create a preview of what the item might look like
        product_name = products[self.selected_tier]
        level_range = level_ranges[self.selected_tier]

        # Generate sample stats based on player level and tier
        sample_stats = {}
        for stat in stat_focus:
            base = 5 + (self.selected_tier * 3)
            variation = random.randint(-2, 2)
            sample_stats[stat] = base + variation

        sample_value = (10 + (self.selected_tier * 5)) * 10

        # Create sample descriptions for different quality levels
        quality_examples = {
            "Common": f"A basic {product_name.lower()} with modest stats.",
            "Uncommon": f"A well-crafted {product_name.lower()} with improved stats.",
            "Rare": f"A finely crafted {product_name.lower()} with excellent stats.",
            "Epic": f"A masterfully crafted {product_name.lower()} with superior stats.",
            "Legendary": f"An exceptional {product_name.lower()} of legendary quality."
        }

        # Create preview embed
        embed = discord.Embed(
            title=f"⚒️ Item Preview: {product_name}",
            description=f"Level Requirement: {level_range[0]}\n\n" +
                       f"Here's a preview of what this item might look like when crafted. " +
                       f"The actual item's stats and quality will depend on your crafting skill " +
                       f"and the materials used.",
            color=discord.Color.gold()
        )

        # Add sample stats
        stats_text = ""
        for stat, value in sample_stats.items():
            stats_text += f"**{stat.capitalize()}:** +{value}\n"

        embed.add_field(
            name="Potential Stats",
            value=stats_text,
            inline=True
        )

        # Add potential qualities
        embed.add_field(
            name="Potential Qualities",
            value="\n".join([f"**{rarity}:** {desc}" for rarity, desc in quality_examples.items()]),
            inline=False
        )

        # Add value range
        embed.add_field(
            name="Estimated Value",
            value=f"💰 {sample_value - 20} - {sample_value + 20} gold",
            inline=False
        )

        # Show required materials
        required_materials = type_data.get("materials", {})
        materials_text = ""
        for category, count in required_materials.items():
            materials_text += f"• {category}: {count}\n"

        embed.add_field(
            name="Required Materials",
            value=materials_text if materials_text else "No materials required",
            inline=False
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def craft_callback(self, interaction: discord.Interaction):
        """Handle craft button click"""
        # Check if materials are available
        type_data = CRAFTING_CATEGORIES.get(self.category, {}).get("types", {}).get(self.type_name, {})
        required_materials = type_data.get("materials", {})
        products = type_data.get("products", ["Item"])
        level_ranges = type_data.get("level_ranges", [(1, 10)])

        # Check if player meets level requirement
        item_level_req = level_ranges[self.selected_tier][0]
        if self.player.level < item_level_req:
            await interaction.response.send_message(
                f"You need to be level {item_level_req} to craft this item!",
                ephemeral=True
            )
            return

        # Check if player has enough materials
        material_counts = {}
        material_quality = 0.0
        total_materials = 0

        # Count materials in inventory by category
        for inv_item in self.player.inventory:
            if "Material:" in inv_item.item.item_type:
                category = inv_item.item.item_type.split(":")[1]
                if category not in material_counts:
                    material_counts[category] = 0
                material_counts[category] += inv_item.quantity

                # Calculate quality based on rarity
                rarity = inv_item.item.rarity
                rarity_value = list(MATERIAL_RARITIES.keys()).index(rarity) / (len(MATERIAL_RARITIES) - 1)
                material_quality += rarity_value * inv_item.quantity
                total_materials += inv_item.quantity

        # Check if all required materials are available
        missing_materials = []
        for category, count in required_materials.items():
            if material_counts.get(category, 0) < count:
                missing_materials.append(f"{category} ({count - material_counts.get(category, 0)} more needed)")

        if missing_materials:
            await interaction.response.send_message(
                f"You don't have enough materials to craft this item! Missing:\n" + 
                "\n".join([f"• {mat}" for mat in missing_materials]),
                ephemeral=True
            )
            return

        # Calculate average material quality
        if total_materials > 0:
            material_quality /= total_materials

        # Get player's crafting skill for this category
        crafting_skill = None

        # Make sure player has crafting_skills attribute
        if not hasattr(self.player, "crafting_skills"):
            self.player.crafting_skills = []

        # Find existing skill or create a new one
        for skill in self.player.crafting_skills:
            if skill.category == self.category:
                crafting_skill = skill
                break

        if not crafting_skill:
            # Create new crafting skill if player doesn't have one for this category
            crafting_skill = CraftingSkill(category=self.category)
            self.player.crafting_skills.append(crafting_skill)

        # Calculate success chance
        success_chance = calculate_crafting_success(
            self.player.level, 
            crafting_skill.level, 
            item_level_req, 
            self.selected_station
        )

        # Determine if crafting is successful
        is_success = random.random() < success_chance

        # Create response embed
        response_embed = discord.Embed(
            title="⚒️ Crafting Results",
            color=discord.Color.green() if is_success else discord.Color.red()
        )

        # Add crafting details to embed
        response_embed.add_field(
            name="Attempted Item",
            value=f"{products[self.selected_tier]}",
            inline=True
        )

        response_embed.add_field(
            name="Crafting Station",
            value=self.selected_station,
            inline=True
        )

        response_embed.add_field(
            name="Success Chance",
            value=f"{int(success_chance * 100)}%",
            inline=True
        )

        # Generate and add the item if successful
        if is_success:
            # Remove materials from inventory
            for category, count in required_materials.items():
                remaining = count
                # Start with lower quality materials first (optimization for player)
                sorted_inv = sorted(
                    [item for item in self.player.inventory if "Material:" + category == item.item.item_type],
                    key=lambda x: list(MATERIAL_RARITIES.keys()).index(x.item.rarity)
                )

                for inv_item in sorted_inv:
                    if remaining <= 0:
                        break

                    if inv_item.quantity <= remaining:
                        remaining -= inv_item.quantity
                        self.player.inventory.remove(inv_item)
                    else:
                        inv_item.quantity -= remaining
                        remaining = 0

            # Generate the crafted item
            crafted_item = generate_crafted_item(
                self.player,
                self.category,
                self.type_name,
                self.selected_tier,
                material_quality,
                self.selected_station
            )

            # Add item to inventory
            self.player.inventory.append(InventoryItem(crafted_item, quantity=1))

            # Save player data
            self.data_manager.save_data()

            # Add item details to embed
            response_embed.description = f"✅ **Success!** You crafted a **{crafted_item.name}**!"

            response_embed.add_field(
                name="Item Description",
                value=crafted_item.description,
                inline=False
            )

            stats_text = "\n".join([f"• {stat.replace('_', ' ').title()}: +{value}" for stat, value in crafted_item.stats.items()])
            response_embed.add_field(
                name="Item Stats",
                value=stats_text or "No stats",
                inline=True
            )

            response_embed.add_field(
                name="Item Value",
                value=f"{crafted_item.value} gold",
                inline=True
            )

            response_embed.add_field(
                name="Required Level",
                value=str(crafted_item.level_req),
                inline=True
            )

            # Add crafting experience
            exp_gained = 10 * (self.selected_tier + 1) * (1 + (0.1 * self.selected_tier))
            level_up = crafting_skill.add_exp(int(exp_gained))

            response_embed.add_field(
                name="Crafting Experience",
                value=f"+{int(exp_gained)} XP" + (" (Level Up!)" if level_up else ""),
                inline=False
            )

            response_embed.set_footer(text=f"Crafting {self.category} - Level {crafting_skill.level}")
        else:
            # Remove half the materials on failure (to create some risk)
            for category, count in required_materials.items():
                wasted = max(1, count // 2)  # At least 1 material is wasted
                remaining = wasted

                sorted_inv = sorted(
                    [item for item in self.player.inventory if "Material:" + category == item.item.item_type],
                    key=lambda x: list(MATERIAL_RARITIES.keys()).index(x.item.rarity)
                )

                for inv_item in sorted_inv:
                    if remaining <= 0:
                        break

                    if inv_item.quantity <= remaining:
                        remaining -= inv_item.quantity
                        self.player.inventory.remove(inv_item)
                    else:
                        inv_item.quantity -= remaining
                        remaining = 0

            # Save player data
            self.data_manager.save_data()

            # Add failure message to embed
            response_embed.description = f"❌ **Failed!** Your attempt to craft a **{products[self.selected_tier]}** was unsuccessful."

            response_embed.add_field(
                name="Materials Lost",
                value="Half of the required materials were wasted in the failed attempt.",
                inline=False
            )

            # Add small amount of crafting experience even on failure
            exp_gained = 5 * (self.selected_tier + 1)
            level_up = crafting_skill.add_exp(int(exp_gained))

            response_embed.add_field(
                name="Crafting Experience",
                value=f"+{int(exp_gained)} XP" + (" (Level Up!)" if level_up else ""),
                inline=False
            )

            response_embed.set_footer(text=f"Crafting {self.category} - Level {crafting_skill.level}")

        # New view for crafting again
        new_view = CraftingItemView(self.player, self.data_manager, self.category, self.type_name)
        await interaction.response.edit_message(embed=response_embed, view=new_view)

    def create_crafting_embed(self) -> discord.Embed:
        """Create embed for crafting interface"""
        type_data = CRAFTING_CATEGORIES.get(self.category, {}).get("types", {}).get(self.type_name, {})
        products = type_data.get("products", ["Item"])
        required_materials = type_data.get("materials", {})
        level_ranges = type_data.get("level_ranges", [(1, 10)])

        # Get the selected product and level range
        product_name = products[self.selected_tier] if self.selected_tier < len(products) else products[0]
        level_range = level_ranges[self.selected_tier] if self.selected_tier < len(level_ranges) else level_ranges[0]

        embed = discord.Embed(
            title=f"⚒️ Craft {product_name}",
            description=f"Crafting a {product_name} (Level {level_range[0]}-{level_range[1]})",
            color=discord.Color.gold()
        )

        # Add required materials section
        materials_text = ""
        player_materials = {}

        # Count materials in inventory by category
        for inv_item in self.player.inventory:
            if "Material:" in inv_item.item.item_type:
                category = inv_item.item.item_type.split(":")[1]
                if category not in player_materials:
                    player_materials[category] = 0
                player_materials[category] += inv_item.quantity

        # Create materials text with current/required counts
        for category, count in required_materials.items():
            have_count = player_materials.get(category, 0)
            emoji = "✅" if have_count >= count else "❌"
            materials_text += f"{emoji} {category}: {have_count}/{count}\n"

        embed.add_field(
            name="Required Materials",
            value=materials_text or "No materials required",
            inline=False
        )

        # Add crafting station info
        station_data = CRAFTING_STATIONS.get(self.selected_station, {})
        station_text = (
            f"**Level Req:** {station_data.get('level_req', 1)}\n"
            f"**Quality Bonus:** +{station_data.get('quality_bonus', 0)}%\n"
            f"**Success Bonus:** +{station_data.get('success_bonus', 0)}%\n"
            f"**Description:** {station_data.get('description', '')}"
        )

        embed.add_field(
            name=f"Crafting Station: {self.selected_station}",
            value=station_text,
            inline=False
        )

        # Get crafting skill level for this category
        skill_level = 1

        # Make sure player has crafting_skills attribute
        if not hasattr(self.player, "crafting_skills"):
            self.player.crafting_skills = []

        # Find existing skill or get default level
        for skill in self.player.crafting_skills:
            if skill.category == self.category:
                skill_level = skill.level
                break

        # Calculate success chance
        success_chance = calculate_crafting_success(
            self.player.level, 
            skill_level, 
            level_range[0], 
            self.selected_station
        )

        # Add crafting details
        craft_details = (
            f"**Player Level:** {self.player.level}\n"
            f"**Crafting Level ({self.category}):** {skill_level}\n"
            f"**Success Chance:** {int(success_chance * 100)}%\n"
            f"**Item Level Requirement:** {level_range[0]}"
        )

        embed.add_field(
            name="Crafting Details",
            value=craft_details,
            inline=False
        )

        return embed

class CraftingEntryView(View):
    def __init__(self, player_data: PlayerData, data_manager: DataManager):
        super().__init__(timeout=60)
        self.player = player_data
        self.data_manager = data_manager

        # Add buttons for main crafting actions
        self.add_buttons()

    def add_buttons(self):
        """Add main crafting options buttons with improved styling"""
        # Craft Items button - Primary action
        craft_button = Button(
            label="Craft Items", 
            emoji="⚒️",
            custom_id="craft",
            style=discord.ButtonStyle.primary
        )
        craft_button.callback = self.craft_callback
        self.add_item(craft_button)

        # Materials Encyclopedia button
        materials_button = Button(
            label="Materials Encyclopedia",
            emoji="📦",
            custom_id="materials",
            style=discord.ButtonStyle.secondary
        )
        materials_button.callback = self.materials_callback
        self.add_item(materials_button)

        # Gather Materials button - Action button
        gather_button = Button(
            label="Gather Materials",
            emoji="🔍",
            custom_id="gather",
            style=discord.ButtonStyle.success
        )
        gather_button.callback = self.gather_callback
        self.add_item(gather_button)

        # Crafting Skills button
        skills_button = Button(
            label="Crafting Skills",
            emoji="📊",
            custom_id="skills",
            style=discord.ButtonStyle.secondary
        )
        skills_button.callback = self.skills_callback
        self.add_item(skills_button)

        # Help button
        help_button = Button(
            label="Help",
            emoji="❓",
            custom_id="craft_help",
            style=discord.ButtonStyle.gray
        )
        help_button.callback = self.help_callback
        self.add_item(help_button)

    async def craft_callback(self, interaction: discord.Interaction):
        """Handle craft button click"""
        category_view = CraftingCategoryView(self.player, self.data_manager)

        embed = discord.Embed(
            title="⚒️ Crafting Workshop",
            description="Select a crafting category to begin creating items.",
            color=discord.Color.gold()
        )

        for category, data in CRAFTING_CATEGORIES.items():
            embed.add_field(
                name=category,
                value=data["description"],
                inline=True
            )

        await interaction.response.edit_message(embed=embed, view=category_view)

    async def materials_callback(self, interaction: discord.Interaction):
        """Handle materials button click"""
        from materials import MaterialsView

        view = MaterialsView(self.player, self.data_manager)
        embed = view.create_materials_embed()

        await interaction.response.edit_message(embed=embed, view=view)

    async def gather_callback(self, interaction: discord.Interaction):
        """Handle gather button click"""
        from materials import GatheringView

        view = GatheringView(self.player, self.data_manager)

        embed = discord.Embed(
            title="🔍 Gathering Materials",
            description="Select a gathering type to begin collecting materials for crafting.",
            color=discord.Color.green()
        )

        await interaction.response.edit_message(embed=embed, view=view)

    async def skills_callback(self, interaction: discord.Interaction):
        """Handle skills button click"""
        embed = discord.Embed(
            title="📊 Crafting Skills",
            description=f"**Your Crafting Skill Levels**",
            color=discord.Color.blue()
        )

        # Ensure player has crafting_skills attribute
        if not hasattr(self.player, "crafting_skills"):
            self.player.crafting_skills = []

        # Check if player has any crafting skills
        if self.player.crafting_skills:
            for skill in self.player.crafting_skills:
                # Calculate exp needed for next level
                exp_needed = int(100 * (skill.level ** 1.5))
                progress = min(1.0, skill.exp / exp_needed)

                # Create progress bar
                bar_length = 20
                filled = int(bar_length * progress)
                progress_bar = "█" * filled + "░" * (bar_length - filled)

                embed.add_field(
                    name=f"{skill.category} (Level {skill.level})",
                    value=f"{progress_bar} {skill.exp}/{exp_needed} XP",
                    inline=False
                )
        else:
            embed.description = "**Your Crafting Skill Levels**\n\nYou haven't developed any crafting skills yet. Start crafting to gain experience!"

        await interaction.response.edit_message(embed=embed, view=self)

    async def help_callback(self, interaction: discord.Interaction):
        """Handle help button click - Shows information about crafting system"""
        embed = discord.Embed(
            title="❓ Crafting System Help",
            description="Guide to the crafting system in Ethereal Ascendancy",
            color=discord.Color.gold()
        )

        embed.add_field(
            name="⚒️ Craft Items",
            value="Create weapons, armor, potions and other useful items.\n"
                  "1. Select a crafting category (Weapons, Armor, etc.)\n"
                  "2. Choose the specific type (Swords, Maces, etc.)\n"
                  "3. Select which tier to craft (higher tiers = better items)\n"
                  "4. Choose your crafting station (better stations = higher success)\n"
                  "5. Click 'Craft Item' to attempt crafting",
            inline=False
        )

        embed.add_field(
            name="📦 Materials",
            value="Materials are required for crafting.\n"
                  "• Higher quality materials produce better items\n"
                  "• Different item types require different materials\n"
                  "• Materials are categorized (Mining, Foraging, Monster Parts, etc.)\n"
                  "• Rarity of materials affects the quality of crafted items",
            inline=False
        )

        embed.add_field(
            name="🔍 Gathering",
            value="Materials can be gathered through various activities.\n"
                  "• Mining: Collect metals, gems, and stone\n"
                  "• Foraging: Gather plants, herbs, and wood\n"
                  "• Monster Parts: Collected from defeated enemies\n"
                  "• Rare materials can be found in dungeons and special events",
            inline=False
        )

        embed.add_field(
            name="📊 Crafting Skills",
            value="Each crafting category has its own skill that improves as you craft.\n"
                  "• Higher skill levels increase success rate\n"
                  "• Higher skill levels unlock better item crafting\n"
                  "• Experience is gained from both successes and failures\n"
                  "• Skill level affects the quality of crafted items",
            inline=False
        )

        # Add back button to return to main crafting view
        back_view = View(timeout=60)
        back_button = Button(
            label="Back to Crafting", 
            emoji="◀️", 
            custom_id="back_to_crafting", 
            style=discord.ButtonStyle.gray
        )

        async def back_callback(back_interaction):
            # Return to main crafting view
            embed = discord.Embed(
                title="🏺 Ethereal Ascendancy Crafting",
                description="Welcome to the crafting system! Here you can create powerful weapons, armor, potions, and other items from materials you've gathered in your adventures.",
                color=discord.Color.gold()
            )

            embed.add_field(
                name="⚒️ Craft Items",
                value="Create weapons, armor, potions and other useful items from gathered materials.",
                inline=True
            )

            embed.add_field(
                name="📦 Materials Encyclopedia",
                value="Browse the encyclopedia of available crafting materials.",
                inline=True
            )

            embed.add_field(
                name="🔍 Gather Materials",
                value="Collect raw materials for crafting from various sources.",
                inline=True
            )

            embed.add_field(
                name="📊 Crafting Skills",
                value="View your progress in various crafting disciplines.",
                inline=True
            )

            # Return to the main crafting view
            entry_view = CraftingEntryView(self.player, self.data_manager)
            await back_interaction.response.edit_message(embed=embed, view=entry_view)

        back_button.callback = back_callback
        back_view.add_item(back_button)

        await interaction.response.edit_message(embed=embed, view=back_view)

async def crafting_command(ctx, data_manager: DataManager):
    """Main crafting command - craft items from gathered materials"""
    player = data_manager.get_player(ctx.author.id)

    view = CraftingEntryView(player, data_manager)

    embed = discord.Embed(
        title="🏺 Ethereal Ascendancy Crafting",
        description="Welcome to the crafting system! Here you can create powerful weapons, armor, potions, and other items from materials you've gathered in your adventures.",
        color=discord.Color.gold()
    )

    embed.add_field(
        name="⚒️ Craft Items",
        value="Create weapons, armor, potions and other useful items from gathered materials.",
        inline=True
    )

    embed.add_field(
        name="📦 Materials Encyclopedia",
        value="Browse the encyclopedia of available crafting materials.",
        inline=True
    )

    embed.add_field(
        name="🔍 Gather Materials",
        value="Collect raw materials for crafting from various sources.",
        inline=True
    )

    embed.add_field(
        name="📊 Crafting Skills",
        value="View your progress in various crafting disciplines.",
        inline=True
    )

    total_materials = 0
    material_types = set()

    # Count materials in inventory
    for inv_item in player.inventory:
        if "Material:" in inv_item.item.item_type:
            total_materials += inv_item.quantity
            material_types.add(inv_item.item.name)

    embed.add_field(
        name="Your Materials",
        value=f"You have {total_materials} materials of {len(material_types)} different types in your inventory.",
        inline=False
    )

    await ctx.send(embed=embed, view=view)