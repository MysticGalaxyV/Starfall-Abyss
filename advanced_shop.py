import discord
from discord.ui import Button, View, Select
import random
import string
from typing import Dict, List, Optional, Any

from data_models import PlayerData, DataManager, Item, InventoryItem
from user_restrictions import RestrictedView, get_target_user, create_restricted_embed_footer

# Item rarities and their stat multipliers
RARITIES = {
    "common": {"multiplier": 1.0, "color": discord.Color.light_grey(), "emoji": "⚪"},
    "uncommon": {"multiplier": 1.5, "color": discord.Color.green(), "emoji": "🟢"},
    "rare": {"multiplier": 2.0, "color": discord.Color.blue(), "emoji": "🔵"},
    "epic": {"multiplier": 3.0, "color": discord.Color.purple(), "emoji": "🟣"},
    "legendary": {"multiplier": 4.0, "color": discord.Color.gold(), "emoji": "🟡"},
    "mythic": {"multiplier": 5.0, "color": discord.Color.red(), "emoji": "🔴"},
    "artifact": {"multiplier": 7.0, "color": discord.Color.teal(), "emoji": "💠"},
    "divine": {"multiplier": 10.0, "color": discord.Color(0xFFFFFF), "emoji": "🌟"}
}

# Weapon types and their base damage formulas
WEAPON_TYPES = {
    "sword": {"base_dmg": 10, "scaling": {"power": 1.0, "speed": 0.3}, "critical_chance": 5, "emoji": "⚔️"},
    "axe": {"base_dmg": 15, "scaling": {"power": 1.2, "speed": 0.1}, "critical_chance": 3, "emoji": "🪓"},
    "dagger": {"base_dmg": 7, "scaling": {"power": 0.7, "speed": 0.7}, "critical_chance": 12, "emoji": "🗡️"},
    "staff": {"base_dmg": 8, "scaling": {"power": 0.8, "hp": 0.3}, "critical_chance": 8, "emoji": "🔮"},
    "bow": {"base_dmg": 9, "scaling": {"power": 0.9, "speed": 0.5}, "critical_chance": 10, "emoji": "🏹"},
    "hammer": {"base_dmg": 18, "scaling": {"power": 1.5, "defense": 0.2}, "critical_chance": 2, "emoji": "🔨"},
    "spear": {"base_dmg": 12, "scaling": {"power": 1.0, "speed": 0.4}, "critical_chance": 7, "emoji": "🔱"},
    "gauntlet": {"base_dmg": 6, "scaling": {"power": 0.6, "defense": 0.6}, "critical_chance": 6, "emoji": "👊"},
    "scythe": {"base_dmg": 14, "scaling": {"power": 1.3, "hp": 0.1}, "critical_chance": 9, "emoji": "🌙"}
}

# Armor types and their defense formulas
ARMOR_TYPES = {
    "light": {"base_def": 5, "scaling": {"defense": 0.7, "speed": 0.5}, "emoji": "🧥"},
    "medium": {"base_def": 10, "scaling": {"defense": 1.0, "speed": 0.3}, "emoji": "👕"},
    "heavy": {"base_def": 15, "scaling": {"defense": 1.3, "speed": -0.1}, "emoji": "🛡️"}
}

# Special effects that can be applied to items
SPECIAL_EFFECTS = {
    "burning": {"description": "Deals additional fire damage over time", "combat_text": "🔥 Burning! {damage} damage"},
    "frost": {"description": "Slows enemy and reduces their defense", "combat_text": "❄️ Frosted! Speed -{amount}%"},
    "poison": {"description": "Deals poison damage over time", "combat_text": "☠️ Poisoned! {damage}/turn"},
    "vampiric": {"description": "Heals for a portion of damage dealt", "combat_text": "🩸 Drained {amount} HP"},
    "electric": {"description": "Has a chance to stun the opponent", "combat_text": "⚡ Stunned for {turns} turns!"},
    "shadow": {"description": "Reduces enemy visibility and accuracy", "combat_text": "👁️ Blinded! {miss_chance}% miss chance"},
    "blessed": {"description": "Increases healing received", "combat_text": "✨ Blessed healing +{amount}%"},
    "cursed": {"description": "Permanently reduces enemy stats", "combat_text": "🌑 Cursed! {stat} reduced by {amount}"},
    "thorns": {"description": "Returns damage to attackers", "combat_text": "🌵 Thorns! {damage} reflected"},
    "berserker": {"description": "Increases damage as HP decreases", "combat_text": "💢 Berserk! Damage +{amount}%"},
    "guardian": {"description": "Grants a temporary shield", "combat_text": "🛡️ Shield absorbs {amount} damage"},
    "swift": {"description": "Grants additional actions per turn", "combat_text": "⏩ Swift! Extra action chance {chance}%"},
    "lucky": {"description": "Increases critical hit chance", "combat_text": "🍀 Lucky! Crit chance +{amount}%"},
    "wise": {"description": "Increases experience gained", "combat_text": "📚 Wise! +{amount}% EXP"},
    "wealthy": {"description": "Increases gold dropped from enemies", "combat_text": "💰 Wealthy! +{amount}% gold"}
}

# Enemy weaknesses and resistances
ENEMY_TRAITS = {
    "undead": {"weak": ["blessed", "fire"], "resist": ["poison", "frost"]},
    "demon": {"weak": ["blessed", "holy"], "resist": ["fire", "cursed"]},
    "beast": {"weak": ["poison", "fire"], "resist": ["electric", "physical"]},
    "elemental": {"weak": ["opposite_element"], "resist": ["same_element"]},
    "construct": {"weak": ["electric", "hammer"], "resist": ["poison", "blade"]},
    "dragon": {"weak": ["ice", "spear"], "resist": ["fire", "physical"]},
    "human": {"weak": [], "resist": []},  # Balanced, no particular weaknesses or resistances
    "fae": {"weak": ["iron", "pure"], "resist": ["magic", "nature"]},
    "plant": {"weak": ["fire", "cutting"], "resist": ["poison", "nature"]},
    "aquatic": {"weak": ["electric", "frost"], "resist": ["water", "fire"]}
}

