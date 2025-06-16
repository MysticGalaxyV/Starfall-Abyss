# Starfall Abyss - Discord RPG Bot

## Overview

Starfall Abyss is a comprehensive Discord RPG bot featuring a class-based progression system, combat mechanics, dungeon exploration, guild management, and extensive crafting systems. The bot uses a JSON-based file storage system for player data persistence and implements a rich user interface using Discord's UI components.

## System Architecture

### Core Architecture
- **Language**: Python 3.11
- **Framework**: discord.py library for Discord bot functionality
- **Data Storage**: JSON file-based persistence (player_data.json)
- **Architecture Pattern**: Modular command-based system with separate modules for different game features

### Key Design Decisions
- **File-based Storage**: Uses JSON files for simplicity and easy debugging, with backup mechanisms
- **Modular Design**: Each major feature (battle system, dungeons, guilds, etc.) is implemented in separate modules
- **UI-driven Interactions**: Extensive use of Discord's Button and Select UI components for rich user experiences
- **User Restriction System**: Implements authorization checks to ensure users can only interact with their own command interfaces

## Key Components

### Data Models (`data_models.py`)
- **PlayerData**: Core player information including level, experience, stats, inventory, and guild membership
- **Item**: Equipment and consumable items with stats, rarity, and level requirements
- **InventoryItem**: Wrapper for items in player inventory with quantity and equipped status
- **DataManager**: Handles all file I/O operations and data persistence

### Battle System (`battle_system.py`, `battle_system_new.py`)
- **BattleEntity**: Represents combatants (players or enemies) with stats and abilities
- **BattleMove**: Defines combat actions with damage multipliers and energy costs
- **Energy Scaling**: Dynamic energy system that scales with player level and training
- **Status Effects**: Temporary buffs/debuffs during combat

### Class System (`utils.py`, `class_change.py`)
- **Starter Classes**: Spirit Striker, Domain Tactician, Flash Rogue
- **Advanced Classes**: Unlockable through progression requirements
- **Class Abilities**: Each class has unique active and passive abilities
- **Class Change**: Players can switch classes with appropriate requirements

### Equipment & Shopping (`equipment.py`, `advanced_shop.py`)
- **Tiered Items**: Equipment scaled by level ranges (1-100+)
- **Rarity System**: Common to Divine tier items with stat multipliers
- **Dynamic Generation**: Procedurally generated items with random stats
- **Special Items**: Unique items with special effects and abilities

### Dungeon System (`dungeons.py`)
- **Progressive Difficulty**: Dungeons scaled from level 1-100
- **Multi-floor Structure**: Each dungeon has multiple floors with increasing difficulty
- **Boss Encounters**: Unique boss fights with special rewards
- **Rare Drops**: Chance for special items and materials

### Guild System (`guild_system.py`)
- **Guild Creation**: Players can create and manage guilds
- **Guild Progression**: Leveling system with unlockable perks
- **Guild Bank**: Shared resources and currency management
- **Guild Challenges**: Weekly objectives for guild members

### Materials & Crafting (`materials.py`, `crafting_system.py`)
- **Material Gathering**: Multiple gathering skills (mining, foraging, fishing)
- **Crafting Categories**: Weapons, armor, accessories, potions, tools
- **Recipe System**: Complex crafting recipes requiring multiple material types
- **Quality Tiers**: Materials and crafted items have rarity levels

### Training & Skills (`training.py`, `advanced_training.py`, `skill_tree.py`)
- **Attribute Training**: Improve core stats through mini-games
- **Skill Trees**: Multiple progression paths for different playstyles
- **Cooldown System**: Time-based limitations on training activities
- **Special Rewards**: Bonus effects for perfect performance

### User Interface & Restrictions (`user_restrictions.py`)
- **Authorized Interactions**: Ensures only command authors can use their interfaces
- **RestrictedView**: Base class for all UI components with user validation
- **Error Handling**: Clear feedback when unauthorized users attempt interactions

## Data Flow

### Player Progression
1. **Character Creation**: Players select starting class and receive initial stats/equipment
2. **Experience Gain**: Combat, dungeons, and activities provide experience points
3. **Level Validation**: Automatic correction system ensures consistent level/XP relationships
4. **Stat Growth**: Training systems allow targeted improvement of specific attributes
5. **Class Evolution**: Advanced classes unlock through meeting specific requirements

### Combat Flow
1. **Battle Initiation**: PvE or PvP combat with enemy generation or player matching
2. **Turn-based Combat**: Players select moves using energy-based action economy
3. **Damage Calculation**: Complex formulas considering stats, equipment, and class bonuses
4. **Status Effects**: Temporary modifications to combat capabilities
5. **Reward Distribution**: Experience, currency, and potential item drops

### Economy System
1. **Currency Management**: Gold and cursed energy as primary currencies
2. **Item Trading**: Player-to-player trading system with offer/acceptance mechanics
3. **Shop Integration**: Tiered shops with level-appropriate items
4. **Guild Economy**: Shared resources and guild bank contributions

## External Dependencies

### Core Dependencies
- **discord.py**: Primary Discord API interface
- **python-dotenv**: Environment variable management for bot tokens
- **Standard Library**: json, datetime, random, asyncio, typing

### Development Tools
- **Replit Environment**: Cloud-based development with Python 3.11
- **Git Integration**: Version control through .gitignore configuration

## Deployment Strategy

### Replit Deployment
- **Run Configuration**: Automatic pip install and python execution
- **Environment Variables**: Bot token managed through .env file
- **Persistent Storage**: JSON files for data persistence across restarts

### Bot Permissions
- **Required Intents**: Message content intent for command processing
- **Optional Intents**: Server members intent for enhanced functionality (commented for testing)
- **Scope Requirements**: Bot needs send messages, use slash commands, and embed links permissions

### Scalability Considerations
- **File-based Storage**: Current JSON approach suitable for small to medium communities
- **Database Migration Path**: Architecture supports future migration to Postgres/Drizzle ORM
- **Modular Structure**: Easy to add new features without affecting existing systems

## Changelog

- June 16, 2025. Initial setup
- June 16, 2025. Fixed advanced training system difficulty scaling:
  - Increased time windows by 1+ seconds for all difficulties (Basic: 4.5s, Advanced: 3.5s, Master: 2.8s)
  - Expanded target zones for timing games (Master difficulty now 18% instead of 10%)
  - Added extra targets for precision training (Basic: 4, Advanced: 6, Master: 8)
  - Improved grid scaling for reaction training (3x3 Basic, 4x4 Advanced/Master)
  - Fixed timing bar interaction error and improved visual feedback
  - Enhanced sequence memorization with longer study times
  - Reduced animation delay for better responsiveness (0.05s frames)

## User Preferences

Preferred communication style: Simple, everyday language.