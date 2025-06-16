import discord
from discord.ui import Button, View, Select
import random
import asyncio
import datetime
from typing import Dict, List, Optional, Tuple, Any

from data_models import PlayerData, DataManager
from utils import GAME_CLASSES

# Training minigames for different skills
TRAINING_MINIGAMES = {
    "Combat Training": {
        "description": "Test your timing and reflexes to land critical hits",
        "primary_attribute": "power",
        "secondary_attribute": "speed",
        "base_exp": 20,
        "cooldown": 2,  # hours
        "emoji": "⚔️",
        "minigame_type": "reaction",
        "difficulty_levels": [
            {"name": "Basic", "exp_multiplier": 1.0, "time_window": 4.5, "attribute_gain": 1},
            {"name": "Advanced", "exp_multiplier": 1.5, "time_window": 3.5, "attribute_gain": 2},
            {"name": "Master", "exp_multiplier": 2.5, "time_window": 2.8, "attribute_gain": 3}
        ],
        "special_rewards": {
            "perfect_score": {"cursed_energy": 100, "effect": {"name": "Combat Focus", "duration": 3, "boost_type": "power", "boost_amount": 10}}
        }
    },
    "Defensive Stance": {
        "description": "Practice your defensive techniques to withstand attacks",
        "primary_attribute": "defense",
        "secondary_attribute": "hp",
        "base_exp": 20,
        "cooldown": 2,  # hours
        "emoji": "🛡️",
        "minigame_type": "sequence",
        "difficulty_levels": [
            {"name": "Basic", "exp_multiplier": 1.0, "sequence_length": 3, "attribute_gain": 1},
            {"name": "Advanced", "exp_multiplier": 1.5, "sequence_length": 5, "attribute_gain": 2},
            {"name": "Master", "exp_multiplier": 2.5, "sequence_length": 7, "attribute_gain": 3}
        ],
        "special_rewards": {
            "perfect_score": {"cursed_energy": 100, "effect": {"name": "Iron Defense", "duration": 3, "boost_type": "defense", "boost_amount": 15}}
        }
    },
    "Agility Course": {
        "description": "Navigate obstacles to improve your speed and reflexes",
        "primary_attribute": "speed",
        "secondary_attribute": "defense",
        "base_exp": 20,
        "cooldown": 2,  # hours
        "emoji": "🏃",
        "minigame_type": "reaction",
        "difficulty_levels": [
            {"name": "Basic", "exp_multiplier": 1.0, "time_window": 4.0, "attribute_gain": 1},
            {"name": "Advanced", "exp_multiplier": 1.5, "time_window": 3.0, "attribute_gain": 2},
            {"name": "Master", "exp_multiplier": 2.5, "time_window": 2.5, "attribute_gain": 3}
        ],
        "special_rewards": {
            "perfect_score": {"cursed_energy": 100, "effect": {"name": "Swift Movements", "duration": 3, "boost_type": "dodge_boost", "boost_amount": 20}}
        }
    },
    "Cursed Energy Control": {
        "description": "Meditate to enhance your cursed energy reserves",
        "primary_attribute": "hp",
        "secondary_attribute": "power",
        "base_exp": 20,
        "cooldown": 2,  # hours
        "emoji": "✨",
        "minigame_type": "timing",
        "difficulty_levels": [
            {"name": "Basic", "exp_multiplier": 1.0, "target_zone": 0.3, "attribute_gain": 1},
            {"name": "Advanced", "exp_multiplier": 1.5, "target_zone": 0.25, "attribute_gain": 2},
            {"name": "Master", "exp_multiplier": 2.5, "target_zone": 0.18, "attribute_gain": 3}
        ],
        "special_rewards": {
            "perfect_score": {"cursed_energy": 100, "effect": {"name": "Energy Surge", "duration": 3, "boost_type": "energy_regen", "boost_amount": 5}}
        }
    },
    "Tactical Analysis": {
        "description": "Study battle tactics to gain an edge in combat",
        "primary_attribute": "defense",
        "secondary_attribute": "power",
        "base_exp": 25,
        "cooldown": 3,  # hours
        "emoji": "📖",
        "minigame_type": "quiz",
        "difficulty_levels": [
            {"name": "Basic", "exp_multiplier": 1.0, "questions": 3, "attribute_gain": 1},
            {"name": "Advanced", "exp_multiplier": 1.5, "questions": 5, "attribute_gain": 2},
            {"name": "Master", "exp_multiplier": 2.5, "questions": 7, "attribute_gain": 3}
        ],
        "special_rewards": {
            "perfect_score": {"cursed_energy": 125, "effect": {"name": "Tactical Insight", "duration": 3, "boost_type": "critical_chance", "boost_amount": 10}}
        }
    },
    "Energy Cultivation": {
        "description": "Meditate to increase your maximum battle energy capacity (not cursed energy/currency)",
        "primary_attribute": "energy",
        "secondary_attribute": "defense",
        "base_exp": 25,
        "cooldown": 4,  # hours
        "emoji": "⚡",
        "minigame_type": "precision",
        "difficulty_levels": [
            {"name": "Basic", "exp_multiplier": 1.0, "targets": 4, "attribute_gain": 1, "energy_gain": 5},
            {"name": "Advanced", "exp_multiplier": 1.5, "targets": 6, "attribute_gain": 2, "energy_gain": 10},
            {"name": "Master", "exp_multiplier": 2.5, "targets": 8, "attribute_gain": 3, "energy_gain": 15}
        ],
        "special_rewards": {
            "perfect_score": {"cursed_energy": 150, "effect": {"name": "Energy Overflow", "duration": 4, "boost_type": "max_energy", "boost_amount": 20}}
        }
    },
    "Shadow Technique": {
        "description": "Practice mysterious shadow techniques to enhance your abilities",
        "primary_attribute": "power",
        "secondary_attribute": "hp",
        "base_exp": 30,
        "cooldown": 4,  # hours
        "emoji": "🌑",
        "minigame_type": "sequence",
        "difficulty_levels": [
            {"name": "Basic", "exp_multiplier": 1.0, "sequence_length": 4, "attribute_gain": 2},
            {"name": "Advanced", "exp_multiplier": 1.5, "sequence_length": 6, "attribute_gain": 3},
            {"name": "Master", "exp_multiplier": 2.5, "sequence_length": 8, "attribute_gain": 4}
        ],
        "special_rewards": {
            "perfect_score": {"cursed_energy": 150, "effect": {"name": "Shadow Form", "duration": 2, "boost_type": "special_damage", "boost_amount": 25}}
        },
        "unlock_requirements": {
            "class_level": 10
        }
    }
}

