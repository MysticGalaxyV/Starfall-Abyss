import discord
from discord.ui import Button, View, Select
import random
import asyncio
import datetime
from typing import Dict, List, Optional, Tuple, Any

from data_models import PlayerData, DataManager
from utils import GAME_CLASSES
from user_restrictions import RestrictedView


class TrainingOptionView(RestrictedView):

    def __init__(self, player_data: PlayerData, data_manager: DataManager, authorized_user):
        super().__init__(authorized_user, timeout=60)
        self.player_data = player_data
        self.data_manager = data_manager
        self.selected_option = None

        # Get available training options based on class
        options = self.get_training_options()

        # Add buttons for each training option
        for option in options:
            btn = Button(label=option["name"],
                         emoji=option["emoji"],
                         style=discord.ButtonStyle.primary)
            btn.option_data = option
            btn.callback = self.option_callback
            self.add_item(btn)

    def get_training_options(self) -> List[Dict[str, Any]]:
        """Get training options based on player class"""
        options = []

        # Common training options for all classes
        options.append({
            "name": "Cardio Training",
            "emoji": "🏃",
            "description": "Improve your stamina and speed",
            "attribute": "speed",
            "base_gain": 1,
            "min_exp": 5,
            "max_exp": 15,
            "time": 20  # seconds
        })

        options.append({
            "name": "Strength Training",
            "emoji": "💪",
            "description": "Build your power and attack",
            "attribute": "power",
            "base_gain": 1,
            "min_exp": 5,
            "max_exp": 15,
            "time": 20  # seconds
        })

        options.append({
            "name": "Defensive Techniques",
            "emoji": "🛡️",
            "description": "Learn to guard and block attacks",
            "attribute": "defense",
            "base_gain": 1,
            "min_exp": 5,
            "max_exp": 15,
            "time": 20  # seconds
        })

        options.append({
            "name": "Cursed Energy Control",
            "emoji": "✨",
            "description": "Increase your cursed energy reserves",
            "attribute": "hp",
            "base_gain": 5,
            "min_exp": 5,
            "max_exp": 15,
            "time": 20  # seconds
        })

        # Add class-specific options
        if self.player_data.class_name == "Spirit Striker":
            options.append({
                "name": "Combo Practice",
                "emoji": "⚡",
                "description": "Perfect your cursed combo technique",
                "attribute": "power",
                "base_gain": 2,
                "min_exp": 10,
                "max_exp": 20,
                "time": 25  # seconds
            })
        elif self.player_data.class_name == "Domain Tactician":
            options.append({
                "name": "Barrier Technique",
                "emoji": "🔮",
                "description": "Strengthen your defensive barriers",
                "attribute": "defense",
                "base_gain": 2,
                "min_exp": 10,
                "max_exp": 20,
                "time": 25  # seconds
            })
        elif self.player_data.class_name == "Flash Rogue":
            options.append({
                "name": "Shadow Movement",
                "emoji": "👻",
                "description": "Enhance your speed and evasion",
                "attribute": "speed",
                "base_gain": 2,
                "min_exp": 10,
                "max_exp": 20,
                "time": 25  # seconds
            })

        return options

    async def option_callback(self, interaction: discord.Interaction):
        """Handle training option selection"""
        custom_id = interaction.data.get("custom_id", "")
        self.selected_option = custom_id

        # Get the option data
        option_data = None
        for item in self.children:
            if isinstance(item, Button) and hasattr(
                    item, 'custom_id') and item.custom_id == custom_id:
                option_data = item.option_data
                break

        if not option_data:
            await interaction.response.send_message(
                "❌ Error: Training option not found!", ephemeral=True)
            return

        # Disable all other buttons to hide options once one is selected
        for item in self.children:
            if isinstance(item, Button) and hasattr(
                    item, 'custom_id') and item.custom_id != custom_id:
                item.disabled = True

        # Check if player can train (cooldown)
        now = datetime.datetime.now()
        cooldown_minutes = 10  # 10 minute cooldown

        if self.player_data.last_train and (
                now - self.player_data.last_train).total_seconds() < (
                    cooldown_minutes * 60):
            remaining = cooldown_minutes * 60 - int(
                (now - self.player_data.last_train).total_seconds())
            minutes, seconds = divmod(remaining, 60)
            await interaction.response.send_message(
                f"❌ You're still tired from your last training session! Rest for {minutes}m {seconds}s more.",
                ephemeral=True)
            return

        # Start training
        await interaction.response.send_message(
            f"🏋️ You begin {option_data['name']} training...\n"
            f"{option_data['description']}\n"
            f"Training will complete in {option_data['time']} seconds.")

        # Simulate training time
        await asyncio.sleep(option_data['time'])

        # Calculate attribute gain
        # Higher level = diminishing returns
        level_factor = max(0.2, 1 - (self.player_data.class_level * 0.05))
        attribute_gain = max(1, int(option_data['base_gain'] * level_factor))

        # Calculate exp gain
        exp_gain = random.randint(option_data['min_exp'],
                                  option_data['max_exp'])

        # Apply training results
        # Attribute points directly modify allocated stats
        self.player_data.allocated_stats[
            option_data['attribute']] += attribute_gain

        # Add exp
        leveled_up = self.player_data.add_exp(exp_gain)

        # Add some battle energy
        battle_energy_gain = random.randint(3, 8)
        energy_added = self.player_data.add_battle_energy(battle_energy_gain)

        # Update last train time
        self.player_data.last_train = now

        # Track training completion for achievements
        if not hasattr(self.player_data, "training_completed"):
            self.player_data.training_completed = 0
        self.player_data.training_completed += 1

        # Check for achievements
        new_achievements = self.data_manager.check_player_achievements(self.player_data)

        # Save player data
        self.data_manager.save_data()

        # Create result embed
        embed = discord.Embed(
            title="🏆 Training Complete!",
            description=f"You've completed {option_data['name']} training!",
            color=discord.Color.green())

        embed.add_field(
            name="Results",
            value=(
                f"**{option_data['attribute'].title()}:** +{attribute_gain}\n"
                f"**EXP Gained:** {exp_gain}\n"
                f"**Battle Energy:** +{energy_added} ✨\n"
                f"**Max Energy:** {self.player_data.max_energy} "
                f"{'(↑ +1)' if training_energy_boost else ''}"),
            inline=False)

        if leveled_up:
            embed.add_field(
                name="Level Up!",
                value=
                (f"🆙 You reached Level {self.player_data.class_level}!\n"
                 f"You gained 3 skill points! Use !skills to allocate them.\n"
                 f"🌟 Max Energy increased by {level_energy_boost}!"),
                inline=False)

        embed.add_field(
            name="Cooldown",
            value=f"You can train again in {cooldown_minutes} minutes.",
            inline=False)

        await interaction.followup.send(embed=embed)

        # Stop the view since we're done with training
        self.stop()


