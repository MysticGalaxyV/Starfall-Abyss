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
from materials import materials_command, gather_command
from crafting_system import crafting_command, CraftingEntryView
from encyclopedia import encyclopedia_command, browser_command, codex_command, EncyclopediaExploreView, ENCYCLOPEDIA_SECTIONS
from skill_tree import skill_tree_command, skills_tree_command
from trading_system import trade_command, t_command, slash_trade

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
GAME_NAME = "🌀 Ethereal Ascendancy"
WELCOME_MESSAGE = f"Welcome to {GAME_NAME}"

# Admin user ID - only this user can use admin commands
ADMIN_USER_ID = 759434349069860945  # Your user ID for admin permissions

# Define a custom check for admin commands
def is_admin():
    async def predicate(ctx):
        return ctx.author.id == ADMIN_USER_ID
    return commands.check(predicate)

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
    
    # Sync slash commands with Discord
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")
    
    # Set status showing all three command methods
    await bot.change_presence(activity=discord.Game(name=f"{GAME_NAME} | !help, @{bot.user.name} help, or /help"))

@bot.event
async def on_message(message):
    # Ignore messages from bots
    if message.author.bot:
        return
        
    # Respond to just the bot mention
    if message.content.strip() == f'<@{bot.user.id}>' or message.content.strip() == f'<@!{bot.user.id}>':
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
            btn = Button(
                label=f"{class_name} ({class_data['role']})",
                style=discord.ButtonStyle.primary,
                custom_id=class_name
            )
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
        await ctx.send(f"❌ You've already chosen the **{player.class_name}** class! You cannot start over.")
        return
    
    # Send welcome message
    welcome_embed = discord.Embed(
        title=WELCOME_MESSAGE,
        description="Embark on an epic journey through mystical realms, challenging dungeons, and legendary battles!",
        color=discord.Color.purple()
    )
    welcome_embed.set_footer(text="Start your journey by selecting a class below")
    
    await ctx.send(embed=welcome_embed)
    
    # Create embed for class selection
    embed = discord.Embed(
        title="🔮 Choose Your Class",
        description="Select a class to begin your adventure. Each class has unique abilities and playstyles that can be mastered as you progress from Level 1 to 1000.",
        color=discord.Color.blue()
    )
    
    # Add class information to embed
    for class_name, class_info in STARTER_CLASSES.items():
        stats_text = "\n".join([f"{stat.title()}: {value}" for stat, value in class_info["stats"].items()])
        embed.add_field(
            name=f"{class_name} ({class_info['role']})",
            value=f"**Active Ability:** {class_info['abilities']['active']}\n"
                  f"**Passive Ability:** {class_info['abilities']['passive']}\n"
                  f"**Stats:**\n{stats_text}",
            inline=False
        )
    
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
        
        # Confirmation message
        confirmation_embed = discord.Embed(
            title="🎉 Class Selected",
            description=f"You have chosen the path of the **{class_name}**!",
            color=discord.Color.green()
        )
        
        confirmation_embed.add_field(
            name="Your Journey Begins",
            value=f"Your stats have been initialized based on your class.\n"
                  f"Use `!profile` to see your stats and `!help` to see available commands.",
            inline=False
        )
        
        await ctx.send(embed=confirmation_embed)
    else:
        await ctx.send("❌ Class selection timed out. Please try again.")