# Class-specific advanced training
CLASS_TRAINING = {
    "Spirit Striker": {
        "Combo Mastery": {
            "description": "Perfect your attack combinations for maximum damage",
            "primary_attribute": "power",
            "secondary_attribute": "speed",
            "base_exp": 30,
            "cooldown": 4,  # hours
            "level_req": 5,
            "emoji": "💥"
        },
        "Soul Resonance": {
            "description": "Align your soul with your cursed energy for greater power",
            "primary_attribute": "hp",
            "secondary_attribute": "power",
            "base_exp": 30,
            "cooldown": 4,  # hours
            "level_req": 10,
            "emoji": "🔮"
        }
    },
    "Domain Tactician": {
        "Barrier Techniques": {
            "description": "Strengthen your defensive barriers",
            "primary_attribute": "defense",
            "secondary_attribute": "hp",
            "base_exp": 30,
            "cooldown": 4,  # hours
            "level_req": 5,
            "emoji": "🔄"
        },
        "Domain Creation": {
            "description": "Practice creating and maintaining your domain",
            "primary_attribute": "hp",
            "secondary_attribute": "defense",
            "base_exp": 30,
            "cooldown": 4,  # hours
            "level_req": 10,
            "emoji": "🌌"
        }
    },
    "Flash Rogue": {
        "Shadowstep": {
            "description": "Master the art of moving through shadows",
            "primary_attribute": "speed",
            "secondary_attribute": "power",
            "base_exp": 30,
            "cooldown": 4,  # hours
            "level_req": 5,
            "emoji": "👻",
            "minigame_type": "sequence",
            "difficulty_levels": [
                {"name": "Basic", "exp_multiplier": 1.0, "sequence_length": 4, "attribute_gain": 2},
                {"name": "Advanced", "exp_multiplier": 1.5, "sequence_length": 6, "attribute_gain": 3},
                {"name": "Master", "exp_multiplier": 2.5, "sequence_length": 8, "attribute_gain": 4}
            ],
            "special_rewards": {
                "perfect_score": {"cursed_energy": 120, "effect": {"name": "Shadow Form", "duration": 2, "boost_type": "dodge_chance", "boost_amount": 15}}
            }
        },
        "Assassination Techniques": {
            "description": "Hone your skills for deadly precision strikes",
            "primary_attribute": "power",
            "secondary_attribute": "speed",
            "base_exp": 30,
            "cooldown": 4,  # hours
            "level_req": 10,
            "emoji": "🗡️",
            "minigame_type": "precision",
            "difficulty_levels": [
                {"name": "Basic", "exp_multiplier": 1.0, "targets": 4, "attribute_gain": 2},
                {"name": "Advanced", "exp_multiplier": 1.5, "targets": 6, "attribute_gain": 3},
                {"name": "Master", "exp_multiplier": 2.5, "targets": 8, "attribute_gain": 4}
            ],
            "special_rewards": {
                "perfect_score": {"cursed_energy": 150, "effect": {"name": "Assassination Focus", "duration": 2, "boost_type": "critical_damage", "boost_amount": 20}}
            }
        }
    },
    # Advanced class training
    "Cursed Specialist": {
        "Reverse Technique": {
            "description": "Learn to use cursed energy for healing",
            "primary_attribute": "hp",
            "secondary_attribute": "defense",
            "base_exp": 40,
            "cooldown": 6,  # hours
            "level_req": 12,
            "emoji": "💚",
            "minigame_type": "timing",
            "difficulty_levels": [
                {"name": "Basic", "exp_multiplier": 1.0, "target_zone": 0.3, "attribute_gain": 2},
                {"name": "Advanced", "exp_multiplier": 1.5, "target_zone": 0.25, "attribute_gain": 3},
                {"name": "Master", "exp_multiplier": 2.5, "target_zone": 0.18, "attribute_gain": 4}
            ],
            "special_rewards": {
                "perfect_score": {"cursed_energy": 180, "effect": {"name": "Healing Aura", "duration": 3, "boost_type": "hp_regen", "boost_amount": 10}}
            }
        }
    },
    "Domain Master": {
        "Domain Expansion": {
            "description": "Perfect your domain expansion technique",
            "primary_attribute": "power",
            "secondary_attribute": "hp",
            "base_exp": 40,
            "cooldown": 6,  # hours
            "level_req": 12,
            "emoji": "🌐",
            "minigame_type": "timing",
            "difficulty_levels": [
                {"name": "Basic", "exp_multiplier": 1.0, "target_zone": 0.3, "attribute_gain": 2},
                {"name": "Advanced", "exp_multiplier": 1.5, "target_zone": 0.25, "attribute_gain": 3},
                {"name": "Master", "exp_multiplier": 2.5, "target_zone": 0.18, "attribute_gain": 5}
            ],
            "special_rewards": {
                "perfect_score": {"cursed_energy": 180, "effect": {"name": "Domain Authority", "duration": 3, "boost_type": "all_stats", "boost_amount": 8}}
            }
        }
    },
    "Shadow Assassin": {
        "Ten Shadows": {
            "description": "Master the technique of summoning shadow creatures",
            "primary_attribute": "power",
            "secondary_attribute": "speed",
            "base_exp": 40,
            "cooldown": 6,  # hours
            "level_req": 12,
            "emoji": "🐺",
            "minigame_type": "sequence",
            "difficulty_levels": [
                {"name": "Basic", "exp_multiplier": 1.0, "sequence_length": 5, "attribute_gain": 2},
                {"name": "Advanced", "exp_multiplier": 1.5, "sequence_length": 7, "attribute_gain": 3},
                {"name": "Master", "exp_multiplier": 2.5, "sequence_length": 10, "attribute_gain": 5}
            ],
            "special_rewards": {
                "perfect_score": {"cursed_energy": 180, "effect": {"name": "Shadow Beast", "duration": 3, "boost_type": "summon_power", "boost_amount": 20}}
            }
        }
    },
    "Limitless Sorcerer": {
        "Infinity": {
            "description": "Explore the concept of infinity with your abilities",
            "primary_attribute": "power",
            "secondary_attribute": "defense",
            "base_exp": 50,
            "cooldown": 8,  # hours
            "level_req": 20,
            "emoji": "♾️",
            "minigame_type": "quiz",
            "difficulty_levels": [
                {"name": "Basic", "exp_multiplier": 1.0, "questions": 5, "attribute_gain": 3},
                {"name": "Advanced", "exp_multiplier": 1.5, "questions": 7, "attribute_gain": 4},
                {"name": "Master", "exp_multiplier": 2.5, "questions": 10, "attribute_gain": 6}
            ],
            "special_rewards": {
                "perfect_score": {"cursed_energy": 250, "effect": {"name": "Limitless", "duration": 3, "boost_type": "cooldown_reduction", "boost_amount": 30}}
            }
        }
    }
}

