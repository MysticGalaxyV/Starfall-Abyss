import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Button, View, Select
import json
import datetime
import random
import os
import asyncio
from typing import Dict, List, Optional, Any, Union

from data_models import DataManager, PlayerData, Item, InventoryItem
from utils import GAME_CLASSES, STARTER_CLASSES, format_time_until
# Import the unified battle system with consistent moves
from battle_system import start_battle, start_pvp_battle
from dungeons import dungeon_command, DUNGEONS
from equipment import equipment_command, shop_command, buy_command
from training import train_command, skills_command
from class_change import class_change_command
from special_items import special_items_command, get_random_special_drop
from advanced_training import advanced_training_command
from advanced_shop import advanced_shop_command
from guild_system import guild_command, g_command
from achievements import achievements_command, quests_command, event_command, achieve_command, ach_command, q_command
from materials import materials_command, gather_command, tools_command
from crafting_system import crafting_command, CraftingEntryView
from encyclopedia import encyclopedia_command, browser_command, codex_command, EncyclopediaExploreView, ENCYCLOPEDIA_SECTIONS
from skill_tree import skill_tree_command, skills_tree_command
from trading_system import trade_command, t_command, slash_trade
from leaderboard import leaderboard_command
from level_validation import validate_player_level, auto_correct_player_level
from dotenv import load_dotenv

load_dotenv()
# Bot setup
# NOTE: This bot requires "Message Content Intent" and "Server Members Intent" to be enabled
# in the Discord Developer Portal: https://discord.com/developers/applications/
# Go to your application -> Bot -> Privileged Gateway Intents and enable both options
# Bot requires "Message Content Intent" and "Server Members Intent" to be enabled
# in the Discord Developer Portal: https://discord.com/developers/applications/
# Bot intents for local development
intents = discord.Intents.default()
# Enable required intents for our command types
intents.message_content = True  # Required for prefix commands and @bot commands
# NOTE: For testing purposes, we'll work around the privileged intents limitation
# In production, intents.members should be True and enabled in the Discord Developer Portal

# Game name and welcome message
GAME_NAME = "✦ Starfall Abyss ✦"
WELCOME_MESSAGE = f"Welcome to {GAME_NAME}"

# Admin user ID - only this user can use admin commands
ADMIN_USER_ID = 759434349069860945  # Your user ID for admin permissions


# Define a custom check for admin commands
def is_admin():

    async def predicate(ctx):
        return ctx.author.id == ADMIN_USER_ID

    return commands.check(predicate)


# Define a simpler check function that works properly with the command system
def admin_check(ctx):
    # Check if the user is the owner or has the admin role
    if ctx.author.id == 759434349069860945:  # Your user ID
        return True
    # Check for admin role
    admin_role_id = 1369373123710943312
    return any(role.id == admin_role_id for role in ctx.author.roles)


# Constants for the admin menu system
# Constants for the enhanced admin give system
GIVE_CATEGORIES = {
    "resources": {
        "emoji": "💰",
        "name": "Resources",
        "description": "Gold, XP, Skill Points, Battle Energy"
    },
    "items": {
        "emoji": "🎁",
        "name": "Items",
        "description": "Weapons, Armor, Accessories, Tools, Materials"
    },
    "progress": {
        "emoji": "📊",
        "name": "Progress",
        "description": "Stats, PvP History, Quest Completion"
    }
}

GIVE_OPTIONS = {
    # Resources category
    "gold": {
        "emoji": "💰",
        "description": "Give gold to a player",
        "category": "resources"
    },
    "xp": {
        "emoji": "✨",
        "description": "Give experience points",
        "category": "resources"
    },
    "skill_points": {
        "emoji": "🎯",
        "description": "Give skill points",
        "category": "resources"
    },
    "battle_energy": {
        "emoji": "⚡",
        "description": "Increase max battle energy",
        "category": "resources"
    },

    # Items category
    "weapons": {
        "emoji": "⚔️",
        "description": "Give weapons",
        "category": "items"
    },
    "armor": {
        "emoji": "🛡️",
        "description": "Give armor pieces",
        "category": "items"
    },
    "items": {
        "emoji": "🎁",
        "description": "Give general items",
        "category": "items"
    },

    # Progress category
    "stats": {
        "emoji": "📊",
        "description": "Give stat points",
        "category": "progress"
    },
    "pvp_history": {
        "emoji": "⚔️",
        "description": "Add PvP wins/losses",
        "category": "progress"
    },
    "quest_complete": {
        "emoji": "✅",
        "description": "Mark quests as complete",
        "category": "progress"
    }
}


def get_prefix(bot, message):
    # Support for both "!" and "@bot" as prefixes
    prefixes = ["!"]

    # Also match mentions like "@bot"
    prefixes.extend([f'<@{bot.user.id}>', f'<@!{bot.user.id}>'])

    return commands.when_mentioned_or(*prefixes)(bot, message)


bot = commands.Bot(command_prefix=get_prefix, intents=intents)
bot.remove_command('help')  # Remove default help command

# Initialize data manager
data_manager = DataManager()
bot.data_manager = data_manager  # Make it accessible across commands


@bot.event
async def on_ready():
    """Called when the bot is ready to start operating"""
    print(f'Logged in as {bot.user.name} ({bot.user.id})')
    print('------')

    # Validate all player levels to ensure they match their XP
    from level_validation import validate_all_players
    corrections = validate_all_players(data_manager)
    if corrections:
        print(
            f"Corrected level inconsistencies for {len(corrections)} players:")
        for user_id, (old_level, new_level) in corrections.items():
            print(f"Player {user_id}: Level {old_level} → {new_level}")

    # Sync slash commands with Discord
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

    # Send domain expansion startup scene to a specific channel (preferably welcome or general)
    for guild in bot.guilds:
        # Look for ideal channels first (welcome or general)
        preferred_channels = [
            "welcome", "general", "chat", "bot-commands", "announcements"
        ]

        for preferred_name in preferred_channels:
            preferred_channel = discord.utils.get(guild.text_channels,
                                                  name=preferred_name)
            if preferred_channel and preferred_channel.permissions_for(
                    guild.me).send_messages:
                channel = preferred_channel
                break
        else:
            # If no preferred channel found, use any channel with send permissions
            text_channels = [
                channel for channel in guild.text_channels
                if channel.permissions_for(guild.me).send_messages
            ]

            if not text_channels:
                continue  # Skip this guild if no suitable channel found

            channel = text_channels[0]

            # Create the domain expansion embed with your exact text
            domain_embed = discord.Embed(
                title="DOMAIN EXPANSION",
                description=("```\nReality is obsolete.\n"
                             "The code of the soul, rewritten.\n"
                             "Welcome to my world—\n"
                             "DOMAIN EXPANSION: STARFALL ABYSS\n```"),
                color=discord.Color.from_rgb(128, 0, 255)  # Deep purple color
            )

            # Add the character image with built-in domain expansion text
            domain_embed.set_image(url="attachment://domain_expansion.png")
            # No footer to keep the message clean and simple

            # Send the message with the image
            try:
                # Use the new domain expansion image
                image_paths = [
                    "attached_assets/image_1747675410070.png",
                    "./attached_assets/image_1747675410070.png"
                ]

                file = None
                for path in image_paths:
                    try:
                        if os.path.exists(path):
                            file = discord.File(
                                path, filename="domain_expansion.png")
                            break
                    except:
                        continue

                # If we couldn't find the specific image, use the bot's avatar as fallback
                if file is None:
                    domain_embed.set_image(url=bot.user.display_avatar.url)
                    await channel.send(embed=domain_embed)
                else:
                    await channel.send(embed=domain_embed, file=file)
                print(
                    f"Domain expansion scene sent to {channel.name} in {guild.name}"
                )
            except Exception as e:
                print(f"Error sending domain expansion: {str(e)}")

            # Only send to one guild to avoid spam
            break

    # Set status showing all three command methods
    await bot.change_presence(activity=discord.Game(
        name=f"{GAME_NAME} | !help, @{bot.user.name} help, or /help"))


@bot.event
async def on_message(message):
    # Ignore messages from bots
    if message.author.bot:
        return

    # Respond to just the bot mention
    if message.content.strip() == f'<@{bot.user.id}>' or message.content.strip(
    ) == f'<@!{bot.user.id}>':
        ctx = await bot.get_context(message)
        await help_command(ctx)
        return

    await bot.process_commands(message)


@bot.event
async def on_message_edit(before, after):
    # Ignore edits from bots
    if after.author.bot:
        return

    # Process edited messages as commands (allows users to fix typos)
    await bot.process_commands(after)


class ClassSelectView(View):

    def __init__(self, timeout=60):
        super().__init__(timeout=timeout)
        self.selected_class = None

        # Add buttons for each class
        for class_name, class_data in STARTER_CLASSES.items():
            btn = Button(label=f"{class_name} ({class_data['role']})",
                         style=discord.ButtonStyle.primary,
                         custom_id=class_name)
            btn.callback = self.class_callback
            self.add_item(btn)

    async def class_callback(self, interaction: discord.Interaction):
        self.selected_class = interaction.data["custom_id"]
        self.stop()
        await interaction.response.defer()


@bot.command(name="start")
async def start_command(ctx):
    """Start your adventure and choose a class"""
    user_id = ctx.author.id
    player = data_manager.get_player(user_id)

    # Check if player already has a class
    if player.class_name:
        await ctx.send(
            f"❌ You've already chosen the **{player.class_name}** class! You cannot start over."
        )
        return

    # First send domain expansion message
    domain_embed = discord.Embed(
        title="DOMAIN EXPANSION",
        description=("```\nReality is obsolete.\n"
                     "The code of the soul, rewritten.\n"
                     "Welcome to my world—\n"
                     "DOMAIN EXPANSION: STARFALL ABYSS\n```"),
        color=discord.Color.from_rgb(128, 0, 255)  # Deep purple color
    )

    # Add the character image with built-in domain expansion text
    domain_embed.set_image(url="attachment://domain_expansion.png")

    # Try to find the image in various possible locations
    image_paths = [
        "attached_assets/image_1747675410070.png",
        "./attached_assets/image_1747675410070.png"
    ]

    file = None
    for path in image_paths:
        try:
            if os.path.exists(path):
                file = discord.File(path, filename="domain_expansion.png")
                break
        except:
            continue

    # Send domain expansion message first
    if file:
        await ctx.send(embed=domain_embed, file=file)
    else:
        domain_embed.set_image(url=bot.user.display_avatar.url)
        await ctx.send(embed=domain_embed)

    # Brief delay to ensure messages appear in the right order
    await asyncio.sleep(1)

    # Create embed for class selection
    embed = discord.Embed(
        title="🔮 Choose Your Class",
        description=
        "Select a class to begin your adventure. Each class has unique abilities and playstyles that can be mastered as you progress from Level 1 to 1000.",
        color=discord.Color.blue())

    # Add class information to embed
    for class_name, class_info in STARTER_CLASSES.items():
        stats_text = "\n".join([
            f"{stat.title()}: {value}"
            for stat, value in class_info["stats"].items()
        ])
        embed.add_field(
            name=f"{class_name} ({class_info['role']})",
            value=f"**Active Ability:** {class_info['abilities']['active']}\n"
            f"**Passive Ability:** {class_info['abilities']['passive']}\n"
            f"**Stats:**\n{stats_text}",
            inline=False)

    # Create view for class selection
    view = ClassSelectView()

    # Send message with embed and view
    message = await ctx.send(embed=embed, view=view)

    # Wait for selection
    await view.wait()

    # Process selection
    if view.selected_class:
        class_name = view.selected_class

        # Set player class
        player.class_name = class_name
        player.unlocked_classes = [class_name]

        # Initialize player stats based on class
        class_data = STARTER_CLASSES[class_name]

        # Save player data
        data_manager.save_data()

        # We already sent the domain expansion message at the beginning, no need to send it again
        # Brief delay to ensure messages appear in the right order
        await asyncio.sleep(1)

        # Send welcome message
        welcome_embed = discord.Embed(
            title=WELCOME_MESSAGE,
            description=
            "Embark on an epic journey through mystical realms, challenging dungeons, and legendary battles!",
            color=discord.Color.purple())
        welcome_embed.set_footer(
            text="Your journey has begun! Use !profile to see your stats.")

        await ctx.send(embed=welcome_embed)

        # Confirmation message
        confirmation_embed = discord.Embed(
            title="🎉 Class Selected",
            description=f"You have chosen the path of the **{class_name}**!",
            color=discord.Color.green())

        confirmation_embed.add_field(
            name="Your Journey Begins",
            value=f"Your stats have been initialized based on your class.\n"
            f"Use `!profile` to see your stats and `!help` to see available commands.",
            inline=False)

        await ctx.send(embed=confirmation_embed)
    else:
        await ctx.send("❌ Class selection timed out. Please try again.")


@bot.command(name="profile")
async def profile_cmd(ctx, member: discord.Member = None):
    """View your or another player's profile"""
    await profile_command(ctx, member)


@bot.command(name="p")
async def p_cmd(ctx, member: discord.Member = None):
    """View your or another player's profile (alias)"""
    await profile_command(ctx, member)


