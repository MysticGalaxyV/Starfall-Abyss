import discord
from discord.ui import View, Button, Select
import random
import asyncio
from typing import Dict, List, Optional
import datetime

from data_manager import PlayerData
from constants import STARTER_CLASSES, CLASSES, SKILLS_COOLDOWN

class ClassSelectView(View):
    """View for selecting a starting class"""
    def __init__(self, timeout=60):
        super().__init__(timeout=timeout)
        self.selected_class = None
        
        # Add buttons for each starter class
        for class_name, data in STARTER_CLASSES.items():
            style = discord.ButtonStyle.primary
            if data["role"] == "Tank":
                style = discord.ButtonStyle.success
            elif data["role"] == "Assassin":
                style = discord.ButtonStyle.danger
                
            btn = Button(
                label=class_name,
                style=style,
                custom_id=class_name
            )
            btn.callback = self.class_callback
            self.add_item(btn)
    
    async def class_callback(self, interaction):
        self.selected_class = interaction.data["custom_id"]
        self.stop()
        await interaction.response.defer()

class SkillPointView(View):
    """View for allocating skill points"""
    def __init__(self, player: PlayerData, timeout=60):
        super().__init__(timeout=timeout)
        self.player = player
        self.allocated_stat = None
        
        # Add buttons for each stat
        stats = [
            ("Power", "⚔️", discord.ButtonStyle.danger),
            ("Defense", "🛡️", discord.ButtonStyle.success),
            ("Speed", "💨", discord.ButtonStyle.primary),
            ("Health", "❤️", discord.ButtonStyle.secondary)
        ]
        
        for name, emoji, style in stats:
            btn = Button(
                label=name,
                emoji=emoji,
                style=style,
                custom_id=name.lower()
            )
            btn.callback = self.stat_callback
            self.add_item(btn)
    
    async def stat_callback(self, interaction):
        stat_name = interaction.data["custom_id"]
        
        # Map UI stat names to actual stat names
        stat_map = {
            "power": "power",
            "defense": "defense",
            "speed": "speed",
            "health": "hp"
        }
        
        if stat_name in stat_map:
            self.allocated_stat = stat_map[stat_name]
            self.stop()
            await interaction.response.defer()

