import discord
from discord.ui import Button, View, Select
import asyncio
import datetime
import random
import math
from typing import Dict, List, Optional, Tuple, Any, Union

from data_models import PlayerData, DataManager
from user_restrictions import RestrictedView

class Guild:
    def __init__(self, name: str, leader_id: int, created_at: datetime.datetime = None):
        self.name = name
        self.leader_id = leader_id
        self.created_at = created_at or datetime.datetime.now()
        self.description = "A guild of adventurers"
        self.level = 1
        self.exp = 0
        self.max_members = 20  # Base max members
        self.members = [leader_id]  # Start with leader
        self.officers = []  # Officer IDs (can invite, kick, etc.)
        self.bank = 0  # Guild bank cursed energy
        self.motd = "Welcome to the guild!"  # Message of the day
        self.emblem = "⚔️"  # Default emblem
        self.color = discord.Color.dark_purple().value  # Guild color (stored as int)
        self.achievements = []  # Guild achievements
        self.achievements_progress = {}  # Progress tracking for achievements
        self.upgrades = {
            "bank_level": 1,
            "member_capacity": 1,
            "exp_boost": 1,
            "cursed_energy_boost": 1  # Renamed from gold_boost
        }

        # Perks based on guild level
        self.perks = {
            # Level 1
            1: {"name": "United We Stand", "description": "Guild members gain +1% XP when adventuring together"},
            # Level 2
            2: {"name": "Shared Resources", "description": "10% chance for extra item drops when in guild parties"},
            # Level 3
            3: {"name": "Guild Tactics", "description": "Guild members deal +2% damage in dungeons"},
            # Level 5
            5: {"name": "Brotherhood", "description": "Guild members gain +5% cursed energy when adventuring together"},
            # Level 10
            10: {"name": "Elite Force", "description": "Guild members gain +5% to all stats in guild raids"}
        }

        # Guild weekly challenges
        self.weekly_challenges = []
        self.weekly_reset = datetime.datetime.now() + datetime.timedelta(days=7)

        # Raid progress
        self.current_raid = None
        self.raid_progress = {}

        # Daily contribution tracking
        self.daily_contributions = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert Guild to dictionary for storage"""
        return {
            "name": self.name,
            "leader_id": self.leader_id,
            "created_at": self.created_at.isoformat(),
            "description": self.description,
            "level": self.level,
            "exp": self.exp,
            "max_members": self.max_members,
            "members": self.members,
            "officers": self.officers,
            "bank": self.bank,
            "motd": self.motd,
            "emblem": self.emblem,
            "color": self.color,
            "achievements": self.achievements,
            "achievements_progress": self.achievements_progress,
            "upgrades": self.upgrades,
            "weekly_challenges": self.weekly_challenges,
            "weekly_reset": self.weekly_reset.isoformat(),
            "current_raid": self.current_raid,
            "raid_progress": self.raid_progress,
            "daily_contributions": self.daily_contributions
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Guild':
        """Create Guild from dictionary data"""
        guild = cls(data["name"], data["leader_id"])
        guild.created_at = datetime.datetime.fromisoformat(data["created_at"])
        guild.description = data["description"]
        guild.level = data["level"]
        guild.exp = data["exp"]
        guild.max_members = data["max_members"]
        guild.members = data["members"]
        guild.officers = data["officers"]
        guild.bank = data["bank"]
        guild.motd = data["motd"]
        guild.emblem = data["emblem"]
        guild.color = data["color"]
        guild.achievements = data["achievements"]
        guild.achievements_progress = data["achievements_progress"]
        guild.upgrades = data["upgrades"]
        guild.weekly_challenges = data["weekly_challenges"]
        guild.weekly_reset = datetime.datetime.fromisoformat(data["weekly_reset"])
        guild.current_raid = data["current_raid"]
        guild.raid_progress = data["raid_progress"]
        guild.daily_contributions = data["daily_contributions"]
        return guild

    def add_exp(self, exp_amount: int) -> bool:
        """Add experience to guild and handle level ups. Returns True if leveled up."""
        self.exp += exp_amount

        # Check for level up
        exp_required = calculate_guild_exp_for_level(self.level)
        if self.exp >= exp_required:
            self.level += 1
            self.max_members = 20 + (5 * (self.level - 1))  # Increase max members with level
            return True

        return False

    def is_officer(self, member_id: int) -> bool:
        """Check if member is an officer or leader"""
        return member_id == self.leader_id or member_id in self.officers

    def can_manage_guild(self, member_id: int) -> bool:
        """Check if member has guild management permissions"""
        return member_id == self.leader_id or member_id in self.officers

    def add_member(self, member_id: int) -> bool:
        """Add member to guild if there's space"""
        if len(self.members) < self.max_members and member_id not in self.members:
            self.members.append(member_id)
            return True
        return False

    def remove_member(self, member_id: int) -> bool:
        """Remove member from guild"""
        if member_id in self.members and member_id != self.leader_id:
            self.members.remove(member_id)
            # Also remove from officers if they are one
            if member_id in self.officers:
                self.officers.remove(member_id)
            return True
        return False

    def promote_member(self, member_id: int) -> bool:
        """Promote a member to officer"""
        if member_id in self.members and member_id not in self.officers and member_id != self.leader_id:
            self.officers.append(member_id)
            return True
        return False

    def demote_officer(self, member_id: int) -> bool:
        """Demote an officer to regular member"""
        if member_id in self.officers:
            self.officers.remove(member_id)
            return True
        return False

    def deposit_gold(self, amount: int) -> bool:
        """Deposit gold into guild bank"""
        self.bank += amount
        return True

    # Legacy method for backward compatibility
    def deposit_cursed_energy(self, amount: int) -> bool:
        """Legacy method that calls deposit_gold"""
        return self.deposit_gold(amount)

    def withdraw_gold(self, amount: int) -> bool:
        """Withdraw gold from guild bank if available"""
        if self.bank >= amount:
            self.bank -= amount
            return True
        return False

    # Legacy method for backward compatibility
    def withdraw_cursed_energy(self, amount: int) -> bool:
        """Legacy method that calls withdraw_gold"""
        return self.withdraw_gold(amount)

    def get_active_perks(self) -> List[Dict[str, str]]:
        """Get all perks active at current guild level"""
        active_perks = []
        for level, perk in self.perks.items():
            if level <= self.level:
                active_perks.append(perk)
        return active_perks

# Guild achievements
GUILD_ACHIEVEMENTS = {
    "first_steps": {
        "name": "First Steps",
        "description": "Reach Guild Level 5",
        "reward": {"gold": 1000, "exp": 500},
        "icon": "👣"
    },
    "rising_force": {
        "name": "Rising Force",
        "description": "Reach Guild Level 10",
        "reward": {"gold": 5000, "exp": 2000},
        "icon": "⬆️"
    },
    "legendary_guild": {
        "name": "Legendary Guild",
        "description": "Reach Guild Level 20",
        "reward": {"gold": 20000, "exp": 10000},
        "icon": "🌟"
    },
    "recruiting_drive": {
        "name": "Recruiting Drive",
        "description": "Have 10 members in your guild",
        "reward": {"gold": 1000, "exp": 300},
        "icon": "👥"
    },
    "full_house": {
        "name": "Full House",
        "description": "Reach maximum guild capacity",
        "reward": {"gold": 5000, "exp": 1000},
        "icon": "🏠"
    },
    "dungeon_masters": {
        "name": "Dungeon Masters",
        "description": "Complete 50 dungeons with guild members",
        "reward": {"gold": 3000, "exp": 1500},
        "icon": "🔍"
    },
    "treasure_hoard": {
        "name": "Treasure Hoard",
        "description": "Accumulate 50,000 cursed energy in the guild bank",
        "reward": {"gold": 5000, "exp": 2000},
        "icon": "💰"
    }
}

# Guild upgrades and their costs
GUILD_UPGRADES = {
    "bank_level": {
        "name": "Bank Upgrade",
        "description": "Increase guild bank capacity and interest rate",
        "max_level": 5,
        "cost_formula": lambda level: 5000 * level,
        "benefit_formula": lambda level: f"Bank capacity: {100000 * level} cursed energy, Interest: {0.5 * level}% daily"
    },
    "member_capacity": {
        "name": "Member Capacity",
        "description": "Increase maximum guild member capacity",
        "max_level": 5,
        "cost_formula": lambda level: 8000 * level,
        "benefit_formula": lambda level: f"+{5 * level} maximum members"
    },
    "exp_boost": {
        "name": "Experience Boost",
        "description": "Boost experience gains for all guild members",
        "max_level": 5,
        "cost_formula": lambda level: 10000 * level,
        "benefit_formula": lambda level: f"+{level}% experience gained"
    },
    "gold_boost": {
        "name": "Gold Boost",
        "description": "Boost gold gains for all guild members",
        "max_level": 5,
        "cost_formula": lambda level: 10000 * level,
        "benefit_formula": lambda level: f"+{level}% gold gained"
    }
}

# Weekly guild challenges
GUILD_WEEKLY_CHALLENGES = [
    {
        "id": "dungeon_conquerors",
        "name": "Dungeon Conquerors",
        "description": "Complete 20 dungeons as a guild",
        "target": 20,
        "reward": {"exp": 1000, "gold": 2000},
        "type": "dungeons_completed"
    },
    {
        "id": "monster_hunters",
        "name": "Monster Hunters",
        "description": "Defeat 100 monsters as a guild",
        "target": 100,
        "reward": {"exp": 1500, "gold": 3000},
        "type": "monsters_defeated"
    },
    {
        "id": "gold_collectors",
        "name": "Gold Collectors",
        "description": "Collect 10,000 gold as a guild",
        "target": 10000,
        "reward": {"exp": 2000, "gold": 5000},
        "type": "gold_collected"
    },
    {
        "id": "item_finders",
        "name": "Item Finders",
        "description": "Find 50 items of uncommon or higher rarity",
        "target": 50,
        "reward": {"exp": 1800, "gold": 4000},
        "type": "items_found"
    }
]

# Guild raids
GUILD_RAIDS = {
    "ancient_dragon": {
        "name": "Ancient Dragon",
        "description": "A legendary dragon hoarding treasure for centuries",
        "level_req": 5,
        "members_req": 5,
        "stages": 3,
        "reward": {"exp": 5000, "cursed_energy": 10000, "special_item": "Dragon Scale Armor"},
        "enemy_types": ["dragon"],
        "duration": 3  # days to complete
    },
    "shadow_citadel": {
        "name": "Shadow Citadel",
        "description": "A fortress ruled by the Shadow Lord",
        "level_req": 10,
        "members_req": 8,
        "stages": 5,
        "reward": {"exp": 10000, "cursed_energy": 20000, "special_item": "Shadow Lord's Crown"},
        "enemy_types": ["undead", "shadow"],
        "duration": 5  # days to complete
    },
    "abyssal_depths": {
        "name": "Abyssal Depths",
        "description": "A realm of ancient horrors beneath the ocean",
        "level_req": 15,
        "members_req": 10,
        "stages": 7,
        "reward": {"exp": 20000, "cursed_energy": 40000, "special_item": "Trident of the Depths"},
        "enemy_types": ["aquatic", "eldritch"],
        "duration": 7  # days to complete
    }
}

def calculate_guild_exp_for_level(level: int) -> int:
    """Calculate experience required for the next guild level"""
    return 1000 * level * level

