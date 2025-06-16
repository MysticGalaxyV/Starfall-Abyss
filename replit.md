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
- June 16, 2025. Fixed core game bugs:
  - Leaderboard: Removed duplicate level display when sorting by level
  - Leaderboard: Improved player name display with cleaner fallback format
  - XP Events: Fixed 2x XP boost multiplier system - now properly applies to all XP gains
  - Achievements: Added automatic checking after battle victories and level ups
  - Quests: Enhanced quest progress tracking for battle victories and gold rewards
- June 16, 2025. Fixed training system exploits and data corruption:
  - Training Spam: Added state management to prevent multiple button clicks bypassing cooldowns
  - Data Corruption: Fixed achievements saving errors by adding defensive programming for corrupted data
  - Achievement Display: Added achievement summary messages to both basic and advanced training completion
  - User Experience: Training now shows clear feedback when spam clicking is attempted
- June 16, 2025. Fully implemented Double XP event system:
  - Fixed add_exp method to properly handle event multipliers across all systems
  - Battle rewards now display event bonuses (e.g., "50 XP → 100 XP (🎉 Double XP Weekend 2x!)")
  - Advanced training system now uses proper event-aware XP method
  - Admin XP commands updated to show event multipliers when active
  - Enhanced visual feedback for all XP gains when events are running
  - Events can be managed via !event command (admin only)
- June 16, 2025. Fixed tool equipping system:
  - Removed duplicate equipped_gathering_tools definition in PlayerData class
  - Enhanced tool detection to support both item_type='tool' and name pattern matching
  - Added level requirement validation for tool equipping
  - Improved efficiency calculation system with tier-based bonuses
  - Fixed tool callback validation and error handling
  - Added test tools to player inventory for validation
  - Players can now equip one tool per gathering type (Mining, Foraging, Herbs, Hunting, Magical)
- June 16, 2025. Fixed gathering system tool recognition:
  - Fixed "No Tool" issue where equipped tools weren't being detected during gathering
  - Improved get_best_tool function to properly match tools across different categories
  - Enhanced tool detection logic to handle cross-category tool usage (e.g., Iron Axe for Mining)
  - Added simplified efficiency calculation that works regardless of tool categorization
  - Fixed duplicate option values error in tool selection dropdown menus
- June 16, 2025. Enhanced tool equipping system display and functionality:
  - Added clear tool usage display during gathering operations
  - Enhanced gathering results to show equipped tool and efficiency bonus
  - Improved tool selection interface with level requirements and efficiency ratings
  - Added better error handling and safe value mapping for dropdown selections
  - Enhanced visual feedback with emojis and clear status indicators
- June 16, 2025. Implemented universal dual weapon equipping system:
  - Enabled dual wielding for all player classes (removed class restrictions)
  - Enhanced equipment system to support weapon2 slot for off-hand weapons
  - Implemented 75% damage penalty for off-hand weapon power bonuses
  - Updated equipment display to show "Main Hand" and "Off Hand" weapon slots
  - Enhanced stats calculation to properly handle both weapons with appropriate penalties
  - Added comprehensive null safety checks for class validation
  - Simplified system by allowing all players to use dual weapons
- June 16, 2025. Unified battle and dungeon move systems:
  - Updated main.py to use battle_system.py instead of battle_system_new.py
  - Both battle command and dungeon encounters now use identical move sets from unified_moves.py
  - All player classes now have consistent abilities across all combat scenarios
- June 16, 2025. Rebalanced battle XP rewards:
  - Battle XP now gives exactly 25% (1/4) of total dungeon completion XP
  - Level 1-4: 12-13 XP per battle (25% of 50 XP Ancient Forest completion)
  - Level 20-24: 125 XP per battle (25% of 500 XP Infernal Citadel completion)
  - Level 50+: 750+ XP per battle (25% of 3000+ XP Astral Nexus completion)
  - Maintains level difference modifiers for fighting stronger/weaker enemies
  - Creates balanced progression where 4 battles equals one dungeon completion
- June 16, 2025. Fixed leaderboard and equipment system bugs:
  - Leaderboard: Fixed username display to show Discord names instead of player IDs
  - Equipment: Fixed equip button errors by adding weapon2 key migration for existing players
  - Equipment: Cleaned up tool name display by removing "Cursed Tool:" prefix from weapon names
  - Dual Wielding: Restored proper class restrictions - only Flash Rogue and Shadow Assassin can dual wield
  - Data Migration: Added automatic cleanup for invalid weapon configurations on player load
- June 16, 2025. Fixed achievement system completion notifications:
  - Battle System: Added achievement display after battle victories with detailed reward information
  - Dungeon System: Added achievement notifications after dungeon completions
  - Level Up System: Enhanced level-up achievement checking for comprehensive coverage
  - Achievement Display: Improved notification format showing badges, points, descriptions, and rewards
  - Data Flow: Fixed missing achievement checking calls throughout major progression systems
  - User Experience: Players now see immediate feedback when completing achievements
- June 16, 2025. Rebalanced achievement shop pricing with even numbers:
  - Server Roles: 150 points each (5 roles × 150 = 750 points total)
  - Profile Tags: 50 points each for 9 tags + 40 points for Ascended Champion tag = 490 points total
  - All prices are now even numbers for cleaner presentation
  - Total shop value remains exactly 1,240 achievement points as requested
  - Improved balance between premium roles and cosmetic tags for better player accessibility
- June 16, 2025. Completely fixed achievement system stat tracking and synchronization:
  - Root Cause: Achievement system expected `dungeons_completed` field but game only updated `dungeon_clears` dictionary
  - Data Synchronization: Added proper stat tracking in dungeon completion system for `dungeons_completed` and `bosses_defeated`
  - Battle Stats: Enhanced battle system to track `gold_earned` for achievement requirements
  - Migration Script: Created sync_achievement_stats.py to fix existing player data (updated 26 dungeon completions for main player)
  - Achievement Validation: Verified system now properly awards achievements (tested: Dungeon Crawler, Dungeon Master, Boss Hunter)
  - System Integration: Achievement checking now works correctly across battles, dungeons, and level-ups with proper stat tracking
- June 16, 2025. Completely eliminated cursed energy currency and unified all systems to use gold:
  - Currency Unification: Removed cursed energy as separate currency, all rewards now use gold exclusively
  - Achievement System: Updated all achievement rewards to use gold instead of cursed energy
  - Training System: Advanced training special rewards now award gold for perfect scores
  - Trading System: Player-to-player trading interface updated to handle gold transactions only
  - Data Models: Added legacy methods (add_cursed_energy/remove_cursed_energy) for backward compatibility that redirect to gold methods
  - Migration Support: Created conversion script to migrate any existing cursed energy balances to gold
  - System Simplification: Single currency system reduces complexity and improves user experience
- June 16, 2025. Fixed critical bot runtime errors and ensured smooth operation:
  - Backward Compatibility: Added cursed_energy property to PlayerData class for legacy code support
  - Achievement System: Fixed advanced shop achievement checking to handle both Achievement objects and dictionary formats
  - Error Resolution: Eliminated AttributeError exceptions in profile and shop commands
  - Data Integrity: Verified all core systems (battles, shops, profiles) function without errors
  - Import Validation: Confirmed all modules load correctly without initialization failures

## User Preferences

Preferred communication style: Simple, everyday language.