class SkillPointsView(View):

    def __init__(self, player_data: PlayerData, data_manager: DataManager):
        super().__init__(timeout=60)
        self.player_data = player_data
        self.data_manager = data_manager

        # Add buttons for each stat
        stats = ["power", "defense", "speed", "hp"]

        for stat in stats:
            btn = Button(label=f"Increase {stat.title()}",
                         emoji=self.get_stat_emoji(stat),
                         style=discord.ButtonStyle.primary)
            btn.stat_name = stat
            btn.callback = self.stat_callback
            self.add_item(btn)

        # Add reset button
        reset_btn = Button(label="Reset Skill Points",
                           emoji="🔄",
                           style=discord.ButtonStyle.danger)
        reset_btn.callback = self.reset_callback
        self.add_item(reset_btn)

    def get_stat_emoji(self, stat: str) -> str:
        """Get emoji for stat"""
        stat_emojis = {
            "power": "⚔️",
            "defense": "🛡️",
            "speed": "💨",
            "hp": "❤️"
        }
        return stat_emojis.get(stat, "📊")

    async def stat_callback(self, interaction: discord.Interaction):
        """Handle stat increase"""
        # Get the stat
        for item in self.children:
            if isinstance(
                    item, Button
            ) and item.custom_id == interaction.data["custom_id"]:
                stat = item.stat_name
                break
        else:
            await interaction.response.send_message("❌ Error: Stat not found!",
                                                    ephemeral=True)
            return

        # Check if player has skill points
        if self.player_data.skill_points <= 0:
            await interaction.response.send_message(
                "❌ You don't have any skill points to allocate!",
                ephemeral=True)
            return

        # Apply stat increase
        self.player_data.skill_points -= 1

        # Initialize stat if not exists
        if stat not in self.player_data.allocated_stats:
            self.player_data.allocated_stats[stat] = 0

        # Apply different increase amounts based on stat
        if stat == "hp":
            self.player_data.allocated_stats[stat] += 10
            increase_amount = 10
        else:
            self.player_data.allocated_stats[stat] += 2
            increase_amount = 2

        # Save player data
        self.data_manager.save_data()

        # Create updated embed
        embed = self.create_skills_embed()

        await interaction.response.edit_message(
            content=f"✅ Added {increase_amount} points to {stat.title()}!",
            embed=embed,
            view=self)

    async def reset_callback(self, interaction: discord.Interaction):
        """Handle skill points reset"""
        # Check if there are points to reset
        total_allocated = sum(self.player_data.allocated_stats.values())

        if total_allocated == 0:
            await interaction.response.send_message(
                "❌ You don't have any allocated skill points to reset!",
                ephemeral=True)
            return

        # Create confirmation buttons
        confirm_view = View()

        confirm_btn = Button(label="Confirm Reset",
                             style=discord.ButtonStyle.danger,
                             emoji="✅")

        cancel_btn = Button(label="Cancel",
                            style=discord.ButtonStyle.secondary,
                            emoji="❌")

        async def confirm_callback(confirm_interaction):
            # Calculate points to refund
            # HP points are worth 1/5 of a skill point (since 1 point gives 10 HP)
            hp_points = self.player_data.allocated_stats.get("hp", 0)
            hp_skill_points = hp_points // 10

            # Other stats are worth 1/2 of a skill point (since 1 point gives 2 stat points)
            other_points = sum([
                v for k, v in self.player_data.allocated_stats.items()
                if k != "hp"
            ])
            other_skill_points = other_points // 2

            # Calculate total points to refund
            refund_points = hp_skill_points + other_skill_points

            # Reset allocated stats
            self.player_data.allocated_stats = {
                "power": 0,
                "defense": 0,
                "speed": 0,
                "hp": 0
            }

            # Refund skill points
            self.player_data.skill_points += refund_points

            # Save player data
            self.data_manager.save_data()

            # Create updated embed
            embed = self.create_skills_embed()

            await confirm_interaction.response.edit_message(
                content=
                f"✅ Reset complete! Refunded {refund_points} skill points.",
                embed=embed,
                view=self)

        async def cancel_callback(cancel_interaction):
            await cancel_interaction.response.edit_message(
                content="❌ Reset cancelled.",
                embed=interaction.message.embeds[0],
                view=self)

        confirm_btn.callback = confirm_callback
        cancel_btn.callback = cancel_callback

        confirm_view.add_item(confirm_btn)
        confirm_view.add_item(cancel_btn)

        await interaction.response.edit_message(
            content=
            "⚠️ Are you sure you want to reset all allocated skill points? This will refund approximately half of your invested points.",
            view=confirm_view)

    def create_skills_embed(self):
        """Create skills embed with current stats"""
        # Get base stats from class
        from utils import GAME_CLASSES
        class_data = GAME_CLASSES[self.player_data.class_name]
        base_stats = class_data["stats"].copy()

        # Add allocated stat points
        for stat, points in self.player_data.allocated_stats.items():
            if stat in base_stats:
                base_stats[stat] += points

        # Create embed
        embed = discord.Embed(
            title="⚡ Skill Points Allocation",
            description=
            f"Character: {self.player_data.class_name} (Level {self.player_data.class_level})\n"
            f"Available Skill Points: **{self.player_data.skill_points}**",
            color=discord.Color.blue())

        # Add current stats
        embed.add_field(
            name="🔢 Current Stats",
            value=
            f"**Power:** {base_stats['power']} (Base: {class_data['stats']['power']} + Allocated: {self.player_data.allocated_stats.get('power', 0)})\n"
            f"**Defense:** {base_stats['defense']} (Base: {class_data['stats']['defense']} + Allocated: {self.player_data.allocated_stats.get('defense', 0)})\n"
            f"**Speed:** {base_stats['speed']} (Base: {class_data['stats']['speed']} + Allocated: {self.player_data.allocated_stats.get('speed', 0)})\n"
            f"**HP:** {base_stats['hp']} (Base: {class_data['stats']['hp']} + Allocated: {self.player_data.allocated_stats.get('hp', 0)})",
            inline=False)

        # Add skill point info
        embed.add_field(name="ℹ️ Skill Point Usage",
                        value="• 1 skill point = +2 Power, Defense, or Speed\n"
                        "• 1 skill point = +10 HP\n"
                        "• Use the buttons below to allocate points",
                        inline=False)

        return embed