class GuildManager:
    def __init__(self, data_manager: DataManager):
        self.data_manager = data_manager
        self.guilds = {}  # name -> Guild
        self.member_guild_map = {}  # user_id -> guild_name

        # Load guild data
        self.load_guilds()

    def load_guilds(self):
        """Load guild data from data manager"""
        if not hasattr(self.data_manager, "guild_data"):
            self.data_manager.guild_data = {}
            self.data_manager.member_guild_map = {}
            self.data_manager.save_data()
        else:
            # Load existing guilds
            for guild_name, guild_data in self.data_manager.guild_data.items():
                self.guilds[guild_name] = Guild.from_dict(guild_data)

            # Load member -> guild mapping
            self.member_guild_map = self.data_manager.member_guild_map.copy()

    def save_guilds(self):
        """Save guild data to data manager"""
        self.data_manager.guild_data = {name: guild.to_dict() for name, guild in self.guilds.items()}
        self.data_manager.member_guild_map = self.member_guild_map.copy()
        self.data_manager.save_data()

    def create_guild(self, name: str, leader_id: int, player_data: PlayerData) -> Tuple[bool, str]:
        """Create a new guild if name is available and player meets requirements"""
        # Check if name is already taken
        if name in self.guilds:
            return False, "A guild with that name already exists."

        # Check if player is already in a guild
        if leader_id in self.member_guild_map:
            return False, "You are already in a guild. Leave your current guild first."

        # Check if player meets level requirement (level 5) - lowered from 10 for better accessibility
        if player_data.class_level < 5:
            return False, f"You must be at least level 5 to create a guild. You are currently level {player_data.class_level}."

        # Check if player has enough cursed energy (1000)
        if player_data.gold < 1000:
            return False, f"You need 1000 💰 gold to create a guild. You currently have {player_data.gold} 💰."

        # Create new guild
        new_guild = Guild(name, leader_id)
        self.guilds[name] = new_guild

        # Update member mapping
        self.member_guild_map[leader_id] = name

        # Deduct cursed energy
        player_data.remove_gold(1000)

        # Save data
        self.save_guilds()
        self.data_manager.save_data()  # Save player data with updated cursed energy

        return True, f"Guild '{name}' has been created for 1000 cursed energy! You are now the leader."

    def get_guild_by_name(self, name: str) -> Optional[Guild]:
        """Get guild by name"""
        return self.guilds.get(name)

    def get_player_guild(self, player_id: int) -> Optional[Guild]:
        """Get a player's guild if they're in one"""
        guild_name = self.member_guild_map.get(player_id)
        if guild_name:
            return self.guilds.get(guild_name)
        return None

    def add_member_to_guild(self, guild_name: str, player_id: int) -> Tuple[bool, str]:
        """Add a player to a guild"""
        # Check if guild exists
        guild = self.guilds.get(guild_name)
        if not guild:
            return False, "Guild does not exist."

        # Check if player is already in a guild
        if player_id in self.member_guild_map:
            return False, "Player is already in a guild."

        # Check if guild has space
        if len(guild.members) >= guild.max_members:
            return False, "Guild is already at maximum capacity."

        # Add member
        guild.add_member(player_id)
        self.member_guild_map[player_id] = guild_name

        # Save data
        self.save_guilds()

        return True, f"You have joined the guild '{guild_name}'!"

    def remove_member_from_guild(self, player_id: int) -> Tuple[bool, str]:
        """Remove a player from their guild"""
        # Check if player is in a guild
        guild_name = self.member_guild_map.get(player_id)
        if not guild_name:
            return False, "You are not in a guild."

        guild = self.guilds.get(guild_name)
        if not guild:
            # Inconsistent state - fix by removing player from mapping
            if player_id in self.member_guild_map:
                del self.member_guild_map[player_id]
                self.save_guilds()
            return False, "Guild not found. Your guild membership has been reset."

        # Check if player is the leader
        if player_id == guild.leader_id:
            # Check if there are other members
            if len(guild.members) > 1:
                return False, "You are the guild leader. You must promote another member to leader before leaving."
            else:
                # Last member is leaving, disband the guild
                del self.guilds[guild_name]
                del self.member_guild_map[player_id]
                self.save_guilds()
                return True, f"As the last member, you have disbanded the guild '{guild_name}'."

        # Remove from guild
        guild.remove_member(player_id)
        del self.member_guild_map[player_id]

        # Save data
        self.save_guilds()

        return True, f"You have left the guild '{guild_name}'."

    def promote_member(self, leader_id: int, target_id: int) -> Tuple[bool, str]:
        """Promote a guild member to officer"""
        # Check if leader is in a guild
        guild_name = self.member_guild_map.get(leader_id)
        if not guild_name:
            return False, "You are not in a guild."

        guild = self.guilds.get(guild_name)
        if not guild:
            return False, "Guild not found."

        # Check if player is the leader
        if leader_id != guild.leader_id:
            return False, "Only the guild leader can promote members."

        # Check if target is in the guild
        if target_id not in guild.members:
            return False, "That player is not in your guild."

        # Check if already an officer
        if target_id in guild.officers:
            return False, "That player is already an officer."

        # Promote
        guild.promote_member(target_id)

        # Save data
        self.save_guilds()

        return True, "Member has been promoted to guild officer."

    def transfer_leadership(self, leader_id: int, new_leader_id: int) -> Tuple[bool, str]:
        """Transfer guild leadership to another member"""
        # Check if current leader is in a guild
        guild_name = self.member_guild_map.get(leader_id)
        if not guild_name:
            return False, "You are not in a guild."

        guild = self.guilds.get(guild_name)
        if not guild:
            return False, "Guild not found."

        # Check if player is the leader
        if leader_id != guild.leader_id:
            return False, "Only the guild leader can transfer leadership."

        # Check if new leader is in the guild
        if new_leader_id not in guild.members:
            return False, "That player is not in your guild."

        # Transfer leadership
        guild.leader_id = new_leader_id

        # Add old leader to officers if not already
        if leader_id not in guild.officers:
            guild.officers.append(leader_id)

        # Save data
        self.save_guilds()

        return True, "Guild leadership has been transferred."

    def rename_guild(self, leader_id: int, new_name: str) -> Tuple[bool, str]:
        """Rename a guild (leader only)"""
        # Check if leader is in a guild
        guild_name = self.member_guild_map.get(leader_id)
        if not guild_name:
            return False, "You are not in a guild."

        guild = self.guilds.get(guild_name)
        if not guild:
            return False, "Guild not found."

        # Check if user is the leader
        if guild.leader_id != leader_id:
            return False, "Only the guild leader can rename the guild."

        # Check if new name is already taken
        if new_name in self.guilds and new_name != guild_name:
            return False, f"The name '{new_name}' is already taken by another guild."

        # Check if new name is valid
        if len(new_name) < 3 or len(new_name) > 32:
            return False, "Guild name must be between 3 and 32 characters."

        # No need to rename if it's the same name
        if new_name == guild_name:
            return False, "That's already your guild's name."

        # Create new guild entry with same data but new name
        self.guilds[new_name] = guild
        self.guilds[new_name].name = new_name

        # Update member mappings
        for member_id in guild.members:
            self.member_guild_map[member_id] = new_name

        # Remove old guild entry
        del self.guilds[guild_name]

        # Save data
        self.save_guilds()

        return True, f"Guild has been renamed from '{guild_name}' to '{new_name}'."

    def contribute_to_guild(self, player_id: int, contribution_amount: int) -> Tuple[bool, str, int]:
        """Contribute gold to guild and gain contribution points"""
        # Check if player is in a guild
        guild_name = self.member_guild_map.get(player_id)
        if not guild_name:
            return False, "You are not in a guild.", 0

        guild = self.guilds.get(guild_name)
        if not guild:
            return False, "Guild not found.", 0

        # Get today's date as string for contribution tracking
        today = datetime.datetime.now().strftime("%Y-%m-%d")

        # Initialize daily contribution tracking if needed
        if today not in guild.daily_contributions:
            guild.daily_contributions[today] = {}

        # Initialize player contribution if needed
        if str(player_id) not in guild.daily_contributions[today]:
            guild.daily_contributions[today][str(player_id)] = 0

        # Add gold to guild bank
        guild.bank += contribution_amount

        # Add contribution points (1 point per 10 gold)
        contribution_points = contribution_amount // 10
        guild.daily_contributions[today][str(player_id)] += contribution_points

        # Update quest progress for guild contribution
        try:
            from achievements import QuestManager
            player_data = self.data_manager.get_player(player_id)
            if player_data:
                quest_manager = QuestManager(self.data_manager)
                quest_manager.update_quest_progress(player_data, "weekly_guild_contribution", contribution_amount)
        except (ImportError, AttributeError):
            pass  # QuestManager not available, skip quest tracking

        # Save data
        self.save_guilds()

        return True, f"You contributed {contribution_amount} 💰 gold to the guild bank.", contribution_points

    def add_guild_exp(self, guild_name: str, exp_amount: int) -> Tuple[bool, bool]:
        """Add experience to a guild. Returns (success, leveled_up)"""
        # Check if guild exists
        guild = self.guilds.get(guild_name)
        if not guild:
            return False, False

        # Add exp and check for level up
        leveled_up = guild.add_exp(exp_amount)

        # Save data
        self.save_guilds()

        return True, leveled_up

    def get_top_guilds(self, count: int = 10) -> List[Dict[str, Any]]:
        """Get top guilds by level and exp"""
        guild_list = [
            {
                "name": name,
                "level": guild.level,
                "exp": guild.exp,
                "members": len(guild.members),
                "leader_id": guild.leader_id,
                "emblem": guild.emblem
            }
            for name, guild in self.guilds.items()
        ]

        # Sort by level first, then by exp
        guild_list.sort(key=lambda g: (g["level"], g["exp"]), reverse=True)

        return guild_list[:count]