# Set bonuses that can be applied when wearing multiple pieces of the same set
SET_BONUSES = {
    "shadow_walker": {
        "pieces": ["Shadow Hood", "Shadow Cloak", "Shadow Boots"],
        "requirement": 2,  # Need 2 pieces for partial bonus
        "partial_bonus": {"speed": 10, "effects": ["shadow"]},
        "full_bonus": {"speed": 25, "effects": ["shadow", "swift"]},
        "description": "Move unseen through the shadows"
    },
    "guardian": {
        "pieces": ["Guardian Helmet", "Guardian Plate", "Guardian Gauntlets"],
        "requirement": 2,
        "partial_bonus": {"defense": 15, "effects": ["thorns"]},
        "full_bonus": {"defense": 35, "effects": ["thorns", "guardian"]},
        "description": "Become an immovable fortress"
    },
    "berserker": {
        "pieces": ["Berserker Helm", "Berserker Armor", "Berserker Greaves"],
        "requirement": 2,
        "partial_bonus": {"power": 15, "effects": ["berserker"]},
        "full_bonus": {"power": 35, "effects": ["berserker", "burning"]},
        "description": "Channel your inner rage"
    },
    "arcane": {
        "pieces": ["Arcane Hat", "Arcane Robes", "Arcane Boots"],
        "requirement": 2,
        "partial_bonus": {"hp": 15, "effects": ["frost"]},
        "full_bonus": {"hp": 35, "effects": ["frost", "electric"]},
        "description": "Harness magical energies"
    }
}