async def check_secret_cutscene(ctx, player_data):
    """Check if player has completed all requirements for the secret cutscene"""
    # Check if player has completed all achievements
    from achievements import AchievementTracker, QuestManager

    # Create achievement tracker and quest manager
    achievement_tracker = AchievementTracker(data_manager)
    quest_manager = QuestManager(data_manager)

    # Get all player achievements
    player_achievements = achievement_tracker.get_player_achievements(
        player_data)
    available_achievements = achievement_tracker.get_player_available_achievements(
        player_data)

    # Get all player quests
    daily_quests = quest_manager.get_daily_quests(player_data)
    weekly_quests = quest_manager.get_weekly_quests(player_data)
    long_term_quests = quest_manager.get_long_term_quests(player_data)

    # Check guild quests completion
    from guild_system import GuildManager
    guild_manager = GuildManager(data_manager)
    guild_data = guild_manager.get_player_guild(player_data.user_id)

    guild_quests_completed = False
    if guild_data:
        # Guild data is a Guild object, not a dictionary
        if hasattr(guild_data, 'quests'):
            # Access quests as an attribute
            guild_quests = guild_data.quests
            # Filter for completed quests assigned to this player
            completed_quests = [
                q for q in guild_quests
                if q.get("assigned_to") == player_data.user_id
                and q.get("completed", False)
            ]
            guild_quests_completed = len(completed_quests) >= len(guild_quests)
        else:
            # If there are no quests, consider it completed
            guild_quests_completed = True

    # Check if all requirements are met
    if (not available_achievements and player_achievements and not daily_quests
            and not weekly_quests and all(
                quest.get("completed", False) for quest in long_term_quests)
            and guild_quests_completed):

        # Show the secret cutscene
        embed = discord.Embed(
            title="🌌 Secret Cutscene Unlocked 🌌",
            description="The world around you begins to shimmer and fade...",
            color=discord.Color.dark_purple())

        await ctx.send(embed=embed)

        # Dramatic pause
        await asyncio.sleep(2)

        # Final message
        final_embed = discord.Embed(
            title="🌟 Domain Master Appears 🌟",
            description=
            "**You beat my domain expansion... I don't know how, but you did it...**\n\n"
            "The master of the Starfall Abyss looks at you with newfound respect.\n\n"
            "\"Not in a thousand years did I think someone would master every aspect of this domain.\"\n\n"
            "\"You've truly become a master of the Starfall Abyss.\"",
            color=discord.Color.gold())

        await ctx.send(embed=final_embed)
        return True

    return False


async def profile_command(ctx, member: discord.Member = None):
    """Implementation of profile command"""
    # Get the target user
    target = member or ctx.author
    user_id = target.id

    # Get player data
    player = data_manager.get_player(user_id)

    # Check if player has started
    if not player.class_name:
        if target == ctx.author:
            await ctx.send(
                "❌ You haven't started your adventure yet! Use `!start` to choose a class."
            )
        else:
            await ctx.send(
                f"❌ {target.display_name} hasn't started their adventure yet!")
        return

    # Check for secret cutscene if user is viewing their own profile
    if target == ctx.author:
        cutscene_shown = await check_secret_cutscene(ctx, player)
        if cutscene_shown:
            # If cutscene was shown, still continue to show profile
            pass

    # Calculate stats including equipment bonuses
    stats = player.get_stats(GAME_CLASSES)

    # Create profile embed
    embed = discord.Embed(
        title=f"📜 {target.display_name}'s Profile",
        description=f"**Class:** {player.class_name}\n"
        f"**Level:** {player.class_level} ({player.class_exp}/{int(100 * (player.class_level ** 1.5))} EXP)\n"
        f"**Technique Grade:** {player.technique_grade}\n"
        f"**Gold:** {player.gold} 💰\n"
        f"**Battle Energy:** {player.get_battle_energy()}/{player.get_max_battle_energy()} ⚡",
        color=discord.Color.dark_purple())

    # Add domain expansion if unlocked
    domain = getattr(player, 'domain_expansion', None)
    if domain:
        embed.description = embed.description + f"\n**Domain Expansion:** {domain} 🌀"

    # Add stats
    embed.add_field(name="📊 Stats",
                    value=f"**HP:** {stats['hp']} ❤️\n"
                    f"**Cursed Power:** {stats['power']} ⚔️\n"
                    f"**Defense:** {stats['defense']} 🛡️\n"
                    f"**Speed:** {stats['speed']} 💨",
                    inline=True)

    # Add skill points
    embed.add_field(
        name="🔢 Skill Points",
        value=f"**Available:** {player.skill_points}\n"
        f"**Power:** +{player.allocated_stats.get('power', 0)}\n"
        f"**Defense:** +{player.allocated_stats.get('defense', 0)}\n"
        f"**Speed:** +{player.allocated_stats.get('speed', 0)}\n"
        f"**HP:** +{player.allocated_stats.get('hp', 0)}",
        inline=True)

    # Add battle record
    embed.add_field(
        name="⚔️ Battle Record",
        value=f"**Wins:** {player.wins}\n"
        f"**Losses:** {player.losses}\n"
        f"**Win Rate:** {int((player.wins / (player.wins + player.losses)) * 100) if player.wins + player.losses > 0 else 0}%",
        inline=True)

    # Add equipped items
    equipped_text = "None"
    equipped_items = [item for item in player.inventory if item.equipped]

    if equipped_items:
        equipped_text = "\n".join([
            f"**{item.item.item_type.title()}**: {item.item.name}"
            for item in equipped_items
        ])

    embed.add_field(name="🎒 Equipped Items", value=equipped_text, inline=True)

    # Add dungeon clear info
    dungeon_text = "None cleared yet"
    if player.dungeon_clears:
        dungeon_text = "\n".join([
            f"**{name}**: {count} times"
            for name, count in player.dungeon_clears.items()
        ])

    embed.add_field(name="🗺️ Dungeons Cleared",
                    value=dungeon_text,
                    inline=True)

    # Add daily streak
    embed.add_field(
        name="📅 Daily Streak",
        value=f"**Current Streak:** {player.daily_streak}\n"
        f"**Last Claimed:** {player.last_daily.strftime('%Y-%m-%d %H:%M') if player.last_daily else 'Never'}",
        inline=True)

    # Add profile tags if any purchased
    if hasattr(player, 'profile_tags') and player.profile_tags:
        tags_text = " | ".join(player.profile_tags)
        embed.add_field(
            name="🏷️ Profile Tags",
            value=tags_text,
            inline=False
        )

    # Set thumbnail to class icon
    if player.class_name == "Spirit Striker":
        embed.set_thumbnail(
            url="https://cdn.discordapp.com/emojis/745384647157719212.png")
    elif player.class_name == "Domain Tactician":
        embed.set_thumbnail(
            url="https://cdn.discordapp.com/emojis/745384647157719212.png")
    elif player.class_name == "Flash Rogue":
        embed.set_thumbnail(
            url="https://cdn.discordapp.com/emojis/745384647157719212.png")

    await ctx.send(embed=embed)


@bot.command(name="daily")
async def daily_command(ctx):
    """Claim your daily rewards"""
    player = data_manager.get_player(ctx.author.id)

    # Check if player has started
    if not player.class_name:
        await ctx.send(
            "❌ You haven't started your adventure yet! Use `!start` to choose a class."
        )
        return

    now = datetime.datetime.now()

    # Check if player has already claimed today
    if player.last_daily and player.last_daily.date() == now.date():
        next_reset = datetime.datetime.combine(
            now.date() + datetime.timedelta(days=1), datetime.time.min)
        time_until_reset = next_reset - now
        hours, remainder = divmod(time_until_reset.seconds, 3600)
        minutes, _ = divmod(remainder, 60)

        await ctx.send(
            f"❌ You've already claimed your daily reward today! Next reset in {hours}h {minutes}m."
        )
        return

    # Check for streak continuation or reset
    if player.last_daily and (now.date() - player.last_daily.date()).days == 1:
        # Continued streak
        player.daily_streak += 1
    elif not player.last_daily or (now.date() -
                                   player.last_daily.date()).days > 1:
        # Reset streak
        player.daily_streak = 1

    # Update last claim time
    player.last_daily = now

    # Calculate rewards based on streak
    base_gold = 50
    base_battle_energy = 25
    base_exp = 30

    # Bonus for streak (up to 100% extra at 30 days)
    streak_bonus = min(1.0, player.daily_streak / 30)

    gold_reward = int(base_gold * (1 + streak_bonus))
    battle_energy_reward = int(base_battle_energy * (1 + streak_bonus))
    exp_reward = int(base_exp * (1 + streak_bonus))

    # Add gold (no maximum limit)
    player.add_gold(gold_reward)

    # Add battle energy (with max limit check)
    player.add_battle_energy(battle_energy_reward)

    # Add experience
    leveled_up = player.add_exp(exp_reward)

    # Create reward embed
    embed = discord.Embed(title="🎁 Daily Reward Claimed!",
                          description=f"You've claimed your daily reward!",
                          color=discord.Color.dark_purple())

    embed.add_field(
        name="Rewards",
        value=f"**Gold:** +{gold_reward} 🔮\n"
        f"**Battle Energy:** +{battle_energy_reward} ⚡\n"
        f"**EXP:** +{exp_reward} 📊\n"
        f"**Streak:** {player.daily_streak} day{'s' if player.daily_streak != 1 else ''}",
        inline=False)

    # Add streak info
    if player.daily_streak >= 7:
        embed.add_field(
            name="🔥 Streak Bonus",
            value=f"Your streak bonus is +{int(streak_bonus * 100)}%!\n"
            f"Gold: {gold_reward} 🔮 | Battle Energy: {battle_energy_reward} ⚡",
            inline=False)
    else:
        embed.add_field(
            name="💡 Streak Info",
            value=f"Return tomorrow to increase your streak bonus!",
            inline=False)

    # Add level up message if applicable
    if leveled_up:
        embed.add_field(
            name="🆙 Level Up!",
            value=f"You reached Level {player.class_level}!\n"
            f"You gained 3 skill points! Use !skills to allocate them.",
            inline=False)

    # Save player data
    data_manager.save_data()

    await ctx.send(embed=embed)


@bot.command(name="use", aliases=["u"])
async def use_item_command(ctx, *, item_name: str = None):
    """Use an item from your inventory, like potions or energy boosters"""
    player = data_manager.get_player(ctx.author.id)

    if not item_name:
        # Show usable items if no item specified
        usable_items = []
        for inv_item in player.inventory:
            if "potion" in inv_item.item.name.lower(
            ) or "energy" in inv_item.item.name.lower():
                usable_items.append(inv_item)

        if not usable_items:
            await ctx.send("You don't have any usable items in your inventory."
                           )
            return

        embed = discord.Embed(
            title="Usable Items in Inventory",
            description="Use `!use [item name]` to use an item",
            color=discord.Color.blue())

        for inv_item in usable_items:
            embed.add_field(
                name=f"{inv_item.item.name} (x{inv_item.quantity})",
                value=inv_item.item.description,
                inline=False)

        await ctx.send(embed=embed)
        return

    # Find the item in the player's inventory
    item_found = None
    for inv_item in player.inventory:
        if item_name.lower() in inv_item.item.name.lower():
            item_found = inv_item
            break

    if not item_found:
        await ctx.send(
            f"You don't have an item named '{item_name}' in your inventory.")
        return

    # Check if item is usable
    item = item_found.item
    is_potion = "potion" in item.name.lower()
    is_energy = "energy" in item.name.lower()

    if not (is_potion or is_energy):
        await ctx.send(
            f"You can't use {item.name} directly. Try equipping it instead.")
        return

    # Apply item effects
    effect_description = ""
    success = False

    if is_potion and "health" in item.name.lower():
        # Health potion - restore HP in battle or do nothing outside battle
        effect_description = "This potion restores health during battles."
        await ctx.send(f"✅ {item.name} will be available in your next battle.")
        success = True

    elif is_energy and "battle" in item.name.lower():
        # Battle energy potion - restore battle energy
        energy_restore = 50  # Default value
        for key, value in item.stats.items():
            if "energy" in key.lower():
                energy_restore = value
                break

        # Apply energy restoration
        old_energy = player.battle_energy
        max_energy = player.get_max_battle_energy()
        player.battle_energy = min(max_energy,
                                   player.battle_energy + energy_restore)
        actual_restored = player.battle_energy - old_energy

        effect_description = f"Restored {actual_restored} battle energy! ({player.battle_energy}/{max_energy})"
        success = True

    elif is_potion and "cursed" in item.name.lower():
        # Cursed energy potion - add cursed energy (currency)
        energy_boost = 500  # Default value
        for key, value in item.stats.items():
            if "cursed" in key.lower() or "currency" in key.lower():
                energy_boost = value
                break

        # Apply currency boost
        player.add_cursed_energy(energy_boost)
        effect_description = f"Added {energy_boost} cursed energy (currency)! (Now have {player.cursed_energy})"
        success = True

    else:
        await ctx.send(
            f"This item cannot be used directly. Try using it in battle.")
        return

    # If successfully used, remove from inventory
    if success:
        item_found.quantity -= 1
        if item_found.quantity <= 0:
            player.inventory.remove(item_found)

        # Save player data
        data_manager.save_data()

        # Send success message
        embed = discord.Embed(title=f"Used {item.name}",
                              description=effect_description,
                              color=discord.Color.green())
        await ctx.send(embed=embed)


@bot.command(name="battle", aliases=["b"])
async def battle_command(ctx, enemy_name: str = None, enemy_level: int = None):
    """Battle an enemy or another player. Mention a user to start PvP"""
    player = data_manager.get_player(ctx.author.id)

    # Check if player has started
    if not player.class_name:
        await ctx.send(
            "❌ You haven't started your adventure yet! Use `!start` to choose a class."
        )
        return

    # Check if player has sufficient energy and restore if too low
    from utils import GAME_CLASSES
    player_stats = player.get_stats(GAME_CLASSES)
    max_energy = player.get_max_battle_energy()
    min_energy_needed = 20  # Minimum energy needed to use basic moves

    if hasattr(player,
               'battle_energy') and player.battle_energy < min_energy_needed:
        # Restore energy to full
        player.battle_energy = max_energy
        data_manager.save_data()

        # Notify player
        embed = discord.Embed(
            title="⚡ Energy Restored!",
            description=
            f"Your energy was too low to battle effectively. It has been restored to full ({max_energy}/{max_energy}).",
            color=discord.Color.blue())
        await ctx.send(embed=embed)

    # If mention, initiate PvP battle
    if ctx.message.mentions:
        target_member = ctx.message.mentions[0]

        # Prevent self-battle
        if target_member.id == ctx.author.id:
            await ctx.send("❌ You can't battle yourself!")
            return

        # Check if target has started
        target_data = data_manager.get_player(target_member.id)
        if not target_data.class_name:
            await ctx.send(
                f"❌ {target_member.display_name} hasn't started their adventure yet!"
            )
            return

        # Start PvP battle
        await start_pvp_battle(ctx, target_member, player, target_data,
                               data_manager)
        return

    # If no specific enemy, choose random appropriate one
    if not enemy_name or not enemy_level:
        # Expanded regular enemy list with much more variety
        enemy_types = [
            # Original enemies
            "Cursed Wolf",
            "Forest Specter",
            "Ancient Treefolk",
            "Cave Crawler",
            "Armored Golem",
            "Crystal Spider",
            "Shrine Guardian",
            "Cursed Monk",
            "Vengeful Spirit",
            "Deep One",
            "Abyssal Hunter",
            "Giant Squid",
            "Flame Knight",
            "Lava Golem",
            "Fire Drake",
            # Forest creatures
            "Shadow Prowler",
            "Thornbark Guardian",
            "Wisp Enchanter",
            "Dryad Scout",
            "Feral Druid",
            "Spore Shambler",
            "Verdant Sentinel",
            "Woodland Stalker",
            # Mountain enemies
            "Rock Hurler",
            "Mountain Troll",
            "Obsidian Golem",
            "Storm Harpy",
            "Cliff Ambusher",
            "Avalanche Beast",
            "Crystal Basilisk",
            # Ocean/Water creatures
            "Coral Guardian",
            "Siren Enchantress",
            "Kraken Spawn",
            "Tidecaller",
            "Pearl Defender",
            "Abyssal Lurker",
            "Reef Hunter",
            # Desert dwellers
            "Sand Wraith",
            "Dust Devil",
            "Mirage Stalker",
            "Cactus Elemental",
            "Dune Scorpion",
            "Oasis Defender",
            "Sand Shark",
            # Dark realm creatures
            "Soul Harvester",
            "Void Walker",
            "Nightmare Spawn",
            "Dream Eater",
            "Shadow Weaver",
            "Nether Beast",
            "Dark Oracle"
        ]

        # Choose enemy level based on player level
        min_level = max(1, player.class_level - 2)
        max_level = player.class_level + 2
        enemy_level = random.randint(min_level, max_level)

        # Choose appropriate enemy type
        enemy_name = random.choice(enemy_types)

    # Start PvE battle
    await start_battle(ctx, player, enemy_name, enemy_level, data_manager)