class GuildInfoView(RestrictedView):
    def __init__(self, guild: Guild, guild_manager: GuildManager, player_data: PlayerData, authorized_user):
        super().__init__(authorized_user, timeout=60)
        self.guild = guild
        self.guild_manager = guild_manager
        self.player_data = player_data

        # Check if player is in the guild
        self.is_member = player_data.user_id in guild.members
        self.is_leader = player_data.user_id == guild.leader_id
        self.is_officer = guild.is_officer(player_data.user_id)

        # Add buttons based on permissions
        self.add_info_buttons()

    def add_info_buttons(self):
        # View members button
        members_btn = Button(
            label="Members",
            style=discord.ButtonStyle.primary,
            emoji="👥"
        )
        members_btn.callback = self.members_callback
        self.add_item(members_btn)

        # View achievements button
        achievements_btn = Button(
            label="Achievements", 
            style=discord.ButtonStyle.primary,
            emoji="🏆"
        )
        achievements_btn.callback = self.achievements_callback
        self.add_item(achievements_btn)

        # View upgrades button
        upgrades_btn = Button(
            label="Upgrades",
            style=discord.ButtonStyle.primary, 
            emoji="⬆️"
        )
        upgrades_btn.callback = self.upgrades_callback
        self.add_item(upgrades_btn)

        # Add guild-specific buttons if player is a member
        if self.is_member:
            # Contribute button
            contribute_btn = Button(
                label="Contribute",
                style=discord.ButtonStyle.success,
                emoji="💰"
            )
            contribute_btn.callback = self.contribute_callback
            self.add_item(contribute_btn)

            # Leave guild button (not for leader)
            if not self.is_leader:
                leave_btn = Button(
                    label="Leave Guild",
                    style=discord.ButtonStyle.danger,
                    emoji="🚪"
                )
                leave_btn.callback = self.leave_callback
                self.add_item(leave_btn)

        # Add management buttons for leaders and officers
        if self.is_leader or self.is_officer:
            manage_btn = Button(
                label="Manage Guild",
                style=discord.ButtonStyle.secondary,
                emoji="⚙️"
            )
            manage_btn.callback = self.manage_callback
            self.add_item(manage_btn)

    async def members_callback(self, interaction: discord.Interaction):
        """Show guild members list"""
        members_embed = discord.Embed(
            title=f"{self.guild.emblem} {self.guild.name} - Members",
            description=f"Total Members: {len(self.guild.members)}/{self.guild.max_members}",
            color=discord.Color(self.guild.color)
        )

        # Get member data from bot
        bot = interaction.client

        # Leader section
        leader_id = self.guild.leader_id
        leader_user = await bot.fetch_user(leader_id)
        leader_name = leader_user.display_name if leader_user else f"User ID: {leader_id}"

        members_embed.add_field(
            name="👑 Leader",
            value=leader_name,
            inline=False
        )

        # Officers section
        if self.guild.officers:
            officer_names = []
            for officer_id in self.guild.officers:
                officer_user = await bot.fetch_user(officer_id)
                officer_name = officer_user.display_name if officer_user else f"User ID: {officer_id}"
                officer_names.append(officer_name)

            members_embed.add_field(
                name="🔰 Officers",
                value="\n".join(officer_names) if officer_names else "None",
                inline=False
            )

        # Regular members
        regular_members = [m for m in self.guild.members if m != leader_id and m not in self.guild.officers]
        if regular_members:
            member_names = []
            for member_id in regular_members:
                member_user = await bot.fetch_user(member_id)
                member_name = member_user.display_name if member_user else f"User ID: {member_id}"
                member_names.append(member_name)

            # Split into columns if many members
            if len(member_names) > 10:
                # Create columns
                columns = []
                column_size = (len(member_names) + 2) // 3  # Distribute across 3 columns
                for i in range(0, len(member_names), column_size):
                    columns.append("\n".join(member_names[i:i+column_size]))

                for i, column in enumerate(columns):
                    members_embed.add_field(
                        name=f"Members ({i+1}/{len(columns)})",
                        value=column,
                        inline=True
                    )
            else:
                members_embed.add_field(
                    name="Members",
                    value="\n".join(member_names),
                    inline=False
                )

        await interaction.response.edit_message(embed=members_embed, view=self)

    async def achievements_callback(self, interaction: discord.Interaction):
        """Show guild achievements"""
        achievements_embed = discord.Embed(
            title=f"{self.guild.emblem} {self.guild.name} - Achievements",
            description="Achievements and accomplishments of your guild",
            color=discord.Color(self.guild.color)
        )

        # Completed achievements
        completed = []
        for achievement_id in self.guild.achievements:
            if achievement_id in GUILD_ACHIEVEMENTS:
                achievement = GUILD_ACHIEVEMENTS[achievement_id]
                completed.append(f"{achievement['icon']} **{achievement['name']}** - {achievement['description']}")

        if completed:
            achievements_embed.add_field(
                name="🏆 Completed Achievements",
                value="\n".join(completed),
                inline=False
            )

        # In-progress achievements
        in_progress = []
        for achievement_id, achievement in GUILD_ACHIEVEMENTS.items():
            if achievement_id not in self.guild.achievements:
                if achievement_id in self.guild.achievements_progress:
                    progress = self.guild.achievements_progress[achievement_id]
                    in_progress.append(f"{achievement['icon']} **{achievement['name']}** - {progress}")
                else:
                    in_progress.append(f"{achievement['icon']} **{achievement['name']}** - {achievement['description']}")

        if in_progress:
            achievements_embed.add_field(
                name="🔄 Available Achievements",
                value="\n".join(in_progress),
                inline=False
            )

        await interaction.response.edit_message(embed=achievements_embed, view=self)

    async def upgrades_callback(self, interaction: discord.Interaction):
        """Show guild upgrades"""
        # Create upgrade view with buttons
        class GuildUpgradeView(discord.ui.View):
            def __init__(self, parent_view):
                super().__init__(timeout=60)
                self.parent_view = parent_view
                self.guild = parent_view.guild
                self.guild_manager = parent_view.guild_manager
                self.player_data = parent_view.player_data
                self.is_leader = parent_view.is_leader
                self.is_officer = parent_view.is_officer

                # Add back button
                back_btn = discord.ui.Button(
                    label="Back to Guild Info",
                    style=discord.ButtonStyle.secondary,
                    row=3
                )
                back_btn.callback = self.back_callback
                self.add_item(back_btn)

                # Only add upgrade buttons if player has permission
                if self.is_leader or self.is_officer:
                    self.add_upgrade_buttons()

            def add_upgrade_buttons(self):
                # Add upgrade buttons for each upgradeable item
                row = 0
                for upgrade_id, upgrade_info in GUILD_UPGRADES.items():
                    # Get current level
                    current_level = self.guild.upgrades.get(upgrade_id, 0)
                    max_level = upgrade_info["max_level"]

                    # Only add button if not at max level
                    if current_level < max_level:
                        next_cost = upgrade_info["cost_formula"](current_level + 1)

                        # Create button with appropriate emoji
                        emoji = "⬆️"
                        if upgrade_id == "bank_level":
                            emoji = "💰"
                        elif upgrade_id == "member_capacity":
                            emoji = "👥"
                        elif upgrade_id == "exp_boost":
                            emoji = "✨"
                        elif upgrade_id == "gold_boost":
                            emoji = "💵"

                        # Create button
                        upgrade_btn = discord.ui.Button(
                            label=f"Upgrade {upgrade_info['name']}",
                            style=discord.ButtonStyle.primary,
                            emoji=emoji,
                            row=row % 3
                        )

                        # Store the upgrade_id and cost for this button
                        upgrade_btn.upgrade_id = upgrade_id
                        upgrade_btn.cost = next_cost
                        upgrade_btn.callback = self.make_upgrade_callback(upgrade_id, next_cost)
                        self.add_item(upgrade_btn)
                        row += 1

            def make_upgrade_callback(self, upgrade_id, cost):
                async def upgrade_callback(btn_interaction):
                    # Check if guild has enough gold
                    if self.guild.bank < cost:
                        await btn_interaction.response.send_message(
                            f"❌ Not enough gold! This upgrade costs {cost} 💰, but the guild bank only has {self.guild.bank} 💰.",
                            ephemeral=True
                        )
                        return

                    # Purchase upgrade
                    current_level = self.guild.upgrades.get(upgrade_id, 0)
                    self.guild.upgrades[upgrade_id] = current_level + 1
                    self.guild.bank -= cost

                    # Save changes
                    self.guild_manager.save_guilds()

                    # Get the new stats
                    upgrade_info = GUILD_UPGRADES[upgrade_id]
                    new_level = self.guild.upgrades[upgrade_id]
                    new_benefit = upgrade_info["benefit_formula"](new_level)

                    # Recreate the upgrades embed with updated info
                    upgrades_embed = discord.Embed(
                        title=f"{self.guild.emblem} {self.guild.name} - Upgrades",
                        description=f"Guild Bank: {self.guild.bank} 💰",
                        color=discord.Color(self.guild.color)
                    )

                    # Add all upgrades to the embed
                    for upg_id, level in self.guild.upgrades.items():
                        if upg_id in GUILD_UPGRADES:
                            upg = GUILD_UPGRADES[upg_id]
                            max_lvl = upg["max_level"]
                            next_lvl = level + 1 if level < max_lvl else level

                            # Calculate benefit and cost
                            current_ben = upg["benefit_formula"](level)

                            if level < max_lvl:
                                next_cst = upg["cost_formula"](next_lvl)
                                upgrades_embed.add_field(
                                    name=f"{upg['name']} (Level {level}/{max_lvl})",
                                    value=f"**Current:** {current_ben}\n"
                                          f"**Next Level Cost:** {next_cst} 💰\n"
                                          f"*{upg['description']}*",
                                    inline=False
                                )
                            else:
                                upgrades_embed.add_field(
                                    name=f"{upg['name']} (Level {level}/{max_lvl}) ✅",
                                    value=f"**Maximum Level!** {current_ben}\n"
                                          f"*{upg['description']}*",
                                    inline=False
                                )

                    # Add success message to footer
                    upgrades_embed.set_footer(text=f"Upgraded {upgrade_info['name']} to level {new_level}! New benefit: {new_benefit}")

                    # Create a new upgrade view with updated buttons
                    new_view = GuildUpgradeView(self.parent_view)
                    await btn_interaction.response.edit_message(embed=upgrades_embed, view=new_view)

                return upgrade_callback

            async def back_callback(self, interaction):
                # Go back to main guild view
                info_embed = discord.Embed(
                    title=f"{self.guild.emblem} {self.guild.name}",
                    description=self.guild.description,
                    color=discord.Color(self.guild.color)
                )

                info_embed.add_field(
                    name="Guild Info",
                    value=f"**Level:** {self.guild.level}\n"
                          f"**Members:** {len(self.guild.members)}/{self.guild.max_members}\n"
                          f"**Founded:** {self.guild.created_at.strftime('%Y-%m-%d')}",
                    inline=True
                )

                info_embed.add_field(
                    name="Guild Bank",
                    value=f"{self.guild.bank} 💰",
                    inline=True
                )

                info_embed.add_field(
                    name="Message of the Day",
                    value=self.guild.motd,
                    inline=False
                )

                await interaction.response.edit_message(embed=info_embed, view=self.parent_view)

        # Create the initial upgrades embed
        upgrades_embed = discord.Embed(
            title=f"{self.guild.emblem} {self.guild.name} - Upgrades",
            description=f"Guild Bank: {self.guild.bank} 💰",
            color=discord.Color(self.guild.color)
        )

        # Current upgrades
        for upgrade_id, level in self.guild.upgrades.items():
            if upgrade_id in GUILD_UPGRADES:
                upgrade = GUILD_UPGRADES[upgrade_id]
                max_level = upgrade["max_level"]
                next_level = level + 1 if level < max_level else level

                # Calculate benefit and cost
                current_benefit = upgrade["benefit_formula"](level)

                if level < max_level:
                    next_cost = upgrade["cost_formula"](next_level)
                    upgrades_embed.add_field(
                        name=f"{upgrade['name']} (Level {level}/{max_level})",
                        value=f"**Current:** {current_benefit}\n"
                              f"**Next Level Cost:** {next_cost} 💰\n"
                              f"*{upgrade['description']}*",
                        inline=False
                    )
                else:
                    upgrades_embed.add_field(
                        name=f"{upgrade['name']} (Level {level}/{max_level}) ✅",
                        value=f"**Maximum Level!** {current_benefit}\n"
                              f"*{upgrade['description']}*",
                        inline=False
                    )

        # Add info about upgrading
        if self.is_leader or self.is_officer:
            upgrades_embed.set_footer(text="Click an upgrade button below to purchase")

        # Create and send the upgrade view
        upgrade_view = GuildUpgradeView(self)
        await interaction.response.edit_message(embed=upgrades_embed, view=upgrade_view)

    async def contribute_callback(self, interaction: discord.Interaction):
        """Handle guild contribution"""
        # Create a modal for cursed energy contribution
        class ContributeModal(discord.ui.Modal):
            def __init__(self, guild_view):
                super().__init__(title=f"Contribute to {guild_view.guild.name}")
                self.guild_view = guild_view

                self.energy_input = discord.ui.TextInput(
                    label="Gold Amount",
                    placeholder="Enter amount of gold to contribute",
                    required=True,
                    min_length=1,
                    max_length=10
                )
                self.add_item(self.energy_input)

            async def on_submit(self, modal_interaction: discord.Interaction):
                # Validate input
                try:
                    energy_amount = int(self.energy_input.value)
                    if energy_amount <= 0:
                        await modal_interaction.response.send_message("Please enter a positive amount.", ephemeral=True)
                        return

                    # Check if player has enough gold
                    if self.guild_view.player_data.gold < energy_amount:
                        await modal_interaction.response.send_message(f"You don't have enough gold. You only have {self.guild_view.player_data.gold} 💰", ephemeral=True)
                        return

                    # Contribute to guild
                    success, message, points = self.guild_view.guild_manager.contribute_to_guild(
                        self.guild_view.player_data.user_id, 
                        energy_amount
                    )

                    if success:
                        # Deduct gold from player
                        self.guild_view.player_data.remove_gold(energy_amount)
                        self.guild_view.guild_manager.data_manager.save_data()

                        # Send success message
                        contrib_embed = discord.Embed(
                            title=f"Contribution to {self.guild_view.guild.name}",
                            description=f"You contributed {energy_amount} 💰 to the guild bank and earned {points} contribution points!",
                            color=discord.Color.green()
                        )
                        contrib_embed.add_field(
                            name="Guild Bank Balance",
                            value=f"{self.guild_view.guild.bank} 💰",
                            inline=True
                        )
                        contrib_embed.add_field(
                            name="Your Remaining Gold",
                            value=f"{self.guild_view.player_data.gold} 💰",
                            inline=True
                        )

                        await modal_interaction.response.send_message(embed=contrib_embed)
                    else:
                        await modal_interaction.response.send_message(message, ephemeral=True)
                except ValueError:
                    await modal_interaction.response.send_message("Please enter a valid number.", ephemeral=True)

        # Show the modal
        await interaction.response.send_modal(ContributeModal(self))

    async def leave_callback(self, interaction: discord.Interaction):
        """Handle leaving the guild"""
        # Create confirmation view
        confirm_view = View(timeout=30)

        async def confirm_button_callback(confirm_interaction):
            # Leave the guild
            success, message = self.guild_manager.remove_member_from_guild(self.player_data.user_id)

            if success:
                await confirm_interaction.response.edit_message(
                    content=message,
                    embed=None,
                    view=None
                )
            else:
                await confirm_interaction.response.edit_message(
                    content=f"Error: {message}",
                    embed=None,
                    view=None
                )

        async def cancel_button_callback(cancel_interaction):
            await cancel_interaction.response.edit_message(
                content="You decided to stay in the guild.",
                embed=None,
                view=None
            )

        # Add confirm and cancel buttons
        confirm_btn = Button(label="Confirm", style=discord.ButtonStyle.danger)
        confirm_btn.callback = confirm_button_callback

        cancel_btn = Button(label="Cancel", style=discord.ButtonStyle.secondary)
        cancel_btn.callback = cancel_button_callback

        confirm_view.add_item(confirm_btn)
        confirm_view.add_item(cancel_btn)

        # Show confirmation
        await interaction.response.edit_message(
            content=f"Are you sure you want to leave the guild '{self.guild.name}'?",
            embed=None,
            view=confirm_view
        )

    async def manage_callback(self, interaction: discord.Interaction):
        """Open guild management view"""
        # Create new view for management
        manage_view = GuildManageView(self.guild, self.guild_manager, self.player_data)

        manage_embed = discord.Embed(
            title=f"{self.guild.emblem} Manage Guild: {self.guild.name}",
            description="Select a management action from the options below:",
            color=discord.Color(self.guild.color)
        )

        await interaction.response.edit_message(embed=manage_embed, view=manage_view)