# Shop items database - organized by level tiers
ADVANCED_SHOP_ITEMS = {
    # Level 1-5 Shop Items
    "novice": [
        # Weapons
        {
            "name": "Wooden Sword",
            "description": "A basic training sword.",
            "item_type": "weapon",
            "weapon_type": "sword",
            "rarity": "common",
            "stats": {"power": 3},
            "level_req": 1,
            "value": 50
        },
        {
            "name": "Wooden Axe",
            "description": "A simple axe for beginners.",
            "item_type": "weapon",
            "weapon_type": "axe",
            "rarity": "common",
            "stats": {"power": 4, "speed": -1},
            "level_req": 1,
            "value": 50
        },
        {
            "name": "Training Dagger",
            "description": "A small blade for quick strikes.",
            "item_type": "weapon",
            "weapon_type": "dagger",
            "rarity": "common",
            "stats": {"power": 2, "speed": 2},
            "level_req": 1,
            "value": 50
        },
        {
            "name": "Apprentice Staff",
            "description": "A simple wooden staff.",
            "item_type": "weapon",
            "weapon_type": "staff",
            "rarity": "common",
            "stats": {"power": 2, "hp": 3},
            "level_req": 1,
            "value": 50
        },

        # Armor
        {
            "name": "Leather Vest",
            "description": "Simple leather protection.",
            "item_type": "armor",
            "armor_type": "light",
            "rarity": "common",
            "stats": {"defense": 3, "speed": 1},
            "level_req": 1,
            "value": 50
        },
        {
            "name": "Padded Armor",
            "description": "Quilted armor offering basic protection.",
            "item_type": "armor",
            "armor_type": "medium",
            "rarity": "common",
            "stats": {"defense": 4},
            "level_req": 1,
            "value": 55
        },
        {
            "name": "Scrap Metal Plate",
            "description": "Cobbled together from scrap metal.",
            "item_type": "armor",
            "armor_type": "heavy",
            "rarity": "common",
            "stats": {"defense": 5, "speed": -1},
            "level_req": 1,
            "value": 60
        },

        # Accessories
        {
            "name": "Leather Boots",
            "description": "Light boots for better mobility.",
            "item_type": "accessory",
            "slot": "feet",
            "rarity": "common",
            "stats": {"speed": 3},
            "level_req": 1,
            "value": 50
        },
        {
            "name": "Traveler's Gloves",
            "description": "Comfortable gloves for long journeys.",
            "item_type": "accessory",
            "slot": "hands",
            "rarity": "common",
            "stats": {"speed": 1, "defense": 1},
            "level_req": 1,
            "value": 50
        },
        {
            "name": "Lucky Charm",
            "description": "A simple charm believed to bring luck.",
            "item_type": "accessory",
            "slot": "neck",
            "rarity": "common",
            "stats": {"power": 1, "defense": 1, "speed": 1},
            "level_req": 1,
            "value": 75
        },

        # Consumables
        {
            "name": "Health Potion",
            "description": "Restores 50 HP during battle.",
            "item_type": "consumable",
            "effect": "heal_hp",
            "effect_value": 50,
            "rarity": "common",
            "stats": {},
            "level_req": 1,
            "value": 30
        },
        {
            "name": "Energy Potion",
            "description": "Restores 50 Energy during battle.",
            "item_type": "consumable",
            "effect": "heal_energy",
            "effect_value": 50,
            "rarity": "common",
            "stats": {},
            "level_req": 1,
            "value": 30
        },
        {
            "name": "Power Elixir",
            "description": "Temporarily increases power by 5.",
            "item_type": "consumable",
            "effect": "boost_power",
            "effect_value": 5,
            "effect_duration": 3,
            "rarity": "common",
            "stats": {},
            "level_req": 3,
            "value": 50
        }
    ],

    # Level 6-15 Shop Items
    "apprentice": [
        # Weapons
        {
            "name": "Steel Sword",
            "description": "A well-crafted steel blade.",
            "item_type": "weapon",
            "weapon_type": "sword",
            "rarity": "uncommon",
            "stats": {"power": 8},
            "level_req": 6,
            "value": 300
        },
        {
            "name": "Battle Axe",
            "description": "A hefty axe for serious damage.",
            "item_type": "weapon",
            "weapon_type": "axe",
            "rarity": "uncommon",
            "stats": {"power": 10, "speed": -2},
            "level_req": 6,
            "value": 320
        },
        {
            "name": "Swift Dagger",
            "description": "A perfectly balanced dagger.",
            "item_type": "weapon",
            "weapon_type": "dagger",
            "rarity": "uncommon",
            "stats": {"power": 6, "speed": 5},
            "level_req": 6,
            "value": 310
        },
        {
            "name": "Enchanter's Staff",
            "description": "A staff with basic enchantments.",
            "item_type": "weapon",
            "weapon_type": "staff",
            "rarity": "uncommon",
            "stats": {"power": 7, "hp": 7},
            "special_effect": "frost",
            "level_req": 6,
            "value": 350
        },
        {
            "name": "Hunter's Bow",
            "description": "A reliable bow for hunting.",
            "item_type": "weapon",
            "weapon_type": "bow",
            "rarity": "uncommon",
            "stats": {"power": 7, "speed": 3},
            "level_req": 7,
            "value": 330
        },

        # Armor
        {
            "name": "Reinforced Leather",
            "description": "Leather armor with metal reinforcements.",
            "item_type": "armor",
            "armor_type": "light",
            "rarity": "uncommon",
            "stats": {"defense": 7, "speed": 3},
            "level_req": 6,
            "value": 300
        },
        {
            "name": "Chainmail",
            "description": "Flexible armor made of interlocking rings.",
            "item_type": "armor",
            "armor_type": "medium",
            "rarity": "uncommon",
            "stats": {"defense": 10, "speed": 1},
            "level_req": 6,
            "value": 350
        },
        {
            "name": "Steel Plate",
            "description": "Solid steel armor for serious protection.",
            "item_type": "armor",
            "armor_type": "heavy",
            "rarity": "uncommon",
            "stats": {"defense": 13, "speed": -2},
            "level_req": 6,
            "value": 400
        },

        # Accessories
        {
            "name": "Explorer's Boots",
            "description": "Sturdy boots made for exploration.",
            "item_type": "accessory",
            "slot": "feet",
            "rarity": "uncommon",
            "stats": {"speed": 8},
            "level_req": 6,
            "value": 300
        },
        {
            "name": "Warrior's Bracers",
            "description": "Bracers that enhance combat ability.",
            "item_type": "accessory",
            "slot": "hands",
            "rarity": "uncommon",
            "stats": {"power": 4, "defense": 3},
            "level_req": 6,
            "value": 320
        },
        {
            "name": "Amulet of Focus",
            "description": "Helps the wearer maintain focus in battle.",
            "item_type": "accessory",
            "slot": "neck",
            "rarity": "uncommon",
            "stats": {"power": 3, "defense": 3, "speed": 3},
            "special_effect": "lucky",
            "level_req": 8,
            "value": 450
        },

        # Consumables
        {
            "name": "Greater Health Potion",
            "description": "Restores 150 HP during battle.",
            "item_type": "consumable",
            "effect": "heal_hp",
            "effect_value": 150,
            "rarity": "uncommon",
            "stats": {},
            "level_req": 6,
            "value": 100
        },
        {
            "name": "Greater Energy Potion",
            "description": "Restores 150 Energy during battle.",
            "item_type": "consumable",
            "effect": "heal_energy",
            "effect_value": 150,
            "rarity": "uncommon",
            "stats": {},
            "level_req": 6,
            "value": 100
        },
        {
            "name": "Defense Elixir",
            "description": "Temporarily increases defense by 10.",
            "item_type": "consumable",
            "effect": "boost_defense",
            "effect_value": 10,
            "effect_duration": 3,
            "rarity": "uncommon",
            "stats": {},
            "level_req": 10,
            "value": 150
        }
    ],

    # Level 16-30 Shop Items
    "adept": [
        # Weapons
        {
            "name": "Enchanted Blade",
            "description": "A blade imbued with magical energy.",
            "item_type": "weapon",
            "weapon_type": "sword",
            "rarity": "rare",
            "stats": {"power": 18},
            "special_effect": "electric",
            "level_req": 16,
            "value": 1000
        },
        {
            "name": "Berserker's Axe",
            "description": "An axe that channels rage into power.",
            "item_type": "weapon",
            "weapon_type": "axe",
            "rarity": "rare",
            "stats": {"power": 22, "speed": -3},
            "special_effect": "berserker",
            "level_req": 16,
            "value": 1150
        },
        {
            "name": "Shadow Dagger",
            "description": "A dagger that moves like shadow.",
            "item_type": "weapon",
            "weapon_type": "dagger",
            "rarity": "rare",
            "stats": {"power": 15, "speed": 12},
            "special_effect": "shadow",
            "level_req": 16,
            "value": 1100
        },
        {
            "name": "Elemental Staff",
            "description": "A staff that channels elemental forces.",
            "item_type": "weapon",
            "weapon_type": "staff",
            "rarity": "rare",
            "stats": {"power": 16, "hp": 15},
            "special_effect": "frost",
            "level_req": 16,
            "value": 1200
        },
        {
            "name": "Thunderbolt Bow",
            "description": "A bow that fires with lightning speed.",
            "item_type": "weapon",
            "weapon_type": "bow",
            "rarity": "rare",
            "stats": {"power": 17, "speed": 8},
            "special_effect": "electric",
            "level_req": 18,
            "value": 1250
        },
        {
            "name": "Guardian Hammer",
            "description": "A mighty hammer that protects its wielder.",
            "item_type": "weapon",
            "weapon_type": "hammer",
            "rarity": "rare",
            "stats": {"power": 25, "defense": 5, "speed": -5},
            "special_effect": "guardian",
            "level_req": 20,
            "value": 1300
        },

        # Armor
        {
            "name": "Shadow Hood",
            "description": "A hood woven from shadowsilk.",
            "item_type": "armor",
            "armor_type": "light",
            "set": "shadow_walker",
            "rarity": "rare",
            "stats": {"defense": 14, "speed": 8},
            "special_effect": "shadow",
            "level_req": 16,
            "value": 1000
        },
        {
            "name": "Shadow Cloak",
            "description": "A cloak that blends with darkness.",
            "item_type": "armor",
            "armor_type": "light",
            "set": "shadow_walker",
            "rarity": "rare",
            "stats": {"defense": 15, "speed": 9},
            "special_effect": "shadow",
            "level_req": 18,
            "value": 1100
        },
        {
            "name": "Guardian Plate",
            "description": "Plate armor with protective enchantments.",
            "item_type": "armor",
            "armor_type": "heavy",
            "set": "guardian",
            "rarity": "rare",
            "stats": {"defense": 25, "speed": -4},
            "special_effect": "thorns",
            "level_req": 20,
            "value": 1300
        },
        {
            "name": "Arcane Robes",
            "description": "Robes imbued with arcane magic.",
            "item_type": "armor",
            "armor_type": "medium",
            "set": "arcane",
            "rarity": "rare",
            "stats": {"defense": 18, "hp": 15},
            "special_effect": "frost",
            "level_req": 22,
            "value": 1200
        },

        # Accessories
        {
            "name": "Shadow Boots",
            "description": "Boots that leave no footprints.",
            "item_type": "accessory",
            "slot": "feet",
            "set": "shadow_walker",
            "rarity": "rare",
            "stats": {"speed": 15},
            "special_effect": "swift",
            "level_req": 16,
            "value": 1000
        },
        {
            "name": "Guardian Gauntlets",
            "description": "Gauntlets that enhance defensive capabilities.",
            "item_type": "accessory",
            "slot": "hands",
            "set": "guardian",
            "rarity": "rare",
            "stats": {"power": 8, "defense": 12},
            "special_effect": "guardian",
            "level_req": 16,
            "value": 1100
        },
        {
            "name": "Medallion of Power",
            "description": "A medallion that enhances the wearer's strength.",
            "item_type": "accessory",
            "slot": "neck",
            "rarity": "rare",
            "stats": {"power": 10, "defense": 5, "speed": 5},
            "special_effect": "berserker",
            "level_req": 25,
            "value": 1500
        },

        # Consumables
        {
            "name": "Superior Health Potion",
            "description": "Restores 300 HP during battle.",
            "item_type": "consumable",
            "effect": "heal_hp",
            "effect_value": 300,
            "rarity": "rare",
            "stats": {},
            "level_req": 16,
            "value": 300
        },
        {
            "name": "Superior Energy Potion",
            "description": "Restores 300 Energy during battle.",
            "item_type": "consumable",
            "effect": "heal_energy",
            "effect_value": 300,
            "rarity": "rare",
            "stats": {},
            "level_req": 16,
            "value": 300
        },
        {
            "name": "Battle Elixir",
            "description": "Temporarily increases all stats by 8.",
            "item_type": "consumable",
            "effect": "boost_all",
            "effect_value": 8,
            "effect_duration": 3,
            "rarity": "rare",
            "stats": {},
            "level_req": 20,
            "value": 500
        }
    ],

    # Level 31-50 Shop Items
    "expert": [
        # Weapons
        {
            "name": "Dragonslayer",
            "description": "A legendary sword forged to slay dragons.",
            "item_type": "weapon",
            "weapon_type": "sword",
            "rarity": "epic",
            "stats": {"power": 30},
            "special_effect": "burning",
            "level_req": 31,
            "value": 3000
        },
        {
            "name": "Void Reaver",
            "description": "An axe that tears through reality.",
            "item_type": "weapon",
            "weapon_type": "axe",
            "rarity": "epic",
            "stats": {"power": 35, "speed": -5},
            "special_effect": "cursed",
            "level_req": 35,
            "value": 3500
        },
        {
            "name": "Soulstealer",
            "description": "A dagger that drains life from its victims.",
            "item_type": "weapon",
            "weapon_type": "dagger",
            "rarity": "epic",
            "stats": {"power": 25, "speed": 20},
            "special_effect": "vampiric",
            "level_req": 33,
            "value": 3200
        },
        {
            "name": "Archmage's Focus",
            "description": "A staff wielded by archmages of legend.",
            "item_type": "weapon",
            "weapon_type": "staff",
            "rarity": "epic",
            "stats": {"power": 28, "hp": 25},
            "special_effect": "electric",
            "level_req": 37,
            "value": 3800
        },
        {
            "name": "Windforce",
            "description": "A bow that harnesses the power of storms.",
            "item_type": "weapon",
            "weapon_type": "bow",
            "rarity": "epic",
            "stats": {"power": 27, "speed": 15},
            "special_effect": "electric",
            "level_req": 39,
            "value": 3600
        },

        # Armor
        {
            "name": "Assassin's Shroud",
            "description": "Armor worn by legendary assassins.",
            "item_type": "armor",
            "armor_type": "light",
            "rarity": "epic",
            "stats": {"defense": 25, "speed": 15},
            "special_effect": "shadow",
            "level_req": 31,
            "value": 3000
        },
        {
            "name": "Warlord's Plate",
            "description": "Armor worn by the greatest warlords.",
            "item_type": "armor",
            "armor_type": "heavy",
            "rarity": "epic",
            "stats": {"defense": 40, "power": 10, "speed": -5},
            "special_effect": "thorns",
            "level_req": 35,
            "value": 3500
        },
        {
            "name": "Archmage's Robes",
            "description": "Robes worn by powerful archmages.",
            "item_type": "armor",
            "armor_type": "medium",
            "rarity": "epic",
            "stats": {"defense": 30, "hp": 30},
            "special_effect": "frost",
            "level_req": 40,
            "value": 4000
        },

        # Accessories
        {
            "name": "Boots of Haste",
            "description": "Boots that grant incredible speed.",
            "item_type": "accessory",
            "slot": "feet",
            "rarity": "epic",
            "stats": {"speed": 25},
            "special_effect": "swift",
            "level_req": 31,
            "value": 3000
        },
        {
            "name": "Gauntlets of Might",
            "description": "Gauntlets that enhance strength to incredible levels.",
            "item_type": "accessory",
            "slot": "hands",
            "rarity": "epic",
            "stats": {"power": 20, "defense": 15},
            "special_effect": "berserker",
            "level_req": 35,
            "value": 3500
        },
        {
            "name": "Amulet of the Titan",
            "description": "An amulet that grants titanic strength.",
            "item_type": "accessory",
            "slot": "neck",
            "rarity": "epic",
            "stats": {"power": 15, "defense": 15, "hp": 15, "speed": 15},
            "special_effect": "guardian",
            "level_req": 45,
            "value": 5000
        },

        # Consumables
        {
            "name": "Master Health Potion",
            "description": "Restores 600 HP during battle.",
            "item_type": "consumable",
            "effect": "heal_hp",
            "effect_value": 600,
            "rarity": "epic",
            "stats": {},
            "level_req": 31,
            "value": 800
        },
        {
            "name": "Master Energy Potion",
            "description": "Restores 600 Energy during battle.",
            "item_type": "consumable",
            "effect": "heal_energy",
            "effect_value": 600,
            "rarity": "epic",
            "stats": {},
            "level_req": 31,
            "value": 800
        },
        {
            "name": "Elixir of Invincibility",
            "description": "Grants immunity to damage for one turn.",
            "item_type": "consumable",
            "effect": "invincible",
            "effect_duration": 1,
            "rarity": "epic",
            "stats": {},
            "level_req": 40,
            "value": 1500
        }
    ],

    # Level 51-100 Shop Items
    "master": [
        # Weapons
        {
            "name": "Godslayer",
            "description": "A sword said to be capable of killing gods.",
            "item_type": "weapon",
            "weapon_type": "sword",
            "rarity": "legendary",
            "stats": {"power": 50},
            "special_effect": "blessed",
            "level_req": 51,
            "value": 10000
        },
        {
            "name": "World Cleaver",
            "description": "An axe that can split mountains.",
            "item_type": "weapon",
            "weapon_type": "axe",
            "rarity": "legendary",
            "stats": {"power": 60, "speed": -10},
            "special_effect": "berserker",
            "level_req": 60,
            "value": 12000
        },
        {
            "name": "Eternal Scythe",
            "description": "A scythe that harvests souls for eternity.",
            "item_type": "weapon",
            "weapon_type": "scythe",
            "rarity": "legendary",
            "stats": {"power": 55, "hp": 20},
            "special_effect": "vampiric",
            "level_req": 70,
            "value": 15000
        },

        # Armor
        {
            "name": "Celestial Plate",
            "description": "Armor forged from fallen stars.",
            "item_type": "armor",
            "armor_type": "heavy",
            "rarity": "legendary",
            "stats": {"defense": 70, "power": 20, "hp": 20},
            "special_effect": "guardian",
            "level_req": 51,
            "value": 10000
        },
        {
            "name": "Draconic Scales",
            "description": "Armor crafted from elder dragon scales.",
            "item_type": "armor",
            "armor_type": "medium",
            "rarity": "legendary",
            "stats": {"defense": 60, "power": 15, "speed": 15},
            "special_effect": "burning",
            "level_req": 75,
            "value": 18000
        },

        # Accessories
        {
            "name": "Crown of Dominion",
            "description": "A crown that grants authority over reality itself.",
            "item_type": "accessory",
            "slot": "head",
            "rarity": "legendary",
            "stats": {"power": 25, "defense": 25, "hp": 25, "speed": 25},
            "special_effect": "blessed",
            "level_req": 100,
            "value": 50000
        }
    ],

    # Special category for class change scrolls and other special items
    "special": [
        {
            "name": "Scroll of Class Change",
            "description": "Allows immediate class change without level restrictions.",
            "item_type": "special",
            "effect": "class_change",
            "rarity": "legendary",
            "level_req": 20,
            "value": 5000
        },
        {
            "name": "Skill Reset Tome",
            "description": "Resets all allocated skill points for redistribution.",
            "item_type": "special",
            "effect": "skill_reset",
            "rarity": "epic",
            "level_req": 10,
            "value": 1000
        },
        {
            "name": "Guild Charter",
            "description": "Required to establish a new guild.",
            "item_type": "special",
            "effect": "create_guild",
            "rarity": "legendary",
            "level_req": 10,
            "value": 10000
        },
        {
            "name": "Character Rename Scroll",
            "description": "Allows you to change your character's nickname.",
            "item_type": "special",
            "effect": "rename",
            "rarity": "rare",
            "level_req": 5,
            "value": 500
        }
    ],

    # Limited-time event items
    "event": [
        {
            "name": "Festive Weapon Skin",
            "description": "A limited-time holiday skin for your weapons.",
            "item_type": "cosmetic",
            "slot": "weapon",
            "rarity": "epic",
            "stats": {},
            "level_req": 1,
            "value": 1000,
            "event": "Winter Festival"
        },
        {
            "name": "Summer Crown",
            "description": "A crown made of exotic flowers that blooms year-round.",
            "item_type": "accessory",
            "slot": "head",
            "rarity": "epic",
            "stats": {"power": 10, "speed": 10, "hp": 10},
            "special_effect": "blessed",
            "level_req": 20,
            "value": 2000,
            "event": "Summer Solstice"
        },
        {
            "name": "Temporal Distortion Device",
            "description": "Grants double XP for 24 hours. Limited-time event item.",
            "item_type": "special",
            "effect": "double_xp",
            "effect_duration": 24,  # hours
            "rarity": "legendary",
            "stats": {},
            "level_req": 1,
            "value": 5000,
            "event": "Time Warp"
        }
    ],

    # Hidden/Secret items (unlocked through special achievements)
    "secret": [
        {
            "name": "Void Blade",
            "description": "A weapon forged from the essence of the void itself.",
            "item_type": "weapon",
            "weapon_type": "sword",
            "rarity": "mythic",
            "stats": {"power": 100},
            "special_effect": "vampiric",
            "level_req": 50,
            "value": 50000,
            "unlock_condition": "Defeat the Void Lord in the Abyssal Depths dungeon"
        },
        {
            "name": "Ancient One's Eye",
            "description": "An amulet containing the eye of an ancient being.",
            "item_type": "accessory",
            "slot": "neck",
            "rarity": "mythic",
            "stats": {"power": 30, "defense": 30, "hp": 30, "speed": 30},
            "special_effect": "wise",
            "level_req": 75,
            "value": 75000,
            "unlock_condition": "Complete all achievements"
        }
    ],

    # Divine items (ultra rare, only obtainable through special events or extremely difficult content)
    "divine": [
        {
            "name": "Eternity",
            "description": "A weapon that exists beyond time and space.",
            "item_type": "weapon",
            "weapon_type": "sword",
            "rarity": "divine",
            "stats": {"power": 150, "defense": 50, "hp": 50, "speed": 50},
            "special_effects": ["blessed", "vampiric", "swift"],
            "level_req": 100,
            "value": 1000000,
            "unlock_condition": "Defeat all Divine Bosses across all servers"
        }
    ]
}