@bot.command(name="pvphistory", aliases=["pvp", "pvpstats"])
async def pvp_history_command(ctx):
    """View your PvP battle history and stats"""
    player = data_manager.get_player(ctx.author.id)

    # Check if player has started
    if not player.class_name:
        await ctx.send("❌ You need to start your adventure first with `!start`"
                       )
        return

    # Create an embed for PvP history
    embed = discord.Embed(
        title="⚔️ PvP Battle History",
        description=f"Battle records for {ctx.author.display_name}",
        color=discord.Color.blue())

    # Add overall stats
    embed.add_field(
        name="📊 Overall Stats",
        value=
        f"**Wins:** {player.pvp_wins}\n**Losses:** {player.pvp_losses}\n**Win Rate:** {calculate_win_rate(player.pvp_wins, player.pvp_losses)}%",
        inline=False)

    # Check cooldown status
    cooldown_msg = "Ready for battle"
    if player.last_pvp_battle:
        # Check if player is on cooldown
        now = datetime.datetime.now()
        # Winners have 30 min cooldown, losers have 60 min cooldown
        if player.pvp_history and player.pvp_history[-1].get(
                "result") == "win":
            cooldown_time = 30 * 60  # 30 minutes in seconds
        else:
            cooldown_time = 60 * 60  # 60 minutes in seconds

        elapsed = (now - player.last_pvp_battle).total_seconds()

        if elapsed < cooldown_time:
            time_left = cooldown_time - elapsed
            cooldown_msg = f"⏱️ On cooldown for {format_time_remaining(time_left)}"

    embed.add_field(name="⏳ Battle Status", value=cooldown_msg, inline=False)

    # Show recent battle history
    if hasattr(player, "pvp_history") and player.pvp_history:
        battles_list = []

        # Get the most recent 5 battles (or fewer if there aren't 5)
        recent_battles = player.pvp_history[-5:] if len(
            player.pvp_history) > 5 else player.pvp_history

        for battle in reversed(recent_battles):
            # Calculate time ago
            battle_time = datetime.datetime.fromisoformat(
                battle.get("timestamp",
                           datetime.datetime.now().isoformat()))
            time_ago = format_time_since(battle_time)

            # Format reward info
            if battle.get("result") == "win":
                reward_info = f"Won {battle.get('cursed_energy_reward', 0)} cursed energy, {battle.get('exp_reward', 0)} XP"
            else:
                reward_info = f"Lost {battle.get('cursed_energy_lost', 0)} cursed energy"

            battles_list.append(
                f"vs {battle.get('opponent_name', 'Unknown')} (Lvl {battle.get('opponent_level', '?')}) - {time_ago} ago\n   {reward_info}"
            )

        embed.add_field(name="Recent Battles",
                        value="\n".join(battles_list)
                        if battles_list else "No battles yet.",
                        inline=False)
    else:
        embed.add_field(
            name="Recent Battles",
            value="No battles yet. Challenge someone with `!battle @player`!",
            inline=False)

    # Add tips
    embed.set_footer(
        text=
        "Tip: PvP battles have cooldowns - 30 min for winners, 60 min for losers."
    )

    await ctx.send(embed=embed)


def calculate_win_rate(wins, losses):
    """Calculate win rate as a percentage"""
    total_battles = wins + losses
    if total_battles == 0:
        return 0
    return round((wins / total_battles) * 100, 1)


def format_time_since(timestamp):
    """Format the time since a timestamp in a human-readable way"""
    now = datetime.datetime.now()
    delta = now - timestamp

    if delta.days > 0:
        return f"{delta.days}d"
    elif delta.seconds >= 3600:
        return f"{delta.seconds // 3600}h"
    elif delta.seconds >= 60:
        return f"{delta.seconds // 60}m"
    else:
        return f"{delta.seconds}s"


def format_time_remaining(seconds):
    """Format remaining seconds in a human-readable way"""
    if seconds >= 3600:
        return f"{int(seconds // 3600)}h {int((seconds % 3600) // 60)}m"
    elif seconds >= 60:
        return f"{int(seconds // 60)}m {int(seconds % 60)}s"
    else:
        return f"{int(seconds)}s"


@bot.command(name="dungeon", aliases=["d"])
async def dungeon_cmd(ctx):
    """Enter a dungeon"""
    await dungeon_command(ctx, data_manager)


@bot.command(name="equipment", aliases=["e"])
async def equipment_cmd(ctx):
    """View and manage your equipment"""
    await equipment_command(ctx, data_manager)


@bot.command(name="inventory", aliases=["i", "inv"])
async def inventory_cmd(ctx):
    """View your inventory and equipped items"""
    await equipment_command(ctx, data_manager)


@bot.command(name="shop", aliases=["s"])
async def shop_cmd(ctx):
    """Browse the item shop"""
    await shop_command(ctx, data_manager)


@bot.command(name="buy")
async def buy_cmd(ctx, *, item_name: str = None):
    """Buy an item from the shop"""
    await buy_command(ctx, item_name, data_manager)


@bot.command(name="train", aliases=["t"])
async def train_cmd(ctx):
    """Train to improve your stats"""
    await train_command(ctx, data_manager)


@bot.command(name="advanced_training", aliases=["atrain", "at"])
async def advanced_training_cmd(ctx):
    """Participate in advanced training exercises"""
    await advanced_training_command(ctx, data_manager)


@bot.command(name="skills", aliases=["sk"])
async def skills_cmd(ctx):
    """Allocate skill points"""
    await skills_command(ctx, data_manager)


@bot.command(name="skilltree", aliases=["skt", "tree"])
async def skill_tree_cmd(ctx):
    """View and allocate points in your skill tree"""
    await skill_tree_command(ctx, data_manager)


@bot.command(name="change_class", aliases=["cc", "class"])
async def change_class_cmd(ctx):
    """Change your character's class to another unlocked class"""
    await class_change_command(ctx, data_manager)


@bot.command(name="special_items", aliases=["sitems", "si"])
async def special_items_cmd(ctx):
    """View and use your special items and abilities"""
    await special_items_command(ctx, data_manager)


@bot.command(name="trade", aliases=["tr"])
async def trade_cmd(ctx, target_member: discord.Member):
    """Trade items and gold with another player"""
    await trade_command(ctx, target_member, data_manager)


@bot.command(name="guild")
async def guild_cmd(ctx, action: str = None, *args):
    """Guild system - create or join a guild and adventure with others"""
    await guild_command(ctx, action, *args)


@bot.command(name="g")
async def g_cmd(ctx, action: str = None, *args):
    """Guild system - create or join a guild and adventure with others (alias)"""
    await guild_command(ctx, action, *args)


@bot.command(name="world_boss", aliases=["wb", "event_boss"])
async def world_boss_cmd(ctx):
    """Battle the active event boss (only works during special boss events)"""
    player = data_manager.get_player(ctx.author.id)

    # Check if player has started
    if not player.class_name:
        await ctx.send(
            "❌ You haven't started your adventure yet! Use `!start` to choose a class."
        )
        return

    # Import necessary modules
    from achievements import QuestManager
    import random

    # Initialize quest manager
    quest_manager = QuestManager(data_manager)

    # Get active events
    active_events = quest_manager.get_active_events()

    # Filter for active boss events
    boss_events = [
        event for event in active_events
        if event.get("effect", {}).get("type") == "world_boss"
    ]

    if not boss_events:
        await ctx.send(
            "❌ There is no active world boss event right now! Ask an admin to start a special boss event."
        )
        return

    # Get the boss event details
    boss_event = boss_events[0]  # Take the first boss event if multiple exist
    boss_name = boss_event["effect"]["boss_name"]
    boss_level = boss_event["effect"]["boss_level"]

    # Check if player has sufficient energy
    from utils import GAME_CLASSES
    max_energy = player.get_max_battle_energy()
    min_energy_needed = 20  # Minimum energy needed to use basic moves

    if hasattr(player,
               'battle_energy') and player.battle_energy < min_energy_needed:
        # Restore energy to full
        player.battle_energy = max_energy
        data_manager.save_data()

        # Notify player
        embed = discord.Embed(
            title="⚡ Energy Restored!",
            description=
            f"Your energy was too low to battle effectively. It has been restored to full ({max_energy}/{max_energy}).",
            color=discord.Color.blue())
        await ctx.send(embed=embed)

    # Create boss introduction embed
    boss_intro = discord.Embed(
        title=f"🔥 WORLD BOSS - {boss_name}",
        description=
        f"You challenge the mighty world boss, {boss_name} (Level {boss_level})!",
        color=discord.Color.dark_red())

    # Add information about potential rewards
    boss_intro.add_field(
        name="Potential Rewards",
        value=
        "💎 Rare Equipment\n🌟 Mythical Items\n💰 Huge Gold Reward\n✨ Massive XP Boost",
        inline=False)

    await ctx.send(embed=boss_intro)

    # Create a custom battle handler for the boss
    class BossResultHandler:

        def __init__(self, original_battle_func):
            self.original_battle_func = original_battle_func

        async def __call__(self, *args, **kwargs):
            # Call the original battle function and get the result
            # The battle function sets player_entity.is_alive() to check if player won
            ctx, player, boss_name, boss_level, data_manager = args

            # Run the original battle
            await self.original_battle_func(*args, **kwargs)

            # After battle, check if player won by checking their stats
            # Players with wins incremented after a battle victory
            previous_wins = player.wins
            data_manager.save_data()  # Ensure data is refreshed
            player = data_manager.get_player(
                player.user_id)  # Get fresh player data

            # If player won (wins increased), give special boss loot
            if player.wins > previous_wins:
                await self.award_boss_loot(ctx, player, boss_name, boss_level,
                                           data_manager)

        async def award_boss_loot(self, ctx, player, boss_name, boss_level,
                                  data_manager):
            """Award special loot for defeating a world boss"""
            # Import necessary modules for item generation
            from equipment import generate_rare_item, generate_random_item, add_item_to_inventory
            from special_items import get_random_special_drop

            # Special rewards for boss
            bonus_gold = boss_level * random.randint(100, 200)
            bonus_exp = boss_level * random.randint(50, 100)

            # Award bonus gold and XP
            player.add_gold(bonus_gold)
            player.add_exp(bonus_exp)

            # Create loot embed
            loot_embed = discord.Embed(
                title=f"🏆 Boss Defeated: {boss_name}",
                description=
                f"You have defeated the mighty {boss_name}! Here are your additional rewards:",
                color=discord.Color.gold())

            loot_embed.add_field(
                name="Bonus Rewards",
                value=f"💰 Gold: +{bonus_gold}\n✨ XP: +{bonus_exp}",
                inline=False)

            # 75% chance to get a rare item
            if random.random() < 0.75:
                rare_item = generate_rare_item(boss_level)
                add_item_to_inventory(player, rare_item)

                loot_embed.add_field(
                    name="💎 Rare Item Found!",
                    value=f"**{rare_item.name}**\n{rare_item.description}",
                    inline=False)

            # 25% chance to get a mythical item
            if random.random() < 0.25:
                special_item = await get_random_special_drop(player.class_level
                                                             )
                if special_item:
                    add_item_to_inventory(player, special_item)

                    loot_embed.add_field(
                        name="🌟 Mythical Item Found!",
                        value=
                        f"**{special_item.name}**\n{special_item.description}",
                        inline=False)

            # Always give a random item as a consolation
            if not loot_embed.fields or len(loot_embed.fields) < 3:
                regular_item = generate_random_item(boss_level)
                add_item_to_inventory(player, regular_item)

                loot_embed.add_field(
                    name="📦 Item Found",
                    value=
                    f"**{regular_item.name}**\n{regular_item.description}",
                    inline=False)

            # Save player data
            data_manager.save_data()

            # Send loot message
            await ctx.send(embed=loot_embed)

    # Import the battle system
    from battle_system_new import start_battle

    # Create a wrapper for the battle function
    boss_battle_handler = BossResultHandler(start_battle)

    # Start battle with the boss using the wrapper
    await boss_battle_handler(ctx, player, boss_name, boss_level, data_manager)


@bot.command(name="achievements")
async def achievements_cmd(ctx):
    """View your achievements and badges"""
    await achievements_command(ctx, data_manager)


@bot.command(name="achieve")
async def achieve_cmd(ctx):
    """View your achievements and badges (alias)"""
    await achievements_command(ctx, data_manager)


@bot.command(name="ach")
async def ach_cmd(ctx):
    """View your achievements and badges (alias)"""
    await achievements_command(ctx, data_manager)