@bot.command(name="profile")
async def profile_command(ctx, member: discord.Member = None):
    """View your or another player's profile"""
    # Get the target user
    target = member or ctx.author
    user_id = target.id
    
    # Get player data
    player = data_manager.get_player(user_id)
    
    # Check if player has started
    if not player.class_name:
        if target == ctx.author:
            await ctx.send("❌ You haven't started your adventure yet! Use `!start` to choose a class.")
        else:
            await ctx.send(f"❌ {target.display_name} hasn't started their adventure yet!")
        return
    
    # Calculate stats including equipment bonuses
    stats = player.get_stats(GAME_CLASSES)
    
    # Create profile embed
    embed = discord.Embed(
        title=f"📜 {target.display_name}'s Profile",
        description=f"**Class:** {player.class_name}\n"
                   f"**Level:** {player.class_level} ({player.class_exp}/{int(100 * (player.class_level ** 1.5))} EXP)\n"
                   f"**Technique Grade:** {player.technique_grade}\n"
                   f"**Cursed Energy:** {player.cursed_energy} 🔮",
        color=discord.Color.dark_purple()
    )
    
    # Add domain expansion if unlocked
    domain = getattr(player, 'domain_expansion', None)
    if domain:
        embed.description = embed.description + f"\n**Domain Expansion:** {domain} 🌀"
    
    # Add stats
    embed.add_field(
        name="📊 Stats",
        value=f"**HP:** {stats['hp']} ❤️\n"
              f"**Cursed Power:** {stats['power']} ⚔️\n"
              f"**Defense:** {stats['defense']} 🛡️\n"
              f"**Speed:** {stats['speed']} 💨\n"
              f"**Energy:** {player.cursed_energy}/{player.max_cursed_energy} ✨",
        inline=True
    )
    
    # Add skill points
    embed.add_field(
        name="🔢 Skill Points",
        value=f"**Available:** {player.skill_points}\n"
              f"**Power:** +{player.allocated_stats.get('power', 0)}\n"
              f"**Defense:** +{player.allocated_stats.get('defense', 0)}\n"
              f"**Speed:** +{player.allocated_stats.get('speed', 0)}\n"
              f"**HP:** +{player.allocated_stats.get('hp', 0)}",
        inline=True
    )
    
    # Add battle record
    embed.add_field(
        name="⚔️ Battle Record",
        value=f"**Wins:** {player.wins}\n"
              f"**Losses:** {player.losses}\n"
              f"**Win Rate:** {int((player.wins / (player.wins + player.losses)) * 100) if player.wins + player.losses > 0 else 0}%",
        inline=True
    )
    
    # Add equipped items
    equipped_text = "None"
    equipped_items = [item for item in player.inventory if item.equipped]
    
    if equipped_items:
        equipped_text = "\n".join([f"**{item.item.item_type.title()}**: {item.item.name}" for item in equipped_items])
    
    embed.add_field(
        name="🎒 Equipped Items",
        value=equipped_text,
        inline=True
    )
    
    # Add dungeon clear info
    dungeon_text = "None cleared yet"
    if player.dungeon_clears:
        dungeon_text = "\n".join([f"**{name}**: {count} times" for name, count in player.dungeon_clears.items()])
    
    embed.add_field(
        name="🗺️ Dungeons Cleared",
        value=dungeon_text,
        inline=True
    )
    
    # Add daily streak
    embed.add_field(
        name="📅 Daily Streak",
        value=f"**Current Streak:** {player.daily_streak}\n"
              f"**Last Claimed:** {player.last_daily.strftime('%Y-%m-%d %H:%M') if player.last_daily else 'Never'}",
        inline=True
    )
    
    # Set thumbnail to class icon
    if player.class_name == "Spirit Striker":
        embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/745384647157719212.png")
    elif player.class_name == "Domain Tactician":
        embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/745384647157719212.png")
    elif player.class_name == "Flash Rogue":
        embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/745384647157719212.png")
    
    await ctx.send(embed=embed)