class AdvancedShopView(RestrictedView):
    def __init__(self, player_data: PlayerData, data_manager: DataManager, authorized_user):
        super().__init__(authorized_user, timeout=180)  # Longer timeout for shop browsing
        self.player_data = player_data
        self.data_manager = data_manager
        self.current_category = "novice"
        self.current_page = 0
        self.items_per_page = 5
        self.filtered_type = None

        # Add category selection
        self.add_category_select()

        # Add item type filter
        self.add_item_type_filter()

        # Add navigation buttons
        self.add_navigation_buttons()

        # Update buttons for initial view
        self.update_buttons()

    def add_category_select(self):
        """Add dropdown for shop categories"""
        categories = [
            discord.SelectOption(label="Novice (Level 1-5)", value="novice", emoji="🔰"),
            discord.SelectOption(label="Apprentice (Level 6-15)", value="apprentice", emoji="🥉"),
            discord.SelectOption(label="Adept (Level 16-30)", value="adept", emoji="🥈"),
            discord.SelectOption(label="Expert (Level 31-50)", value="expert", emoji="🥇"),
            discord.SelectOption(label="Master (Level 51+)", value="master", emoji="👑"),
            discord.SelectOption(label="Special Items", value="special", emoji="✨"),
            discord.SelectOption(label="Event Items", value="event", emoji="🎉")
        ]

        # Only add secret items if player has the achievement
        if hasattr(self.player_data, "achievements") and any(a.get("id") == "discover_secret" for a in self.player_data.achievements):
            categories.append(discord.SelectOption(label="Secret Items", value="secret", emoji="🔍"))

        # Only add divine items for max level players
        if self.player_data.class_level >= 100:
            categories.append(discord.SelectOption(label="Divine Items", value="divine", emoji="🌟"))

        category_select = Select(
            placeholder="Select Item Category",
            options=categories,
            custom_id="category_select"
        )
        category_select.callback = self.category_callback
        self.add_item(category_select)

    def add_item_type_filter(self):
        """Add dropdown for item type filtering"""
        item_types = [
            discord.SelectOption(label="All Items", value="all", emoji="🔍"),
            discord.SelectOption(label="Weapons", value="weapon", emoji="⚔️"),
            discord.SelectOption(label="Armor", value="armor", emoji="🛡️"),
            discord.SelectOption(label="Accessories", value="accessory", emoji="💍"),
            discord.SelectOption(label="Consumables", value="consumable", emoji="🧪"),
            discord.SelectOption(label="Special", value="special", emoji="✨")
        ]

        type_select = Select(
            placeholder="Filter by Item Type",
            options=item_types,
            custom_id="type_select"
        )
        type_select.callback = self.type_filter_callback
        self.add_item(type_select)

    def add_navigation_buttons(self):
        """Add navigation and action buttons"""
        # Previous page button
        prev_btn = Button(
            label="Previous",
            style=discord.ButtonStyle.secondary,
            emoji="⬅️",
            custom_id="prev_page",
            disabled=True  # Initially disabled on first page
        )
        prev_btn.callback = self.prev_page_callback
        self.add_item(prev_btn)

        # Next page button
        next_btn = Button(
            label="Next",
            style=discord.ButtonStyle.secondary,
            emoji="➡️",
            custom_id="next_page"
        )
        next_btn.callback = self.next_page_callback
        self.add_item(next_btn)

        # Balance button (shows player cursed energy)
        balance_btn = Button(
            label=f"Balance: {self.player_data.gold} 💰",
            style=discord.ButtonStyle.primary,
            emoji="💰",
            custom_id="balance",
            disabled=True  # Just an indicator, not clickable
        )
        self.add_item(balance_btn)

    async def category_callback(self, interaction: discord.Interaction):
        """Handle category selection"""
        self.current_category = interaction.data["values"][0]
        self.current_page = 0
        self.update_buttons()

        await interaction.response.edit_message(
            embed=self.create_shop_embed(),
            view=self
        )

    async def type_filter_callback(self, interaction: discord.Interaction):
        """Handle item type filter selection"""
        selected_type = interaction.data["values"][0]
        self.filtered_type = None if selected_type == "all" else selected_type
        self.current_page = 0
        self.update_buttons()

        await interaction.response.edit_message(
            embed=self.create_shop_embed(),
            view=self
        )

    async def prev_page_callback(self, interaction: discord.Interaction):
        """Handle previous page button"""
        self.current_page = max(0, self.current_page - 1)
        self.update_buttons()

        await interaction.response.edit_message(
            embed=self.create_shop_embed(),
            view=self
        )

    async def next_page_callback(self, interaction: discord.Interaction):
        """Handle next page button"""
        items = self.get_filtered_items()
        max_pages = (len(items) - 1) // self.items_per_page + 1

        self.current_page = min(self.current_page + 1, max_pages - 1)
        self.update_buttons()

        await interaction.response.edit_message(
            embed=self.create_shop_embed(),
            view=self
        )

    def get_filtered_items(self):
        """Get items filtered by category and type"""
        items = ADVANCED_SHOP_ITEMS.get(self.current_category, [])

        # Apply item type filter if set
        if self.filtered_type:
            items = [item for item in items if item["item_type"] == self.filtered_type]

        # Filter out items player doesn't meet requirements for
        available_items = []
        for item in items:
            # Check level requirement
            if item["level_req"] <= self.player_data.class_level:
                # Check special unlock conditions
                if "unlock_condition" in item:
                    # For simplicity, we're assuming if a condition exists and player can see the item,
                    # they've met the condition (real implementation would check specifics)
                    available_items.append(item)
                else:
                    available_items.append(item)
            else:
                # Still add it but mark as locked
                item_copy = item.copy()
                item_copy["locked"] = True
                available_items.append(item_copy)

        return available_items

    def update_buttons(self):
        """Update button states based on current page and filters"""
        items = self.get_filtered_items()
        max_pages = (len(items) - 1) // self.items_per_page + 1

        # Update navigation buttons
        prev_button = discord.utils.get(self.children, custom_id="prev_page")
        if prev_button:
            prev_button.disabled = self.current_page == 0

        next_button = discord.utils.get(self.children, custom_id="next_page")
        if next_button:
            next_button.disabled = self.current_page >= max_pages - 1

        # Update balance display
        balance_button = discord.utils.get(self.children, custom_id="balance")
        if balance_button:
            balance_button.label = f"Balance: {self.player_data.gold} 💰"

        # Clear existing buy buttons and add new ones
        buy_buttons = [item for item in self.children if item.custom_id and item.custom_id.startswith("buy_")]
        for button in buy_buttons:
            self.remove_item(button)

        # Add buy buttons for current page
        start_idx = self.current_page * self.items_per_page
        end_idx = min(start_idx + self.items_per_page, len(items))

        for i in range(start_idx, end_idx):
            item = items[i]

            # Get rarity color and emoji
            rarity_info = RARITIES.get(item["rarity"], {"emoji": "⚪", "color": discord.Color.light_grey()})

            # Create buy button
            if item.get("locked", False):
                buy_btn = Button(
                    label=f"Locked: {item['name']} ({item['value']} 💰)",
                    style=discord.ButtonStyle.secondary,
                    emoji=rarity_info["emoji"],
                    custom_id=f"buy_{i}",
                    disabled=True
                )
            else:
                buy_btn = Button(
                    label=f"Buy: {item['name']} ({item['value']} 💰)",
                    style=discord.ButtonStyle.primary,
                    emoji=rarity_info["emoji"],
                    custom_id=f"buy_{i}",
                    disabled=self.player_data.gold < item["value"]
                )
                buy_btn.callback = self.buy_callback

            self.add_item(buy_btn)

    async def buy_callback(self, interaction: discord.Interaction):
        """Handle item purchase"""
        # Get the item index from the button custom_id
        item_idx = int(interaction.data["custom_id"].split("_")[1])
        items = self.get_filtered_items()

        # Calculate the actual index based on current page
        actual_idx = self.current_page * self.items_per_page + (item_idx - (self.current_page * self.items_per_page))

        if actual_idx < len(items):
            item_data = items[actual_idx]

            # Check if player has enough gold
            if self.player_data.gold >= item_data["value"]:
                # Create the item
                from data_models import Item

                # Handle special effects
                special_effect = item_data.get("special_effect", None)

                new_item = Item(
                    item_id=generate_item_id(),
                    name=item_data["name"],
                    description=item_data["description"],
                    item_type=item_data["item_type"],
                    rarity=item_data["rarity"],
                    stats=item_data["stats"],
                    level_req=item_data["level_req"],
                    value=item_data["value"]
                )

                # Handle special items with effects
                if item_data["item_type"] == "special":
                    if item_data.get("effect") == "class_change":
                        # Give the player a class change scroll
                        from equipment import add_item_to_inventory
                        add_item_to_inventory(self.player_data, new_item)

                        # Deduct gold (currency)
                        self.player_data.remove_gold(item_data["value"])

                        # Save data
                        self.data_manager.save_data()

                        # Create success message
                        success_embed = discord.Embed(
                            title="Item Purchased!",
                            description=f"You purchased a {item_data['rarity']} {item_data['name']}!\n\n"
                                      f"Use it from your inventory to change class without level restrictions.",
                            color=RARITIES[item_data["rarity"]]["color"]
                        )

                        # Update shop view
                        self.update_buttons()
                        await interaction.response.edit_message(embed=success_embed, view=self)
                        return
                    elif item_data.get("effect") == "create_guild":
                        # Give the player a guild charter
                        from equipment import add_item_to_inventory
                        add_item_to_inventory(self.player_data, new_item)

                        # Deduct gold (currency)
                        self.player_data.remove_gold(item_data["value"])

                        # Save data
                        self.data_manager.save_data()

                        # Create success message
                        success_embed = discord.Embed(
                            title="Item Purchased!",
                            description=f"You purchased a {item_data['rarity']} {item_data['name']}!\n\n"
                                      f"Use it to establish your own guild with the !guild create command.",
                            color=RARITIES[item_data["rarity"]]["color"]
                        )

                        # Update shop view
                        self.update_buttons()
                        await interaction.response.edit_message(embed=success_embed, view=self)
                        return

                # Add to inventory (regular items)
                from equipment import add_item_to_inventory
                add_item_to_inventory(self.player_data, new_item)

                # Deduct gold using the proper method
                self.player_data.remove_gold(item_data["value"])

                # Save data
                self.data_manager.save_data()

                # Create success message
                success_embed = discord.Embed(
                    title="Item Purchased!",
                    description=f"You purchased a {item_data['rarity']} {item_data['name']}!\n\n"
                              f"View it in your inventory with !equipment",
                    color=RARITIES[item_data["rarity"]]["color"]
                )

                # Add item stats
                stats_text = ""
                for stat, value in item_data["stats"].items():
                    stats_text += f"{stat.capitalize()}: +{value}\n"

                if stats_text:
                    success_embed.add_field(name="Stats", value=stats_text, inline=True)

                # Add special effects if any
                if special_effect:
                    effect_desc = SPECIAL_EFFECTS.get(special_effect, {}).get("description", "Special effect")
                    success_embed.add_field(name="Special Effect", value=f"{special_effect.capitalize()}: {effect_desc}", inline=True)

                # Update buttons for gold change
                self.update_buttons()

                # Show the success message
                await interaction.response.edit_message(embed=success_embed, view=self)
            else:
                # Not enough gold
                error_embed = discord.Embed(
                    title="Not Enough Gold",
                    description=f"You need {item_data['value']} gold to purchase this item, but you only have {self.player_data.gold}.",
                    color=discord.Color.red()
                )

                await interaction.response.send_message(embed=error_embed, ephemeral=True)

    def create_shop_embed(self):
        """Create shop embed for current view"""
        filtered_items = self.get_filtered_items()

        # Get category display info
        category_info = {
            "novice": {"name": "Novice Shop", "description": "Basic equipment for beginners (Level 1-5)", "color": discord.Color.green()},
            "apprentice": {"name": "Apprentice Shop", "description": "Better equipment for advancing adventurers (Level 6-15)", "color": discord.Color.blue()},
            "adept": {"name": "Adept Shop", "description": "Quality equipment for experienced adventurers (Level 16-30)", "color": discord.Color.purple()},
            "expert": {"name": "Expert Shop", "description": "Exceptional equipment for elite adventurers (Level 31-50)", "color": discord.Color.gold()},
            "master": {"name": "Master Shop", "description": "Legendary equipment for master adventurers (Level 51+)", "color": discord.Color.red()},
            "special": {"name": "Special Items", "description": "Unique and powerful items with special effects", "color": discord.Color.teal()},
            "event": {"name": "Event Shop", "description": "Limited-time items from special events", "color": discord.Color.orange()},
            "secret": {"name": "Secret Shop", "description": "Rare items unlocked through special achievements", "color": discord.Color.dark_gray()},
            "divine": {"name": "Divine Artifacts", "description": "Divine items of incomparable power", "color": discord.Color.gold()}
        }

        info = category_info.get(self.current_category, {"name": "Shop", "description": "Buy items", "color": discord.Color.blue()})

        # Create the embed
        embed = discord.Embed(
            title=info["name"],
            description=f"{info['description']}\nGold: {self.player_data.gold} 💰",
            color=info["color"]
        )

        # Add filter info
        filter_text = "All Items"
        if self.filtered_type:
            filter_text = f"{self.filtered_type.capitalize()} Items"

        embed.add_field(
            name="Filter",
            value=filter_text,
            inline=True
        )

        # Add page info
        max_pages = (len(filtered_items) - 1) // self.items_per_page + 1
        embed.add_field(
            name="Page",
            value=f"{self.current_page + 1}/{max_pages}",
            inline=True
        )

        # Add balance info
        embed.add_field(
            name="Your Gold",
            value=f"{self.player_data.gold} 💰",
            inline=True
        )

        # Add items on current page
        start_idx = self.current_page * self.items_per_page
        end_idx = min(start_idx + self.items_per_page, len(filtered_items))

        if start_idx < len(filtered_items):
            for i in range(start_idx, end_idx):
                item = filtered_items[i]

                # Get weapon/armor type emoji if applicable
                type_emoji = ""
                if item["item_type"] == "weapon" and "weapon_type" in item:
                    type_emoji = WEAPON_TYPES.get(item["weapon_type"], {}).get("emoji", "")
                elif item["item_type"] == "armor" and "armor_type" in item:
                    type_emoji = ARMOR_TYPES.get(item["armor_type"], {}).get("emoji", "")

                # Get rarity emoji
                rarity_emoji = RARITIES.get(item["rarity"], {}).get("emoji", "⚪")

                # Format item stats
                stats_text = ""
                for stat, value in item["stats"].items():
                    stats_text += f"{stat.capitalize()}: +{value}, "

                if stats_text:
                    stats_text = stats_text[:-2]  # Remove trailing comma and space

                # Add special effect
                special_effect = item.get("special_effect", None)
                if special_effect:
                    effect_desc = SPECIAL_EFFECTS.get(special_effect, {}).get("description", "Special effect")
                    stats_text += f"\nEffect: {effect_desc}"

                # Handle locked items
                if item.get("locked", False):
                    title = f"{i+1}. {rarity_emoji} {type_emoji} {item['name']} (Locked)"
                    value = f"**Level Required:** {item['level_req']} (You: {self.player_data.class_level})\n"
                    value += f"**Price:** {item['value']} 💰\n"
                    value += f"*{item['description']}*\n"

                    # Still show stats but indicate they're locked
                    if stats_text:
                        value += f"*Stats (Locked): {stats_text}*"
                else:
                    title = f"{i+1}. {rarity_emoji} {type_emoji} {item['name']}"
                    value = f"**Level Required:** {item['level_req']}\n"
                    value += f"**Price:** {item['value']} 💰\n"
                    value += f"*{item['description']}*\n"

                    if stats_text:
                        value += f"**Stats:** {stats_text}"

                    # Add set bonus info if applicable
                    if "set" in item:
                        set_name = item["set"]
                        if set_name in SET_BONUSES:
                            set_info = SET_BONUSES[set_name]
                            value += f"\n**Set:** {set_name} ({len(set_info['pieces'])} pieces)"

                embed.add_field(
                    name=title,
                    value=value,
                    inline=False
                )
        else:
            embed.add_field(
                name="No Items Found",
                value="No items match your current filters.",
                inline=False
            )

        # Add footer
        embed.set_footer(text="Use the buttons below to navigate and buy items.")

        return embed

def generate_item_id() -> str:
    """Generate a unique item ID"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=12))

async def advanced_shop_command(ctx, data_manager: DataManager):
    """Browse the enhanced item shop with categories and filters"""
    # Only the command author can interact with their own shop interface
    player_data = data_manager.get_player(ctx.author.id)

    shop_view = AdvancedShopView(player_data, data_manager, ctx.author)
    shop_embed = shop_view.create_shop_embed()

    # Add footer to indicate who can use this interface
    shop_embed.set_footer(text=f"🔒 Only {ctx.author.display_name} can interact with this interface")

    await ctx.send(embed=shop_embed, view=shop_view)