# REACTION MINIGAME - Find and click targets
class TargetButton(Button):
    def __init__(self, is_target: bool, parent_view, row: int = 0):
        # Define the button appearance
        if is_target:
            super().__init__(
                label="Target!",
                style=discord.ButtonStyle.green,
                emoji="🎯",
                row=row
            )
        else:
            super().__init__(
                label="Miss",
                style=discord.ButtonStyle.gray,
                emoji="❌",
                row=row
            )

        self.is_target = is_target
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        # Handle the button click
        if self.is_target:
            self.parent_view.score += 1
            await interaction.response.edit_message(
                content=f"🎯 Hit! Score: {self.parent_view.score}/{self.parent_view.max_score}",
                view=None
            )
        else:
            await interaction.response.edit_message(
                content=f"❌ Miss! Score: {self.parent_view.score}/{self.parent_view.max_score}",
                view=None
            )

        self.parent_view.round_complete = True
        self.parent_view.stop()

# SEQUENCE MINIGAME - Remember and repeat patterns
class SequenceButton(Button):
    def __init__(self, symbol: str, order: int, parent_view, row: int = 0):
        # Default style for all sequence buttons
        super().__init__(
            label=symbol,
            style=discord.ButtonStyle.primary,
            row=row
        )

        self.symbol = symbol
        self.order = order
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        # Handle the button click
        if self.parent_view.expected_next == self.order:
            # Correct sequence step
            self.parent_view.current_sequence_position += 1

            # If completed the whole sequence
            if self.parent_view.current_sequence_position >= len(self.parent_view.current_sequence):
                self.parent_view.score += 1
                await interaction.response.edit_message(
                    content=f"✅ Sequence complete! Score: {self.parent_view.score}/{self.parent_view.max_score}",
                    view=None
                )
                self.parent_view.round_complete = True
                self.parent_view.stop()
            else:
                # Update expected next button
                self.parent_view.expected_next = self.parent_view.current_sequence[self.parent_view.current_sequence_position]
                await interaction.response.defer()  # Just acknowledge without changing the message
        else:
            # Incorrect sequence step
            await interaction.response.edit_message(
                content=f"❌ Incorrect sequence! Score: {self.parent_view.score}/{self.parent_view.max_score}",
                view=None
            )
            self.parent_view.round_complete = True
            self.parent_view.stop()

# TIMING MINIGAME - Stop the moving indicator at the right time
class TimingBar(View):
    def __init__(self, parent_view, target_zone: float, timeout: float = 10):
        super().__init__(timeout=timeout)
        self.parent_view = parent_view
        self.target_zone = target_zone  # Size of the target zone (0.0-1.0)
        self.position = 0.0  # 0.0 to 1.0 representing position on bar
        self.direction = 1  # 1 for right, -1 for left
        self.base_speed = 0.025  # Base movement speed
        self.speed = self.base_speed  # Current speed (can vary)
        self.acceleration = 0.0005  # Slight acceleration for smoothness
        self.task = None
        self.stopped = False

        # Add the stop button
        stop_btn = Button(label="STOP", style=discord.ButtonStyle.danger)
        stop_btn.callback = self.stop_callback
        self.add_item(stop_btn)

    async def start(self, interaction: discord.Interaction):
        # Initial render
        self.position = 0.0
        await interaction.edit_original_response(
            content=self.render_bar(),
            view=self
        )

        # Start the animation
        self.task = asyncio.create_task(self.animate(interaction))

    def render_bar(self) -> str:
        """Render a text-based timing bar"""
        bar_length = 30  # Even longer for smoother movement
        target_start = int((0.5 - self.target_zone/2) * bar_length)
        target_end = int((0.5 + self.target_zone/2) * bar_length)

        # Create the bar with target zone
        bar = ["⬛"] * bar_length
        for i in range(target_start, target_end+1):
            if i < len(bar):
                bar[i] = "🟩"

        # Add the indicator with smooth positioning
        indicator_pos = min(bar_length-1, max(0, int(self.position * bar_length)))
        
        # Add trailing effect for smoother visual
        if indicator_pos > 0 and bar[indicator_pos-1] not in ["🟩"]:
            bar[indicator_pos-1] = "🟡"  # Trail effect
        
        bar[indicator_pos] = "🔴"

        # Progress indicator
        progress = f"{int(self.position * 100):3d}%"
        zone_info = f"Target: {int(self.target_zone * 100)}% | Position: {progress}"
        
        return f"🎯 Stop the red ball in the green zone!\n{zone_info}\n\n|{''.join(bar)}|"

    async def animate(self, interaction: discord.Interaction):
        """Animate the timing bar"""
        try:
            while not self.stopped:
                # Slightly vary speed for more natural movement
                self.speed = self.base_speed + (self.acceleration * abs(self.position - 0.5))
                
                # Update position
                self.position += self.speed * self.direction

                # Change direction if hitting edge with slight bounce effect
                if self.position >= 1.0:
                    self.position = 1.0
                    self.direction = -1
                    self.speed = self.base_speed  # Reset speed at edges
                elif self.position <= 0.0:
                    self.position = 0.0
                    self.direction = 1
                    self.speed = self.base_speed  # Reset speed at edges

                # Update the message
                try:
                    await interaction.edit_original_response(content=self.render_bar())
                except:
                    # If editing fails (e.g. message deleted), stop the animation
                    self.stopped = True
                    break

                # Ultra-smooth animation with high frame rate
                await asyncio.sleep(0.025)
        except asyncio.CancelledError:
            # Task was cancelled, clean up
            self.stopped = True
        except Exception as e:
            print(f"Error in timing bar animation: {e}")
            self.stopped = True

    async def stop_callback(self, interaction: discord.Interaction):
        """Handle stopping the timing bar"""
        # Stop the animation
        self.stopped = True
        if self.task and not self.task.done():
            self.task.cancel()

        # Check if in target zone
        bar_length = 20
        target_start = (0.5 - self.target_zone/2)
        target_end = (0.5 + self.target_zone/2)
        success = target_start <= self.position <= target_end

        # Update the view based on result
        if success:
            self.parent_view.score += 1
            await interaction.response.edit_message(
                content=f"✅ Perfect timing! Score: {self.parent_view.score}/{self.parent_view.max_score}",
                view=None
            )
        else:
            await interaction.response.edit_message(
                content=f"❌ Missed the target zone! Score: {self.parent_view.score}/{self.parent_view.max_score}",
                view=None
            )

        # Signal completion
        self.parent_view.round_complete = True
        self.parent_view.stop()