class PlayerSystem:
    """Handles player-related functionality"""
    @staticmethod
    async def start_new_character(ctx, player: PlayerData, data_manager) -> bool:
        """
        Start a new character creation process
        Returns: bool indicating if character was created
        """
        # Check if player already has a character
        if player.class_name:
            await ctx.send(f"❌ You already have a character ({player.class_name}, Level {player.class_level}).")
            return False
        
        # Create embed with class information
        embed = discord.Embed(
            title="⚔️ Choose Your Class",
            description="Select a starting class for your character:",
            color=discord.Color.blue()
        )
        
        for class_name, data in STARTER_CLASSES.items():
            # Format abilities
            abilities = f"🔥 Active: {data['abilities']['active']}\n🌟 Passive: {data['abilities']['passive']}"
            
            # Format stats
            stats = "\n".join([f"{stat.title()}: {value}" for stat, value in data["stats"].items()])
            
            embed.add_field(
                name=f"{class_name} ({data['role']})",
                value=f"**Stats:**\n{stats}\n\n**Abilities:**\n{abilities}",
                inline=True
            )
        
        # Send the message with class selection view
        view = ClassSelectView()
        message = await ctx.send(embed=embed, view=view)
        
        # Wait for selection
        await view.wait()
        
        if view.selected_class:
            # Player selected a class
            selected_class = view.selected_class
            player.class_name = selected_class
            
            # Set up initial stats based on class
            player.base_stats = STARTER_CLASSES[selected_class]["stats"].copy()
            player.current_stats = player.base_stats.copy()
            
            # Add to unlocked classes
            player.unlocked_classes.append(selected_class)
            
            # Set initial abilities based on class
            player.abilities = [
                STARTER_CLASSES[selected_class]["abilities"]["active"],
                STARTER_CLASSES[selected_class]["abilities"]["passive"]
            ]
            
            # Save data
            data_manager.save_data()
            
            # Create confirmation embed
            embed = discord.Embed(
                title="🎮 Character Created!",
                description=f"You are now a level 1 {selected_class}!",
                color=discord.Color.green()
            )
            
            embed.add_field(
                name="Stats",
                value="\n".join([f"{stat.title()}: {value}" for stat, value in player.current_stats.items()]),
                inline=True
            )
            
            embed.add_field(
                name="Abilities",
                value="\n".join(player.abilities),
                inline=True
            )
            
            embed.add_field(
                name="Next Steps",
                value=(
                    "Use `!profile` to view your character\n"
                    "Use `!train` to start gaining XP\n"
                    "Use `!dungeon` to explore dungeons\n"
                    "Use `!help` for more commands"
                ),
                inline=False
            )
            
            await message.edit(embed=embed, view=None)
            return True
        else:
            # Player didn't make a selection
            await message.edit(
                content="❌ Character creation cancelled. Use `!start` to try again.",
                embed=None, 
                view=None
            )
            return False
    
    @staticmethod
    async def show_profile(ctx, player: PlayerData, user=None):
        """Display a player's profile"""
        if not player.class_name:
            await ctx.send("❌ You haven't created a character yet! Use `!start` to begin.")
            return
        
        # Create profile embed
        embed = discord.Embed(
            title=f"{user.name if user else ctx.author.name}'s Profile",
            color=discord.Color.blue()
        )
        
        # Character information
        embed.add_field(
            name="Character",
            value=(
                f"**Class:** {player.class_name}\n"
                f"**Level:** {player.class_level}\n"
                f"**XP:** {player.class_exp}/{player.level_requirement}\n"
                f"**Cursed Energy:** {player.cursed_energy}/{player.max_cursed_energy}\n"
                f"**Currency:** {player.currency} 🌀"
            ),
            inline=False
        )
        
        # Stats with equipment bonuses
        embed.add_field(
            name="Stats",
            value=(
                f"**HP:** {player.current_stats['hp']}/{player.current_stats['max_hp']}\n"
                f"**Power:** {player.current_stats['power']}\n"
                f"**Defense:** {player.current_stats['defense']}\n"
                f"**Speed:** {player.current_stats['speed']}\n"
                f"**Skill Points:** {player.skill_points}"
            ),
            inline=True
        )
        
        # Abilities
        abilities_text = "None" if not player.abilities else "\n".join(player.abilities)
        embed.add_field(
            name="Abilities",
            value=abilities_text,
            inline=True
        )
        
        # Equipment
        equipment_text = ""
        for slot, item in player.equipped_items.items():
            if item:
                equipment_text += f"**{slot.title()}:** {item['name']}\n"
            else:
                equipment_text += f"**{slot.title()}:** None\n"
        
        embed.add_field(
            name="Equipment",
            value=equipment_text if equipment_text else "No equipment",
            inline=False
        )
        
        # Statistics
        embed.add_field(
            name="Statistics",
            value=(
                f"**Wins:** {player.wins}\n"
                f"**Losses:** {player.losses}\n"
                f"**Dungeons Completed:** {sum(player.dungeons_completed.values())}"
            ),
            inline=True
        )
        
        # Skills improvement prompt if player has skill points
        if player.skill_points > 0:
            embed.set_footer(text=f"You have {player.skill_points} skill points! Use !skills to allocate them.")
        
        await ctx.send(embed=embed)
    
    @staticmethod
    async def train_player(ctx, player: PlayerData):
        """Train the player to gain XP and currency"""
        if not player.class_name:
            await ctx.send("❌ You haven't created a character yet! Use `!start` to begin.")
            return
        
        # Check cooldown
        current_time = datetime.datetime.now()
        if player.last_train:
            time_since_last_train = (current_time - player.last_train).total_seconds()
            cooldown = SKILLS_COOLDOWN  # seconds (5 minutes)
            
            if time_since_last_train < cooldown:
                time_left = cooldown - time_since_last_train
                minutes = int(time_left // 60)
                seconds = int(time_left % 60)
                await ctx.send(f"⏳ You're still tired from your last training session. Rest for {minutes}m {seconds}s before training again.")
                return
        
        # Start training
        embed = discord.Embed(
            title="🏋️‍♂️ Training Session",
            description=f"{ctx.author.name} is training...",
            color=discord.Color.blue()
        )
        message = await ctx.send(embed=embed)
        
        # Choose a training scenario based on class
        scenarios = [
            f"practicing curse techniques in a training ground",
            f"sparring with other students",
            f"focusing on core strength and endurance",
            f"meditating to improve cursed energy control",
            f"studying ancient curse techniques",
            f"practicing dodging and movement",
        ]
        
        # Add class-specific scenarios
        if player.class_name == "Spirit Striker":
            scenarios.extend([
                "practicing cursed combo techniques",
                "working on enhancing strike power",
                "improving cursed energy channeling into attacks"
            ])
        elif player.class_name == "Domain Tactician":
            scenarios.extend([
                "constructing barriers of various sizes",
                "studying defensive techniques",
                "practicing barrier pulses and extensions"
            ])
        elif player.class_name == "Flash Rogue":
            scenarios.extend([
                "practicing shadowstep movements",
                "working on stealth and evasion",
                "enhancing speed and precision strikes"
            ])
        
        # Select a random scenario
        scenario = random.choice(scenarios)
        
        # Simulate training
        await asyncio.sleep(1)
        embed.description = f"{ctx.author.name} is {scenario}..."
        await message.edit(embed=embed)
        
        await asyncio.sleep(2)
        
        # Calculate rewards
        base_xp = random.randint(15, 25)
        level_bonus = player.class_level * 0.5
        xp_earned = int(base_xp + level_bonus)
        
        base_currency = random.randint(5, 10)
        currency_earned = int(base_currency + (player.class_level * 0.3))
        
        # Apply rewards
        level_up = player.add_exp(xp_earned)
        player.currency += currency_earned
        
        # Update last train time
        player.last_train = current_time
        
        # Show results
        embed.title = "🏋️‍♂️ Training Complete!"
        embed.description = f"{ctx.author.name} finished {scenario}"
        embed.color = discord.Color.green()
        
        embed.add_field(
            name="Rewards",
            value=(
                f"XP Gained: {xp_earned}\n"
                f"Currency Gained: {currency_earned} 🌀\n"
                f"Current XP: {player.class_exp}/{player.level_requirement}"
            ),
            inline=False
        )
        
        if level_up:
            embed.add_field(
                name="Level Up!",
                value=(
                    f"🎉 You reached level {player.class_level}!\n"
                    f"You gained 3 skill points!\n"
                    f"Use !skills to allocate them."
                ),
                inline=False
            )
        
        await message.edit(embed=embed)
        
        # Training may have unearthed an item (small chance)
        if random.random() < 0.15:  # 15% chance
            from constants import generate_random_item
            item = generate_random_item(player.class_level, quality_bonus=-1)  # Slightly lower quality than dungeons
            player.add_to_inventory(item)
            
            item_embed = discord.Embed(
                title="🔍 Found an Item!",
                description=f"While training, you discovered something interesting!",
                color=discord.Color.gold()
            )
            
            item_embed.add_field(
                name=item["name"],
                value=f"{item['description']}\n\nThe item has been added to your inventory.",
                inline=False
            )
            
            await ctx.send(embed=item_embed)
    
    @staticmethod
    async def allocate_skill_points(ctx, player: PlayerData):
        """Allow player to allocate skill points"""
        if not player.class_name:
            await ctx.send("❌ You haven't created a character yet! Use `!start` to begin.")
            return
        
        if player.skill_points <= 0:
            await ctx.send("❌ You don't have any skill points to allocate! Level up to earn more.")
            return
        
        # Create skills embed
        embed = discord.Embed(
            title="⬆️ Allocate Skill Points",
            description=(
                f"You have **{player.skill_points}** skill points to allocate.\n"
                f"Choose a stat to improve:"
            ),
            color=discord.Color.purple()
        )
        
        # Show current stats
        embed.add_field(
            name="Current Stats",
            value=(
                f"**Power:** {player.base_stats['power']} (+1)\n"
                f"**Defense:** {player.base_stats['defense']} (+1)\n"
                f"**Speed:** {player.base_stats['speed']} (+1)\n"
                f"**Health:** {player.base_stats['hp']} (+5)"
            ),
            inline=False
        )
        
        # Class recommendation
        recommended_stat = ""
        if player.class_name == "Spirit Striker":
            recommended_stat = "Power is recommended for Spirit Strikers for stronger attacks."
        elif player.class_name == "Domain Tactician":
            recommended_stat = "Defense is recommended for Domain Tacticians for stronger barriers."
        elif player.class_name == "Flash Rogue":
            recommended_stat = "Speed is recommended for Flash Rogues for quicker strikes."
            
        if recommended_stat:
            embed.add_field(name="Class Recommendation", value=recommended_stat, inline=False)
        
        # Send the message with skill point allocation view
        view = SkillPointView(player)
        message = await ctx.send(embed=embed, view=view)
        
        # Wait for selection
        await view.wait()
        
        if view.allocated_stat:
            # Player selected a stat
            old_value = player.base_stats[view.allocated_stat]
            
            # Allocate the point
            success = player.allocate_skill_point(view.allocated_stat)
            
            if success:
                new_value = player.base_stats[view.allocated_stat]
                
                # Update embed for confirmation
                confirm_embed = discord.Embed(
                    title="⬆️ Skill Point Allocated!",
                    description=f"You improved your {view.allocated_stat.title()} from {old_value} to {new_value}!",
                    color=discord.Color.green()
                )
                
                # Show remaining points
                if player.skill_points > 0:
                    confirm_embed.set_footer(text=f"You have {player.skill_points} skill points remaining. Use !skills to allocate more.")
                
                await message.edit(embed=confirm_embed, view=None)
            else:
                await message.edit(content="❌ Failed to allocate skill point. Please try again.", embed=None, view=None)
        else:
            # Player didn't make a selection
            await message.edit(content="❌ Skill point allocation cancelled.", embed=None, view=None)

    @staticmethod
    async def daily_reward(ctx, player: PlayerData):
        """Give daily rewards to the player"""
        if not player.class_name:
            await ctx.send("❌ You haven't created a character yet! Use `!start` to begin.")
            return
        
        # Check if already claimed today
        current_time = datetime.datetime.now()
        if player.last_daily:
            time_since_last_daily = (current_time - player.last_daily).total_seconds()
            
            # Check if 24 hours have passed
            if time_since_last_daily < 86400:  # 24 hours in seconds
                next_daily = player.last_daily + datetime.timedelta(days=1)
                time_left = next_daily - current_time
                
                hours = int(time_left.total_seconds() // 3600)
                minutes = int((time_left.total_seconds() % 3600) // 60)
                
                await ctx.send(f"⏳ You've already claimed your daily reward! Next reward in **{hours}h {minutes}m**.")
                return
            
            # Check if streak continues (within 48 hours)
            if time_since_last_daily < 172800:  # 48 hours in seconds
                player.daily_streak += 1
            else:
                # Streak broken
                player.daily_streak = 1
        else:
            # First daily claim
            player.daily_streak = 1
        
        # Update last daily timestamp
        player.last_daily = current_time
        
        # Calculate rewards based on streak
        base_currency = 50
        streak_bonus = min(player.daily_streak * 10, 100)  # Cap at +100
        currency_reward = base_currency + streak_bonus
        
        base_xp = 25
        xp_reward = base_xp + (player.daily_streak * 5)
        
        # Apply rewards
        level_up = player.add_exp(xp_reward)
        player.currency += currency_reward
        
        # Full restore
        player.full_restore()
        
        # Create reward embed
        embed = discord.Embed(
            title="🎁 Daily Reward Claimed!",
            description=f"You've claimed your daily reward!",
            color=discord.Color.gold()
        )
        
        embed.add_field(
            name="Rewards",
            value=(
                f"Currency: {base_currency} + {streak_bonus} (streak bonus) = **{currency_reward}** 🌀\n"
                f"XP: {base_xp} + {player.daily_streak * 5} (streak bonus) = **{xp_reward}**\n"
                f"HP and CE fully restored!"
            ),
            inline=False
        )
        
        embed.add_field(
            name="Daily Streak",
            value=f"Current streak: **{player.daily_streak}** day{'s' if player.daily_streak != 1 else ''}",
            inline=False
        )
        
        # Bonus item on milestone streaks
        if player.daily_streak in [7, 14, 30, 60, 90]:
            from constants import generate_random_item
            item = generate_random_item(player.class_level, quality_bonus=1)  # Better quality for milestone
            player.add_to_inventory(item)
            
            embed.add_field(
                name="🎉 Streak Milestone Bonus!",
                value=f"You received a **{item['name']}**!\n{item['description']}",
                inline=False
            )
        
        # Level up message
        if level_up:
            embed.add_field(
                name="Level Up!",
                value=(
                    f"🎉 You reached level {player.class_level}!\n"
                    f"You gained 3 skill points!"
                ),
                inline=False
            )
        
        await ctx.send(embed=embed)