class GuildManageView(View):
    def __init__(self, guild: Guild, guild_manager: GuildManager, player_data: PlayerData):
        super().__init__(timeout=60)
        self.guild = guild
        self.guild_manager = guild_manager
        self.player_data = player_data
        self.is_leader = player_data.user_id == guild.leader_id

        # Add management buttons
        self.add_management_buttons()

    def add_management_buttons(self):
        # Edit description
        desc_btn = Button(
            label="Edit Description",
            style=discord.ButtonStyle.primary
        )
        desc_btn.callback = self.edit_desc_callback
        self.add_item(desc_btn)

        # Edit MOTD
        motd_btn = Button(
            label="Edit Message of the Day",
            style=discord.ButtonStyle.primary
        )
        motd_btn.callback = self.edit_motd_callback
        self.add_item(motd_btn)

        # Invite member
        invite_btn = Button(
            label="Invite Member",
            style=discord.ButtonStyle.success
        )
        invite_btn.callback = self.invite_callback
        self.add_item(invite_btn)

        # Leader-only buttons
        if self.is_leader:
            # Promote/Demote member
            promote_btn = Button(
                label="Promote/Demote Members",
                style=discord.ButtonStyle.success
            )
            promote_btn.callback = self.promote_demote_callback
            self.add_item(promote_btn)

            # Transfer leadership
            transfer_btn = Button(
                label="Transfer Leadership",
                style=discord.ButtonStyle.danger
            )
            transfer_btn.callback = self.transfer_callback
            self.add_item(transfer_btn)

        # Back to info button
        back_btn = Button(
            label="Back to Guild Info",
            style=discord.ButtonStyle.secondary
        )
        back_btn.callback = self.back_callback
        self.add_item(back_btn)

    async def edit_desc_callback(self, interaction: discord.Interaction):
        """Handle editing guild description"""
        # Create a modal for editing description
        class DescriptionModal(discord.ui.Modal):
            def __init__(self, manage_view):
                super().__init__(title=f"Edit Guild Description")
                self.manage_view = manage_view

                self.description_input = discord.ui.TextInput(
                    label="Guild Description",
                    placeholder="Enter new guild description",
                    required=True,
                    min_length=1,
                    max_length=200,
                    default=self.manage_view.guild.description
                )
                self.add_item(self.description_input)

            async def on_submit(self, modal_interaction: discord.Interaction):
                # Update guild description
                self.manage_view.guild.description = self.description_input.value
                self.manage_view.guild_manager.save_guilds()

                # Send success message
                await modal_interaction.response.send_message(
                    f"Guild description updated successfully!",
                    ephemeral=True
                )

                # Update the main view
                info_view = GuildInfoView(
                    self.manage_view.guild,
                    self.manage_view.guild_manager,
                    self.manage_view.player_data
                )

                info_embed = discord.Embed(
                    title=f"{self.manage_view.guild.emblem} {self.manage_view.guild.name}",
                    description=self.manage_view.guild.description,
                    color=discord.Color(self.manage_view.guild.color)
                )

                info_embed.add_field(
                    name="Guild Info",
                    value=f"**Level:** {self.manage_view.guild.level}\n"
                          f"**Members:** {len(self.manage_view.guild.members)}/{self.manage_view.guild.max_members}\n"
                          f"**Founded:** {self.manage_view.guild.created_at.strftime('%Y-%m-%d')}",
                    inline=True
                )

                info_embed.add_field(
                    name="Guild Bank",
                    value=f"{self.manage_view.guild.bank} 🌀",
                    inline=True
                )

                info_embed.add_field(
                    name="Message of the Day",
                    value=self.manage_view.guild.motd,
                    inline=False
                )

                await interaction.edit_original_response(embed=info_embed, view=info_view)

        # Show the modal
        await interaction.response.send_modal(DescriptionModal(self))

    async def edit_motd_callback(self, interaction: discord.Interaction):
        """Handle editing Message of the Day"""
        # Create a modal for editing MOTD
        class MotdModal(discord.ui.Modal):
            def __init__(self, manage_view):
                super().__init__(title=f"Edit Message of the Day")
                self.manage_view = manage_view

                self.motd_input = discord.ui.TextInput(
                    label="Message of the Day",
                    placeholder="Enter new message of the day",
                    required=True,
                    min_length=1,
                    max_length=200,
                    default=self.manage_view.guild.motd
                )
                self.add_item(self.motd_input)

            async def on_submit(self, modal_interaction: discord.Interaction):
                # Update guild MOTD
                self.manage_view.guild.motd = self.motd_input.value
                self.manage_view.guild_manager.save_guilds()

                # Send success message
                await modal_interaction.response.send_message(
                    f"Guild Message of the Day updated successfully!",
                    ephemeral=True
                )

                # Update the main view
                manage_embed = discord.Embed(
                    title=f"{self.manage_view.guild.emblem} Manage Guild: {self.manage_view.guild.name}",
                    description="Select a management action from the options below:",
                    color=discord.Color(self.manage_view.guild.color)
                )

                manage_embed.add_field(
                    name="Message of the Day",
                    value=self.manage_view.guild.motd,
                    inline=False
                )

                await interaction.edit_original_response(embed=manage_embed, view=self.manage_view)

        # Show the modal
        await interaction.response.send_modal(MotdModal(self))

    async def invite_callback(self, interaction: discord.Interaction):
        """Handle inviting members to the guild"""
        # Create a modal for member invitation
        class InviteModal(discord.ui.Modal):
            def __init__(self, manage_view):
                super().__init__(title=f"Invite Member to Guild")
                self.manage_view = manage_view

                self.member_input = discord.ui.TextInput(
                    label="Member ID",
                    placeholder="Enter the Discord User ID of the member to invite",
                    required=True,
                    min_length=1,
                    max_length=20
                )
                self.add_item(self.member_input)

            async def on_submit(self, modal_interaction: discord.Interaction):
                # Try to get user ID
                try:
                    member_id = int(self.member_input.value)

                    # Check if member exists
                    try:
                        member = await modal_interaction.client.fetch_user(member_id)

                        # Check if guild has space
                        if len(self.manage_view.guild.members) >= self.manage_view.guild.max_members:
                            await modal_interaction.response.send_message(
                                "Guild is already at maximum capacity.",
                                ephemeral=True
                            )
                            return

                        # Check if member is already in a guild
                        if member_id in self.manage_view.guild_manager.member_guild_map:
                            await modal_interaction.response.send_message(
                                "This player is already in a guild.",
                                ephemeral=True
                            )
                            return

                        # Add member to guild
                        success, message = self.manage_view.guild_manager.add_member_to_guild(
                            self.manage_view.guild.name,
                            member_id
                        )

                        if success:
                            await modal_interaction.response.send_message(
                                f"Successfully invited {member.display_name} to the guild!",
                                ephemeral=True
                            )
                        else:
                            await modal_interaction.response.send_message(
                                f"Error: {message}",
                                ephemeral=True
                            )
                    except discord.NotFound:
                        await modal_interaction.response.send_message(
                            "Could not find a Discord user with that ID.",
                            ephemeral=True
                        )
                except ValueError:
                    await modal_interaction.response.send_message(
                        "Please enter a valid Discord User ID.",
                        ephemeral=True
                    )

        # Show the modal
        await interaction.response.send_modal(InviteModal(self))

    async def promote_demote_callback(self, interaction: discord.Interaction):
        """Handle promoting/demoting members"""
        # Get non-leader guild members
        bot = interaction.client
        regular_members = []
        officer_members = []

        for member_id in self.guild.members:
            if member_id != self.guild.leader_id:
                try:
                    member = await bot.fetch_user(member_id)
                    if member_id in self.guild.officers:
                        officer_members.append((member_id, member.display_name))
                    else:
                        regular_members.append((member_id, member.display_name))
                except discord.NotFound:
                    # Skip members that can't be found
                    pass

        # Create selection options
        member_options = []

        # Add regular members for promotion
        for member_id, display_name in regular_members:
            member_options.append(
                discord.SelectOption(
                    label=f"Promote: {display_name}",
                    value=f"promote_{member_id}",
                    emoji="⬆️",
                    description=f"Promote to officer"
                )
            )

        # Add officer members for demotion
        for member_id, display_name in officer_members:
            member_options.append(
                discord.SelectOption(
                    label=f"Demote: {display_name}",
                    value=f"demote_{member_id}",
                    emoji="⬇️",
                    description=f"Demote to regular member"
                )
            )

        # Check if we have any members to display
        if not member_options:
            await interaction.response.send_message(
                "There are no members to promote or demote.",
                ephemeral=True
            )
            return

        # Create select menu
        members_select = Select(
            placeholder="Select member to promote/demote",
            options=member_options,
            min_values=1,
            max_values=1
        )

        async def select_callback(select_interaction):
            value = select_interaction.data["values"][0]
            action, member_id = value.split("_")
            member_id = int(member_id)

            if action == "promote":
                # Promote member to officer
                if self.guild.promote_member(member_id):
                    self.guild_manager.save_guilds()
                    await select_interaction.response.send_message(
                        "Member promoted to officer successfully!",
                        ephemeral=True
                    )
                else:
                    await select_interaction.response.send_message(
                        "Failed to promote member.",
                        ephemeral=True
                    )
            elif action == "demote":
                # Demote officer to regular member
                if self.guild.demote_officer(member_id):
                    self.guild_manager.save_guilds()
                    await select_interaction.response.send_message(
                        "Officer demoted to regular member successfully!",
                        ephemeral=True
                    )
                else:
                    await select_interaction.response.send_message(
                        "Failed to demote officer.",
                        ephemeral=True
                    )

            # Update the main view
            await interaction.edit_original_response(
                embed=discord.Embed(
                    title=f"{self.guild.emblem} Manage Guild: {self.guild.name}",
                    description="Select a management action from the options below:",
                    color=discord.Color(self.guild.color)
                ),
                view=self
            )

        members_select.callback = select_callback

        # Create a new view with the select menu
        select_view = View(timeout=60)
        select_view.add_item(members_select)

        # Add a back button
        back_btn = Button(label="Back", style=discord.ButtonStyle.secondary)

        async def back_callback(back_interaction):
            await back_interaction.response.edit_message(
                embed=discord.Embed(
                    title=f"{self.guild.emblem} Manage Guild: {self.guild.name}",
                    description="Select a management action from the options below:",
                    color=discord.Color(self.guild.color)
                ),
                view=self
            )

        back_btn.callback = back_callback
        select_view.add_item(back_btn)

        # Send the view
        await interaction.response.edit_message(
            embed=discord.Embed(
                title=f"{self.guild.emblem} {self.guild.name} - Promote/Demote Members",
                description="Select a member to promote or demote:",
                color=discord.Color(self.guild.color)
            ),
            view=select_view
        )

    async def transfer_callback(self, interaction: discord.Interaction):
        """Handle transferring guild leadership"""
        # Get non-leader guild members
        bot = interaction.client
        member_options = []

        for member_id in self.guild.members:
            if member_id != self.guild.leader_id:
                try:
                    member = await bot.fetch_user(member_id)
                    member_options.append(
                        discord.SelectOption(
                            label=member.display_name,
                            value=str(member_id),
                            description=f"Transfer leadership to this member"
                        )
                    )
                except discord.NotFound:
                    # Skip members that can't be found
                    pass

        # Check if we have any members to display
        if not member_options:
            await interaction.response.send_message(
                "There are no members to transfer leadership to.",
                ephemeral=True
            )
            return

        # Create select menu
        transfer_select = Select(
            placeholder="Select new guild leader",
            options=member_options,
            min_values=1,
            max_values=1
        )

        async def select_callback(select_interaction):
            # Get the selected member ID
            new_leader_id = int(select_interaction.data["values"][0])

            # Create confirmation view
            confirm_view = View(timeout=30)

            async def confirm_button_callback(confirm_interaction):
                # Transfer leadership
                success, message = self.guild_manager.transfer_leadership(
                    self.player_data.user_id,
                    new_leader_id
                )

                if success:
                    # Update the main view (to info view since user is no longer leader)
                    info_view = GuildInfoView(
                        self.guild,
                        self.guild_manager,
                        self.player_data
                    )

                    info_embed = discord.Embed(
                        title=f"{self.guild.emblem} {self.guild.name}",
                        description=self.guild.description,
                        color=discord.Color(self.guild.color)
                    )

                    info_embed.add_field(
                        name="Guild Info",
                        value=f"**Level:** {self.guild.level}\n"
                              f"**Members:** {len(self.guild.members)}/{self.guild.max_members}\n"
                              f"**Founded:** {self.guild.created_at.strftime('%Y-%m-%d')}",
                        inline=True
                    )

                    info_embed.add_field(
                        name="Guild Bank",
                        value=f"{self.guild.bank} 💰",
                        inline=True
                    )

                    info_embed.add_field(
                        name="Message of the Day",
                        value=self.guild.motd,
                        inline=False
                    )

                    await confirm_interaction.response.edit_message(
                        content=f"Guild leadership transferred successfully!",
                        embed=info_embed,
                        view=info_view
                    )
                else:
                    await confirm_interaction.response.edit_message(
                        content=f"Error: {message}",
                        embed=None,
                        view=None
                    )

            async def cancel_button_callback(cancel_interaction):
                await cancel_interaction.response.edit_message(
                    content="Leadership transfer cancelled.",
                    embed=None,
                    view=None
                )

            # Add confirm and cancel buttons
            confirm_btn = Button(label="Confirm", style=discord.ButtonStyle.danger)
            confirm_btn.callback = confirm_button_callback

            cancel_btn = Button(label="Cancel", style=discord.ButtonStyle.secondary)
            cancel_btn.callback = cancel_button_callback

            confirm_view.add_item(confirm_btn)
            confirm_view.add_item(cancel_btn)

            # Get new leader name
            new_leader = await bot.fetch_user(new_leader_id)
            new_leader_name = new_leader.display_name if new_leader else f"User ID: {new_leader_id}"

            # Show confirmation
            await select_interaction.response.edit_message(
                content=f"Are you sure you want to transfer guild leadership to {new_leader_name}? This action cannot be undone!",
                embed=None,
                view=confirm_view
            )

        transfer_select.callback = select_callback

        # Create a new view with the select menu
        select_view = View(timeout=60)
        select_view.add_item(transfer_select)

        # Add a back button
        back_btn = Button(label="Back", style=discord.ButtonStyle.secondary)

        async def back_callback(back_interaction):
            await back_interaction.response.edit_message(
                embed=discord.Embed(
                    title=f"{self.guild.emblem} Manage Guild: {self.guild.name}",
                    description="Select a management action from the options below:",
                    color=discord.Color(self.guild.color)
                ),
                view=self
            )

        back_btn.callback = back_callback
        select_view.add_item(back_btn)

        # Send the view
        await interaction.response.edit_message(
            embed=discord.Embed(
                title=f"{self.guild.emblem} {self.guild.name} - Transfer Leadership",
                description="Select a member to transfer leadership to:",
                color=discord.Color(self.guild.color)
            ),
            view=select_view
        )

    async def back_callback(self, interaction: discord.Interaction):
        """Go back to guild info view"""
        info_view = GuildInfoView(
            self.guild,
            self.guild_manager,
            self.player_data
        )

        info_embed = discord.Embed(
            title=f"{self.guild.emblem} {self.guild.name}",
            description=self.guild.description,
            color=discord.Color(self.guild.color)
        )

        info_embed.add_field(
            name="Guild Info",
            value=f"**Level:** {self.guild.level}\n"
                  f"**Members:** {len(self.guild.members)}/{self.guild.max_members}\n"
                  f"**Founded:** {self.guild.created_at.strftime('%Y-%m-%d')}",
            inline=True
        )

        info_embed.add_field(
            name="Guild Bank",
            value=f"{self.guild.bank} 💰",
            inline=True
        )

        info_embed.add_field(
            name="Message of the Day",
            value=self.guild.motd,
            inline=False
        )

        await interaction.response.edit_message(embed=info_embed, view=info_view)