# QUIZ MINIGAME - Answer trivia questions
class QuizButton(Button):
    def __init__(self, answer: str, is_correct: bool, parent_view, row: int = 0):
        # All answers look the same until selected
        super().__init__(
            label=answer,
            style=discord.ButtonStyle.secondary,
            row=row
        )

        self.is_correct = is_correct
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        # Handle answer selection
        if self.is_correct:
            self.parent_view.score += 1
            await interaction.response.edit_message(
                content=f"✅ Correct! Score: {self.parent_view.score}/{self.parent_view.max_score}",
                view=None
            )
        else:
            await interaction.response.edit_message(
                content=f"❌ Incorrect! The correct answer was: {self.parent_view.correct_answer}\nScore: {self.parent_view.score}/{self.parent_view.max_score}",
                view=None
            )

        self.parent_view.round_complete = True
        self.parent_view.stop()

# PRECISION MINIGAME - Track and click moving targets
class MovingTargetButton(Button):
    def __init__(self, is_active: bool, position: Tuple[int, int], parent_view):
        # Set button appearance with proper labels
        super().__init__(
            label="🔴" if is_active else "⬜",
            style=discord.ButtonStyle.danger if is_active else discord.ButtonStyle.secondary,
            row=position[0]  # Use row as Y coordinate
        )

        self.is_active = is_active
        self.parent_view = parent_view
        self.position = position

    async def callback(self, interaction: discord.Interaction):
        # Handle target click
        if self.is_active:
            self.parent_view.hits += 1
            await interaction.response.edit_message(
                content=f"🎯 Target hit! Hits: {self.parent_view.hits}/{self.parent_view.target_count}",
                view=None
            )
        else:
            await interaction.response.edit_message(
                content=f"❌ Missed! Hits: {self.parent_view.hits}/{self.parent_view.target_count}",
                view=None
            )

        self.parent_view.round_complete = True
        self.parent_view.stop()