@bot.command(name="daily")
async def daily_command(ctx):
    """Claim your daily rewards"""
    player = data_manager.get_player(ctx.author.id)
    
    # Check if player has started
    if not player.class_name:
        await ctx.send("❌ You haven't started your adventure yet! Use `!start` to choose a class.")
        return
    
    now = datetime.datetime.now()
    
    # Check if player has already claimed today
    if player.last_daily and player.last_daily.date() == now.date():
        next_reset = datetime.datetime.combine(now.date() + datetime.timedelta(days=1), datetime.time.min)
        time_until_reset = next_reset - now
        hours, remainder = divmod(time_until_reset.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        
        await ctx.send(f"❌ You've already claimed your daily reward today! Next reset in {hours}h {minutes}m.")
        return
    
    # Check for streak continuation or reset
    if player.last_daily and (now.date() - player.last_daily.date()).days == 1:
        # Continued streak
        player.daily_streak += 1
    elif not player.last_daily or (now.date() - player.last_daily.date()).days > 1:
        # Reset streak
        player.daily_streak = 1
    
    # Update last claim time
    player.last_daily = now
    
    # Calculate rewards based on streak
    base_cursed_energy = 50
    base_exp = 30
    
    # Bonus for streak (up to 100% extra at 30 days)
    streak_bonus = min(1.0, player.daily_streak / 30)
    
    cursed_energy_reward = int(base_cursed_energy * (1 + streak_bonus))
    exp_reward = int(base_exp * (1 + streak_bonus))
    
    # Add rewards (with max limit check)
    player.cursed_energy += cursed_energy_reward
    if player.cursed_energy > player.max_cursed_energy:
        player.cursed_energy = player.max_cursed_energy
    leveled_up = player.add_exp(exp_reward)
    
    # Create reward embed
    embed = discord.Embed(
        title="🎁 Daily Reward Claimed!",
        description=f"You've claimed your daily reward!",
        color=discord.Color.dark_purple()
    )
    
    embed.add_field(
        name="Rewards",
        value=f"**Cursed Energy:** +{cursed_energy_reward} 🔮\n"
              f"**EXP:** +{exp_reward} 📊\n"
              f"**Streak:** {player.daily_streak} day{'s' if player.daily_streak != 1 else ''}",
        inline=False
    )
    
    # Add streak info
    if player.daily_streak >= 7:
        embed.add_field(
            name="🔥 Streak Bonus",
            value=f"Your streak bonus is +{int(streak_bonus * 100)}%!",
            inline=False
        )
    else:
        embed.add_field(
            name="💡 Streak Info",
            value=f"Return tomorrow to increase your streak bonus!",
            inline=False
        )
    
    # Add level up message if applicable
    if leveled_up:
        embed.add_field(
            name="🆙 Level Up!",
            value=f"You reached Level {player.class_level}!\n"
                  f"You gained 3 skill points! Use !skills to allocate them.",
            inline=False
        )
    
    # Save player data
    data_manager.save_data()
    
    await ctx.send(embed=embed)

@bot.command(name="battle", aliases=["b"])
async def battle_command(ctx, enemy_name: str = None, enemy_level: int = None):
    """Battle an enemy or another player. Mention a user to start PvP"""
    player = data_manager.get_player(ctx.author.id)
    
    # Check if player has started
    if not player.class_name:
        await ctx.send("❌ You haven't started your adventure yet! Use `!start` to choose a class.")
        return
    
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
            await ctx.send(f"❌ {target_member.display_name} hasn't started their adventure yet!")
            return
        
        # Start PvP battle
        await start_pvp_battle(ctx, target_member, player, target_data, data_manager)
        return
    
    # If no specific enemy, choose random appropriate one
    if not enemy_name or not enemy_level:
        enemy_types = [
            "Cursed Wolf", "Forest Specter", "Ancient Treefolk",
            "Cave Crawler", "Armored Golem", "Crystal Spider",
            "Shrine Guardian", "Cursed Monk", "Vengeful Spirit",
            "Deep One", "Abyssal Hunter", "Giant Squid",
            "Flame Knight", "Lava Golem", "Fire Drake"
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
        await ctx.send("❌ You need to start your adventure first with `!start`")
        return
    
    # Create an embed for PvP history
    embed = discord.Embed(
        title="⚔️ PvP Battle History",
        description=f"Battle records for {ctx.author.display_name}",
        color=discord.Color.blue()
    )
    
    # Add overall stats
    embed.add_field(
        name="📊 Overall Stats",
        value=f"**Wins:** {player.pvp_wins}\n**Losses:** {player.pvp_losses}\n**Win Rate:** {calculate_win_rate(player.pvp_wins, player.pvp_losses)}%",
        inline=False
    )
    
    # Check cooldown status
    cooldown_msg = "Ready for battle"
    if player.last_pvp_battle:
        # Check if player is on cooldown
        now = datetime.datetime.now()
        # Winners have 30 min cooldown, losers have 60 min cooldown
        if player.pvp_history and player.pvp_history[-1].get("result") == "win":
            cooldown_time = 30 * 60  # 30 minutes in seconds
        else:
            cooldown_time = 60 * 60  # 60 minutes in seconds
            
        elapsed = (now - player.last_pvp_battle).total_seconds()
        
        if elapsed < cooldown_time:
            time_left = cooldown_time - elapsed
            cooldown_msg = f"⏱️ On cooldown for {format_time_remaining(time_left)}"
    
    embed.add_field(
        name="⏳ Battle Status",
        value=cooldown_msg,
        inline=False
    )
    
    # Show recent battle history
    if hasattr(player, "pvp_history") and player.pvp_history:
        battles_list = []
        
        # Get the most recent 5 battles (or fewer if there aren't 5)
        recent_battles = player.pvp_history[-5:] if len(player.pvp_history) > 5 else player.pvp_history
        
        for battle in reversed(recent_battles):
            # Calculate time ago
            battle_time = datetime.datetime.fromisoformat(battle.get("timestamp", datetime.datetime.now().isoformat()))
            time_ago = format_time_since(battle_time)
            
            # Format reward info
            if battle.get("result") == "win":
                reward_info = f"Won {battle.get('cursed_energy_reward', 0)} cursed energy, {battle.get('exp_reward', 0)} XP"
            else:
                reward_info = f"Lost {battle.get('cursed_energy_lost', 0)} cursed energy"
                
            battles_list.append(f"vs {battle.get('opponent_name', 'Unknown')} (Lvl {battle.get('opponent_level', '?')}) - {time_ago} ago\n   {reward_info}")
        
        embed.add_field(
            name="Recent Battles",
            value="\n".join(battles_list) if battles_list else "No battles yet.",
            inline=False
        )
    else:
        embed.add_field(
            name="Recent Battles",
            value="No battles yet. Challenge someone with `!battle @player`!",
            inline=False
        )
        
    # Add tips
    embed.set_footer(text="Tip: PvP battles have cooldowns - 30 min for winners, 60 min for losers.")
    
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
    
@bot.command(name="advanced_training", aliases=["atrain"])
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

@bot.command(name="guild", aliases=["g"])
async def guild_cmd(ctx, action: str = None, *args):
    """Guild system - create or join a guild and adventure with others"""
    await guild_command(ctx, action, *args)

@bot.command(name="achievements", aliases=["achieve", "ach"])
async def achievements_cmd(ctx):
    """View your achievements and badges"""
    await achievements_command(ctx, data_manager)

@bot.command(name="quests", aliases=["q"])
async def quests_cmd(ctx):
    """View your active quests and special events"""
    await quests_command(ctx, data_manager)

@bot.command(name="event")
@is_admin()
async def event_cmd(ctx, action: str = None, event_id: str = None, duration: float = None):
    """[Admin] Manage server-wide special events"""
    await event_command(ctx, data_manager, action, event_id, duration)

@bot.command(name="advanced_shop", aliases=["ashop"])
async def advanced_shop_cmd(ctx):
    """Browse the enhanced item shop with categories and filters"""
    await advanced_shop_command(ctx, data_manager)

@bot.command(name="balance", aliases=["bal", "ce", "energy"])
async def balance_cmd(ctx):
    """Check your current cursed energy balance"""
    player = data_manager.get_player(ctx.author.id)
    
    embed = discord.Embed(
        title=f"{ctx.author.display_name}'s Cursed Energy",
        description=f"🔮 **Cursed Energy:** {player.cursed_energy}/{player.max_cursed_energy}",
        color=discord.Color.dark_purple()
    )
    
    # Show achievement points if any
    if hasattr(player, "achievements"):
        from achievements import AchievementTracker
        achievement_tracker = AchievementTracker(data_manager)
        points = achievement_tracker.get_player_achievement_points(player)
        if points > 0:
            embed.add_field(
                name="Achievement Points",
                value=f"🏆 **Points:** {points}",
                inline=False
            )
    
    await ctx.send(embed=embed)

@bot.command(name="materials", aliases=["mats", "mat"])
async def materials_cmd(ctx):
    """View the materials encyclopedia"""
    await materials_command(ctx, data_manager)

@bot.command(name="gather", aliases=["collect"])
async def gather_cmd(ctx):
    """Gather materials for crafting"""
    await gather_command(ctx, data_manager)

@bot.command(name="craft", aliases=["crafting"])
async def craft_cmd(ctx):
    """Craft items from gathered materials"""
    await crafting_command(ctx, data_manager)

@bot.command(name="encyclopedia", aliases=["codex", "browser", "items"])
async def encyclopedia_cmd(ctx, category: str = None):
    """Browse the item and material encyclopedia"""
    await encyclopedia_command(ctx, data_manager, category)

# Slash commands implementation
@bot.tree.command(name="start", description="Begin your adventure and choose a class")
async def slash_start(interaction: discord.Interaction):
    ctx = await bot.get_context(interaction)
    await start_command(ctx)

@bot.tree.command(name="profile", description="View your character profile or another player's profile")
@app_commands.describe(member="The player whose profile you want to view (optional)")
async def slash_profile(interaction: discord.Interaction, member: discord.Member = None):
    ctx = await bot.get_context(interaction)
    await profile_command(ctx, member)

@bot.tree.command(name="daily", description="Claim your daily rewards")
async def slash_daily(interaction: discord.Interaction):
    ctx = await bot.get_context(interaction)
    await daily_command(ctx)

@bot.tree.command(name="battle", description="Battle an enemy or another player")
@app_commands.describe(
    enemy_name="Name of the enemy to battle (optional)",
    enemy_level="Level of the enemy (optional)"
)
async def slash_battle(interaction: discord.Interaction, enemy_name: str = None, enemy_level: int = None):
    ctx = await bot.get_context(interaction)
    await battle_command(ctx, enemy_name, enemy_level)

@bot.tree.command(name="pvphistory", description="View your PvP battle history and stats")
async def slash_pvp_history(interaction: discord.Interaction):
    ctx = await bot.get_context(interaction)
    await pvp_history_command(ctx)

@bot.tree.command(name="dungeon", description="Enter a dungeon")
async def slash_dungeon(interaction: discord.Interaction):
    ctx = await bot.get_context(interaction)
    await dungeon_command(ctx, data_manager)

@bot.tree.command(name="equipment", description="View and manage your equipment")
async def slash_equipment(interaction: discord.Interaction):
    ctx = await bot.get_context(interaction)
    await equipment_command(ctx, data_manager)
    
@bot.tree.command(name="inventory", description="View your inventory and equipped items")
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

@bot.tree.command(name="advanced_training", description="Participate in advanced training exercises")
async def slash_advanced_training(interaction: discord.Interaction):
    ctx = await bot.get_context(interaction)
    await advanced_training_command(ctx, data_manager)

@bot.tree.command(name="skills", description="Allocate skill points")
async def slash_skills(interaction: discord.Interaction):
    ctx = await bot.get_context(interaction)
    await skills_command(ctx, data_manager)
    
@bot.tree.command(name="skilltree", description="View and allocate points in your skill tree")
async def slash_skill_tree(interaction: discord.Interaction):
    ctx = await bot.get_context(interaction)
    await skill_tree_command(ctx, data_manager)

@bot.tree.command(name="change_class", description="Change your character's class to another unlocked class")
async def slash_change_class(interaction: discord.Interaction):
    ctx = await bot.get_context(interaction)
    await class_change_command(ctx, data_manager)

@bot.tree.command(name="special_items", description="View and use your special items and abilities")
async def slash_special_items(interaction: discord.Interaction):
    ctx = await bot.get_context(interaction)
    await special_items_command(ctx, data_manager)
    
@bot.tree.command(name="trade", description="Trade items and gold with another player")
@app_commands.describe(target_member="The player you want to trade with")
async def slash_trade_command(interaction: discord.Interaction, target_member: discord.Member):
    ctx = await bot.get_context(interaction)
    await trade_command(ctx, target_member, data_manager)

@bot.tree.command(name="guild", description="Guild system - create, join, or manage a guild")
@app_commands.describe(
    action="Guild action (create, join, leave, etc.)",
    args="Additional arguments for the action"
)
async def slash_guild(interaction: discord.Interaction, action: str = None, args: str = None):
    ctx = await bot.get_context(interaction)
    if args:
        args_list = args.split()
    else:
        args_list = []
    await guild_command(ctx, action, *args_list)

@bot.tree.command(name="achievements", description="View your achievements and badges")
async def slash_achievements(interaction: discord.Interaction):
    ctx = await bot.get_context(interaction)
    await achievements_command(ctx, data_manager)

@bot.tree.command(name="quests", description="View your active quests and special events")
async def slash_quests(interaction: discord.Interaction):
    ctx = await bot.get_context(interaction)
    await quests_command(ctx, data_manager)

@bot.tree.command(name="event", description="[Admin] Manage server-wide special events")
@app_commands.describe(
    action="Event action: start, list, end",
    event_id="Event ID to manage",
    duration="Duration in days (for start action)"
)
async def slash_event(interaction: discord.Interaction, action: str = None, event_id: str = None, duration: float = None):
    # Check if the user is the admin
    if interaction.user.id != ADMIN_USER_ID:
        await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
        return
        
    ctx = await bot.get_context(interaction)
    await event_command(ctx, data_manager, action, event_id, duration)

@bot.tree.command(name="balance", description="Check your current cursed energy balance")
async def slash_balance(interaction: discord.Interaction):
    ctx = await bot.get_context(interaction)
    await balance_cmd(ctx)

@bot.tree.command(name="advanced_shop", description="Browse the enhanced item shop with categories and filters")
async def slash_advanced_shop(interaction: discord.Interaction):
    ctx = await bot.get_context(interaction)
    await advanced_shop_command(ctx, data_manager)
    
@bot.tree.command(name="materials", description="View the materials encyclopedia")
async def slash_materials(interaction: discord.Interaction):
    ctx = await bot.get_context(interaction)
    await materials_command(ctx, data_manager)

@bot.tree.command(name="gather", description="Gather materials for crafting")
async def slash_gather(interaction: discord.Interaction):
    ctx = await bot.get_context(interaction)
    await gather_command(ctx, data_manager)

@bot.tree.command(name="craft", description="Craft items from gathered materials")
async def slash_craft(interaction: discord.Interaction):
    player = data_manager.get_player(interaction.user.id)
    view = CraftingEntryView(player, data_manager)
    embed = discord.Embed(
        title="🔨 Crafting Workshop",
        description="Welcome to the crafting workshop! Here you can craft items from materials you've gathered.",
        color=discord.Color.gold()
    )
    await interaction.response.send_message(embed=embed, view=view)

@bot.tree.command(name="encyclopedia", description="Browse the item and material encyclopedia")
@app_commands.describe(category="Category to browse (optional)")
async def slash_encyclopedia(interaction: discord.Interaction, category: str = None):
    player = data_manager.get_player(interaction.user.id)
    
    view = EncyclopediaExploreView(player, data_manager)
    
    embed = discord.Embed(
        title="📚 Ethereal Ascendancy Encyclopedia",
        description="Welcome to the comprehensive encyclopedia of Ethereal Ascendancy! Browse thousands of items, materials, equipment, and more.",
        color=discord.Color.blue()
    )
    
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
                inline=True
            )
    
    # Add player info
    embed.set_footer(text=f"Player: {player.name} | Level: {player.level}")
    
    await interaction.response.send_message(embed=embed, view=view)

@bot.command(name="help")
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
                "usage": "!profile [user] or /profile",
                "notes": "Shows character level, class, stats, and equipment"
            },
            "Daily": {
                "description": "Claim your daily rewards",
                "usage": "!daily or /daily",
                "notes": "Claim cursed energy and items every 24 hours"
            },
            "Balance": {
                "description": "Check your current cursed energy balance",
                "usage": "!balance (aliases: !bal, !ce, !energy) or /balance",
                "notes": "View your current cursed energy and achievement points"
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
                "usage": "!battle [@player] OR !battle [enemy_name] [enemy_level] (alias: !b) or /battle",
                "notes": "PvE and PvP combat with special abilities and effects"
            },
            "PvP History": {
                "description": "View your PvP battle history and stats",
                "usage": "!pvphistory (aliases: !pvp, !pvpstats) or /pvphistory",
                "notes": "See your win/loss record, recent battles, and cooldown status"
            },
            "Train": {
                "description": "Train to improve your stats",
                "usage": "!train (alias: !t) or /train",
                "notes": "Basic training to gain small stat improvements"
            },
            "Advanced Training": {
                "description": "Participate in advanced training exercises",
                "usage": "!advanced_train (alias: !at) or /advanced_train",
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
                "notes": "Shop with more items, categories, and filtering options"
            },
            "Buy": {
                "description": "Buy an item from the shop",
                "usage": "!buy <item_name>",
                "notes": "Purchase items with cursed energy to improve your character"
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
                "notes": "Collect raw materials from the environment for crafting"
            }
        },
        "Crafting": {
            "Materials": {
                "description": "View the materials encyclopedia",
                "usage": "!materials (aliases: !mats, !mat) or /materials",
                "notes": "Browse all available crafting materials and their uses"
            },
            "Craft": {
                "description": "Craft items from gathered materials",
                "usage": "!craft (alias: !crafting) or /craft",
                "notes": "Create weapons, armor, potions, and other items from materials"
            },
            "Encyclopedia": {
                "description": "Browse the complete item encyclopedia",
                "usage": "!encyclopedia [category] (aliases: !codex, !browser, !items) or /encyclopedia",
                "notes": "Browse all items, weapons, armor, and materials in the game"
            }
        },
        "Guild": {
            "Guild": {
                "description": "Guild system - create, join, or manage a guild",
                "usage": "!guild [action] [args] (alias: !g) or /guild",
                "notes": "Actions: create, join, leave, list, members, contribute, and more"
            },
            "Guild Dungeon": {
                "description": "Enter a dungeon with guild members",
                "usage": "!guild dungeon or /guild dungeon",
                "notes": "Team up with guild members for better rewards"
            }
        },
        "Progress": {
            "Achievements": {
                "description": "View your achievements and badges",
                "usage": "!achievements (aliases: !achieve, !ach) or /achievements",
                "notes": "Track your accomplishments and earn rewards"
            },
            "Quests": {
                "description": "View your active quests",
                "usage": "!quests (alias: !q) or /quests",
                "notes": "Daily, weekly, and long-term quests with rewards"
            },
            "Change Class": {
                "description": "Change to another unlocked class",
                "usage": "!change_class or /change_class",
                "notes": "Requires appropriate level or special items"
            },
            "Special Items": {
                "description": "View and use your special items and abilities",
                "usage": "!special_items (aliases: !sitems, !si) or /special_items",
                "notes": "Use transformation items and special abilities"
            }
        },
        "Events": {
            "Events": {
                "description": "View active server events",
                "usage": "!quests (check Events section) or /quests",
                "notes": "Special temporary events with unique bonuses"
            },
            "Event Admin": {
                "description": "Admin command to manage server events",
                "usage": "!event [action] [event_id] [duration]",
                "notes": "Admin only: start, list, end"
            }
        }
    }
    
    help_embeds = []
    
    if category:
        if category.title() in help_pages:
            embed = discord.Embed(
                title=f"{category.title()} Commands",
                color=discord.Color.purple()
            )
            
            for cmd, data in help_pages[category.title()].items():
                embed.add_field(
                    name=cmd,
                    value=f"{data['description']}\nUsage: {data['usage']}",
                    inline=False
                )
            help_embeds.append(embed)
        else:
            await ctx.send("❌ Invalid category! Use !help to see all categories.")
            return
    else:
        # Create embeds for each category
        for category, commands in help_pages.items():
            embed = discord.Embed(
                title=f"{category} Commands",
                color=discord.Color.purple()
            )
            
            for cmd, data in commands.items():
                embed.add_field(
                    name=cmd,
                    value=f"{data['description']}\nUsage: {data['usage']}",
                    inline=False
                )
            
            embed.set_footer(text=f"Page {len(help_embeds) + 1}/{len(help_pages)}")
            help_embeds.append(embed)
    
    class HelpView(View):
        def __init__(self, help_embeds, timeout=60):
            super().__init__(timeout=timeout)
            self.help_embeds = help_embeds
            self.current_page = 0
            
            # Add buttons
            prev_btn = Button(label="◀️", custom_id="prev", style=discord.ButtonStyle.gray)
            prev_btn.callback = self.prev_callback
            
            next_btn = Button(label="▶️", custom_id="next", style=discord.ButtonStyle.gray)
            next_btn.callback = self.next_callback
            
            self.add_item(prev_btn)
            self.add_item(next_btn)
        
        async def prev_callback(self, interaction: discord.Interaction):
            self.current_page = (self.current_page - 1) % len(self.help_embeds)
            await interaction.response.edit_message(embed=self.help_embeds[self.current_page])
        
        async def next_callback(self, interaction: discord.Interaction):
            self.current_page = (self.current_page + 1) % len(self.help_embeds)
            await interaction.response.edit_message(embed=self.help_embeds[self.current_page])
    
    view = HelpView(help_embeds)
    await ctx.send(embed=help_embeds[0], view=view)

# Bot token - read from environment variable
TOKEN = os.getenv('BOT_TOKEN')
if not TOKEN:
    # For development only - in production, use a real token
    print("WARNING: No Discord bot token found in environment variables.")
    print("Using a test token to allow code review. The bot will not connect to Discord.")
    print("Set the BOT_TOKEN environment variable with a real token for production use.")
    TOKEN = "test_token_for_development_only" # This will cause the bot to fail connecting, but code will run

# Sync slash commands with Discord
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
        print("\nERROR: Privileged intents are required but not enabled in the Discord Developer Portal.")
        print("This is a testing environment, so we'll continue with development.")
        print("In a real deployment, enable 'Server Members Intent' and 'Message Content Intent'")
        print("in the Discord Developer Portal: https://discord.com/developers/applications/")
        
        # Continue with development tasks without running the bot
        print("\nContinuing with skill tree and trading system development...")