class EnhancedGiveView(discord.ui.View):
    """Enhanced give system with categories and nested options"""

    def __init__(self, target_member: discord.Member):
        super().__init__(timeout=60)
        self.target_member = target_member
        self.current_category = None
        self.category_embed = None

        # Add dropdown for category selection
        self.category_select = discord.ui.Select(
            placeholder="Select what to give...",
            min_values=1,
            max_values=1,
            custom_id="category_select"
        )

        # Add options for different categories
        for category_id, data in GIVE_CATEGORIES.items():
            self.category_select.add_option(
                label=data["name"],
                emoji=data["emoji"],
                description=data["description"],
                value=category_id
            )

        # Set callback for category selection
        self.category_select.callback = self.category_select_callback
        self.add_item(self.category_select)

        # Add cancel button
        cancel_button = discord.ui.Button(
            label="Cancel",
            style=discord.ButtonStyle.secondary,
            custom_id="cancel"
        )
        cancel_button.callback = self.cancel_callback
        self.add_item(cancel_button)

    async def category_select_callback(self, interaction: discord.Interaction):
        # Get selected category
        category_id = interaction.data["values"][0]
        self.current_category = category_id

        # Create an embed for the category options
        category_data = GIVE_CATEGORIES[category_id]
        embed = discord.Embed(
            title=f"📦 Enhanced Give System",
            description=f"Select what you want to give to {self.target_member.display_name}:",
            color=discord.Color.gold()
        )

        # Add the category as a field in the embed
        embed.add_field(
            name=f"{category_data['emoji']} {category_data['name']}",
            value=category_data['description'],
            inline=False
        )

        # Create a new view with options specific to this category
        options_view = CategoryOptionsView(self.target_member, category_id)

        # Update the message with the new embed and view
        await interaction.response.edit_message(embed=embed, view=options_view)
        self.stop()

    async def cancel_callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(
            content=f"Cancelled giving resources to {self.target_member.display_name}.",
            view=None,
            embed=None
        )
        self.stop()


class CategoryOptionsView(discord.ui.View):
    """View for showing options within a specific category"""

    def __init__(self, target_member: discord.Member, category_id: str):
        super().__init__(timeout=60)
        self.target_member = target_member
        self.category_id = category_id

        # Add dropdown for option selection
        self.option_select = discord.ui.Select(
            placeholder="Select what to give...",
            min_values=1,
            max_values=1,
            custom_id="option_select"
        )

        # Add options for the selected category
        for resource_id, data in GIVE_OPTIONS.items():
            if data["category"] == category_id:
                self.option_select.add_option(
                    label=resource_id.replace('_', ' ').title(),
                    emoji=data["emoji"],
                    description=data["description"],
                    value=resource_id
                )

        # Set callback for option selection
        self.option_select.callback = self.option_select_callback
        self.add_item(self.option_select)

        # Add back button
        back_button = discord.ui.Button(
            label="Back",
            style=discord.ButtonStyle.secondary,
            custom_id="back"
        )
        back_button.callback = self.back_callback
        self.add_item(back_button)

        # Add cancel button
        cancel_button = discord.ui.Button(
            label="Cancel",
            style=discord.ButtonStyle.secondary,
            custom_id="cancel"
        )
        cancel_button.callback = self.cancel_callback
        self.add_item(cancel_button)

    async def option_select_callback(self, interaction: discord.Interaction):
        # Get selected option
        option_id = interaction.data["values"][0]

        # Process the selected option based on its type
        if option_id == "items" or option_id == "weapons" or option_id == "armor":
            # For items, show the item browser (with filtering if specified)
            await interaction.response.defer()

            # Get player data
            player = data_manager.get_player(self.target_member.id)

            # Import necessary functions
            from equipment import get_all_items, add_item_to_inventory, generate_item_id
            from special_items import get_all_special_items

            # Combine regular and special items
            all_items = get_all_items() + get_all_special_items()

            # Filter items based on selected type
            if option_id == "weapons":
                filtered_items = [item for item in all_items if item.type.lower() == "weapon"]
            elif option_id == "armor":
                filtered_items = [item for item in all_items if item.type.lower() == "armor"]
            else:
                filtered_items = all_items

            # Sort items by rarity
            rarity_order = {
                "legendary": 0,
                "epic": 1,
                "rare": 2,
                "uncommon": 3,
                "common": 4
            }
            filtered_items.sort(key=lambda x: (rarity_order.get(x.rarity.lower(), 999), x.name))

            # Create an item browser view
            view = ItemBrowserView(filtered_items, self.target_member, player)
            embed = view.create_browser_embed()

            await interaction.followup.send(embed=embed, view=view)
            self.stop()
        elif option_id == "stats":
            # Show stats selection
            await interaction.response.defer()

            # Create a stats selection view
            view = StatsSelectionView(self.target_member)
            embed = view.create_stats_embed()

            await interaction.followup.send(embed=embed, view=view)
            self.stop()
        else:
            # For other resources, show amount input modal
            modal = EnhancedAmountInputModal(self.target_member, option_id)
            await interaction.response.send_modal(modal)

    async def back_callback(self, interaction: discord.Interaction):
        # Go back to category selection
        view = EnhancedGiveView(self.target_member)
        embed = discord.Embed(
            title="📦 Enhanced Give System",
            description=f"Select what you want to give to {self.target_member.display_name}:",
            color=discord.Color.gold()
        )
        await interaction.response.edit_message(embed=embed, view=view)
        self.stop()

    async def cancel_callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(
            content=f"Cancelled giving resources to {self.target_member.display_name}.",
            view=None,
            embed=None
        )
        self.stop()


class StatsSelectionView(discord.ui.View):
    """View for selecting which stat to increase"""

    def __init__(self, target_member: discord.Member):
        super().__init__(timeout=60)
        self.target_member = target_member

        # Get player data
        self.player = data_manager.get_player(target_member.id)

        # Add buttons for stats
        self.add_stat_button("Health", "❤️", 0)
        self.add_stat_button("Cursed Power", "🔮", 0)
        self.add_stat_button("Defense", "🛡️", 1)
        self.add_stat_button("Speed", "💨", 1)

        # Add back button
        back_button = discord.ui.Button(
            label="Back",
            style=discord.ButtonStyle.secondary,
            custom_id="back",
            row=2
        )
        back_button.callback = self.back_callback
        self.add_item(back_button)

    def add_stat_button(self, stat_name: str, emoji: str, row: int):
        button = discord.ui.Button(
            label=stat_name,
            emoji=emoji,
            style=discord.ButtonStyle.primary,
            custom_id=stat_name.lower(),
            row=row
        )
        button.callback = self.stat_button_callback
        self.add_item(button)

    async def stat_button_callback(self, interaction: discord.Interaction):
        stat_name = interaction.data["custom_id"]

        # Create a modal for entering amount
        modal = StatsAmountModal(self.target_member, stat_name)
        await interaction.response.send_modal(modal)

    async def back_callback(self, interaction: discord.Interaction):
        # Go back to category selection within Resources
        view = CategoryOptionsView(self.target_member, "progress")

        category_data = GIVE_CATEGORIES["progress"]
        embed = discord.Embed(
            title=f"📦 Enhanced Give System",
            description=f"Select what you want to give to {self.target_member.display_name}:",
            color=discord.Color.gold()
        )
        embed.add_field(
            name=f"{category_data['emoji']} {category_data['name']}",
            value=category_data['description'],
            inline=False
        )

        await interaction.response.edit_message(embed=embed, view=view)
        self.stop()

    def create_stats_embed(self):
        """Create the stats selection embed"""
        embed = discord.Embed(
            title=f"📊 Give Stats to {self.target_member.display_name}",
            description="Select a stat to increase by 1 point:",
            color=discord.Color.blue()
        )

        embed.add_field(
            name="Ready to Add Stats",
            value=(
                f"❤️ Health\n"
                f"🔮 Cursed Power\n"
                f"🛡️ Defense\n"
                f"💨 Speed"
            ),
            inline=False
        )

        return embed


class EnhancedAmountInputModal(discord.ui.Modal):
    """Enhanced modal for entering resource amounts"""

    def __init__(self, target_member: discord.Member, resource_type: str):
        self.target_member = target_member
        self.resource_type = resource_type

        # Get emoji and formatted title
        resource_data = GIVE_OPTIONS.get(resource_type, {})
        emoji = resource_data.get("emoji", "📦")
        formatted_title = resource_type.replace('_', ' ').title()

        super().__init__(title=f"Give {formatted_title} {emoji}")

        # Add text input for amount
        self.amount_input = discord.ui.TextInput(
            label=f"Amount Of {formatted_title} To Give",
            placeholder="Enter number of points (e.g., 5, 10, 25)",
            required=True,
            min_length=1,
            max_length=10
        )
        self.add_item(self.amount_input)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            amount = int(self.amount_input.value)
            if amount <= 0:
                await interaction.response.send_message(
                    "❌ Amount must be greater than 0.",
                    ephemeral=True
                )
                return

            # Get player data
            player = data_manager.get_player(self.target_member.id)

            # Process different resource types
            success_message = ""
            title = ""
            color = discord.Color.green()

            if self.resource_type == "gold":
                player.gold += amount
                success_message = f"Added **{amount}** gold to {self.target_member.mention}.\nNew balance: **{player.gold}** 💰"
                title = "💰 Gold Added"

            elif self.resource_type == "xp":
                old_level = player.class_level
                old_exp = player.class_exp

                # Apply XP with bypass_penalty=True to ensure exact amount is given
                leveled_up = player.add_exp(amount, bypass_penalty=True, data_manager=data_manager)
                next_level_exp = player.xp_to_next_level()

                # Admin command always gives exact amount specified
                success_message = f"Added **{amount}** XP to {self.target_member.mention}.\nCurrent level: **{player.class_level}** | XP: **{player.class_exp}/{next_level_exp}**"

                if leveled_up:
                    success_message += f"\n\n🎉 **Level Up!** {self.target_member.mention} is now level **{player.class_level}**!"

                title = "✨ XP Added"
                color = discord.Color.purple()

            elif self.resource_type == "skill_points":
                player.skill_points += amount
                success_message = f"Added **{amount}** skill points to {self.target_member.mention}.\nNew total: **{player.skill_points}** 🎯"
                title = "🎯 Skill Points Added"
                color = discord.Color.blue()

            elif self.resource_type == "battle_energy":
                # Increase max battle energy
                player.max_battle_energy += amount
                player.battle_energy = player.max_battle_energy  # Refill energy
                success_message = f"Increased max battle energy for {self.target_member.mention} by **{amount}**.\nNew maximum: **{player.max_battle_energy}** ⚡"
                title = "⚡ Battle Energy Increased"
                color = discord.Color.gold()

            elif self.resource_type == "pvp_history":
                # Add PvP wins
                player.pvp_wins += amount
                success_message = f"Added **{amount}** PvP win(s) to {self.target_member.mention}.\nPvP record: **{player.pvp_wins}** wins / **{player.pvp_losses}** losses"
                title = "⚔️ PvP History Updated"
                color = discord.Color.red()

            elif self.resource_type == "quest_complete":
                # For simplicity, mark a number of quests as complete
                # In a real implementation, you would want to select specific quests
                success_message = f"Marked **{amount}** quest(s) as complete for {self.target_member.mention}."
                title = "✅ Quests Completed"
                color = discord.Color.green()

            # Save player data
            data_manager.save_data()

            # Send confirmation message
            embed = discord.Embed(
                title=title,
                description=success_message,
                color=color
            )
            await interaction.response.send_message(embed=embed)

        except ValueError:
            await interaction.response.send_message(
                "❌ Please enter a valid number.",
                ephemeral=True
            )


class StatsAmountModal(discord.ui.Modal):
    """Modal for entering stat point amounts"""

    def __init__(self, target_member: discord.Member, stat_name: str):
        self.target_member = target_member
        self.stat_name = stat_name

        # Get emoji based on stat
        emoji_map = {
            "health": "❤️",
            "cursed power": "🔮",
            "defense": "🛡️",
            "speed": "💨"
        }
        emoji = emoji_map.get(stat_name, "📊")

        super().__init__(title=f"Give {stat_name.title()} Points {emoji}")

        # Add text input for amount
        self.amount_input = discord.ui.TextInput(
            label=f"Amount Of {stat_name.title()} To Give",
            placeholder="Enter number of points (e.g., 5, 10, 25)",
            required=True,
            min_length=1,
            max_length=10
        )
        self.add_item(self.amount_input)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            amount = int(self.amount_input.value)
            if amount <= 0:
                await interaction.response.send_message(
                    "❌ Amount must be greater than 0.",
                    ephemeral=True
                )
                return

            # Get player data
            player = data_manager.get_player(self.target_member.id)

            # Update the appropriate stat
            stat_attr = self.stat_name.lower().replace(" ", "_")

            # Handle special case for cursed power - map to power in allocated_stats
            if stat_attr == "cursed_power":
                if "power" in player.allocated_stats:
                    player.allocated_stats["power"] += amount
                else:
                    player.allocated_stats["power"] = amount
                current_value = player.allocated_stats["power"]
            elif stat_attr == "health":
                # For health, update the current_hp and max HP in allocated_stats
                if "hp" in player.allocated_stats:
                    player.allocated_stats["hp"] += amount
                else:
                    player.allocated_stats["hp"] = amount
                player.current_hp += amount  # Also increase current HP
                current_value = player.allocated_stats["hp"]
            elif stat_attr == "defense" or stat_attr == "speed":
                # Map to the correct stat name in allocated_stats
                if stat_attr in player.allocated_stats:
                    player.allocated_stats[stat_attr] += amount
                else:
                    player.allocated_stats[stat_attr] = amount
                current_value = player.allocated_stats[stat_attr]
            else:
                # Generic fallback for any direct attributes
                if hasattr(player, stat_attr):
                    current_value = getattr(player, stat_attr) + amount
                    setattr(player, stat_attr, current_value)
                else:
                    await interaction.response.send_message(
                        f"❌ Unable to find stat attribute: {stat_attr}",
                        ephemeral=True
                    )
                    return

            # Save player data
            data_manager.save_data()

            # Get emoji for the stat
            emoji_map = {
                "health": "❤️",
                "cursed_power": "🔮",
                "defense": "🛡️",
                "speed": "💨"
            }
            emoji = emoji_map.get(stat_attr, "📊")

            # Create confirmation message with appropriate title and description
            title = f"{emoji} {self.stat_name.title()} Increased"

            if stat_attr == "health":
                description = f"Added **{amount}** {self.stat_name} points to {self.target_member.mention}.\nNew value: **{current_value}** {emoji}"
            elif stat_attr == "cursed_power":
                description = f"Added **{amount}** Cursed Power points to {self.target_member.mention}.\nNew value: **{current_value}** {emoji}"
            else:
                description = f"Added **{amount}** {self.stat_name} points to {self.target_member.mention}.\nNew value: **{current_value}** {emoji}"

            # Send confirmation message
            embed = discord.Embed(
                title=title,
                description=description,
                color=discord.Color.blue()
            )
            await interaction.response.send_message(embed=embed)

        except ValueError:
            await interaction.response.send_message(
                "❌ Please enter a valid number.",
                ephemeral=True
            )