# Main training minigame view
class TrainingMinigameView(View):
    def __init__(self, player_data: PlayerData, training_type: str, training_data: Dict[str, Any], data_manager: DataManager):
        super().__init__(timeout=60)
        self.player_data = player_data
        self.training_type = training_type
        self.training_data = training_data
        self.data_manager = data_manager

        # Get difficulty settings
        self.difficulty_levels = training_data["difficulty_levels"]

        # Minigame state
        self.current_difficulty = None
        self.score = 0
        self.max_score = 0
        self.round_complete = False

        # Sequence minigame specific
        self.current_sequence = []
        self.current_sequence_position = 0
        self.expected_next = None

        # Quiz minigame specific
        self.correct_answer = ""

        # Precision minigame specific
        self.hits = 0
        self.target_count = 0

        # Add the start button
        start_button = Button(label="Start Training", style=discord.ButtonStyle.primary, emoji="🏋️")
        start_button.callback = self.start_callback
        self.add_item(start_button)

        # Add the cancel button
        cancel_button = Button(label="Cancel", style=discord.ButtonStyle.secondary, emoji="❌")
        cancel_button.callback = self.cancel_callback
        self.add_item(cancel_button)

    async def start_callback(self, interaction: discord.Interaction):
        """Start the training minigame"""
        # Remove the start and cancel buttons
        self.clear_items()

        # Create a difficulty select
        difficulty_select = Select(
            placeholder="Select difficulty",
            options=[
                discord.SelectOption(
                    label=level["name"],
                    description=f"Exp multiplier: {level['exp_multiplier']}x",
                    value=str(i)
                ) for i, level in enumerate(self.difficulty_levels)
            ]
        )

        # Add callback for difficulty selection
        async def difficulty_callback(interaction: discord.Interaction):
            # Get selected difficulty with error handling
            try:
                if not interaction.data or "values" not in interaction.data:
                    await interaction.response.send_message("Error: No difficulty selected.", ephemeral=True)
                    return
                selected_idx = int(interaction.data["values"][0])
                self.current_difficulty = self.difficulty_levels[selected_idx]
            except (KeyError, IndexError, ValueError) as e:
                await interaction.response.send_message(f"Error selecting difficulty: {e}", ephemeral=True)
                return

            # Remove the select menu
            self.clear_items()

            # Run the appropriate minigame
            minigame_type = self.training_data["minigame_type"]

            await interaction.response.edit_message(
                content=f"Starting {self.current_difficulty['name']} {self.training_type}...",
                view=self
            )

            # Choose the right minigame
            if minigame_type == "reaction":
                await self.run_reaction_minigame(interaction)
            elif minigame_type == "sequence":
                await self.run_sequence_minigame(interaction)
            elif minigame_type == "timing":
                await self.run_timing_minigame(interaction)
            elif minigame_type == "quiz":
                await self.run_quiz_minigame(interaction)
            elif minigame_type == "precision":
                await self.run_precision_minigame(interaction)
            else:
                await interaction.edit_original_response(
                    content=f"❌ Unknown minigame type: {minigame_type}",
                    view=None
                )

        difficulty_select.callback = difficulty_callback
        self.add_item(difficulty_select)

        # Update the message
        await interaction.response.edit_message(
            content=f"Select difficulty for {self.training_type}:",
            view=self
        )

    async def run_reaction_minigame(self, interaction: discord.Interaction):
        """Run the reaction speed minigame"""
        # Set up minigame parameters
        time_window = self.current_difficulty.get("time_window", 2.0)  # Time in seconds to hit the target
        rounds = 5  # Number of rounds
        self.max_score = rounds
        self.score = 0

        for round_num in range(1, rounds + 1):
            # Create a grid of buttons (one target, rest are misses)
            # Grid size increases with difficulty
            if time_window >= 4.0:  # Basic
                grid_size = 3  # 3x3 grid
            elif time_window >= 3.0:  # Advanced
                grid_size = 4  # 4x4 grid
            else:  # Master
                grid_size = 4  # Keep at 4x4 for fairness
            
            target_x = random.randint(0, grid_size - 1)
            target_y = random.randint(0, grid_size - 1)

            # Create a new view for this round
            round_view = View(timeout=time_window)

            # Add buttons to the grid
            for y in range(grid_size):
                for x in range(grid_size):
                    is_target = (x == target_x and y == target_y)
                    button = TargetButton(is_target, self, row=y)
                    round_view.add_item(button)

            # Show the grid
            self.round_complete = False
            await interaction.edit_original_response(
                content=f"Round {round_num}/{rounds} - Click the target button! 🎯",
                view=round_view
            )

            # Wait for the round to complete or timeout
            if time_window > 0:
                try:
                    await asyncio.wait_for(
                        round_view.wait(), 
                        timeout=time_window
                    )
                except asyncio.TimeoutError:
                    # Time's up
                    await interaction.edit_original_response(
                        content=f"⏱️ Time's up! Score: {self.score}/{self.max_score}",
                        view=None
                    )
                    self.round_complete = True

            # Short pause between rounds
            if round_num < rounds and self.round_complete:
                await asyncio.sleep(1.5)

        # After all rounds, process the results
        await self.process_training_results(interaction)

    async def run_sequence_minigame(self, interaction: discord.Interaction):
        """Run the sequence memorization minigame"""
        # Set up minigame parameters
        sequence_length = self.current_difficulty.get("sequence_length", 4)
        rounds = 3  # Number of different sequences
        self.max_score = rounds
        self.score = 0

        # Symbols for the buttons
        symbols = ["🔴", "🔵", "🟢", "🟡", "⚪", "🟠", "🟣", "⚫"]

        for round_num in range(1, rounds + 1):
            # Generate a random sequence
            self.current_sequence = [random.randint(0, len(symbols) - 1) for _ in range(sequence_length)]

            # Create a view to display the sequence
            display_view = View(timeout=None)
            for i, symbol_idx in enumerate(self.current_sequence):
                # Calculate row number - max 5 buttons per row
                row_num = i // 5
                button = Button(
                    label=f"{i+1}: {symbols[symbol_idx]}",
                    style=discord.ButtonStyle.secondary,
                    disabled=True,
                    row=row_num
                )
                display_view.add_item(button)

            # Show the sequence to memorize
            await interaction.edit_original_response(
                content=f"Round {round_num}/{rounds} - Memorize this sequence:",
                view=display_view
            )

            # Wait before hiding the sequence - increased time for better memorization
            await asyncio.sleep(sequence_length * 1.2)  # More time for memorization

            # Hide the sequence and show a "Get ready" message
            await interaction.edit_original_response(
                content=f"Round {round_num}/{rounds} - Now reproduce the sequence from memory!",
                view=None
            )

            # Small pause to let player prepare
            await asyncio.sleep(1.0)

            # Create a view for repeating the sequence
            sequence_view = View(timeout=sequence_length * 2.0)  # Time based on sequence length

            # Add the buttons in a randomized order
            shuffled_indices = list(range(len(symbols)))
            random.shuffle(shuffled_indices)

            # Split into rows if needed
            buttons_per_row = 4
            for i, symbol_idx in enumerate(shuffled_indices[:8]):  # Limit to 8 buttons max
                row_num = i // buttons_per_row
                button = SequenceButton(
                    symbol=symbols[symbol_idx],
                    order=symbol_idx,
                    parent_view=self,
                    row=row_num
                )
                sequence_view.add_item(button)

            # Reset for this round
            self.current_sequence_position = 0
            self.expected_next = self.current_sequence[0]
            self.round_complete = False

            # Show the buttons for player to repeat sequence
            await interaction.edit_original_response(
                content=f"Round {round_num}/{rounds} - Now repeat the sequence!",
                view=sequence_view
            )

            # Wait for round completion or timeout
            try:
                await asyncio.wait_for(
                    sequence_view.wait(),
                    timeout=sequence_length * 2.5
                )
            except asyncio.TimeoutError:
                # Time's up
                await interaction.edit_original_response(
                    content=f"⏱️ Time's up! Score: {self.score}/{self.max_score}",
                    view=None
                )
                self.round_complete = True

            # Short pause between rounds
            if round_num < rounds and self.round_complete:
                await asyncio.sleep(1.5)

        # After all rounds, show a processing message
        await interaction.edit_original_response(
            content="Training complete! Processing results...",
            view=None
        )

        # Small pause for better user experience
        await asyncio.sleep(1.0)

        # Process the results
        await self.process_training_results(interaction)

    async def run_timing_minigame(self, interaction: discord.Interaction):
        """Run the timing bar minigame"""
        # Set up minigame parameters
        target_zone = self.current_difficulty.get("target_zone", 0.2)  # Width of target zone (0.0-1.0)
        rounds = 3  # Number of rounds
        self.max_score = rounds
        self.score = 0

        for round_num in range(1, rounds + 1):
            # Create and start a timing bar
            timing_bar = TimingBar(self, target_zone)

            # Reset round state
            self.round_complete = False

            # Start the timing bar
            interaction_copy = interaction
            await timing_bar.start(interaction_copy)

            # Wait for round completion or timeout
            try:
                await asyncio.wait_for(
                    timing_bar.wait(),
                    timeout=10.0  # Maximum 10 seconds per round
                )
            except asyncio.TimeoutError:
                # Time's up (should be handled by the timing bar itself)
                pass

            # Short pause between rounds
            if round_num < rounds and self.round_complete:
                await asyncio.sleep(1.5)

        # After all rounds, process the results
        await self.process_training_results(interaction)

    async def run_quiz_minigame(self, interaction: discord.Interaction):
        """Run the knowledge quiz minigame"""
        # Set up minigame parameters
        question_count = self.current_difficulty.get("questions", 3)
        self.max_score = question_count
        self.score = 0

        # Quiz questions related to the game
        questions = [
            {
                "question": "What resource is used to perform special moves in battles?",
                "answers": ["Energy", "Gold", "Health", "Experience"],
                "correct": "Energy"
            },
            {
                "question": "Which of these is NOT a basic character class?",
                "answers": ["Limitless Sorcerer", "Spirit Striker", "Domain Tactician", "Flash Rogue"],
                "correct": "Limitless Sorcerer"
            },
            {
                "question": "What is the main currency used for transactions?",
                "answers": ["Gold", "Cursed Energy", "Gems", "Scrolls"],
                "correct": "Gold"
            },
            {
                "question": "Which attribute affects how much damage you deal?",
                "answers": ["Power", "Defense", "Speed", "HP"],
                "correct": "Power"
            },
            {
                "question": "What can you earn by completing achievements?",
                "answers": ["Experience and rewards", "New classes", "New locations", "New weapons"],
                "correct": "Experience and rewards"
            },
            {
                "question": "What determines your maximum Energy in battles?",
                "answers": ["Level and training", "Equipment", "Class", "Guild rank"],
                "correct": "Level and training"
            },
            {
                "question": "How can you obtain rare equipment?",
                "answers": ["All of the above", "Defeating strong enemies", "Completing quests", "Purchasing from special shops"],
                "correct": "All of the above"
            },
            {
                "question": "Which training is focused on increasing your Energy capacity?",
                "answers": ["Energy Cultivation", "Cursed Energy Control", "Tactical Analysis", "Combat Training"],
                "correct": "Energy Cultivation"
            },
            {
                "question": "What feature allows players to work together?",
                "answers": ["Guilds", "Parties", "Alliances", "Clans"],
                "correct": "Guilds"
            },
            {
                "question": "Which attribute helps you avoid enemy attacks?",
                "answers": ["Speed", "Defense", "Power", "HP"],
                "correct": "Speed"
            }
        ]

        # Shuffle and select questions for this round
        selected_questions = random.sample(questions, min(question_count, len(questions)))

        for q_idx, question_data in enumerate(selected_questions):
            # Create a view with answer buttons
            quiz_view = View(timeout=15.0)  # 15 seconds to answer

            # Shuffle the answers
            answers = question_data["answers"].copy()
            random.shuffle(answers)

            # Store the correct answer
            self.correct_answer = question_data["correct"]

            # Add buttons for each answer
            for i, answer in enumerate(answers):
                is_correct = (answer == question_data["correct"])
                row = i // 2  # Two answers per row
                button = QuizButton(answer, is_correct, self, row=row)
                quiz_view.add_item(button)

            # Show the question
            self.round_complete = False
            await interaction.edit_original_response(
                content=f"Question {q_idx+1}/{len(selected_questions)}:\n\n{question_data['question']}",
                view=quiz_view
            )

            # Wait for answer or timeout
            try:
                await asyncio.wait_for(
                    quiz_view.wait(),
                    timeout=15.0
                )
            except asyncio.TimeoutError:
                # Time's up
                await interaction.edit_original_response(
                    content=f"⏱️ Time's up! The correct answer was: {question_data['correct']}\nScore: {self.score}/{self.max_score}",
                    view=None
                )
                self.round_complete = True

            # Short pause between questions
            if q_idx < len(selected_questions) - 1 and self.round_complete:
                await asyncio.sleep(1.5)

        # After all questions, process the results
        await self.process_training_results(interaction)

    async def run_precision_minigame(self, interaction: discord.Interaction):
        """Run the precision targeting minigame"""
        # Set up minigame parameters
        target_count = self.current_difficulty.get("targets", 4)
        
        # Grid size and time scale with difficulty
        if target_count <= 4:  # Basic
            grid_size = 3  # 3x3 grid
            time_per_target = 3.0  # +1 second for all difficulties
        elif target_count <= 6:  # Advanced
            grid_size = 4  # 4x4 grid
            time_per_target = 3.0  # +1 second
        else:  # Master
            grid_size = 4  # Keep 4x4 for Master (more targets, same space = harder)
            time_per_target = 3.0  # +1 second

        self.target_count = target_count
        self.hits = 0

        for target_idx in range(target_count):
            # Create a grid with one active target
            target_view = View(timeout=time_per_target)

            # Random position for the target
            target_x = random.randint(0, grid_size - 1)
            target_y = random.randint(0, grid_size - 1)

            # Add buttons to grid
            for y in range(grid_size):
                for x in range(grid_size):
                    is_active = (x == target_x and y == target_y)
                    button = MovingTargetButton(is_active, (y, x), self)
                    target_view.add_item(button)

            # Show the grid
            self.round_complete = False
            await interaction.edit_original_response(
                content=f"🎯 Target {target_idx+1}/{target_count} - Hit the red target!\nGrid: {grid_size}x{grid_size} | Time: {time_per_target}s",
                view=target_view
            )

            # Wait for click or timeout
            try:
                await asyncio.wait_for(
                    target_view.wait(),
                    timeout=time_per_target
                )
            except asyncio.TimeoutError:
                # Time's up
                await interaction.edit_original_response(
                    content=f"⏱️ Time's up! Hits: {self.hits}/{self.target_count}",
                    view=None
                )
                self.round_complete = True

            # Short pause between targets
            if target_idx < target_count - 1 and self.round_complete:
                await asyncio.sleep(1.0)

        # Convert hits to score for consistency with other minigames
        self.score = self.hits
        self.max_score = self.target_count

        # After all targets, process the results
        await self.process_training_results(interaction)

    async def process_training_results(self, interaction: discord.Interaction):
        """Process training results and award rewards"""
        # Calculate success percentage
        success_percent = (self.score / self.max_score) * 100 if self.max_score > 0 else 0

        # Calculate experience and attribute gains
        exp_multiplier = self.current_difficulty.get("exp_multiplier", 1.0)
        base_exp = self.training_data.get("base_exp", 20)

        # Apply score-based scaling
        score_multiplier = self.score / self.max_score if self.max_score > 0 else 0

        # Calculate final experience gain
        exp_gain = int(base_exp * exp_multiplier * score_multiplier)

        # Calculate attribute gains
        attribute_gain = self.current_difficulty.get("attribute_gain", 1) if success_percent >= 50 else 0

        # Get the primary and secondary attributes to improve
        primary_attr = self.training_data.get("primary_attribute")
        secondary_attr = self.training_data.get("secondary_attribute")

        # Special handling for energy attribute if present
        energy_gain = 0
        if primary_attr == "energy" and success_percent >= 50:
            energy_gain = self.current_difficulty.get("energy_gain", 5)

        # Apply the gains
        levelup_threshold = 100 * self.player_data.class_level
        old_level = self.player_data.class_level

        # Update XP
        self.player_data.class_exp += exp_gain

        # Check for level up
        leveled_up = False
        while self.player_data.class_exp >= levelup_threshold:
            self.player_data.class_exp -= levelup_threshold
            self.player_data.class_level += 1
            self.player_data.skill_points += 3
            levelup_threshold = 100 * self.player_data.class_level
            leveled_up = True

        # Apply attribute gains if applicable
        if attribute_gain > 0:
            # Primary attribute
            if primary_attr in self.player_data.allocated_stats:
                self.player_data.allocated_stats[primary_attr] += attribute_gain
            elif primary_attr == "energy":
                self.player_data.energy_training += energy_gain

            # Secondary attribute (half the gain)
            if secondary_attr in self.player_data.allocated_stats:
                self.player_data.allocated_stats[secondary_attr] += max(1, attribute_gain // 2)

        # Check for special rewards for perfect score
        special_rewards = None
        if success_percent == 100 and "special_rewards" in self.training_data and "perfect_score" in self.training_data["special_rewards"]:
            special_rewards = self.training_data["special_rewards"]["perfect_score"]

            # Apply gold reward if present (previously cursed_energy)
            if "cursed_energy" in special_rewards:
                # Convert cursed_energy rewards to gold
                gold_reward = special_rewards["cursed_energy"]
                self.player_data.gold += gold_reward

            # Apply effect if present
            if "effect" in special_rewards:
                effect = special_rewards["effect"]

                # Initialize effects dict if not present
                if not hasattr(self.player_data, "effects"):
                    self.player_data.effects = {}

                # Add the effect with expiration time
                now = datetime.datetime.now()
                expiration = now + datetime.timedelta(hours=effect["duration"])

                self.player_data.effects[effect["name"]] = {
                    "boost_type": effect["boost_type"],
                    "boost_amount": effect["boost_amount"],
                    "expires": expiration.isoformat()
                }

        # Set training cooldown
        cooldown_hours = self.training_data.get("cooldown", 2)
        now = datetime.datetime.now()
        cooldown_until = now + datetime.timedelta(hours=cooldown_hours)

        # Initialize training cooldowns if not present
        if not hasattr(self.player_data, "training_cooldowns"):
            self.player_data.training_cooldowns = {}

        self.player_data.training_cooldowns[self.training_type] = cooldown_until.isoformat()

        # Track training completion for achievements
        if not hasattr(self.player_data, "advanced_training_completed"):
            self.player_data.advanced_training_completed = 0
        self.player_data.advanced_training_completed += 1

        # Update quest progress for training completion
        from achievements import QuestManager
        quest_manager = QuestManager(self.data_manager)
        
        # Update daily training quests
        completed_daily_quests = quest_manager.update_quest_progress(
            self.player_data, "daily_training")
        
        # Update weekly training quests
        completed_weekly_quests = quest_manager.update_quest_progress(
            self.player_data, "weekly_training")
        
        # Update long-term training quests
        completed_longterm_quests = quest_manager.update_quest_progress(
            self.player_data, "total_training")

        # Check for achievements
        new_achievements = self.data_manager.check_player_achievements(self.player_data)

        # Save player data
        self.data_manager.save_data()

        # Create results embed
        embed = discord.Embed(
            title=f"🏋️ {self.training_type} Results",
            description=f"You completed the training with {success_percent:.1f}% success!",
            color=discord.Color.green() if success_percent >= 70 else (
                discord.Color.gold() if success_percent >= 40 else discord.Color.red()
            )
        )

        # Add score
        embed.add_field(
            name="Score",
            value=f"{self.score}/{self.max_score}",
            inline=True
        )

        # Add difficulty
        embed.add_field(
            name="Difficulty",
            value=self.current_difficulty["name"],
            inline=True
        )

        # Add attribute gains
        gains_text = ""
        if attribute_gain > 0:
            if primary_attr == "energy":
                gains_text += f"**Energy Capacity:** +{energy_gain} ⚡\n"
            else:
                gains_text += f"**{primary_attr.title()}:** +{attribute_gain}\n"

            if secondary_attr in self.player_data.allocated_stats:
                secondary_gain = max(1, attribute_gain // 2)
                gains_text += f"**{secondary_attr.title()}:** +{secondary_gain}\n"
        else:
            gains_text = "None (Score too low)"

        embed.add_field(
            name="Attribute Gains",
            value=gains_text,
            inline=False
        )

        # Add special rewards if any
        if special_rewards:
            rewards_text = ""
            if "cursed_energy" in special_rewards:
                rewards_text += f"**Gold:** +{special_rewards['cursed_energy']} 💰\n"

            if "effect" in special_rewards:
                effect = special_rewards["effect"]
                rewards_text += f"**Effect:** {effect['name']} (Lasts {effect['duration']} hours)\n"
                rewards_text += f"  • {effect['boost_type'].replace('_', ' ').title()} +{effect['boost_amount']}\n"

            embed.add_field(
                name="Perfect Score Rewards",
                value=rewards_text,
                inline=False
            )

        # Add experience
        embed.add_field(
            name="Experience",
            value=f"**EXP Gained:** {exp_gain}",
            inline=True
        )

        # Add level up notification if applicable
        if leveled_up:
            embed.add_field(
                name="Level Up!",
                value=f"🆙 You reached Level {self.player_data.class_level}!\n"
                      f"You gained 3 skill points! Use !skills to allocate them.",
                inline=False
            )

        # Add cooldown info
        embed.add_field(
            name="Cooldown",
            value=f"This training will be available again in {cooldown_hours} hours.",
            inline=False
        )

        # Show results
        await interaction.edit_original_response(
            content=None,
            embed=embed,
            view=None
        )

        # Stop the view
        self.stop()

    async def cancel_callback(self, interaction: discord.Interaction):
        """Handle cancellation"""
        await interaction.response.edit_message(
            content="❌ Training cancelled.",
            view=None
        )
        self.stop()

class AdvancedTrainingView(View):
    def __init__(self, player_data: PlayerData, data_manager: DataManager):
        super().__init__(timeout=60)
        self.player_data = player_data
        self.data_manager = data_manager

        # Get available training options
        self.training_options = self.get_available_training()

        # Create select menu for training options
        self.training_select = Select(
            placeholder="Select a training exercise",
            min_values=1,
            max_values=1
        )

        # Add options to select menu
        for name, data in self.training_options.items():
            # Check if on cooldown
            on_cooldown = False
            cooldown_text = ""

            if hasattr(self.player_data, "training_cooldowns") and name in self.player_data.training_cooldowns:
                try:
                    cooldown_time = datetime.datetime.fromisoformat(self.player_data.training_cooldowns[name])
                    now = datetime.datetime.now()

                    if cooldown_time > now:
                        on_cooldown = True
                        time_left = cooldown_time - now
                        hours = time_left.seconds // 3600
                        minutes = (time_left.seconds % 3600) // 60
                        cooldown_text = f" (Cooldown: {hours}h {minutes}m)"
                except (ValueError, TypeError):
                    # Invalid datetime format, ignore cooldown
                    pass

            # Add option with emoji and description
            self.training_select.add_option(
                label=f"{name}{cooldown_text}",
                emoji=data.get("emoji", "🏋️"),
                description=data.get("description", "")[:100],  # Limit description length
                value=name,
                default=False
            )

            # Note: The disabled parameter isn't supported in this version of discord.py
            # We'll handle disabled items another way when processing selections

        # Add callback for training selection
        self.training_select.callback = self.training_select_callback
        self.add_item(self.training_select)

        # Add cancel button
        cancel_button = Button(label="Cancel", style=discord.ButtonStyle.secondary)
        cancel_button.callback = self.cancel_callback
        self.add_item(cancel_button)

    def get_available_training(self) -> Dict[str, Dict[str, Any]]:
        """Get all training options available to the player"""
        available_training = {}

        # Add all standard training minigames
        for name, data in TRAINING_MINIGAMES.items():
            # Check for unlock requirements
            if "unlock_requirements" in data:
                reqs = data["unlock_requirements"]

                # Check class level requirements
                if "class_level" in reqs and self.player_data.class_level < reqs["class_level"]:
                    continue

            # Add to available options
            available_training[name] = data

        # Add class-specific training if appropriate
        if self.player_data.class_name in CLASS_TRAINING:
            class_training = CLASS_TRAINING[self.player_data.class_name]

            for name, data in class_training.items():
                # Add debug info to training description
                if "description" in data:
                    data["description"] = f"{data['description']} (Level req: {data.get('level_req', 1)})"

                # Check level requirements - make sure level 5 trainings are available at level 4
                if "level_req" in data and self.player_data.class_level < data["level_req"] - 1:
                    continue

                # Add to available options
                available_training[name] = data

        return available_training

    async def training_select_callback(self, interaction: discord.Interaction):
        """Handle training selection"""
        # Get selected training with error handling
        try:
            if not interaction.data or "values" not in interaction.data:
                await interaction.response.send_message("Error: No training selected.", ephemeral=True)
                return
            selected_training = interaction.data["values"][0]
            training_data = self.training_options[selected_training]
        except (KeyError, IndexError) as e:
            await interaction.response.send_message(f"Error selecting training: {e}", ephemeral=True)
            return

        # Check cooldown before allowing training
        if hasattr(self.player_data, "training_cooldowns") and selected_training in self.player_data.training_cooldowns:
            try:
                cooldown_time = datetime.datetime.fromisoformat(self.player_data.training_cooldowns[selected_training])
                now = datetime.datetime.now()

                if cooldown_time > now:
                    # Still on cooldown
                    time_left = cooldown_time - now
                    hours = time_left.seconds // 3600
                    minutes = (time_left.seconds % 3600) // 60
                    await interaction.response.send_message(
                        f"❌ {selected_training} is still on cooldown! Wait {hours}h {minutes}m before training again.",
                        ephemeral=True
                    )
                    return
            except (ValueError, TypeError):
                # Invalid datetime format, allow training
                pass

        # Create minigame view
        training_view = TrainingMinigameView(
            self.player_data,
            selected_training,
            training_data,
            self.data_manager
        )

        # Create training embed
        embed = discord.Embed(
            title=f"🏋️ {selected_training}",
            description=training_data.get("description", "Improve your skills through training."),
            color=discord.Color.blue()
        )

        # Add attribute info
        primary = training_data.get("primary_attribute", "").title()
        secondary = training_data.get("secondary_attribute", "").title()

        embed.add_field(
            name="Attributes Trained",
            value=f"Primary: **{primary}**\nSecondary: **{secondary}**",
            inline=True
        )

        # Add difficulty info
        difficulties = training_data.get("difficulty_levels", [])
        difficulty_text = "\n".join([f"• **{d['name']}**: {d.get('exp_multiplier', 1.0)}x XP" for d in difficulties])

        embed.add_field(
            name="Difficulty Levels",
            value=difficulty_text or "None available",
            inline=True
        )

        # Add player stats
        embed.add_field(
            name="Your Stats",
            value=f"**Level:** {self.player_data.class_level}\n" +
                  f"**Class:** {self.player_data.class_name}",
            inline=True
        )

        # Send message with embed and training view
        await interaction.response.send_message(
            embed=embed,
            view=training_view
        )

        # Stop this view
        self.stop()

    async def cancel_callback(self, interaction: discord.Interaction):
        """Handle cancellation"""
        await interaction.response.edit_message(
            content="❌ Training selection cancelled.",
            view=None
        )
        self.stop()

async def advanced_training_command(ctx, data_manager: DataManager):
    """Participate in advanced training exercises"""
    player_data = data_manager.get_player(ctx.author.id)

    # Check if player has started
    if not player_data.class_name:
        await ctx.send("❌ You haven't started your adventure yet! Use `!start` to choose a class.")
        return

    # Create training view
    view = AdvancedTrainingView(player_data, data_manager)

    # Create embed
    embed = discord.Embed(
        title="🏋️ Advanced Training",
        description="Select a training exercise to improve your skills. Each training focuses on different attributes and provides experience points.",
        color=discord.Color.blue()
    )

    # Add current stats
    from utils import GAME_CLASSES
    player_stats = player_data.get_stats(GAME_CLASSES)

    embed.add_field(
        name="📊 Current Stats",
        value=f"**HP:** {player_stats['hp']} ❤️\n"
              f"**Power:** {player_stats['power']} ⚔️\n"
              f"**Defense:** {player_stats['defense']} 🛡️\n"
              f"**Speed:** {player_stats['speed']} 💨",
        inline=True
    )

    embed.add_field(
        name="🧠 Class Progress",
        value=f"**Level:** {player_data.class_level}\n"
              f"**EXP:** {player_data.class_exp}/{100 * player_data.class_level}\n"
              f"**Class:** {player_data.class_name}",
        inline=True
    )

    # Send message with embed and view
    await ctx.send(embed=embed, view=view)