class GuildShopView(RestrictedView):
    def __init__(self, player_data: PlayerData, guild: Guild, guild_manager: GuildManager, data_manager: DataManager, authorized_user):
        super().__init__(authorized_user, timeout=120)
        self.player_data = player_data
        self.guild = guild
        self.guild_manager = guild_manager
        self.data_manager = data_manager
        self.page = 0
        self.items_per_page = 5
        self.category = "All"

        # Guild shop items
        self.shop_items = [
            {
                "name": "Guild Expansion Permit",
                "description": "Increases maximum member capacity by 5",
                "price": 5000,
                "category": "Upgrade",
                "function": self.purchase_guild_expansion
            },
            {
                "name": "Guild Banner",
                "description": "Decorative banner for your guild with +2% XP bonus",
                "price": 2500,
                "category": "Decoration",
                "function": self.purchase_guild_banner
            },
            {
                "name": "Guild Storage Expansion",
                "description": "Adds 10 slots to guild storage",
                "price": 3000,
                "category": "Upgrade",
                "function": self.purchase_storage_expansion
            },
            {
                "name": "Guild XP Boost",
                "description": "30% more guild XP for 7 days",
                "price": 7500,
                "category": "Boost",
                "function": self.purchase_xp_boost
            },
            {
                "name": "Rare Material Crate",
                "description": "Contains assorted rare crafting materials for guild members",
                "price": 4000,
                "category": "Resources",
                "function": self.purchase_material_crate
            },
            {
                "name": "Guild Emblem Customization",
                "description": "Allows changing the guild emblem",
                "price": 1000,
                "category": "Decoration",
                "function": self.purchase_emblem_customization
            },
            {
                "name": "Guild Dungeon Key",
                "description": "Unlocks a special guild dungeon for 24 hours",
                "price": 10000,
                "category": "Special",
                "function": self.purchase_dungeon_key
            }
        ]

        self.add_item(discord.ui.Select(
            placeholder="Select Category",
            options=[
                discord.SelectOption(label="All", value="All"),
                discord.SelectOption(label="Upgrade", value="Upgrade"),
                discord.SelectOption(label="Decoration", value="Decoration"),
                discord.SelectOption(label="Boost", value="Boost"),
                discord.SelectOption(label="Resources", value="Resources"),
                discord.SelectOption(label="Special", value="Special")
            ],
            custom_id="category_select"
        ))

        self.category_select = self.children[0]
        self.category_select.callback = self.category_callback

        self.add_navigation_buttons()
        self.add_info_button()

    def add_navigation_buttons(self):
        """Add previous and next page buttons"""
        prev_button = discord.ui.Button(
            style=discord.ButtonStyle.secondary,
            label="Previous",
            custom_id="prev_page",
            disabled=True
        )
        prev_button.callback = self.prev_page_callback
        self.add_item(prev_button)

        next_button = discord.ui.Button(
            style=discord.ButtonStyle.secondary,
            label="Next",
            custom_id="next_page",
            disabled=True
        )
        next_button.callback = self.next_page_callback
        self.add_item(next_button)

        self.prev_button = prev_button
        self.next_button = next_button
        self.update_button_states()

    def add_info_button(self):
        """Add button to show info about guild bank"""
        info_button = discord.ui.Button(
            style=discord.ButtonStyle.secondary,
            label="Guild Bank Info",
            custom_id="bank_info"
        )
        info_button.callback = self.bank_info_callback
        self.add_item(info_button)

    def update_button_states(self):
        """Update button states based on current page"""
        filtered_items = self.get_filtered_items()
        max_pages = math.ceil(len(filtered_items) / self.items_per_page)

        self.prev_button.disabled = self.page <= 0
        self.next_button.disabled = self.page >= max_pages - 1 or max_pages == 0

    def get_filtered_items(self):
        """Get items filtered by category"""
        if self.category == "All":
            return self.shop_items
        return [item for item in self.shop_items if item["category"] == self.category]

    async def category_callback(self, interaction: discord.Interaction):
        """Handle category selection"""
        self.category = interaction.data["values"][0]
        self.page = 0  # Reset page when category changes
        self.update_button_states()
        await interaction.response.edit_message(embed=self.create_shop_embed(), view=self)

    async def prev_page_callback(self, interaction: discord.Interaction):
        """Handle previous page button"""
        self.page -= 1
        self.update_button_states()
        await interaction.response.edit_message(embed=self.create_shop_embed(), view=self)

    async def next_page_callback(self, interaction: discord.Interaction):
        """Handle next page button"""
        self.page += 1
        self.update_button_states()
        await interaction.response.edit_message(embed=self.create_shop_embed(), view=self)

    async def bank_info_callback(self, interaction: discord.Interaction):
        """Show information about guild bank"""
        bank_embed = discord.Embed(
            title=f"{self.guild.name} Bank",
            description="Your guild's financial status",
            color=discord.Color.gold()
        )

        bank_embed.add_field(
            name="Current Balance",
            value=f"💰 {self.guild.bank:,} Gold",
            inline=False
        )

        # Show recent transactions (placeholder)
        bank_embed.add_field(
            name="Member Contributions",
            value="Use `!guild contribute <amount>` to add to the guild bank.",
            inline=False
        )

        await interaction.response.edit_message(embed=bank_embed, view=self)

    def create_shop_embed(self):
        """Create shop embed for current view"""
        filtered_items = self.get_filtered_items()
        max_pages = math.ceil(len(filtered_items) / self.items_per_page)

        if max_pages == 0:
            max_pages = 1

        shop_embed = discord.Embed(
            title=f"{self.guild.name} Guild Shop",
            description=f"Use guild funds to purchase upgrades and items.\n**Current Balance:** 💰 {self.guild.bank:,} Gold",
            color=discord.Color.blue()
        )

        # Add guild shop items for current page
        start_idx = self.page * self.items_per_page
        page_items = filtered_items[start_idx:start_idx + self.items_per_page]

        if not page_items:
            shop_embed.add_field(
                name="No Items Available",
                value="No items found in this category",
                inline=False
            )
        else:
            for i, item in enumerate(page_items, 1):
                affordable = self.guild.bank >= item["price"]
                price_text = f"💰 {item['price']:,} Gold"
                if not affordable:
                    price_text = f"❌ {price_text} (Not enough funds)"

                shop_embed.add_field(
                    name=f"{i}. {item['name']} - {price_text}",
                    value=f"{item['description']}\n`!guild buy {i + start_idx}`",
                    inline=False
                )

        shop_embed.set_footer(text=f"Page {self.page + 1}/{max_pages} • Category: {self.category}")
        return shop_embed

    async def purchase_guild_expansion(self, interaction: discord.Interaction):
        """Purchase guild expansion"""
        # Check if user has permission
        if not self.guild.can_manage_guild(self.player_data.user_id):
            await interaction.response.send_message("❌ Only guild officers or the leader can purchase this upgrade.", ephemeral=True)
            return False

        # Increase max members
        self.guild.max_members += 5

        await interaction.response.send_message(f"✅ Guild capacity increased to {self.guild.max_members} members!")
        return True

    async def purchase_guild_banner(self, interaction: discord.Interaction):
        """Purchase guild banner"""
        # Add banner to guild perks
        if "guild_banner" not in self.guild.upgrades:
            self.guild.upgrades["guild_banner"] = {"level": 1, "bonus": 0.02}
        else:
            # Upgrade existing banner
            self.guild.upgrades["guild_banner"]["level"] += 1
            self.guild.upgrades["guild_banner"]["bonus"] += 0.01

        await interaction.response.send_message(f"✅ Guild Banner purchased! Members now get +{self.guild.upgrades['guild_banner']['bonus'] * 100}% XP bonus.")
        return True

    async def purchase_storage_expansion(self, interaction: discord.Interaction):
        """Purchase storage expansion"""
        # Initialize storage if it doesn't exist
        if "storage" not in self.guild.upgrades:
            self.guild.upgrades["storage"] = {"slots": 10}
        else:
            # Add more slots
            self.guild.upgrades["storage"]["slots"] += 10

        await interaction.response.send_message(f"✅ Guild storage expanded! Total slots: {self.guild.upgrades['storage']['slots']}")
        return True

    async def purchase_xp_boost(self, interaction: discord.Interaction):
        """Purchase XP boost"""
        # Set XP boost with expiration date
        expiration = datetime.datetime.now() + datetime.timedelta(days=7)
        self.guild.upgrades["xp_boost"] = {
            "multiplier": 1.3,
            "expires": expiration.isoformat()
        }

        await interaction.response.send_message("✅ Guild XP Boost active for 7 days! All guild XP earned will be increased by 30%.")
        return True

    async def purchase_material_crate(self, interaction: discord.Interaction):
        """Purchase material crate for guild members"""
        # Generate random rare materials
        materials = [
            "Dragon Scale", "Phoenix Feather", "Mithril Ore", 
            "Enchanted Wood", "Void Crystal", "Moonsilver"
        ]

        # Add to guild storage for distribution
        if "storage_items" not in self.guild.upgrades:
            self.guild.upgrades["storage_items"] = {}

        for material in materials:
            quantity = random.randint(3, 8)
            if material in self.guild.upgrades["storage_items"]:
                self.guild.upgrades["storage_items"][material] += quantity
            else:
                self.guild.upgrades["storage_items"][material] = quantity

        materials_list = ", ".join([f"{random.randint(3, 8)}x {m}" for m in random.sample(materials, 3)])
        await interaction.response.send_message(f"✅ Material Crate purchased! Added to guild storage: {materials_list} and more!")
        return True

    async def purchase_emblem_customization(self, interaction: discord.Interaction):
        """Purchase emblem customization"""
        # Allow customization of guild emblem
        self.guild.upgrades["custom_emblem"] = True

        await interaction.response.send_message("✅ Guild Emblem Customization purchased! Use `!guild emblem` to customize your guild's emblem.")
        return True

    async def purchase_dungeon_key(self, interaction: discord.Interaction):
        """Purchase special guild dungeon key"""
        # Add special dungeon with expiration
        expiration = datetime.datetime.now() + datetime.timedelta(hours=24)

        # Choose a random special dungeon
        special_dungeons = [
            "Crystal Caverns", "Ancient Treasury", "Forgotten Temple",
            "Dragon's Lair", "Abyssal Depths"
        ]

        dungeon = random.choice(special_dungeons)

        self.guild.upgrades["special_dungeon"] = {
            "name": dungeon,
            "expires": expiration.isoformat(),
            "rewards_multiplier": 1.5
        }

        await interaction.response.send_message(f"✅ Special Guild Dungeon Key purchased! '{dungeon}' is now available for 24 hours with 50% bonus rewards. Start with `!guild dungeon`!")
        return True