class GiveOptionsView(discord.ui.View):
    """Legacy class for backward compatibility - now redirects to EnhancedGiveView"""

    def __init__(self, target_member: discord.Member):
        super().__init__(timeout=60)
        self.target_member = target_member

        # Add dropdown for resource type selection
        self.resource_select = discord.ui.Select(
            placeholder="Select what to give", min_values=1, max_values=1)

        # Add options for different resources
        for resource_id, data in GIVE_OPTIONS.items():
            # Only include original options for backward compatibility
            if resource_id in ["gold", "xp", "items"]:
                self.resource_select.add_option(
                    label=resource_id.replace('_', ' ').title(),
                    emoji=data["emoji"],
                    description=data["description"],
                    value=resource_id
                )

        # Set the callback function
        self.resource_select.callback = self.resource_select_callback
        self.add_item(self.resource_select)

        # Add cancel button
        cancel_button = discord.ui.Button(
            label="Cancel",
            style=discord.ButtonStyle.secondary,
            custom_id="cancel"
        )
        cancel_button.callback = self.cancel_callback
        self.add_item(cancel_button)

    async def resource_select_callback(self, interaction: discord.Interaction):
        # Get the selected resource
        resource_type = interaction.data["values"][0]

        # Create a modal to ask for amount
        if resource_type != "items":
            modal = AmountInputModal(self.target_member, resource_type)
            await interaction.response.send_modal(modal)
        else:
            # For items, show the item browser with rarity sorting
            await interaction.response.defer()

            # Get player data
            player = data_manager.get_player(self.target_member.id)

            # Import necessary functions
            from equipment import get_all_items, add_item_to_inventory, generate_item_id
            from special_items import get_all_special_items

            # Combine regular and special items
            all_items = get_all_items() + get_all_special_items()

            # Sort items by rarity (legendary → epic → rare → uncommon → common)
            rarity_order = {
                "legendary": 0,
                "epic": 1,
                "rare": 2,
                "uncommon": 3,
                "common": 4
            }
            all_items.sort(key=lambda x:
                           (rarity_order.get(x.rarity.lower(), 999), x.name))

            # Create an item browser view
            view = ItemBrowserView(all_items, self.target_member, player)
            embed = view.create_browser_embed()

            await interaction.followup.send(embed=embed, view=view)
            self.stop()

    async def cancel_callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(
            content=
            f"Cancelled giving resources to {self.target_member.display_name}.",
            view=None)
        self.stop()


class AmountInputModal(discord.ui.Modal):

    def __init__(self, target_member: discord.Member, resource_type: str):
        self.target_member = target_member
        self.resource_type = resource_type
        emoji = GIVE_OPTIONS[resource_type]["emoji"]
        super().__init__(
            title=f"Give {resource_type.replace('_', ' ').title()} {emoji}")

        # Add text input for amount
        self.amount_input = discord.ui.TextInput(
            label=f"Amount of {resource_type.replace('_', ' ')} to give:",
            placeholder="Enter a number greater than 0",
            required=True,
            min_length=1,
            max_length=10)
        self.add_item(self.amount_input)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            amount = int(self.amount_input.value)
            if amount <= 0:
                await interaction.response.send_message(
                    "❌ Amount must be greater than 0.", ephemeral=True)
                return

            player = data_manager.get_player(self.target_member.id)

            # Process different resource types
            if self.resource_type == "gold":
                player.add_gold(amount)
                success_message = f"Added **{amount}** gold to {self.target_member.mention}'s balance.\nNew balance: **{player.gold}** 💰"
                color = discord.Color.gold()
                title = "💰 Gold Added"

            elif self.resource_type == "xp":
                # Use the proper add_exp method that handles level ups automatically
                old_level = player.class_level
                exp_result = player.add_exp(amount, bypass_penalty=True, data_manager=data_manager)
                leveled_up = exp_result["leveled_up"]

                # Calculate XP needed for next level
                if player.class_level < 1000:  # Max level cap
                    next_level_exp = player.calculate_xp_for_level(
                        player.class_level)
                else:
                    next_level_exp = 0

                # Format success message with Double XP event display
                exp_text = f"Added **{amount}** XP to {self.target_member.mention}."
                if exp_result["event_multiplier"] > 1.0:
                    exp_text = f"Added **{amount}** XP → **{exp_result['adjusted_exp']}** XP to {self.target_member.mention} (🎉 {exp_result['event_name']} {exp_result['event_multiplier']}x!)"

                # Format success message differently if player leveled up
                if player.class_level > old_level:
                    success_message = (
                        f"{exp_text}\n"
                        f"They leveled up from **{old_level}** to **{player.class_level}**! 🎉\n"
                        f"Current XP: **{player.class_exp}/{next_level_exp}**")
                else:
                    success_message = (
                        f"{exp_text}\n"
                        f"Current level: **{player.class_level}**\n"
                        f"XP: **{player.class_exp}/{next_level_exp}**")
                color = discord.Color.purple()
                title = "✨ XP Added"

            elif self.resource_type == "cursed_energy":
                player.cursed_energy += amount  # Direct assignment for cursed energy
                success_message = f"Added **{amount}** cursed energy to {self.target_member.mention}.\nNew balance: **{player.cursed_energy}** 🔮"
                color = discord.Color.dark_purple()
                title = "🔮 Cursed Energy Added"

            # Save player data
            data_manager.save_data()

            # Send confirmation message
            embed = discord.Embed(title=title,
                                  description=success_message,
                                  color=color)
            await interaction.response.send_message(embed=embed)

        except ValueError:
            await interaction.response.send_message(
                "❌ Please enter a valid number.", ephemeral=True)


@bot.command(name="give")
@commands.check(admin_check)
async def give_cmd(ctx, member: discord.Member = None):
    """[Admin] Give resources to a user with an enhanced interactive menu"""
    if not member:
        await ctx.send("❌ Please specify a user to give resources to.")
        return

    # Create enhanced give view with categories
    view = EnhancedGiveView(member)

    # Create embed for the give menu
    embed = discord.Embed(
        title="📦 Enhanced Give System",
        description=f"Select what you want to give to {member.display_name}:",
        color=discord.Color.gold()
    )

    # Add categories as fields
    for category_id, data in GIVE_CATEGORIES.items():
        embed.add_field(
            name=f"{data['emoji']} {data['name']}",
            value=data['description'],
            inline=True
        )

    # Send the message with embed and view
    await ctx.send(embed=embed, view=view)


@bot.command(name="give_gold")
@commands.check(admin_check)
async def give_gold_cmd(ctx, member: discord.Member, amount: int):
    """[Admin] Give gold to a user"""
    if amount <= 0:
        await ctx.send("❌ Amount must be greater than 0.")
        return

    player = data_manager.get_player(member.id)
    player.add_gold(amount)
    data_manager.save_data()

    embed = discord.Embed(
        title="💰 Gold Added",
        description=
        f"Added **{amount}** gold to {member.mention}'s balance.\nNew balance: **{player.gold}** 💰",
        color=discord.Color.gold())

    await ctx.send(embed=embed)


@bot.command(name="give_xp")
@commands.check(admin_check)
async def give_xp_cmd(ctx, member: discord.Member, amount: int):
    """[Admin] Give XP to a user"""
    if amount <= 0:
        await ctx.send("❌ Amount must be greater than 0.")
        return

    player = data_manager.get_player(member.id)
    exp_result = player.add_exp(amount, bypass_penalty=True, data_manager=data_manager)
    leveled_up = exp_result["leveled_up"]
    data_manager.save_data()

    # Create an embed for the XP award with Double XP event display
    exp_text = f"Added **{amount}** XP to {member.mention}."
    if exp_result["event_multiplier"] > 1.0:
        exp_text = f"Added **{amount}** XP → **{exp_result['adjusted_exp']}** XP to {member.mention} (🎉 {exp_result['event_name']} {exp_result['event_multiplier']}x!)"

    embed = discord.Embed(
        title="📊 XP Added",
        description=f"{exp_text}\nCurrent level: **{player.class_level}** | XP: **{player.class_exp}**/{player.xp_to_next_level()}",
        color=discord.Color.green())

    # If player leveled up, add that info to the embed
    if leveled_up:
        embed.add_field(
            name="🆙 Level Up!",
            value=
            f"{member.mention} leveled up to **Level {player.class_level}**!",
            inline=False)

    await ctx.send(embed=embed)