async def train_command(ctx, data_manager: DataManager):
    """Train to improve your stats"""
    player_data = data_manager.get_player(ctx.author.id)

    # Check if player has started
    if not player_data.class_name:
        await ctx.send(
            "❌ You haven't started your adventure yet! Use `!start` to choose a class."
        )
        return

    # Check for cooldown
    now = datetime.datetime.now()
    cooldown_minutes = 10  # 10 minute cooldown

    if player_data.last_train and (now - player_data.last_train
                                   ).total_seconds() < (cooldown_minutes * 60):
        remaining = cooldown_minutes * 60 - int(
            (now - player_data.last_train).total_seconds())
        minutes, seconds = divmod(remaining, 60)
        await ctx.send(
            f"❌ You're still tired from your last training session! Rest for {minutes}m {seconds}s more."
        )
        return

    # Create training embed
    embed = discord.Embed(
        title="🏋️ Training Grounds",
        description=
        f"Welcome to the training grounds, {ctx.author.display_name}!\n"
        f"Choose a training option to improve your character.",
        color=discord.Color.blue())

    # Add current stats
    from utils import GAME_CLASSES
    stats = player_data.get_stats(GAME_CLASSES)

    embed.add_field(name="📊 Current Stats",
                    value=f"**Power:** {stats['power']} ⚔️\n"
                    f"**Defense:** {stats['defense']} 🛡️\n"
                    f"**Speed:** {stats['speed']} 💨\n"
                    f"**HP:** {stats['hp']} ❤️",
                    inline=True)

    # Add level info
    embed.add_field(
        name="📈 Level Info",
        value=f"**Level:** {player_data.class_level}\n"
        f"**EXP:** {player_data.class_exp}/{int(100 * (player_data.class_level ** 1.5))}\n"
        f"**Class:** {player_data.class_name}",
        inline=True)

    # Create training view
    training_view = TrainingOptionView(player_data, data_manager, ctx.author)

    await ctx.send(embed=embed, view=training_view)


async def skills_command(ctx, data_manager: DataManager):
    """Allocate skill points"""
    player_data = data_manager.get_player(ctx.author.id)

    # Check if player has started
    if not player_data.class_name:
        await ctx.send(
            "❌ You haven't started your adventure yet! Use `!start` to choose a class."
        )
        return

    # Check if player has skill points
    if player_data.skill_points <= 0:
        await ctx.send(
            "❌ You don't have any skill points to allocate! Level up to earn more points."
        )
        return

    # Create skills view
    skills_view = SkillPointsView(player_data, data_manager)
    embed = skills_view.create_skills_embed()

    await ctx.send(embed=embed, view=skills_view)