class GuildTeamDungeonView(View):
    def __init__(self, leader_data: PlayerData, guild: Guild, guild_manager: GuildManager, data_manager: DataManager):
        super().__init__(timeout=300)  # Longer timeout for team formation
        self.leader_data = leader_data
        self.guild = guild
        self.guild_manager = guild_manager
        self.data_manager = data_manager
        self.team_members = [leader_data.user_id]
        self.max_team_size = 4
        self.dungeon_name = None
        self.ready_members = set()

        # Add select menus and buttons
        self.add_all_components()

    def add_all_components(self):
        # Add member selection
        self.add_member_select()

        # Add dungeon selection
        self.add_dungeon_select()

        # Add control buttons
        self.add_control_buttons()

    def add_member_select(self):
        """Add dropdown for member selection"""
        # Get available guild members (excluding the leader)
        member_options = []

        for member_id in self.guild.members:
            if member_id != self.leader_data.user_id:
                # Add option - will need to fetch usernames when displaying
                member_options.append(
                    discord.SelectOption(
                        label=f"Member ID: {member_id}",
                        value=str(member_id),
                        description="Add to dungeon team"
                    )
                )

        # Don't add if no options available
        if not member_options:
            return

        # Limit to max 25 options (Discord limitation)
        member_options = member_options[:25]

        member_select = Select(
            placeholder="Add guild members to team",
            options=member_options,
            min_values=1,
            max_values=1,
            custom_id="member_select"
        )
        member_select.callback = self.member_select_callback
        self.add_item(member_select)

    def add_dungeon_select(self):
        """Add dropdown for dungeon selection"""
        from dungeons import DUNGEONS

        # Get player level for requirement check
        player_level = self.leader_data.class_level

        dungeon_options = []
        for dungeon_name, dungeon_data in DUNGEONS.items():
            # Check if player meets level requirement
            if player_level >= dungeon_data["level_req"]:
                dungeon_options.append(
                    discord.SelectOption(
                        label=dungeon_name,
                        value=dungeon_name,
                        description=f"Level {dungeon_data['level_req']}+ | {dungeon_data['floors']} floors",
                        emoji="🔍"
                    )
                )
            else:
                # Add but mark as locked
                dungeon_options.append(
                    discord.SelectOption(
                        label=f"{dungeon_name} (Locked)",
                        value=f"locked_{dungeon_name}",
                        description=f"Required Level: {dungeon_data['level_req']} | Your Level: {player_level}",
                        emoji="🔒"
                    )
                )

        dungeon_select = Select(
            placeholder="Select dungeon to explore",
            options=dungeon_options,
            min_values=1,
            max_values=1,
            custom_id="dungeon_select"
        )
        dungeon_select.callback = self.dungeon_select_callback
        self.add_item(dungeon_select)

    def add_control_buttons(self):
        """Add buttons for starting/canceling the dungeon run"""
        # Start button
        start_btn = Button(
            label="Start Dungeon",
            style=discord.ButtonStyle.success,
            emoji="⚔️",
            custom_id="start_btn",
            disabled=True  # Initially disabled
        )
        start_btn.callback = self.start_callback
        self.add_item(start_btn)

        # Ready button
        ready_btn = Button(
            label="Ready",
            style=discord.ButtonStyle.primary,
            emoji="✅",
            custom_id="ready_btn"
        )
        ready_btn.callback = self.ready_callback
        self.add_item(ready_btn)

        # Cancel button
        cancel_btn = Button(
            label="Cancel",
            style=discord.ButtonStyle.danger,
            emoji="❌",
            custom_id="cancel_btn"
        )
        cancel_btn.callback = self.cancel_callback
        self.add_item(cancel_btn)

    async def update_member_display_names(self, interaction):
        """Update member IDs with display names in the view"""
        # Handle different types of context objects
        if hasattr(interaction, 'bot'):
            bot = interaction.bot  # For Context objects
        elif hasattr(interaction, 'client'):
            bot = interaction.client  # For Interaction objects
        else:
            # Fallback if neither attribute is available
            bot = interaction.guild.me._state.client if hasattr(interaction, 'guild') and interaction.guild else None

        # If we still don't have a bot reference, return early
        if not bot:
            return

        member_select = discord.utils.get(self.children, custom_id="member_select")

        if member_select:
            updated_options = []
            for option in member_select.options:
                try:
                    member_id = int(option.value)
                    member = await bot.fetch_user(member_id)
                    updated_options.append(
                        discord.SelectOption(
                            label=member.display_name,
                            value=option.value,
                            description="Add to dungeon team"
                        )
                    )
                except (ValueError, discord.NotFound):
                    # Keep original option if can't update
                    updated_options.append(option)

            # Update options if any were changed
            if updated_options:
                member_select.options = updated_options

    async def update_team_embed(self, interaction: discord.Interaction):
        """Update the team status embed"""
        bot = interaction.client

        # Create new team embed
        team_embed = discord.Embed(
            title="🔍 Guild Dungeon Team",
            description=f"Form a team with guild members to tackle a dungeon together!",
            color=discord.Color(self.guild.color)
        )

        # Add team members section
        team_members_text = ""
        for i, member_id in enumerate(self.team_members):
            try:
                member = await bot.fetch_user(member_id)
                name = member.display_name

                # Add ready status
                if member_id in self.ready_members:
                    team_members_text += f"{i+1}. {name} ✅\n"
                else:
                    team_members_text += f"{i+1}. {name}\n"
            except discord.NotFound:
                team_members_text += f"{i+1}. User ID: {member_id}\n"

        team_embed.add_field(
            name=f"Team Members ({len(self.team_members)}/{self.max_team_size})",
            value=team_members_text if team_members_text else "No members added yet",
            inline=False
        )

        # Add selected dungeon
        from dungeons import DUNGEONS
        if self.dungeon_name and self.dungeon_name in DUNGEONS:
            dungeon = DUNGEONS[self.dungeon_name]
            team_embed.add_field(
                name="Selected Dungeon",
                value=f"**{self.dungeon_name}**\n{dungeon['description']}\n"
                      f"Level: {dungeon['level_req']}+ | Floors: {dungeon['floors']}",
                inline=False
            )
        else:
            team_embed.add_field(
                name="Dungeon",
                value="No dungeon selected yet",
                inline=False
            )

        # Add ready status section
        ready_status = f"{len(self.ready_members)}/{len(self.team_members)} members ready"
        team_embed.add_field(
            name="Ready Status",
            value=ready_status,
            inline=False
        )

        # Update button states
        start_btn = discord.utils.get(self.children, custom_id="start_btn")
        if start_btn:
            # Enable start button if everyone is ready and dungeon is selected
            all_ready = len(self.ready_members) == len(self.team_members)
            start_btn.disabled = not (all_ready and self.dungeon_name and len(self.team_members) > 0)

        # Update the message
        await interaction.response.edit_message(embed=team_embed, view=self)

    async def member_select_callback(self, interaction: discord.Interaction):
        """Handle member selection"""
        member_id = int(interaction.data["values"][0])

        # Check if team is already full
        if len(self.team_members) >= self.max_team_size:
            await interaction.response.send_message(
                f"Team is already at maximum capacity ({self.max_team_size} members).",
                ephemeral=True
            )
            return

        # Check if member is already on team
        if member_id in self.team_members:
            await interaction.response.send_message(
                "This member is already on the team.",
                ephemeral=True
            )
            return

        # Add member to team
        self.team_members.append(member_id)

        # Update the team display
        await self.update_team_embed(interaction)

    async def dungeon_select_callback(self, interaction: discord.Interaction):
        """Handle dungeon selection"""
        dungeon_value = interaction.data["values"][0]

        # Check if dungeon is locked
        if dungeon_value.startswith("locked_"):
            await interaction.response.send_message(
                "You don't meet the level requirements for this dungeon.",
                ephemeral=True
            )
            return

        # Set selected dungeon
        self.dungeon_name = dungeon_value

        # Update the team display
        await self.update_team_embed(interaction)

    async def ready_callback(self, interaction: discord.Interaction):
        """Handle ready button press"""
        user_id = interaction.user.id

        # Check if user is on the team
        if user_id not in self.team_members:
            await interaction.response.send_message(
                "You are not part of this dungeon team.",
                ephemeral=True
            )
            return

        # Toggle ready status
        if user_id in self.ready_members:
            self.ready_members.remove(user_id)
        else:
            self.ready_members.add(user_id)

        # Update the team display
        await self.update_team_embed(interaction)

    async def start_callback(self, interaction: discord.Interaction):
        """Handle starting the dungeon"""
        try:
            # Check if user is the team leader
            if interaction.user.id != self.leader_data.user_id:
                await interaction.response.send_message(
                    "Only the team leader can start the dungeon.",
                    ephemeral=True
                )
                return

            # Check if dungeon is selected
            if not self.dungeon_name:
                await interaction.response.send_message(
                    "Please select a dungeon first.",
                    ephemeral=True
                )
                return

            # Check if all members are ready
            if len(self.ready_members) != len(self.team_members):
                await interaction.response.send_message(
                    "Not all team members are ready.",
                    ephemeral=True
                )
                return

            # Import dungeon system
            from dungeons import DUNGEONS, DungeonProgressView

            # Check if dungeon exists
            if self.dungeon_name not in DUNGEONS:
                await interaction.response.send_message(
                    "Selected dungeon not found.",
                    ephemeral=True
                )
                return

            # Acknowledge the interaction immediately to prevent timeout
            await interaction.response.defer()

            # Create a list of player data for all team members
            team_player_data = []
            for member_id in self.team_members:
                player_data = self.data_manager.get_player(member_id)
                if player_data:
                    team_player_data.append(player_data)

            # Start the dungeon with team
            dungeon_data = DUNGEONS[self.dungeon_name]

            # Add guild bonus to dungeon
            guild_dungeon_bonus = {}

            # Apply guild perks based on level
            active_perks = self.guild.get_active_perks()
            for perk in active_perks:
                if perk["name"] == "United We Stand":
                    guild_dungeon_bonus["exp_bonus"] = 0.01  # 1% XP bonus
                elif perk["name"] == "Guild Tactics":
                    guild_dungeon_bonus["damage_bonus"] = 0.02  # 2% damage bonus
                elif perk["name"] == "Brotherhood":
                    guild_dungeon_bonus["gold_bonus"] = 0.05  # 5% gold bonus
        except Exception as e:
            # Handle any exceptions by responding to the user
            try:
                await interaction.followup.send(f"❌ Error starting dungeon: {str(e)}", ephemeral=True)
            except:
                if not interaction.response.is_done():
                    await interaction.response.send_message(f"❌ Error starting dungeon", ephemeral=True)
            return

        try:
            # Create the dungeon progress view with guild team
            dungeon_view = DungeonProgressView(
                self.leader_data,  # Main player leading the run
                DUNGEONS[self.dungeon_name],
                self.data_manager,
                self.dungeon_name,
                guild=self.guild,
                guild_bonus=guild_dungeon_bonus,
                team_player_data=team_player_data
            )

            # Send the dungeon view message
            dungeon_embed = discord.Embed(
                title=f"⚔️ Guild Dungeon: {self.dungeon_name}",
                description=f"Your guild team is embarking on a dungeon adventure!",
                color=discord.Color.blue()
            )

            # Show team members who are ready
            members_str = ""
            for i, member_id in enumerate(self.team_members):
                try:
                    member = await interaction.client.fetch_user(member_id)
                    members_str += f"{i+1}. {member.display_name} ✅\n"
                except:
                    members_str += f"{i+1}. Member ID: {member_id} ✅\n"

            dungeon_embed.add_field(
                name="Team Members",
                value=members_str,
                inline=False
            )

            # Start the dungeon
            await interaction.followup.send(embed=dungeon_embed, view=dungeon_view)

        except Exception as e:
            # Handle errors in dungeon creation
            await interaction.followup.send(f"❌ Error starting dungeon: {str(e)}", ephemeral=True)

        # Update guild achievement progress
        if "dungeon_conquerors" in self.guild.achievements_progress:
            self.guild.achievements_progress["dungeon_conquerors"] += 1
        else:
            self.guild.achievements_progress["dungeon_conquerors"] = 1

        # Save guild data
        self.guild_manager.save_guilds()

        # Create dungeon start embed
        dungeon_embed = discord.Embed(
            title=f"🔍 Entering {self.dungeon_name}",
            description=f"A guild team of {len(team_player_data)} members enters the {self.dungeon_name}!\n\n"
                       f"{dungeon_data['description']}",
            color=discord.Color.gold()
        )

        # Add team members
        team_list = ""
        for i, player in enumerate(team_player_data):
            # Get the member's username from interaction or use user_id as fallback
            member_name = f"Member {player.user_id}"
            if hasattr(player, 'username'):
                member_name = player.username
            team_list += f"{i+1}. **{member_name}** (Level {player.class_level} {player.class_name})\n"

        dungeon_embed.add_field(
            name="Guild Team",
            value=team_list,
            inline=False
        )

        # Add guild bonus
        bonus_text = ""
        if guild_dungeon_bonus:
            for bonus_type, bonus_value in guild_dungeon_bonus.items():
                if bonus_type == "exp_bonus":
                    bonus_text += f"• EXP Bonus: +{int(bonus_value * 100)}%\n"
                elif bonus_type == "damage_bonus":
                    bonus_text += f"• Damage Bonus: +{int(bonus_value * 100)}%\n"
                elif bonus_type == "gold_bonus":
                    bonus_text += f"• Gold Bonus: +{int(bonus_value * 100)}%\n"

            dungeon_embed.add_field(
                name="Guild Bonus",
                value=bonus_text or "None",
                inline=False
            )

        # Add dungeon info
        dungeon_embed.add_field(
            name="Dungeon Info",
            value=f"Floors: {dungeon_data['floors']}\n"
                  f"Recommended Level: {dungeon_data['level_req']}+",
            inline=False
        )

        # Start the dungeon
        await interaction.response.edit_message(embed=dungeon_embed, view=dungeon_view)

    async def cancel_callback(self, interaction: discord.Interaction):
        """Handle canceling the dungeon team formation"""
        user_id = interaction.user.id

        # If leader cancels, disband the team
        if user_id == self.leader_data.user_id:
            cancel_embed = discord.Embed(
                title="Dungeon Team Disbanded",
                description="The team leader has disbanded the dungeon team.",
                color=discord.Color.red()
            )

            await interaction.response.edit_message(embed=cancel_embed, view=None)
        else:
            # If team member cancels, remove them from the team
            if user_id in self.team_members:
                self.team_members.remove(user_id)
                if user_id in self.ready_members:
                    self.ready_members.remove(user_id)

                # Update the team display
                await self.update_team_embed(interaction)
            else:
                await interaction.response.send_message(
                    "You are not part of this dungeon team.",
                    ephemeral=True
                )