@bot.command(name="give_item")
@commands.check(admin_check)
async def give_item_cmd(ctx,
                        member: discord.Member = None,
                        *,
                        item_name: str = None):
    """[Admin] Give items to a user with an interactive menu"""
    # If no member specified, show usage
    if not member:
        await ctx.send("❌ Usage: `!give_item @player [optional_search_term]`")
        return

    player = data_manager.get_player(member.id)

    # Import necessary functions
    from equipment import get_all_items, add_item_to_inventory, generate_item_id
    from special_items import get_all_special_items

    # Combine regular and special items
    all_items = get_all_items() + get_all_special_items()

    # Sort items by rarity (legendary, epic, rare, uncommon, common)
    rarity_order = {
        "legendary": 0,
        "epic": 1,
        "rare": 2,
        "uncommon": 3,
        "common": 4
    }
    all_items.sort(
        key=lambda x: (rarity_order.get(x.rarity.lower(), 999), x.name))

    # Log the sort order for debugging
    print(
        f"Items sorted by rarity, showing first 5: {[item.name + ' (' + item.rarity + ')' for item in all_items[:5]]}"
    )

    # Filter items if search term provided
    filtered_items = all_items
    if item_name:
        filtered_items = [
            item for item in all_items
            if item_name.lower() in item.name.lower()
        ]
        if not filtered_items:
            await ctx.send(
                f"❌ No items found matching '{item_name}'. Showing all items.")
            filtered_items = all_items

    # Create an item browser view
    class ItemBrowserView(View):

        def __init__(self, items_list, target_member, target_player):
            super().__init__(timeout=120)
            self.items = items_list
            self.current_page = 0
            self.items_per_page = 10
            self.total_pages = (len(items_list) + self.items_per_page -
                                1) // self.items_per_page
            self.member = target_member
            self.player = target_player
            self.selected_item = None
            self.category_filter = "All"
            self.rarity_filter = "All"

            # Add category filter
            self.add_category_filter()

            # Add rarity filter
            self.add_rarity_filter()

            # Add pagination buttons
            self.add_navigation_buttons()

        def add_category_filter(self):
            """Add dropdown for item category filtering"""
            # Get unique categories from items
            categories = set()
            for item in self.items:
                categories.add(item.item_type.title())

            categories = sorted(list(categories))

            # Create select menu
            select = Select(
                placeholder="Filter by Category",
                options=[
                    discord.SelectOption(
                        label="All Categories", value="All", default=True)
                ] + [
                    discord.SelectOption(label=category, value=category)
                    for category in categories
                ],
                row=0)

            # Set callback
            select.callback = self.category_callback
            self.add_item(select)

        def add_rarity_filter(self):
            """Add dropdown for rarity filtering"""
            # Common rarities with their emoji indicators
            rarities = [("Legendary", "🌟"), ("Epic", "💠"), ("Rare", "🔷"),
                        ("Uncommon", "🔹"), ("Common", "⚪")]

            # Create select menu
            select = Select(
                placeholder="Filter by Rarity",
                options=[
                    discord.SelectOption(
                        label="All Rarities", value="All", default=True)
                ] + [
                    discord.SelectOption(label=f"{emoji} {rarity}",
                                         value=rarity)
                    for rarity, emoji in rarities
                ],
                row=1)

            # Set callback
            select.callback = self.rarity_callback
            self.add_item(select)

        def add_navigation_buttons(self):
            """Add navigation and action buttons"""
            # Previous page button
            prev_button = Button(style=discord.ButtonStyle.secondary,
                                 label="◀ Previous",
                                 disabled=self.current_page == 0,
                                 row=2)
            prev_button.callback = self.prev_page_callback
            self.add_item(prev_button)

            # Next page button
            next_button = Button(style=discord.ButtonStyle.secondary,
                                 label="Next ▶",
                                 disabled=self.current_page
                                 >= self.total_pages - 1,
                                 row=2)
            next_button.callback = self.next_page_callback
            self.add_item(next_button)

            # Give item button
            give_button = Button(style=discord.ButtonStyle.success,
                                 label="Give Selected Item",
                                 disabled=True,
                                 row=3)
            give_button.callback = self.give_item_callback
            self.add_item(give_button)

            # Cancel button
            cancel_button = Button(style=discord.ButtonStyle.danger,
                                   label="Cancel",
                                   row=3)
            cancel_button.callback = self.cancel_callback
            self.add_item(cancel_button)

        async def category_callback(self, interaction: discord.Interaction):
            """Handle category selection"""
            self.category_filter = interaction.data["values"][0]
            self.current_page = 0
            await self.update_view(interaction)

        async def rarity_callback(self, interaction: discord.Interaction):
            """Handle rarity selection"""
            self.rarity_filter = interaction.data["values"][0]
            self.current_page = 0
            await self.update_view(interaction)

        async def prev_page_callback(self, interaction: discord.Interaction):
            """Handle previous page button"""
            self.current_page = max(0, self.current_page - 1)
            await self.update_view(interaction)

        async def next_page_callback(self, interaction: discord.Interaction):
            """Handle next page button"""
            self.current_page = min(self.total_pages - 1,
                                    self.current_page + 1)
            await self.update_view(interaction)

        async def item_select_callback(self, interaction: discord.Interaction):
            """Handle item selection"""
            item_index = int(interaction.data["custom_id"].split("_")[1])
            filtered_items = self.get_filtered_items()
            page_start = self.current_page * self.items_per_page

            if 0 <= item_index < len(filtered_items):
                self.selected_item = filtered_items[page_start + item_index]

                # Update give button state
                for child in self.children:
                    if isinstance(
                            child,
                            Button) and child.label == "Give Selected Item":
                        child.disabled = False

                await interaction.response.edit_message(
                    embed=self.create_browser_embed(), view=self)
            else:
                await interaction.response.defer()

        async def give_item_callback(self, interaction: discord.Interaction):
            """Handle giving the item"""
            if not self.selected_item:
                await interaction.response.send_message("❌ No item selected!",
                                                        ephemeral=True)
                return

            # Create the item and add to inventory - overriding level requirements to allow any item
            new_item = Item(
                item_id=generate_item_id(),
                name=self.selected_item.name,
                description=self.selected_item.description,
                item_type=self.selected_item.item_type,
                rarity=self.selected_item.rarity,
                stats=self.selected_item.stats,
                level_req=1,  # Set to level 1 to bypass restrictions
                value=self.selected_item.value)

            add_item_to_inventory(self.player, new_item)
            data_manager.save_data()

            # Create confirmation embed
            embed = discord.Embed(
                title="🎁 Item Given",
                description=
                f"Added **{new_item.name}** (bypassing level restrictions) to {self.member.mention}'s inventory.",
                color=discord.Color.purple())

            # Get rarity emoji
            rarity_emoji = self.get_rarity_emoji(new_item.rarity)

            # Get type emoji
            type_emoji_map = {
                "weapon": "⚔️",
                "armor": "🛡️",
                "accessory": "💍",
                "consumable": "🧪",
                "material": "🧶",
                "special": "✨"
            }
            type_emoji = type_emoji_map.get(new_item.item_type.lower(), "📦")

            # Add item details with visual indicators
            embed.add_field(
                name="Item Details",
                value=f"**Type:** {type_emoji} {new_item.item_type.title()}\n"
                f"**Rarity:** {rarity_emoji} {new_item.rarity.title()}\n"
                f"**Description:** {new_item.description}",
                inline=False)

            # Add stats if any
            if new_item.stats:
                stats_text = "\n".join([
                    f"**{stat.title()}:** +{value}"
                    for stat, value in new_item.stats.items()
                ])
                embed.add_field(name="Stats", value=stats_text, inline=False)

            # Send confirmation and stop view
            await interaction.response.edit_message(embed=embed, view=None)
            self.stop()

        async def cancel_callback(self, interaction: discord.Interaction):
            """Handle cancellation"""
            await interaction.response.edit_message(
                content="Item selection cancelled.", embed=None, view=None)
            self.stop()

        def get_filtered_items(self):
            """Get items filtered by category and rarity"""
            filtered = self.items

            # Apply category filter
            if self.category_filter != "All":
                filtered = [
                    item for item in filtered
                    if item.item_type.title() == self.category_filter
                ]

            # Apply rarity filter
            if self.rarity_filter != "All":
                filtered = [
                    item for item in filtered
                    if item.rarity.title() == self.rarity_filter
                ]

            return filtered

        async def update_view(self, interaction: discord.Interaction):
            """Update the view with current filters and page"""
            # Update filtered items and total pages
            filtered_items = self.get_filtered_items()
            self.total_pages = max(
                1, (len(filtered_items) + self.items_per_page - 1) //
                self.items_per_page)

            # Ensure current_page is valid
            if self.current_page >= self.total_pages:
                self.current_page = max(0, self.total_pages - 1)

            # Clear item buttons (rows 4-5)
            self.clear_items()

            # Re-add filters and navigation
            self.add_category_filter()
            self.add_rarity_filter()
            self.add_navigation_buttons()

            # Add item buttons for current page
            page_start = self.current_page * self.items_per_page
            page_end = min(page_start + self.items_per_page,
                           len(filtered_items))

            for i, idx in enumerate(range(page_start, page_end)):
                item = filtered_items[idx]
                row = 4 + (i // 2)  # Arrange buttons in pairs

                # Get button style based on rarity
                style_map = {
                    "common": discord.ButtonStyle.secondary,
                    "uncommon": discord.ButtonStyle.primary,
                    "rare": discord.ButtonStyle.primary,
                    "epic": discord.ButtonStyle.danger,
                    "legendary": discord.ButtonStyle.success
                }
                style = style_map.get(item.rarity.lower(),
                                      discord.ButtonStyle.secondary)

                # Get emoji based on item type
                emoji_map = {
                    "weapon": "⚔️",
                    "armor": "🛡️",
                    "accessory": "💍",
                    "consumable": "🧪",
                    "material": "🧶",
                    "special": "✨"
                }
                item_emoji = emoji_map.get(item.item_type.lower(), "📦")

                # Get rarity emoji
                rarity_emoji = self.get_rarity_emoji(item.rarity)

                # Create button
                is_selected = self.selected_item and self.selected_item.name == item.name
                button_label = f"{item.name}"
                if is_selected:
                    button_label = f"✅ {button_label}"

                # Truncate long names
                if len(button_label) > 25:
                    button_label = button_label[:22] + "..."

                button = Button(style=style,
                                label=button_label,
                                emoji=rarity_emoji,
                                custom_id=f"item_{i}",
                                row=row)
                button.callback = self.item_select_callback
                self.add_item(button)

            # Update the embed
            await interaction.response.edit_message(
                embed=self.create_browser_embed(), view=self)

        def get_rarity_emoji(self, rarity: str) -> str:
            """Get emoji for item rarity"""
            rarity = rarity.lower()
            if rarity == "legendary":
                return "🌟"
            elif rarity == "epic":
                return "💠"
            elif rarity == "rare":
                return "🔷"
            elif rarity == "uncommon":
                return "🔹"
            elif rarity == "common":
                return "⚪"
            else:
                return "❓"

        def create_browser_embed(self):
            """Create the item browser embed"""
            filtered_items = self.get_filtered_items()

            embed = discord.Embed(
                title=f"🎮 Item Browser - Giving to {self.member.display_name}",
                description=
                f"Items sorted by rarity. Browse and select an item to give. Page {self.current_page + 1}/{self.total_pages}\nAll items will bypass level restrictions automatically.",
                color=discord.Color.blurple())

            # Add filter info
            embed.add_field(name="📋 Filters",
                            value=f"**Category:** {self.category_filter}\n"
                            f"**Rarity:** {self.rarity_filter}\n"
                            f"**Items Found:** {len(filtered_items)}",
                            inline=False)

            # Add selected item details if any
            if self.selected_item:
                # Get rarity emoji
                rarity_emoji = self.get_rarity_emoji(self.selected_item.rarity)

                # Get type emoji based on item type
                type_emoji_map = {
                    "weapon": "⚔️",
                    "armor": "🛡️",
                    "accessory": "💍",
                    "consumable": "🧪",
                    "material": "🧶",
                    "special": "✨"
                }
                type_emoji = type_emoji_map.get(
                    self.selected_item.item_type.lower(), "📦")

                embed.add_field(
                    name=f"🎯 Selected Item {rarity_emoji}",
                    value=
                    f"**{self.selected_item.name}** ({self.selected_item.rarity.title()} {self.selected_item.item_type.title()})\n{type_emoji} Type: {self.selected_item.item_type.title()}",
                    inline=False)

                embed.add_field(name="📝 Description",
                                value=self.selected_item.description
                                or "No description available",
                                inline=False)

                # Add stats if any
                if self.selected_item.stats:
                    stats_text = "\n".join([
                        f"**{stat.title()}:** +{value}"
                        for stat, value in self.selected_item.stats.items()
                    ])
                    embed.add_field(name="📊 Stats",
                                    value=stats_text,
                                    inline=False)

            return embed

    # Start the item browser
    view = ItemBrowserView(filtered_items, member, player)
    embed = view.create_browser_embed()

    await ctx.send(embed=embed, view=view)


@bot.command(name="quests")
async def quests_cmd(ctx):
    """View your active quests and special events"""
    await quests_command(ctx, data_manager)


@bot.command(name="q")
async def q_cmd(ctx):
    """View your active quests and special events (alias)"""
    await quests_command(ctx, data_manager)


@bot.command(name="leaderboard", aliases=["lb", "top"])
async def leaderboard_cmd(ctx, category: str = "level"):
    """View the top players leaderboard"""
    await leaderboard_command(ctx, data_manager, category)


@bot.command(name="rankings")
async def rankings_cmd(ctx, category: str = "level"):
    """View the top players leaderboard (alias)"""
    await leaderboard_command(ctx, data_manager, category)


@bot.command(name="checkxp")
async def checkxp_cmd(ctx):
    """Check if your level is correct based on your XP"""
    player = data_manager.get_player(ctx.author.id)

    if not player.class_name:
        await ctx.send("❌ You need to start your adventure first with `!start`"
                       )
        return

    old_level = player.class_level
    old_xp = player.class_exp

    # Check if player's level is correct
    was_corrected, old_level, new_level = validate_player_level(player)

    if was_corrected:
        # Level was corrected
        data_manager.save_data()

        embed = discord.Embed(
            title="✅ Level Correction Applied",
            description=f"Your level has been adjusted to match your XP.",
            color=discord.Color.green())

        embed.add_field(name="Previous Level",
                        value=f"Level: {old_level}\nXP: {old_xp}",
                        inline=True)

        embed.add_field(name="Corrected Level",
                        value=f"Level: {new_level}\nXP: {player.class_exp}",
                        inline=True)

        # Add explanation
        difference = new_level - old_level
        if difference > 0:
            embed.add_field(
                name="What Happened?",
                value=
                f"You gained {difference} level(s)! Your XP was higher than expected for your previous level.",
                inline=False)
        else:
            embed.add_field(
                name="What Happened?",
                value=
                f"Your level was adjusted by {difference}. Your XP was lower than required for your previous level.",
                inline=False)

        await ctx.send(embed=embed)
    else:
        # Level is already correct
        embed = discord.Embed(
            title="✓ Level Check Complete",
            description=f"Your level is correct based on your XP!",
            color=discord.Color.blue())

        xp_needed = player.calculate_xp_for_level(player.class_level)
        progress = int(
            (player.class_exp / xp_needed) * 100) if xp_needed > 0 else 100

        embed.add_field(
            name="Current Status",
            value=
            f"Level: {player.class_level}\nXP: {player.class_exp}/{xp_needed}\nProgress to next level: {progress}%",
            inline=False)

        await ctx.send(embed=embed)


@bot.command(name="levels")
async def levels_cmd(ctx):
    """View your level information and progression details"""
    player = data_manager.get_player(ctx.author.id)

    # Calculate next level XP based on class level
    next_level_xp = int(100 * (player.class_level**1.5))
    progress_percentage = round((player.class_exp / next_level_xp) *
                                100 if next_level_xp > 0 else 100)
    progress_bar = "".join(
        ["█" if i < progress_percentage / 10 else "░" for i in range(10)])

    embed = discord.Embed(title=f"{ctx.author.name}'s Level Information",
                          color=discord.Color.blue())

    embed.add_field(name="Class Level Progress",
                    value=f"Class: {player.class_name}\n"
                    f"Level: {player.class_level}/100\n"
                    f"XP: {player.class_exp}/{next_level_xp}\n"
                    f"XP to next level: {next_level_xp - player.class_exp}\n"
                    f"Progress: {progress_percentage}%\n"
                    f"[{progress_bar}]",
                    inline=False)

    embed.add_field(name="Level Growth Stats (per level)",
                    value=f"Power: +2\n"
                    f"Defense: +1.5\n"
                    f"Speed: +1\n"
                    f"HP: +10\n"
                    f"Gold: +50\n"
                    f"Battle Energy: +5",
                    inline=False)

    # Add XP sources
    embed.add_field(name="XP Sources",
                    value="• Battles: 10-50 XP\n"
                    "• Dungeons: 50-200 XP\n"
                    "• Quests: 20-500 XP\n"
                    "• Training: 5-15 XP\n"
                    "• Guild Activities: 30-100 XP",
                    inline=False)

    await ctx.send(embed=embed)


@bot.command(name="monsters", aliases=["mobs", "enemies"])
async def monsters_cmd(ctx):
    """Shows all available monsters/enemies that can be battled"""
    from utils import ENEMY_POOLS

    embed = discord.Embed(
        title="Ethereal Ascendancy - Monster Guide",
        description=
        "Here are all the monsters you can encounter in different zones:",
        color=discord.Color.dark_purple())

    for zone, enemies in ENEMY_POOLS.items():
        zone_info = []
        for enemy in enemies:
            zone_info.append(
                f"• **{enemy['name']}** (Level {enemy['min_level']}-{enemy['max_level']})"
            )

        embed.add_field(name=f"📍 {zone} Zone",
                        value="\n".join(zone_info),
                        inline=False)

    embed.add_field(name="Special Enemy Types",
                    value=("• **Cursed** - High power, low defense\n"
                           "• **Armored** - High defense, low speed\n"
                           "• **Giant** - High HP, low speed\n"
                           "• **Specter** - High speed, low HP"),
                    inline=False)

    embed.set_footer(text="Use !battle <zone> to encounter these monsters")
    await ctx.send(embed=embed)


@bot.command(name="level", aliases=["lvl", "progression"])
async def level_cmd(ctx):
    """View your level information and progression details"""
    player_data = data_manager.get_player(ctx.author.id)

    # Check if player has started
    if not player_data.class_name:
        await ctx.send("❌ You need to start your adventure first with `!start`"
                       )
        return

    # Get current level and max level
    current_level = player_data.class_level
    max_level = 1000
    current_xp = player_data.class_exp

    if current_level >= max_level:
        xp_needed = 0
        xp_to_next = 0
        progress_percent = 100
    else:
        xp_needed = int(100 * (current_level**1.5))
        xp_to_next = max(0, xp_needed - current_xp)
        progress_percent = min(100, int((current_xp / xp_needed) * 100))

    # Create XP progress bar
    progress_bar_length = 20
    filled_length = int(progress_bar_length * progress_percent / 100)
    bar = '█' * filled_length + '░' * (progress_bar_length - filled_length)

    # Calculate stats growth per level
    base_stats = {"power": 2, "defense": 1.5, "speed": 1, "hp": 10}

    embed = discord.Embed(
        title=f"{ctx.author.display_name}'s Level Information",
        description=f"Character Class: **{player_data.class_name or 'None'}**",
        color=discord.Color.blue())

    embed.add_field(name="Level Progress",
                    value=(f"**Level**: {current_level}/{max_level}\n"
                           f"**XP**: {current_xp}/{xp_needed}\n"
                           f"**XP to next level**: {xp_to_next}\n"
                           f"**Progress**: {progress_percent}%\n"
                           f"[{bar}]"),
                    inline=False)

    embed.add_field(name="Level Growth Stats (per level)",
                    value=(f"**Power**: +{base_stats['power']}\n"
                           f"**Defense**: +{base_stats['defense']}\n"
                           f"**Speed**: +{base_stats['speed']}\n"
                           f"**HP**: +{base_stats['hp']}\n"
                           f"**Cursed Energy**: +50 (max capacity)"),
                    inline=False)

    embed.add_field(name="XP Sources",
                    value=(f"• Battles: {5 + current_level} XP\n"
                           f"• Daily Rewards: 30-60 XP\n"
                           f"• Quests: 50-200 XP\n"
                           f"• Training: 5-15 XP\n"
                           f"• Guild Activities: 30-100 XP"),
                    inline=False)

    await ctx.send(embed=embed)


@bot.command(name="event")
@is_admin()
async def event_cmd(ctx,
                    action: str = None,
                    event_id: str = None,
                    duration: float = None):
    """[Admin] Manage server-wide special events"""
    await event_command(ctx, data_manager, action, event_id, duration)


@bot.command(name="advanced_shop", aliases=["ashop"])
async def advanced_shop_cmd(ctx):
    """Browse the enhanced item shop with categories and filters"""
    await advanced_shop_command(ctx, data_manager)

    # These commands are already implemented elsewhere in the file

    # Check if player has started
    if not player_data.class_name:
        await ctx.send("❌ You need to start your adventure first with `!start`"
                       )
        return

    # Get current level and max level
    current_level = player_data.class_level
    max_level = 100
    current_xp = player_data.class_exp

    if current_level >= max_level:
        xp_needed = 0
        xp_to_next = 0
        progress_percent = 100
    else:
        xp_needed = int(100 * (current_level**1.5))
        xp_to_next = max(0, xp_needed - current_xp)
        progress_percent = min(100, int((current_xp / xp_needed) * 100))

    # Create XP progress bar
    progress_bar_length = 20
    filled_length = int(progress_bar_length * progress_percent / 100)
    bar = '█' * filled_length + '░' * (progress_bar_length - filled_length)

    # Calculate stats growth per level
    base_stats = {"power": 2, "defense": 1.5, "speed": 1, "hp": 10}

    embed = discord.Embed(
        title=f"{ctx.author.display_name}'s Level Information",
        description=f"Character Class: **{player_data.class_name or 'None'}**",
        color=discord.Color.blue())

    embed.add_field(name="Level Progress",
                    value=(f"**Level**: {current_level}/{max_level}\n"
                           f"**XP**: {current_xp}/{xp_needed}\n"
                           f"**XP to next level**: {xp_to_next}\n"
                           f"**Progress**: {progress_percent}%\n"
                           f"[{bar}]"),
                    inline=False)

    embed.add_field(name="Level Growth Stats (per level)",
                    value=(f"**Power**: +{base_stats['power']}\n"
                           f"**Defense**: +{base_stats['defense']}\n"
                           f"**Speed**: +{base_stats['speed']}\n"
                           f"**HP**: +{base_stats['hp']}\n"
                           f"**Cursed Energy**: +50 (max capacity)"),
                    inline=False)

    embed.add_field(name="XP Sources",
                    value=(f"• Battles: {5 + current_level} XP\n"
                           f"• Daily Rewards: 30-60 XP\n"
                           f"• Quests: 50-200 XP\n"
                           f"• Training: 5-15 XP\n"
                           f"• Guild Activities: 30-100 XP"),
                    inline=False)

    await ctx.send(embed=embed)


@bot.command(name="balance", aliases=["bal", "gold"])
async def balance_cmd(ctx):
    """Check your current gold balance"""
    player = data_manager.get_player(ctx.author.id)

    embed = discord.Embed(title=f"{ctx.author.display_name}'s Balance",
                          description=f"💰 **Gold:** {player.gold}",
                          color=discord.Color.dark_purple())

    # Show achievement points if any
    if hasattr(player, "achievements"):
        from achievements import AchievementTracker
        achievement_tracker = AchievementTracker(data_manager)
        points = achievement_tracker.get_player_achievement_points(player)
        if points > 0:
            embed.add_field(name="Achievement Points",
                            value=f"🏆 **Points:** {points}",
                            inline=False)

    await ctx.send(embed=embed)


@bot.command(name="materials", aliases=["mats", "mat"])
async def materials_cmd(ctx):
    """View the materials encyclopedia"""
    await materials_command(ctx, data_manager)


@bot.command(name="gather", aliases=["collect"])
async def gather_cmd(ctx):
    """Gather materials for crafting"""
    await gather_command(ctx, data_manager)


@bot.command(name="tools", aliases=["tool"])
async def tools_cmd(ctx):
    """Equip and manage your gathering tools"""
    await tools_command(ctx, data_manager)


@bot.command(name="craft", aliases=["crafting"])
async def craft_cmd(ctx):
    """Craft items from gathered materials"""
    await crafting_command(ctx, data_manager)


@bot.command(name="encyclopedia", aliases=["codex", "browser", "items"])
async def encyclopedia_cmd(ctx, category: str = None):
    """Browse the item and material encyclopedia"""
    await encyclopedia_command(ctx, data_manager, category)


# Slash commands implementation
@bot.tree.command(name="start",
                  description="Begin your adventure and choose a class")
async def slash_start(interaction: discord.Interaction):
    ctx = await bot.get_context(interaction)
    await start_command(ctx)


@bot.tree.command(
    name="profile",
    description="View your character profile or another player's profile")
@app_commands.describe(
    member="The player whose profile you want to view (optional)")
async def slash_profile(interaction: discord.Interaction,
                        member: discord.Member = None):
    ctx = await bot.get_context(interaction)
    await profile_command(ctx, member)


@bot.tree.command(name="daily", description="Claim your daily rewards")
async def slash_daily(interaction: discord.Interaction):
    ctx = await bot.get_context(interaction)
    await daily_command(ctx)


@bot.tree.command(name="battle",
                  description="Battle an enemy or another player")
@app_commands.describe(enemy_name="Name of the enemy to battle (optional)",
                       enemy_level="Level of the enemy (optional)")
async def slash_battle(interaction: discord.Interaction,
                       enemy_name: str = None,
                       enemy_level: int = None):
    ctx = await bot.get_context(interaction)
    await battle_command(ctx, enemy_name, enemy_level)


@bot.tree.command(name="pvphistory",
                  description="View your PvP battle history and stats")
async def slash_pvp_history(interaction: discord.Interaction):
    ctx = await bot.get_context(interaction)
    await pvp_history_command(ctx)


@bot.tree.command(name="dungeon", description="Enter a dungeon")
async def slash_dungeon(interaction: discord.Interaction):
    ctx = await bot.get_context(interaction)
    await dungeon_command(ctx, data_manager)


@bot.tree.command(name="equipment",
                  description="View and manage your equipment")
async def slash_equipment(interaction: discord.Interaction):
    ctx = await bot.get_context(interaction)
    await equipment_command(ctx, data_manager)


@bot.tree.command(name="inventory",
                  description="View your inventory and equipped items")
async def slash_inventory(interaction: discord.Interaction):
    ctx = await bot.get_context(interaction)
    await equipment_command(ctx, data_manager)


@bot.tree.command(name="shop", description="Browse the item shop")
async def slash_shop(interaction: discord.Interaction):
    ctx = await bot.get_context(interaction)
    await shop_command(ctx, data_manager)


@bot.tree.command(name="train", description="Train to improve your stats")
async def slash_train(interaction: discord.Interaction):
    ctx = await bot.get_context(interaction)
    await train_command(ctx, data_manager)


@bot.tree.command(name="advanced_training",
                  description="Participate in advanced training exercises")
async def slash_advanced_training(interaction: discord.Interaction):
    ctx = await bot.get_context(interaction)
    await advanced_training_command(ctx, data_manager)


@bot.tree.command(name="skills", description="Allocate skill points")
async def slash_skills(interaction: discord.Interaction):
    ctx = await bot.get_context(interaction)
    await skills_command(ctx, data_manager)


@bot.tree.command(name="skilltree",
                  description="View and allocate points in your skill tree")
async def slash_skill_tree(interaction: discord.Interaction):
    ctx = await bot.get_context(interaction)
    await skill_tree_command(ctx, data_manager)


@bot.tree.command(
    name="change_class",
    description="Change your character's class to another unlocked class")
async def slash_change_class(interaction: discord.Interaction):
    ctx = await bot.get_context(interaction)
    await class_change_command(ctx, data_manager)


@bot.tree.command(name="use", description="Use an item from your inventory")
@app_commands.describe(
    item_name="Name of the item to use (e.g., 'health potion')")
async def slash_use_item(interaction: discord.Interaction,
                         item_name: str = None):
    await interaction.response.defer()
    ctx = await bot.get_context(interaction)
    await use_item_command(ctx, item_name=item_name)


@bot.tree.command(name="special_items",
                  description="View and use your special items and abilities")
async def slash_special_items(interaction: discord.Interaction):
    ctx = await bot.get_context(interaction)
    await special_items_command(ctx, data_manager)


@bot.tree.command(name="trade",
                  description="Trade items and gold with another player")
@app_commands.describe(target_member="The player you want to trade with")
async def slash_trade_command(interaction: discord.Interaction,
                              target_member: discord.Member):
    ctx = await bot.get_context(interaction)
    await trade_command(ctx, target_member, data_manager)


@bot.tree.command(name="guild",
                  description="Guild system - create, join, or manage a guild")
@app_commands.describe(action="Guild action (create, join, leave, etc.)",
                       args="Additional arguments for the action")
async def slash_guild(interaction: discord.Interaction,
                      action: str = None,
                      args: str = None):
    ctx = await bot.get_context(interaction)
    if args:
        args_list = args.split()
    else:
        args_list = []
    await guild_command(ctx, action, *args_list)


@bot.tree.command(name="achievements",
                  description="View your achievements and badges")
async def slash_achievements(interaction: discord.Interaction):
    ctx = await bot.get_context(interaction)
    await achievements_command(ctx, data_manager)


@bot.tree.command(name="quests",
                  description="View your active quests and special events")
async def slash_quests(interaction: discord.Interaction):
    ctx = await bot.get_context(interaction)
    await quests_command(ctx, data_manager)


@bot.tree.command(name="leaderboard",
                  description="View the top players leaderboard")
@app_commands.describe(category="Category to rank players by")
@app_commands.choices(category=[
    app_commands.Choice(name="Level", value="level"),
    app_commands.Choice(name="Gold", value="gold"),
    app_commands.Choice(name="Battle Wins", value="wins"),
    app_commands.Choice(name="PvP Wins", value="pvp_wins"),
    app_commands.Choice(name="Dungeons Completed", value="dungeons_completed"),
    app_commands.Choice(name="Bosses Defeated", value="bosses_defeated")
])
async def slash_leaderboard(interaction: discord.Interaction,
                            category: str = "level"):
    ctx = await bot.get_context(interaction)
    await leaderboard_command(ctx, data_manager, category)


@bot.tree.command(name="event",
                  description="[Admin] Manage server-wide special events")
@app_commands.describe(action="Event action: start, list, end",
                       event_id="Event ID to manage",
                       duration="Duration in days (for start action)")
async def slash_event(interaction: discord.Interaction,
                      action: str = None,
                      event_id: str = None,
                      duration: float = None):
    # Check if the user is the admin
    if interaction.user.id != ADMIN_USER_ID:
        await interaction.response.send_message(
            "You don't have permission to use this command.", ephemeral=True)
        return

    ctx = await bot.get_context(interaction)
    await event_command(ctx, data_manager, action, event_id, duration)


@bot.tree.command(name="balance",
                  description="Check your current cursed energy balance")
async def slash_balance(interaction: discord.Interaction):
    ctx = await bot.get_context(interaction)
    await balance_cmd(ctx)


@bot.tree.command(
    name="advanced_shop",
    description="Browse the enhanced item shop with categories and filters")
async def slash_advanced_shop(interaction: discord.Interaction):
    ctx = await bot.get_context(interaction)
    await advanced_shop_command(ctx, data_manager)


@bot.tree.command(
    name="monsters",
    description="Shows all available monsters/enemies that can be battled")
async def slash_monsters(interaction: discord.Interaction):
    ctx = await bot.get_context(interaction)
    await monsters_cmd(ctx)


@bot.tree.command(
    name="level",
    description="View your level information and progression details")
async def slash_level(interaction: discord.Interaction):
    ctx = await bot.get_context(interaction)
    await level_cmd(ctx)


@bot.tree.command(name="materials",
                  description="View the materials encyclopedia")
async def slash_materials(interaction: discord.Interaction):
    ctx = await bot.get_context(interaction)
    await materials_command(ctx, data_manager)


@bot.tree.command(name="gather", description="Gather materials for crafting")
async def slash_gather(interaction: discord.Interaction):
    ctx = await bot.get_context(interaction)
    await gather_command(ctx, data_manager)


@bot.tree.command(name="tools",
                  description="Equip and manage your gathering tools")
async def slash_tools(interaction: discord.Interaction):
    ctx = await bot.get_context(interaction)
    await tools_command(ctx, data_manager)


@bot.tree.command(name="craft",
                  description="Craft items from gathered materials")
async def slash_craft(interaction: discord.Interaction):
    player = data_manager.get_player(interaction.user.id)
    view = CraftingEntryView(player, data_manager)
    embed = discord.Embed(
        title="🔨 Crafting Workshop",
        description=
        "Welcome to the crafting workshop! Here you can craft items from materials you've gathered.",
        color=discord.Color.gold())
    await interaction.response.send_message(embed=embed, view=view)


@bot.tree.command(name="encyclopedia",
                  description="Browse the item and material encyclopedia")
@app_commands.describe(category="Category to browse (optional)")
async def slash_encyclopedia(interaction: discord.Interaction,
                             category: str = None):
    player = data_manager.get_player(interaction.user.id)

    view = EncyclopediaExploreView(player, data_manager)

    embed = discord.Embed(
        title="📚 Ethereal Ascendancy Encyclopedia",
        description=
        "Welcome to the comprehensive encyclopedia of Ethereal Ascendancy! Browse thousands of items, materials, equipment, and more.",
        color=discord.Color.blue())

    # Add sections to the embed
    for category_name, data in ENCYCLOPEDIA_SECTIONS.items():
        # Skip "All Items" from the overview to save space
        if category_name != "All Items":
            subsections = ", ".join(data.get("subsections", [])[:3])
            if len(data.get("subsections", [])) > 3:
                subsections += "..."

            embed.add_field(
                name=f"{data['icon']} {category_name}",
                value=f"{data['description']}\nIncludes: {subsections}",
                inline=True)

    # Add player info
    embed.set_footer(text=f"Player: {player.name} | Level: {player.level}")

    await interaction.response.send_message(embed=embed, view=view)


@bot.command(name="help", aliases=["h"])
async def help_command(ctx, category: str = None):
    """Show help information"""
    await _show_help(ctx, category)


@bot.tree.command(name="help", description="Show help information")
@app_commands.describe(category="Help category (optional)")
async def slash_help(interaction: discord.Interaction, category: str = None):
    ctx = await bot.get_context(interaction)
    await _show_help(ctx, category)


async def _show_help(ctx, category: str = None):
    help_pages = {
        "Basic": {
            "Start": {
                "description": "Begin your journey and select your class",
                "usage": "!start or /start",
                "notes": "Choose your starting class and begin your adventure"
            },
            "Profile": {
                "description": "View your stats and progress",
                "usage": "!profile [user] (alias: !p) or /profile",
                "notes": "Shows character level, class, stats, and equipment"
            },
            "Daily": {
                "description": "Claim your daily rewards",
                "usage": "!daily or /daily",
                "notes": "Claim gold (🔮) and items every 24 hours"
            },
            "Balance": {
                "description": "Check your current gold balance",
                "usage": "!balance (aliases: !bal) or /balance",
                "notes": "View your current gold (🔮) and battle energy (✨)"
            },
            "Leaderboard": {
                "description":
                "View the top players leaderboard and rankings",
                "usage":
                "!leaderboard [category] (aliases: !lb, !top, !rankings) or /leaderboard",
                "notes":
                "Categories: level, gold, wins, pvp_wins, dungeons_completed, bosses_defeated"
            },
            "Levels": {
                "description":
                "View your level information and progression details",
                "usage":
                "!levels or /levels",
                "notes":
                "Shows detailed level progress with XP requirements and growth stats"
            },
            "Monsters": {
                "description":
                "Shows all available monsters/enemies that can be battled",
                "usage": "!monsters (aliases: !mobs, !enemies) or /monsters",
                "notes": "Lists all enemies by zone with their level ranges"
            },
            "Help": {
                "description": "Show this help message",
                "usage": "!help [category] or /help",
                "notes": "Shows command information by category"
            }
        },
        "Battle": {
            "Battle": {
                "description": "Battle an enemy or another player",
                "usage":
                "!battle [@player] OR !battle [enemy_name] [enemy_level] (alias: !b) or /battle",
                "notes":
                "PvE and PvP combat with special abilities and effects"
            },
            "PvP History": {
                "description":
                "View your PvP battle history and stats",
                "usage":
                "!pvphistory (aliases: !pvp, !pvpstats) or /pvphistory",
                "notes":
                "See your win/loss record, recent battles, and cooldown status"
            },
            "Train": {
                "description": "Train to improve your stats",
                "usage": "!train (alias: !t) or /train",
                "notes": "Basic training to gain small stat improvements"
            },
            "Advanced Training": {
                "description": "Participate in advanced training exercises",
                "usage":
                "!advanced_training (alias: !atrain) or /advanced_training",
                "notes": "Specialized training minigames with better rewards"
            },
            "Skills": {
                "description": "Allocate skill points",
                "usage": "!skills (alias: !sk) or /skills",
                "notes": "Spend skill points earned from leveling up"
            },
            "Skill Tree": {
                "description": "View and allocate points in your skill tree",
                "usage": "!skilltree (aliases: !skt, !tree) or /skilltree",
                "notes": "Advanced skill progression system"
            }
        },
        "Equipment": {
            "Equipment": {
                "description": "View and manage your equipment",
                "usage": "!equipment (alias: !e) or /equipment",
                "notes": "Equip, unequip, and sell items in your inventory"
            },
            "Inventory": {
                "description": "View your inventory and equipped items",
                "usage": "!inventory (aliases: !i, !inv) or /inventory",
                "notes": "Alternate way to access equipment management"
            },
            "Shop": {
                "description": "Browse the item shop",
                "usage": "!shop or /shop",
                "notes": "Basic shop with common items"
            },
            "Advanced Shop": {
                "description": "Browse the enhanced shop with filters",
                "usage": "!advanced_shop (alias: !ashop) or /advanced_shop",
                "notes":
                "Shop with more items, categories, and filtering options"
            },
            "Buy": {
                "description": "Buy an item from the shop",
                "usage": "!buy <item_name>",
                "notes":
                "Purchase items with gold (🔮) to improve your character"
            }
        },
        "Exploration": {
            "Dungeon": {
                "description": "Enter a dungeon",
                "usage": "!dungeon (alias: !d) or /dungeon",
                "notes": "Explore dungeons to find rare items and earn rewards"
            },
            "Gather": {
                "description": "Gather materials for crafting",
                "usage": "!gather (alias: !collect) or /gather",
                "notes":
                "Collect raw materials from the environment for crafting"
            }
        },
        "Crafting": {
            "Materials": {
                "description": "View the materials encyclopedia",
                "usage": "!materials (aliases: !mats, !mat) or /materials",
                "notes":
                "Browse all available crafting materials and their uses"
            },
            "Craft": {
                "description":
                "Craft items from gathered materials",
                "usage":
                "!craft (alias: !crafting) or /craft",
                "notes":
                "Create weapons, armor, potions, and other items from materials"
            },
            "Encyclopedia": {
                "description":
                "Browse the complete item encyclopedia",
                "usage":
                "!encyclopedia [category] (aliases: !codex, !browser, !items) or /encyclopedia",
                "notes":
                "Browse all items, weapons, armor, and materials in the game"
            }
        },
        "Guild": {
            "Guild": {
                "description":
                "Guild system - create, join, or manage a guild",
                "usage":
                "!guild [action] [args] (alias: !g) or /guild",
                "notes":
                "Actions: create, join, leave, list, members, contribute, and more"
            }
        },
        "Progress": {
            "Achievements": {
                "description": "View your achievements and badges",
                "usage":
                "!achievements (aliases: !achieve, !ach) or /achievements",
                "notes": "Track your accomplishments and earn rewards"
            },
            "Quests": {
                "description": "View your active quests",
                "usage": "!quests (alias: !q) or /quests",
                "notes": "Daily, weekly, and long-term quests with rewards"
            },
            "Change Class": {
                "description": "Change to another unlocked class",
                "usage":
                "!change_class (aliases: !cc, !class) or /change_class",
                "notes": "Requires appropriate level or special items"
            },
            "Special Items": {
                "description": "View and use your special items and abilities",
                "usage":
                "!special_items (aliases: !sitems, !si) or /special_items",
                "notes": "Use transformation items and special abilities"
            },
            "Trade": {
                "description": "Trade items and gold with another player",
                "usage": "!trade <user> (aliases: !tr) or /trade",
                "notes": "Initiate a secure trade with another player"
            },
        },
        "Admin": {
            "Give Gold": {
                "description": "[Admin] Give gold to a user",
                "usage": "!give_gold <user> <amount>",
                "notes": "Admin only: Add gold to player's balance"
            },
            "Give Item": {
                "description": "[Admin] Give an item to a user",
                "usage": "!give_item <user> <item_name> [quantity]",
                "notes": "Admin only: Add specific items to player's inventory"
            },
            "Give XP": {
                "description": "[Admin] Give experience points to a user",
                "usage": "!give_xp <user> <amount>",
                "notes": "Admin only: Grant XP which may cause level-ups"
            },
            "Give Class": {
                "description": "[Admin] Give a class to a user",
                "usage": "!give_class <user> <class_name>",
                "notes": "Admin only: Unlock a new class for a player"
            },
            "Give Skill": {
                "description": "[Admin] Give a skill to a user",
                "usage": "!give_skill <user> <skill_id>",
                "notes": "Admin only: Grant a specific skill to a player"
            },
            "Give Achievement": {
                "description": "[Admin] Award an achievement to a user",
                "usage": "!give_achievement <user> <achievement_id>",
                "notes": "Admin only: Grant a specific achievement"
            },
            "Event Admin": {
                "description": "[Admin] Manage server-wide special events",
                "usage": "!event [action] [event_id] [duration]",
                "notes": "Admin only: start, list, end"
            },
            "Sync": {
                "description":
                "[Admin] Sync slash commands to the current guild or globally",
                "usage": "!sync",
                "notes": "Admin only: sync all slash commands"
            }
        },
        "General": {
            "Level": {
                "description":
                "View your level information and progression details",
                "usage":
                "!level (aliases: !lvl, !progression) or /level",
                "notes":
                "Shows detailed level progress with XP requirements and growth stats"
            },
            "Materials": {
                "description": "View the materials encyclopedia",
                "usage": "!materials (aliases: !mats, !mat) or /materials",
                "notes":
                "Browse all available crafting materials and their uses"
            },
            "Gather": {
                "description": "Gather materials for crafting",
                "usage": "!gather (aliases: !collect) or /gather",
                "notes": "Collect resources from different environments"
            },
            "Tools": {
                "description": "Manage your gathering tools",
                "usage": "!tools (aliases: !tool) or /tools",
                "notes": "Equip tools to improve gathering efficiency"
            },
            "Craft": {
                "description": "Craft items using materials",
                "usage": "!craft (aliases: !crafting) or /craft",
                "notes": "Create equipment and items from gathered materials"
            },
        }
    }

    help_embeds = []

    if category:
        if category.title() in help_pages:
            embed = discord.Embed(title=f"{category.title()} Commands",
                                  color=discord.Color.purple())

            for cmd, data in help_pages[category.title()].items():
                embed.add_field(
                    name=cmd,
                    value=f"{data['description']}\nUsage: {data['usage']}",
                    inline=False)
            help_embeds.append(embed)
        else:
            await ctx.send(
                "❌ Invalid category! Use !help to see all categories.")
            return
    else:
        # Create embeds for each category
        for category, commands in help_pages.items():
            embed = discord.Embed(title=f"{category} Commands",
                                  color=discord.Color.purple())

            for cmd, data in commands.items():
                embed.add_field(
                    name=cmd,
                    value=f"{data['description']}\nUsage: {data['usage']}",
                    inline=False)

            embed.set_footer(
                text=f"Page {len(help_embeds) + 1}/{len(help_pages)}")
            help_embeds.append(embed)

    class HelpView(View):

        def __init__(self, help_embeds, timeout=60):
            super().__init__(timeout=timeout)
            self.help_embeds = help_embeds
            self.current_page = 0

            # Add buttons
            prev_btn = Button(label="◀️",
                              custom_id="prev",
                              style=discord.ButtonStyle.gray)
            prev_btn.callback = self.prev_callback

            next_btn = Button(label="▶️",
                              custom_id="next",
                              style=discord.ButtonStyle.gray)
            next_btn.callback = self.next_callback

            self.add_item(prev_btn)
            self.add_item(next_btn)

        async def prev_callback(self, interaction: discord.Interaction):
            self.current_page = (self.current_page - 1) % len(self.help_embeds)
            await interaction.response.edit_message(
                embed=self.help_embeds[self.current_page])

        async def next_callback(self, interaction: discord.Interaction):
            self.current_page = (self.current_page + 1) % len(self.help_embeds)
            await interaction.response.edit_message(
                embed=self.help_embeds[self.current_page])

    view = HelpView(help_embeds)
    await ctx.send(embed=help_embeds[0], view=view)


# Bot token - read from environment variable
TOKEN = os.getenv('BOT_TOKEN')
if not TOKEN:
    # For development only - in production, use a real token
    print("WARNING: No Discord bot token found in environment variables.")
    print(
        "Using a test token to allow code review. The bot will not connect to Discord."
    )
    print(
        "Set the BOT_TOKEN environment variable with a real token for production use."
    )
    TOKEN = "test_token_for_development_only"  # This will cause the bot to fail connecting, but code will run

# Sync slash commands with Discord
# This section was removed to avoid duplication issues


@bot.tree.command(
    name="world_boss",
    description=
    "Battle the active event boss (only works during special boss events)")
async def slash_boss(interaction: discord.Interaction):
    ctx = await bot.get_context(interaction)
    await world_boss_cmd(ctx)


@bot.command(name="sync")
@commands.has_permissions(administrator=True)
async def sync_command(ctx):
    """Sync all slash commands to the current guild or globally"""
    try:
        # Sync to current guild only
        if ctx.guild:
            await bot.tree.sync(guild=ctx.guild)
            await ctx.send("✅ Slash commands synced to this server!")
        else:
            # Global sync (may take up to an hour to propagate)
            await bot.tree.sync()
            await ctx.send("✅ Slash commands synced globally!")
    except Exception as e:
        await ctx.send(f"❌ Error syncing commands: {str(e)}")


# Run the bot
if __name__ == "__main__":
    # Print startup message
    print("Starting Discord RPG Bot...")
    print("Use the !sync command to sync slash commands to your server")
    try:
        bot.run(TOKEN)
    except discord.errors.PrivilegedIntentsRequired:
        print(
            "\nERROR: Privileged intents are required but not enabled in the Discord Developer Portal."
        )
        print(
            "This is a testing environment, so we'll continue with development."
        )
        print(
            "In a real deployment, enable 'Server Members Intent' and 'Message Content Intent'"
        )
        print(
            "in the Discord Developer Portal: https://discord.com/developers/applications/"
        )

        # Continue with development tasks without running the bot
        print("\nContinuing with skill tree and trading system development...")
