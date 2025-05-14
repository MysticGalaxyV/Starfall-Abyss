import discord
from discord.ext import commands
from discord.ui import Button, View, Select
import json
import datetime
import random
import os
import asyncio
from typing import Dict, List, Optional, Any, Union

from data_models import DataManager, PlayerData, Item, InventoryItem
from utils import GAME_CLASSES, STARTER_CLASSES
from battle_system import start_battle, start_pvp_battle
from dungeons import dungeon_command, DUNGEONS
from equipment import equipment_command, shop_command, buy_command
from training import train_command, skills_command
from class_change import class_change_command
from special_items import special_items_command, get_random_special_drop
from advanced_training import advanced_training_command

# Bot setup
intents = discord.Intents.default()
intents.message_content = True

def get_prefix(bot, message):
    prefixes = ['!', f'<@{bot.user.id}> ', f'<@!{bot.user.id}> ']  # The space after mentions is important
    return prefixes

bot = commands.Bot(command_prefix=get_prefix, intents=intents)
bot.remove_command('help')  # Remove default help command

# Initialize data manager
data_manager = DataManager()

@bot.event
async def on_ready():
    """Called when the bot is ready to start operating"""
    print(f'Logged in as {bot.user.name} ({bot.user.id})')
    print('------')
    await bot.change_presence(activity=discord.Game(name="!help for commands"))

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
    
    # Create embed for class selection
    embed = discord.Embed(
        title="🔮 Choose Your Class",
        description="Select a class to begin your adventure. Each class has unique abilities and playstyles.",
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
                   f"**Gold:** {player.gold} 🌀",
        color=discord.Color.blue()
    )
    
    # Add stats
    embed.add_field(
        name="📊 Stats",
        value=f"**HP:** {stats['hp']} ❤️\n"
              f"**Power:** {stats['power']} ⚔️\n"
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
    base_gold = 50
    base_exp = 30
    
    # Bonus for streak (up to 100% extra at 30 days)
    streak_bonus = min(1.0, player.daily_streak / 30)
    
    gold_reward = int(base_gold * (1 + streak_bonus))
    exp_reward = int(base_exp * (1 + streak_bonus))
    
    # Add rewards
    player.gold += gold_reward
    leveled_up = player.add_exp(exp_reward)
    
    # Create reward embed
    embed = discord.Embed(
        title="🎁 Daily Reward Claimed!",
        description=f"You've claimed your daily reward!",
        color=discord.Color.gold()
    )
    
    embed.add_field(
        name="Rewards",
        value=f"**Gold:** +{gold_reward} 🌀\n"
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

@bot.command(name="battle")
async def battle_command(ctx, enemy_name: str = None, enemy_level: int = None):
    """Battle an enemy or another player"""
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

@bot.command(name="dungeon")
async def dungeon_cmd(ctx):
    """Enter a dungeon"""
    await dungeon_command(ctx, data_manager)

@bot.command(name="equipment")
async def equipment_cmd(ctx):
    """View and manage your equipment"""
    await equipment_command(ctx, data_manager)

@bot.command(name="shop")
async def shop_cmd(ctx):
    """Browse the item shop"""
    await shop_command(ctx, data_manager)

@bot.command(name="buy")
async def buy_cmd(ctx, *, item_name: str = None):
    """Buy an item from the shop"""
    await buy_command(ctx, item_name, data_manager)

@bot.command(name="train")
async def train_cmd(ctx):
    """Train to improve your stats"""
    await train_command(ctx, data_manager)
    
@bot.command(name="advanced_training")
async def advanced_training_cmd(ctx):
    """Participate in advanced training exercises"""
    await advanced_training_command(ctx, data_manager)

@bot.command(name="skills")
async def skills_cmd(ctx):
    """Allocate skill points"""
    await skills_command(ctx, data_manager)

@bot.command(name="change_class")
async def change_class_cmd(ctx):
    """Change your character's class to another unlocked class"""
    await class_change_command(ctx, data_manager)

@bot.command(name="special_items")
async def special_items_cmd(ctx):
    """View and use your special items and abilities"""
    await special_items_command(ctx, data_manager)

@bot.command(name="help")
async def help_command(ctx, category: str = None):
    """Show help information"""
    help_pages = {
        "Basic": {
            "Start": {
                "description": "Begin your journey and select your class",
                "usage": "!start"
            },
            "Profile": {
                "description": "View your stats and progress",
                "usage": "!profile [user]"
            },
            "Daily": {
                "description": "Claim your daily rewards",
                "usage": "!daily"
            },
            "Change Class": {
                "description": "Change to another unlocked class",
                "usage": "!change_class"
            },
            "Special Items": {
                "description": "View and use your special items and abilities",
                "usage": "!special_items"
            },
            "Help": {
                "description": "Show this help message",
                "usage": "!help [category]"
            }
        },
        "Battle": {
            "Battle": {
                "description": "Battle an enemy or another player",
                "usage": "!battle [@player] OR !battle [enemy_name] [enemy_level]"
            },
            "Train": {
                "description": "Train to improve your stats",
                "usage": "!train"
            },
            "Advanced Training": {
                "description": "Participate in advanced training exercises",
                "usage": "!advanced_training"
            },
            "Skills": {
                "description": "Allocate skill points",
                "usage": "!skills"
            }
        },
        "Equipment": {
            "Equipment": {
                "description": "View and manage your equipment",
                "usage": "!equipment"
            },
            "Shop": {
                "description": "Browse available items",
                "usage": "!shop"
            },
            "Buy": {
                "description": "Purchase an item",
                "usage": "!buy <item_name>"
            }
        },
        "Dungeons": {
            "Dungeon": {
                "description": "Enter a dungeon",
                "usage": "!dungeon"
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
    raise ValueError("No Discord bot token found in environment variables. Please set BOT_TOKEN.")

# Run the bot
if __name__ == "__main__":
    bot.run(TOKEN)