async def guild_command(ctx, action: str = None, *args):
    """Main guild command handler"""
    # Get data manager from context
    bot = ctx.bot
    data_manager = bot.data_manager

    # Initialize guild manager if not already
    if not hasattr(bot, "guild_manager"):
        bot.guild_manager = GuildManager(data_manager)

    guild_manager = bot.guild_manager

    # Get player data
    player_data = data_manager.get_player(ctx.author.id)

    # Process commands
    if not action:
        # Show guild info if in a guild, otherwise show help
        guild = guild_manager.get_player_guild(ctx.author.id)

        if guild:
            # Show guild info
            info_embed = discord.Embed(
                title=f"{guild.emblem} {guild.name}",
                description=guild.description,
                color=discord.Color(guild.color)
            )

            info_embed.add_field(
                name="Guild Info",
                value=f"**Level:** {guild.level}\n"
                      f"**Members:** {len(guild.members)}/{guild.max_members}\n"
                      f"**Founded:** {guild.created_at.strftime('%Y-%m-%d')}",
                inline=True
            )

            info_embed.add_field(
                name="Guild Bank",
                value=f"{guild.bank} 🌀",
                inline=True
            )

            info_embed.add_field(
                name="Message of the Day",
                value=guild.motd,
                inline=False
            )

            # Create interactive view
            guild_view = GuildInfoView(guild, guild_manager, player_data, ctx.author)

            await ctx.send(embed=info_embed, view=guild_view)
        else:
            # Show guild help
            help_embed = discord.Embed(
                title="Guild System",
                description="Join or create a guild to team up with other players!",
                color=discord.Color.blue()
            )

            help_embed.add_field(
                name="Available Commands",
                value="• `!guild create <name>` - Create a new guild\n"
                      "• `!guild join <name>` - Join an existing guild\n"
                      "• `!guild list` - List all guilds\n"
                      "• `!guild dungeon` - Enter a dungeon with guild members\n"
                      "• `!guild help` - Show this help message",
                inline=False
            )

            await ctx.send(embed=help_embed)

    elif action.lower() == "create":
        # Check if player has guild charter item
        if player_data.gold < 1000:
            await ctx.send("❌ You need 1,000 💰 Gold to create a guild. Current balance: {} 💰".format(player_data.gold))
            return

        # Get guild name from arguments
        if not args:
            await ctx.send("Please provide a name for your guild. Usage: `!guild create <name>`")
            return

        guild_name = " ".join(args)

        # Currency will be deducted by the create_guild method
        # No need to deduct it here or we'll double-charge the player


        # Check if name is valid
        if len(guild_name) < 3 or len(guild_name) > 32:
            await ctx.send("Guild name must be between 3 and 32 characters.")
            return

        # Try to create guild
        success, message = guild_manager.create_guild(guild_name, ctx.author.id, player_data)

        if success:
            # Remove charter from inventory
            for i, inv_item in enumerate(player_data.inventory):
                if inv_item.item.name == "Guild Charter":
                    player_data.inventory.pop(i)
                    break

            # Save data
            data_manager.save_data()

            # Send success message
            guild = guild_manager.get_guild_by_name(guild_name)

            success_embed = discord.Embed(
                title=f"Guild Created: {guild_name}",
                description=message,
                color=discord.Color.green()
            )

            success_embed.add_field(
                name="Next Steps",
                value="• Use `!guild` to view your guild info\n"
                      "• Invite members with `!guild invite <user_id>`\n"
                      "• Customize your guild with `!guild edit`",
                inline=False
            )

            await ctx.send(embed=success_embed)
        else:
            await ctx.send(f"Error: {message}")

    elif action.lower() == "join":
        # Check if already in a guild
        if guild_manager.get_player_guild(ctx.author.id):
            await ctx.send("You are already in a guild. Leave your current guild first with `!guild leave`.")
            return

        # Get guild name from arguments
        if not args:
            await ctx.send("Please provide the name of the guild to join. Usage: `!guild join <name>`")
            return

        guild_name = " ".join(args)

        # Try to join guild
        success, message = guild_manager.add_member_to_guild(guild_name, ctx.author.id)

        if success:
            await ctx.send(message)
        else:
            await ctx.send(f"Error: {message}")

    elif action.lower() == "leave":
        # Try to leave guild
        success, message = guild_manager.remove_member_from_guild(ctx.author.id)

        if success:
            await ctx.send(message)
        else:
            await ctx.send(f"Error: {message}")

    elif action.lower() == "rename":
        # Check if a guild name was provided
        if not args:
            await ctx.send("Please provide a new name for your guild. Usage: `!guild rename <new_name>`")
            return

        new_guild_name = " ".join(args)

        # Try to rename guild
        success, message = guild_manager.rename_guild(ctx.author.id, new_guild_name)

        if success:
            await ctx.send(f"✅ {message}")
        else:
            await ctx.send(f"❌ Error: {message}")

    elif action.lower() == "list":
        # Get top guilds
        top_guilds = guild_manager.get_top_guilds(10)

        if not top_guilds:
            await ctx.send("There are no guilds yet. Create one with `!guild create <name>`!")
            return

        # Create embed
        list_embed = discord.Embed(
            title="Guild Rankings",
            description="Top guilds by level and experience",
            color=discord.Color.gold()
        )

        # Add guilds to embed
        for i, guild_info in enumerate(top_guilds):
            # Get leader name
            try:
                leader = await bot.fetch_user(guild_info["leader_id"])
                leader_name = leader.display_name
            except discord.NotFound:
                leader_name = f"User ID: {guild_info['leader_id']}"

            list_embed.add_field(
                name=f"{i+1}. {guild_info['emblem']} {guild_info['name']} (Level {guild_info['level']})",
                value=f"Leader: {leader_name}\n"
                      f"Members: {guild_info['members']}\n"
                      f"Experience: {guild_info['exp']}",
                inline=False
            )

        await ctx.send(embed=list_embed)

    elif action.lower() == "shop":
        # Access the guild shop for purchasing items and upgrades
        guild = guild_manager.get_player_guild(ctx.author.id)
        if not guild:
            await ctx.send("❌ You are not in a guild. Join or create a guild first!")
            return

        # Create and show the guild shop
        shop_view = GuildShopView(player_data, guild, guild_manager, data_manager, ctx.author)
        shop_embed = shop_view.create_shop_embed()
        await ctx.send(embed=shop_embed, view=shop_view)

    elif action.lower() == "buy":
        # Handle guild item purchasing
        guild = guild_manager.get_player_guild(ctx.author.id)
        if not guild:
            await ctx.send("❌ You are not in a guild. Join or create a guild first!")
            return

        # Check if user has permission to make purchases
        if not guild.can_manage_guild(ctx.author.id):
            await ctx.send("❌ Only guild officers or the leader can make purchases for the guild.")
            return

        # Check if we have an item ID
        if not args:
            await ctx.send("❌ Please specify the item number to buy. Use `!guild shop` to view available items.")
            return

        try:
            item_number = int(args[0])
        except ValueError:
            await ctx.send("❌ Please provide a valid item number.")
            return

        # Create a temporary shop view to access the items
        shop_view = GuildShopView(player_data, guild, guild_manager, data_manager)
        all_items = shop_view.shop_items

        # Check if item exists
        if item_number < 1 or item_number > len(all_items):
            await ctx.send(f"❌ Invalid item number. Choose between 1-{len(all_items)}.")
            return

        # Get the selected item (1-indexed for users, 0-indexed for list)
        item = all_items[item_number - 1]

        # Check if guild has enough funds
        if guild.bank < item["price"]:
            await ctx.send(f"❌ Your guild doesn't have enough funds. The {item['name']} costs 💰 {item['price']:,} Gold, but your guild only has 💰 {guild.bank:,}.")
            return

        # Deduct price from guild bank
        guild.bank -= item["price"]

        # Use the item's purchase function
        purchase_success = await item["function"](ctx)

        if purchase_success:
            # Save guild data
            guild_manager.save_guilds()
            await ctx.send(f"✅ Successfully purchased {item['name']} for 💰 {item['price']:,} Gold!")
        else:
            # Refund if the purchase function returned False
            guild.bank += item["price"]
            guild_manager.save_guilds()

    elif action.lower() == "dungeon":
        # Check if in a guild
        guild = guild_manager.get_player_guild(ctx.author.id)

        if not guild:
            await ctx.send("You are not in a guild. Join or create one first!")
            return

        # Create team formation view
        team_view = GuildTeamDungeonView(player_data, guild, guild_manager, data_manager)

        # Create team formation embed
        team_embed = discord.Embed(
            title="🔍 Guild Dungeon Team",
            description=f"Form a team with guild members to tackle a dungeon together!",
            color=discord.Color(guild.color)
        )

        team_embed.add_field(
            name=f"Team Members (1/{team_view.max_team_size})",
            value=f"1. {ctx.author.display_name}",
            inline=False
        )

        team_embed.add_field(
            name="Dungeon",
            value="No dungeon selected yet",
            inline=False
        )

        team_embed.add_field(
            name="Ready Status",
            value="0/1 members ready",
            inline=False
        )

        # Update member display names - using the current context instead of trying to get a new one
        await team_view.update_member_display_names(ctx)

        await ctx.send(embed=team_embed, view=team_view)

    elif action.lower() == "help":
        # Show detailed help
        help_embed = discord.Embed(
            title="Guild System Guide",
            description="Complete guide to the guild system and commands",
            color=discord.Color.blue()
        )

        # Basic commands
        help_embed.add_field(
            name="Basic Commands",
            value="• `!guild` - View your guild info\n"
                  "• `!guild create <name>` - Create a new guild\n"
                  "• `!guild join <name>` - Join an existing guild\n"
                  "• `!guild leave` - Leave your current guild\n"
                  "• `!guild list` - Show top guilds",
            inline=False
        )

        # Guild member commands
        help_embed.add_field(
            name="Member Commands",
            value="• `!guild contribute <amount>` - Contribute cursed energy to guild bank\n"
                  "• `!guild shop` - Browse and purchase guild upgrades and items\n"
                  "• `!guild buy <item#>` - Purchase items from the guild shop\n"
                  "• `!guild dungeon` - Form a team for guild dungeon run\n"
                  "• `!guild members` - View guild members",
            inline=False
        )

        # Guild management commands
        help_embed.add_field(
            name="Management Commands (Leader & Officers)",
            value="• `!guild invite <user_id>` - Invite a player to the guild\n"
                  "• `!guild kick <user_id>` - Remove a member from the guild\n"
                  "• `!guild promote <user_id>` - Promote member to officer\n"
                  "• `!guild demote <user_id>` - Demote officer to member\n"
                  "• `!guild motd <message>` - Set message of the day\n"
                  "• `!guild desc <description>` - Set guild description\n"
                  "• `!guild emblem <emoji>` - Set guild emblem\n"
                  "• `!guild rename <new_name>` - Change guild name (leader only)",
            inline=False
        )

        # Guild benefits
        help_embed.add_field(
            name="Guild Benefits",
            value="• Share resources and coordinate with other players\n"
                  "• Receive bonuses when adventuring with guild members\n"
                  "• Access guild-exclusive content\n"
                  "• Earn guild achievements and rewards\n"
                  "• Participate in guild events and challenges",
            inline=False
        )

        await ctx.send(embed=help_embed)

    else:
        # Unknown action
        await ctx.send(f"Unknown guild command: {action}. Use `!guild help` to see available commands.")

# Alias for guild command
async def g_command(ctx, action: str = None, *args):
    """Alias for guild command"""
    await guild_command(ctx, action, *args)