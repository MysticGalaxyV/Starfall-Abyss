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
                {"name": "Basic", "exp_multiplier": 1.0, "time_window": 3.0, "attribute_gain": 1},
                {"name": "Advanced", "exp_multiplier": 1.5, "time_window": 2.0, "attribute_gain": 2},
                {"name": "Master", "exp_multiplier": 2.5, "time_window": 1.0, "attribute_gain": 3}
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
                {"name": "Basic", "exp_multiplier": 1.0, "time_window": 2.5, "attribute_gain": 1},
                {"name": "Advanced", "exp_multiplier": 1.5, "time_window": 1.5, "attribute_gain": 2},
                {"name": "Master", "exp_multiplier": 2.5, "time_window": 0.8, "attribute_gain": 3}
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
                {"name": "Advanced", "exp_multiplier": 1.5, "target_zone": 0.2, "attribute_gain": 2},
                {"name": "Master", "exp_multiplier": 2.5, "target_zone": 0.1, "attribute_gain": 3}
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
                {"name": "Basic", "exp_multiplier": 1.0, "targets": 3, "attribute_gain": 1, "energy_gain": 5},
                {"name": "Advanced", "exp_multiplier": 1.5, "targets": 5, "attribute_gain": 2, "energy_gain": 10},
                {"name": "Master", "exp_multiplier": 2.5, "targets": 7, "attribute_gain": 3, "energy_gain": 15}
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
                "emoji": "👻"
            },
            "Assassination Techniques": {
                "description": "Hone your skills for deadly precision strikes",
                "primary_attribute": "power",
                "secondary_attribute": "speed",
                "base_exp": 30,
                "cooldown": 4,  # hours
                "level_req": 10,
                "emoji": "🗡️"
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
                "emoji": "💚"
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
                "emoji": "🌐"
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
                "emoji": "🐺"
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
                "emoji": "♾️"
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
            self.speed = 0.05  # How fast the indicator moves per step
            self.task = None
            self.stopped = False

            # Add the stop button
            stop_btn = Button(label="STOP", style=discord.ButtonStyle.danger)
            stop_btn.callback = self.stop_callback
            self.add_item(stop_btn)

        async def start(self, interaction: discord.Interaction):
            # Initial render
            self.position = 0.0
            await interaction.response.send_message(
                content=self.render_bar(),
                view=self
            )

            # Start the animation
            self.task = asyncio.create_task(self.animate(interaction))

        def render_bar(self) -> str:
            """Render a text-based timing bar"""
            bar_length = 20
            target_start = int((0.5 - self.target_zone/2) * bar_length)
            target_end = int((0.5 + self.target_zone/2) * bar_length)

            # Create the bar with target zone
            bar = ["□"] * bar_length
            for i in range(target_start, target_end+1):
                bar[i] = "■"

            # Add the indicator
            indicator_pos = min(bar_length-1, int(self.position * bar_length))
            bar[indicator_pos] = "🔴"

            return f"⏱️ Stop the indicator in the target zone!\n\n|{''.join(bar)}|"

        async def animate(self, interaction: discord.Interaction):
            """Animate the timing bar"""
            try:
                while not self.stopped:
                    # Move the indicator
                    self.position += self.direction * self.speed

                    # Bounce at the edges
                    if self.position >= 1.0:
                        self.position = 1.0
                        self.direction = -1
                    elif self.position <= 0.0:
                        self.position = 0.0
                        self.direction = 1

                    # Update the message
                    await interaction.edit_original_response(content=self.render_bar())

                    # Small delay between frames
                    await asyncio.sleep(0.1)
            except Exception as e:
                print(f"Animation error: {e}")

        async def stop_callback(self, interaction: discord.Interaction):
            """Handle stopping the timing bar"""
            self.stopped = True
            if self.task:
                self.task.cancel()

            # Calculate if successful (indicator in target zone)
            center = 0.5
            half_target = self.target_zone / 2
            in_target = (center - half_target) <= self.position <= (center + half_target)

            if in_target:
                self.parent_view.score += 1
                await interaction.response.edit_message(
                    content=f"🎯 Perfect timing! Score: {self.parent_view.score}/{self.parent_view.max_score}",
                    view=None
                )
            else:
                await interaction.response.edit_message(
                    content=f"❌ Missed the target zone! Score: {self.parent_view.score}/{self.parent_view.max_score}",
                    view=None
                )

            self.parent_view.round_complete = True
            self.parent_view.stop()

    # QUIZ MINIGAME - Answer RPG-themed questions 
    class QuizButton(Button):
        def __init__(self, answer: str, is_correct: bool, parent_view, row: int = 0):
            super().__init__(
                label=answer,
                style=discord.ButtonStyle.secondary,
                row=row
            )

            self.is_correct = is_correct
            self.parent_view = parent_view

        async def callback(self, interaction: discord.Interaction):
            if self.is_correct:
                self.parent_view.score += 1
                await interaction.response.edit_message(
                    content=f"✅ Correct! Score: {self.parent_view.score}/{self.parent_view.max_score}",
                    view=None
                )
            else:
                await interaction.response.edit_message(
                    content=f"❌ Incorrect! The correct answer was: {self.parent_view.current_correct_answer}\nScore: {self.parent_view.score}/{self.parent_view.max_score}",
                    view=None
                )

            self.parent_view.round_complete = True
            self.parent_view.stop()

    # PRECISION MINIGAME - Hit moving targets to enhance precision
    class MovingTargetButton(Button):
        def __init__(self, is_active: bool, position: Tuple[int, int], parent_view):
            row = position[0]
            # Default button style
            super().__init__(
                label="○" if is_active else "·",
                style=discord.ButtonStyle.secondary if is_active else discord.ButtonStyle.gray,
                row=row
            )

            self.is_active = is_active
            self.parent_view = parent_view
            self.position = position

        async def callback(self, interaction: discord.Interaction):
            if self.is_active:
                self.parent_view.score += 1
                await interaction.response.edit_message(
                    content=f"🎯 Precise hit! Score: {self.parent_view.score}/{self.parent_view.max_score}",
                    view=None
                )
            else:
                await interaction.response.edit_message(
                    content=f"❌ Missed the active target! Score: {self.parent_view.score}/{self.parent_view.max_score}",
                    view=None
                )

            self.parent_view.round_complete = True
            self.parent_view.stop()

    class TrainingMinigameView(View):
        def __init__(self, player_data: PlayerData, training_type: str, training_data: Dict[str, Any], data_manager: DataManager):
            super().__init__(timeout=60)
            self.player_data = player_data
            self.training_type = training_type
            self.training_data = training_data
            self.data_manager = data_manager
            self.result = None
            self.score = 0
            self.max_score = 5
            self.current_step = 0
            self.round_complete = False
            # Default to the 'Basic' difficulty level
            self.selected_difficulty = "Basic"
            # Select the difficulty data
            self.difficulty = next((d for d in self.training_data.get("difficulty_levels", []) 
                              if d["name"] == self.selected_difficulty), {})

            # Add start button
            start_btn = Button(
                label="Start Training",
                style=discord.ButtonStyle.green,
                emoji=training_data["emoji"]
            )
            start_btn.callback = self.start_callback
            self.add_item(start_btn)

            # Add cancel button
            cancel_btn = Button(
                label="Cancel",
                style=discord.ButtonStyle.red,
                emoji="❌"
            )
            cancel_btn.callback = self.cancel_callback
            self.add_item(cancel_btn)

        async def start_callback(self, interaction: discord.Interaction):
            """Start the training minigame"""
            # Clear buttons
            self.clear_items()

            # Get minigame type
            minigame_type = self.training_data.get("minigame_type", "reaction")

            # Get appropriate emoji and message
            emoji_map = {
                "reaction": "🎯",
                "sequence": "🔢",
                "timing": "⏱️",
                "quiz": "🧠",
                "precision": "🎯"
            }
            emoji = emoji_map.get(minigame_type, "🏋️")

            # Send instructions based on minigame type
            instructions = {
                "reaction": "Click the highlighted target as quickly as possible!",
                "sequence": "Memorize the sequence and repeat it in the correct order!",
                "timing": "Stop the moving indicator when it's in the target zone!",
                "quiz": "Answer the combat strategy questions correctly!",
                "precision": "Hit the active target to improve your precision!"
            }

            instruction_text = instructions.get(minigame_type, "Complete the training challenges!")

            await interaction.response.edit_message(
                content=f"{emoji} **{self.training_type} Training**\n\n"
                       f"{self.training_data['description']}\n\n"
                       f"{instruction_text}",
                view=None
            )

            await asyncio.sleep(2)

            # Select and run the appropriate minigame type
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
                # Fallback to reaction game if unknown type
                await self.run_reaction_minigame(interaction)

        async def run_reaction_minigame(self, interaction: discord.Interaction):
            """Run the reaction speed minigame"""
            for i in range(self.max_score):
                self.current_step = i + 1
                self.round_complete = False

                # Create a round view for this step
                round_view = View(timeout=5)

                # Add target buttons in random positions
                positions = list(range(3*3))  # 3x3 grid
                random.shuffle(positions)

                # Add target button and dummy buttons
                for j in range(9):
                    is_target = (j == positions[0])
                    button = TargetButton(is_target=is_target, parent_view=self, row=j//3)
                    round_view.add_item(button)

                # Show the round view
                try:
                    round_msg = await interaction.followup.send(
                        content=f"Round {self.current_step}/{self.max_score} - Click the target!",
                        view=round_view
                    )

                    # Get time window from difficulty
                    time_window = self.difficulty.get("time_window", 5.0)

                    # Wait for this step to complete
                    await asyncio.sleep(time_window)

                    # If the round was not completed, count it as a miss
                    if not self.round_complete:
                        await interaction.followup.send(
                            content=f"⏱️ Time's up! Score: {self.score}/{self.max_score}"
                        )
                except Exception as e:
                    print(f"Error in reaction minigame round: {e}")

                # Short pause between rounds
                await asyncio.sleep(1)

        async def run_sequence_minigame(self, interaction: discord.Interaction):
            """Run the sequence memorization minigame"""
            # Possible symbols for sequence
            symbols = ["🔴", "🔵", "🟢", "🟡", "⚪", "🟣", "🟠", "⚫"]

            for i in range(self.max_score):
                self.current_step = i + 1
                self.round_complete = False

                # Get sequence length from difficulty
                seq_length = self.difficulty.get("sequence_length", 3)

                # Generate random sequence
                sequence = [random.randint(0, len(symbols)-1) for _ in range(seq_length)]
                self.current_sequence = sequence
                self.current_sequence_position = 0
                self.expected_next = sequence[0]

                # First, show the sequence to memorize
                sequence_text = " → ".join([symbols[s] for s in sequence])
                await interaction.followup.send(
                    content=f"Round {self.current_step}/{self.max_score} - Memorize this sequence!\n{sequence_text}"
                )

                # Wait for player to memorize
                memorize_time = min(5, 1 + seq_length)
                await asyncio.sleep(memorize_time)

                # Now show the buttons to reproduce the sequence
                sequence_view = View(timeout=10)

                # Add buttons for each symbol
                for j, symbol in enumerate(symbols):
                    button = SequenceButton(symbol=symbol, order=j, parent_view=self, row=j//4)
                    sequence_view.add_item(button)

                try:
                    await interaction.followup.send(
                        content=f"Now reproduce the sequence in order!",
                        view=sequence_view
                    )

                    # Wait for sequence completion or timeout
                    await asyncio.sleep(10)

                    if not self.round_complete:
                        await interaction.followup.send(
                            content=f"⏱️ Time's up! Score: {self.score}/{self.max_score}"
                        )
                except Exception as e:
                    print(f"Error in sequence minigame round: {e}")

                # Short pause between rounds
                await asyncio.sleep(1)

        async def run_timing_minigame(self, interaction: discord.Interaction):
            """Run the timing bar minigame"""
            for i in range(self.max_score):
                self.current_step = i + 1
                self.round_complete = False

                # Get target zone size from difficulty
                target_zone = self.difficulty.get("target_zone", 0.3)

                # Create and start timing bar
                timing_bar = TimingBar(parent_view=self, target_zone=target_zone)

                try:
                    await timing_bar.start(interaction)

                    # Wait for completion or timeout
                    await asyncio.sleep(10)

                    if not self.round_complete:
                        await interaction.followup.send(
                            content=f"⏱️ Time's up! Score: {self.score}/{self.max_score}"
                        )
                except Exception as e:
                    print(f"Error in timing minigame round: {e}")

                # Short pause between rounds
                await asyncio.sleep(1)

        async def run_quiz_minigame(self, interaction: discord.Interaction):
            """Run the knowledge quiz minigame"""
            # RPG-themed quiz questions and answers
            quiz_questions = [
                {
                    "question": "Which is the most effective strategy against a heavily armored opponent?",
                    "answers": ["Use speed to your advantage", "Match strength with strength", "Aim for weak points", "Retreat and heal"],
                    "correct": 2
                },
                {
                    "question": "What should you prioritize in a long battle?",
                    "answers": ["Maximum damage output", "Energy conservation", "Healing items", "Defensive stance"],
                    "correct": 1
                },
                {
                    "question": "When facing multiple opponents, what's the best approach?",
                    "answers": ["Focus on the strongest enemy", "Divide and conquer", "Area attacks", "Defensive position"],
                    "correct": 2
                },
                {
                    "question": "What's most important for a balanced combat style?",
                    "answers": ["Power techniques", "Defensive techniques", "Speed techniques", "Balance of all attributes"],
                    "correct": 3
                },
                {
                    "question": "Which resource is most critical to manage in extended combat?",
                    "answers": ["Health points", "Energy", "Position", "Item usage"],
                    "correct": 1
                },
                {
                    "question": "What's the best counter to an agile opponent?",
                    "answers": ["Match their speed", "Use area attacks", "Predict movement patterns", "Heavy armor"],
                    "correct": 2
                },
                {
                    "question": "When should you use your strongest ability?",
                    "answers": ["At the start of battle", "When your HP is low", "When the enemy is vulnerable", "Save it for emergencies"],
                    "correct": 2
                }
            ]

            # Shuffle questions
            random.shuffle(quiz_questions)

            # Get number of questions from difficulty
            num_questions = min(self.max_score, self.difficulty.get("questions", 3))
            selected_questions = quiz_questions[:num_questions]

            for i, question_data in enumerate(selected_questions):
                self.current_step = i + 1
                self.round_complete = False

                question = question_data["question"]
                answers = question_data["answers"]
                correct_index = question_data["correct"]

                # Save correct answer for feedback
                self.current_correct_answer = answers[correct_index]

                # Create quiz view
                quiz_view = View(timeout=15)

                # Add answer buttons
                for j, answer in enumerate(answers):
                    button = QuizButton(answer=answer, is_correct=(j == correct_index), parent_view=self, row=j)
                    quiz_view.add_item(button)

                try:
                    await interaction.followup.send(
                        content=f"Question {self.current_step}/{num_questions}:\n**{question}**",
                        view=quiz_view
                    )

                    # Wait for answer or timeout
                    await asyncio.sleep(15)

                    if not self.round_complete:
                        await interaction.followup.send(
                            content=f"⏱️ Time's up! The correct answer was: {self.current_correct_answer}\nScore: {self.score}/{self.max_score}"
                        )
                except Exception as e:
                    print(f"Error in quiz minigame round: {e}")

                # Short pause between rounds
                await asyncio.sleep(1)

        async def run_precision_minigame(self, interaction: discord.Interaction):
            """Run the precision targeting minigame"""
            # Get number of targets from difficulty
            num_targets = self.difficulty.get("targets", 5)
            self.max_score = num_targets

            for i in range(num_targets):
                self.current_step = i + 1
                self.round_complete = False

                # Create a 3x3 grid view
                grid_view = View(timeout=5)

                # Randomly position the active target
                active_row = random.randint(0, 2)
                active_col = random.randint(0, 2)

                # Add buttons to the grid
                for row in range(3):
                    for col in range(3):
                        is_active = (row == active_row and col == active_col)
                        button = MovingTargetButton(
                            is_active=is_active, 
                            position=(row, col),
                            parent_view=self
                        )
                        grid_view.add_item(button)

                try:
                    await interaction.followup.send(
                        content=f"Target {self.current_step}/{num_targets} - Hit the active target (○)!",
                        view=grid_view
                    )

                    # Wait for this step to complete
                    await asyncio.sleep(5)

                    if not self.round_complete:
                        await interaction.followup.send(
                            content=f"⏱️ Time's up! Score: {self.score}/{self.max_score}"
                        )
                except Exception as e:
                    print(f"Error in precision minigame round: {e}")

                # Short pause between rounds
                await asyncio.sleep(1)

            # Calculate training results
            performance = self.score / self.max_score

            # Base attribute gains
            primary_attr = self.training_data["primary_attribute"]
            secondary_attr = self.training_data["secondary_attribute"]

            # Calculate attribute gains based on performance
            primary_gain = max(1, int(3 * performance))  # 0-3 points
            secondary_gain = max(0, int(2 * performance))  # 0-2 points

            # Handle battle energy training differently - this increases max battle energy capacity
            energy_gain = 0
            if primary_attr == "energy":
                # Get the selected difficulty level from the training data
                difficulty_level = next((d for d in self.training_data["difficulty_levels"] 
                                  if d["name"] == self.selected_difficulty), None)
                if difficulty_level and "energy_gain" in difficulty_level:
                    # Calculate battle energy gain based on performance and difficulty level
                    energy_gain = max(1, int(difficulty_level["energy_gain"] * performance))

            # Apply different increases for HP
            if primary_attr == "hp":
                primary_gain *= 5  # 5x multiplier for HP
            if secondary_attr == "hp":
                secondary_gain *= 5  # 5x multiplier for HP

            # Calculate exp gain based on performance
            exp_gain = int(self.training_data["base_exp"] * performance)

            # Initialize allocated stats if not exists
            if not hasattr(self.player_data, "allocated_stats") or not self.player_data.allocated_stats:
                self.player_data.allocated_stats = {"power": 0, "defense": 0, "speed": 0, "hp": 0}

            # Apply attribute gains
            if primary_attr == "energy" and energy_gain > 0:
                # Increase the player's max energy capacity through energy_training field
                if not hasattr(self.player_data, "energy_training"):
                    self.player_data.energy_training = 0
                self.player_data.energy_training += energy_gain
                # Also update battle energy to reflect the new maximum
                max_energy = self.player_data.get_max_battle_energy()
                self.player_data.battle_energy = min(max_energy, self.player_data.battle_energy + energy_gain)

                secondary_attr_to_apply = secondary_attr
            else:
                # Normal attribute increases
                self.player_data.allocated_stats[primary_attr] += primary_gain
                secondary_attr_to_apply = secondary_attr

            # Always apply secondary attribute gain
            self.player_data.allocated_stats[secondary_attr_to_apply] += secondary_gain

            # Apply exp gain
            leveled_up = self.player_data.add_exp(exp_gain)

            # Update quest progress for training
            from achievements import QuestManager
            quest_manager = QuestManager(self.data_manager)

            # Update daily training quests
            completed_daily_quests = quest_manager.update_quest_progress(self.player_data, "daily_training")

            # Update weekly advanced training quests
            completed_weekly_quests = quest_manager.update_quest_progress(self.player_data, "weekly_advanced_training")

            # Update training cooldowns
            if not hasattr(self.player_data, "training_cooldowns"):
                self.player_data.training_cooldowns = {}

            # Set cooldown
            now = datetime.datetime.now()
            self.player_data.training_cooldowns[self.training_type] = (now + datetime.timedelta(hours=self.training_data["cooldown"])).isoformat()

            # Update quest progress
            from achievements import QuestManager
            quest_manager = QuestManager(self.data_manager)

            # Update daily training quests
            completed_quests = quest_manager.update_quest_progress(self.player_data, "daily_training")
            for quest in completed_quests:
                quest_manager.award_quest_rewards(self.player_data, quest)

            # Update weekly training quests
            completed_weekly = quest_manager.update_quest_progress(self.player_data, "weekly_training")
            for quest in completed_weekly:
                quest_manager.award_quest_rewards(self.player_data, quest)

            # Save player data
            self.data_manager.save_data()

            # Create results embed
            embed = discord.Embed(
                title=f"🏋️ {self.training_type} Training Complete!",
                description=f"Score: {self.score}/{self.max_score} ({int(performance * 100)}%)",
                color=discord.Color.green() if performance >= 0.6 else discord.Color.gold() if performance >= 0.3 else discord.Color.red()
            )

            # Add energy gain info if this was energy training
            if primary_attr == "energy" and energy_gain > 0:
                embed.add_field(
                    name="⚡ Energy Capacity Increased!",
                    value=f"Your maximum battle energy capacity has increased by **{energy_gain}** points!\n"
                          f"New maximum battle energy: **{self.player_data.get_max_battle_energy()}**",
                    inline=False
                )

            # Add attribute gains
            embed.add_field(
                name="Attribute Gains",
                value=f"**{primary_attr.title()}:** +{primary_gain}\n"
                      f"**{secondary_attr.title()}:** +{secondary_gain}",
                inline=True
            )

            # Add exp gain
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
                value=f"This training will be available again in {self.training_data['cooldown']} hours.",
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
                            time_remaining = cooldown_time - now
                            hours, remainder = divmod(time_remaining.seconds, 3600)
                            minutes, _ = divmod(remainder, 60)

                            on_cooldown = True
                            cooldown_text = f" (Cooldown: {hours}h {minutes}m)"
                    except (ValueError, TypeError):
                        pass

                description = data["description"]
                if on_cooldown:
                    description = f"ON COOLDOWN{cooldown_text}"

                self.training_select.add_option(
                    label=name,
                    description=description[:100],  # Discord limit
                    value=name,
                    emoji=data["emoji"],
                    default=False
                )

            # Set callback
            self.training_select.callback = self.training_select_callback

            # Add select menu
            self.add_item(self.training_select)

            # Add cancel button
            cancel_btn = Button(
                label="Cancel",
                style=discord.ButtonStyle.red,
                emoji="❌"
            )
            cancel_btn.callback = self.cancel_callback
            self.add_item(cancel_btn)

        def get_available_training(self) -> Dict[str, Dict[str, Any]]:
            """Get all training options available to the player"""
            result = {}

            # Add basic training options for everyone
            for name, data in TRAINING_MINIGAMES.items():
                result[name] = data

            # Add class-specific training if available
            if self.player_data.class_name in CLASS_TRAINING:
                class_training = CLASS_TRAINING[self.player_data.class_name]

                for name, data in class_training.items():
                    # Check level requirement
                    if self.player_data.class_level >= data.get("level_req", 0):
                        result[name] = data

            return result

        async def training_select_callback(self, interaction: discord.Interaction):
            """Handle training selection"""
            training_name = self.training_select.values[0]
            training_data = self.training_options[training_name]

            # Check cooldown
            if hasattr(self.player_data, "training_cooldowns") and training_name in self.player_data.training_cooldowns:
                try:
                    cooldown_time = datetime.datetime.fromisoformat(self.player_data.training_cooldowns[training_name])
                    now = datetime.datetime.now()

                    if cooldown_time > now:
                        time_remaining = cooldown_time - now
                        hours, remainder = divmod(time_remaining.seconds, 3600)
                        minutes, _ = divmod(remainder, 60)

                        await interaction.response.send_message(
                            f"⏳ This training is still on cooldown for {hours}h {minutes}m.",
                            ephemeral=True
                        )
                        return
                except (ValueError, TypeError):
                    pass

            # Create training minigame view
            training_view = TrainingMinigameView(self.player_data, training_name, training_data, self.data_manager)

            # Create training embed
            embed = discord.Embed(
                title=f"🏋️ {training_name} Training",
                description=training_data["description"],
                color=discord.Color.blue()
            )

            embed.add_field(
                name="Training Focus",
                value=f"Primary: **{training_data['primary_attribute'].title()}**\n"
                      f"Secondary: **{training_data['secondary_attribute'].title()}**",
                inline=True
            )

            embed.add_field(
                name="Potential Rewards",
                value=f"Base EXP: **{training_data['base_exp']}**\n"
                      f"Attribute Points: **1-3** (based on performance)",
                inline=True
            )

            embed.add_field(
                name="Cooldown",
                value=f"This training has a cooldown of **{training_data['cooldown']} hours** after completion.",
                inline=False
            )

            # Show training view
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

        # Add level info
        embed.add_field(
            name="📈 Level Information",
            value=f"**Level:** {player_data.class_level}\n"
                  f"**EXP:** {player_data.class_exp}/{int(100 * (player_data.class_level ** 1.5))}\n"
                  f"**Class:** {player_data.class_name}",
            inline=True
        )

        # Send message with embed and view
        await ctx.send(embed=embed, view=view)import discord
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
            {"name": "Basic", "exp_multiplier": 1.0, "time_window": 3.0, "attribute_gain": 1},
            {"name": "Advanced", "exp_multiplier": 1.5, "time_window": 2.0, "attribute_gain": 2},
            {"name": "Master", "exp_multiplier": 2.5, "time_window": 1.0, "attribute_gain": 3}
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
            {"name": "Basic", "exp_multiplier": 1.0, "time_window": 2.5, "attribute_gain": 1},
            {"name": "Advanced", "exp_multiplier": 1.5, "time_window": 1.5, "attribute_gain": 2},
            {"name": "Master", "exp_multiplier": 2.5, "time_window": 0.8, "attribute_gain": 3}
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
            {"name": "Advanced", "exp_multiplier": 1.5, "target_zone": 0.2, "attribute_gain": 2},
            {"name": "Master", "exp_multiplier": 2.5, "target_zone": 0.1, "attribute_gain": 3}
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
            {"name": "Basic", "exp_multiplier": 1.0, "targets": 3, "attribute_gain": 1, "energy_gain": 5},
            {"name": "Advanced", "exp_multiplier": 1.5, "targets": 5, "attribute_gain": 2, "energy_gain": 10},
            {"name": "Master", "exp_multiplier": 2.5, "targets": 7, "attribute_gain": 3, "energy_gain": 15}
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
            "emoji": "👻"
        },
        "Assassination Techniques": {
            "description": "Hone your skills for deadly precision strikes",
            "primary_attribute": "power",
            "secondary_attribute": "speed",
            "base_exp": 30,
            "cooldown": 4,  # hours
            "level_req": 10,
            "emoji": "🗡️"
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
            "emoji": "💚"
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
            "emoji": "🌐"
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
            "emoji": "🐺"
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
            "emoji": "♾️"
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
        self.speed = 0.05  # How fast the indicator moves per step
        self.task = None
        self.stopped = False
        
        # Add the stop button
        stop_btn = Button(label="STOP", style=discord.ButtonStyle.danger)
        stop_btn.callback = self.stop_callback
        self.add_item(stop_btn)
    
    async def start(self, interaction: discord.Interaction):
        # Initial render
        self.position = 0.0
        await interaction.response.send_message(
            content=self.render_bar(),
            view=self
        )
        
        # Start the animation
        self.task = asyncio.create_task(self.animate(interaction))
    
    def render_bar(self) -> str:
        """Render a text-based timing bar"""
        bar_length = 20
        target_start = int((0.5 - self.target_zone/2) * bar_length)
        target_end = int((0.5 + self.target_zone/2) * bar_length)
        
        # Create the bar with target zone
        bar = ["□"] * bar_length
        for i in range(target_start, target_end+1):
            bar[i] = "■"
        
        # Add the indicator
        indicator_pos = min(bar_length-1, int(self.position * bar_length))
        bar[indicator_pos] = "🔴"
        
        return f"⏱️ Stop the indicator in the target zone!\n\n|{''.join(bar)}|"
    
    async def animate(self, interaction: discord.Interaction):
        """Animate the timing bar"""
        try:
            while not self.stopped:
                # Move the indicator
                self.position += self.direction * self.speed
                
                # Bounce at the edges
                if self.position >= 1.0:
                    self.position = 1.0
                    self.direction = -1
                elif self.position <= 0.0:
                    self.position = 0.0
                    self.direction = 1
                
                # Update the message
                await interaction.edit_original_response(content=self.render_bar())
                
                # Small delay between frames
                await asyncio.sleep(0.1)
        except Exception as e:
            print(f"Animation error: {e}")
    
    async def stop_callback(self, interaction: discord.Interaction):
        """Handle stopping the timing bar"""
        self.stopped = True
        if self.task:
            self.task.cancel()
        
        # Calculate if successful (indicator in target zone)
        center = 0.5
        half_target = self.target_zone / 2
        in_target = (center - half_target) <= self.position <= (center + half_target)
        
        if in_target:
            self.parent_view.score += 1
            await interaction.response.edit_message(
                content=f"🎯 Perfect timing! Score: {self.parent_view.score}/{self.parent_view.max_score}",
                view=None
            )
        else:
            await interaction.response.edit_message(
                content=f"❌ Missed the target zone! Score: {self.parent_view.score}/{self.parent_view.max_score}",
                view=None
            )
        
        self.parent_view.round_complete = True
        self.parent_view.stop()

# QUIZ MINIGAME - Answer RPG-themed questions 
class QuizButton(Button):
    def __init__(self, answer: str, is_correct: bool, parent_view, row: int = 0):
        super().__init__(
            label=answer,
            style=discord.ButtonStyle.secondary,
            row=row
        )
        
        self.is_correct = is_correct
        self.parent_view = parent_view
    
    async def callback(self, interaction: discord.Interaction):
        if self.is_correct:
            self.parent_view.score += 1
            await interaction.response.edit_message(
                content=f"✅ Correct! Score: {self.parent_view.score}/{self.parent_view.max_score}",
                view=None
            )
        else:
            await interaction.response.edit_message(
                content=f"❌ Incorrect! The correct answer was: {self.parent_view.current_correct_answer}\nScore: {self.parent_view.score}/{self.parent_view.max_score}",
                view=None
            )
        
        self.parent_view.round_complete = True
        self.parent_view.stop()

# PRECISION MINIGAME - Hit moving targets to enhance precision
class MovingTargetButton(Button):
    def __init__(self, is_active: bool, position: Tuple[int, int], parent_view):
        row = position[0]
        # Default button style
        super().__init__(
            label="○" if is_active else "·",
            style=discord.ButtonStyle.secondary if is_active else discord.ButtonStyle.gray,
            row=row
        )
        
        self.is_active = is_active
        self.parent_view = parent_view
        self.position = position
    
    async def callback(self, interaction: discord.Interaction):
        if self.is_active:
            self.parent_view.score += 1
            await interaction.response.edit_message(
                content=f"🎯 Precise hit! Score: {self.parent_view.score}/{self.parent_view.max_score}",
                view=None
            )
        else:
            await interaction.response.edit_message(
                content=f"❌ Missed the active target! Score: {self.parent_view.score}/{self.parent_view.max_score}",
                view=None
            )
        
        self.parent_view.round_complete = True
        self.parent_view.stop()

class TrainingMinigameView(View):
    def __init__(self, player_data: PlayerData, training_type: str, training_data: Dict[str, Any], data_manager: DataManager):
        super().__init__(timeout=60)
        self.player_data = player_data
        self.training_type = training_type
        self.training_data = training_data
        self.data_manager = data_manager
        self.result = None
        self.score = 0
        self.max_score = 5
        self.current_step = 0
        self.round_complete = False
        # Default to the 'Basic' difficulty level
        self.selected_difficulty = "Basic"
        # Select the difficulty data
        self.difficulty = next((d for d in self.training_data.get("difficulty_levels", []) 
                          if d["name"] == self.selected_difficulty), {})
        
        # Add start button
        start_btn = Button(
            label="Start Training",
            style=discord.ButtonStyle.green,
            emoji=training_data["emoji"]
        )
        start_btn.callback = self.start_callback
        self.add_item(start_btn)
        
        # Add cancel button
        cancel_btn = Button(
            label="Cancel",
            style=discord.ButtonStyle.red,
            emoji="❌"
        )
        cancel_btn.callback = self.cancel_callback
        self.add_item(cancel_btn)
    
    async def start_callback(self, interaction: discord.Interaction):
        """Start the training minigame"""
        # Clear buttons
        self.clear_items()
        
        # Get minigame type
        minigame_type = self.training_data.get("minigame_type", "reaction")
        
        # Get appropriate emoji and message
        emoji_map = {
            "reaction": "🎯",
            "sequence": "🔢",
            "timing": "⏱️",
            "quiz": "🧠",
            "precision": "🎯"
        }
        emoji = emoji_map.get(minigame_type, "🏋️")
        
        # Send instructions based on minigame type
        instructions = {
            "reaction": "Click the highlighted target as quickly as possible!",
            "sequence": "Memorize the sequence and repeat it in the correct order!",
            "timing": "Stop the moving indicator when it's in the target zone!",
            "quiz": "Answer the combat strategy questions correctly!",
            "precision": "Hit the active target to improve your precision!"
        }
        
        instruction_text = instructions.get(minigame_type, "Complete the training challenges!")
        
        await interaction.response.edit_message(
            content=f"{emoji} **{self.training_type} Training**\n\n"
                   f"{self.training_data['description']}\n\n"
                   f"{instruction_text}",
            view=None
        )
        
        await asyncio.sleep(2)
        
        # Select and run the appropriate minigame type
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
            # Fallback to reaction game if unknown type
            await self.run_reaction_minigame(interaction)
    
    async def run_reaction_minigame(self, interaction: discord.Interaction):
        """Run the reaction speed minigame"""
        for i in range(self.max_score):
            self.current_step = i + 1
            self.round_complete = False
            
            # Create a round view for this step
            round_view = View(timeout=5)
            
            # Add target buttons in random positions
            positions = list(range(3*3))  # 3x3 grid
            random.shuffle(positions)
            
            # Add target button and dummy buttons
            for j in range(9):
                is_target = (j == positions[0])
                button = TargetButton(is_target=is_target, parent_view=self, row=j//3)
                round_view.add_item(button)
            
            # Show the round view
            try:
                round_msg = await interaction.followup.send(
                    content=f"Round {self.current_step}/{self.max_score} - Click the target!",
                    view=round_view
                )
                
                # Get time window from difficulty
                time_window = self.difficulty.get("time_window", 5.0)
                
                # Wait for this step to complete
                await asyncio.sleep(time_window)
                
                # If the round was not completed, count it as a miss
                if not self.round_complete:
                    await interaction.followup.send(
                        content=f"⏱️ Time's up! Score: {self.score}/{self.max_score}"
                    )
            except Exception as e:
                print(f"Error in reaction minigame round: {e}")
            
            # Short pause between rounds
            await asyncio.sleep(1)
    
    async def run_sequence_minigame(self, interaction: discord.Interaction):
        """Run the sequence memorization minigame"""
        # Possible symbols for sequence
        symbols = ["🔴", "🔵", "🟢", "🟡", "⚪", "🟣", "🟠", "⚫"]
        
        for i in range(self.max_score):
            self.current_step = i + 1
            self.round_complete = False
            
            # Get sequence length from difficulty
            seq_length = self.difficulty.get("sequence_length", 3)
            
            # Generate random sequence
            sequence = [random.randint(0, len(symbols)-1) for _ in range(seq_length)]
            self.current_sequence = sequence
            self.current_sequence_position = 0
            self.expected_next = sequence[0]
            
            # First, show the sequence to memorize
            sequence_text = " → ".join([symbols[s] for s in sequence])
            await interaction.followup.send(
                content=f"Round {self.current_step}/{self.max_score} - Memorize this sequence!\n{sequence_text}"
            )
            
            # Wait for player to memorize
            memorize_time = min(5, 1 + seq_length)
            await asyncio.sleep(memorize_time)
            
            # Now show the buttons to reproduce the sequence
            sequence_view = View(timeout=10)
            
            # Add buttons for each symbol
            for j, symbol in enumerate(symbols):
                button = SequenceButton(symbol=symbol, order=j, parent_view=self, row=j//4)
                sequence_view.add_item(button)
            
            try:
                await interaction.followup.send(
                    content=f"Now reproduce the sequence in order!",
                    view=sequence_view
                )
                
                # Wait for sequence completion or timeout
                await asyncio.sleep(10)
                
                if not self.round_complete:
                    await interaction.followup.send(
                        content=f"⏱️ Time's up! Score: {self.score}/{self.max_score}"
                    )
            except Exception as e:
                print(f"Error in sequence minigame round: {e}")
            
            # Short pause between rounds
            await asyncio.sleep(1)
    
    async def run_timing_minigame(self, interaction: discord.Interaction):
        """Run the timing bar minigame"""
        for i in range(self.max_score):
            self.current_step = i + 1
            self.round_complete = False
            
            # Get target zone size from difficulty
            target_zone = self.difficulty.get("target_zone", 0.3)
            
            # Create and start timing bar
            timing_bar = TimingBar(parent_view=self, target_zone=target_zone)
            
            try:
                await timing_bar.start(interaction)
                
                # Wait for completion or timeout
                await asyncio.sleep(10)
                
                if not self.round_complete:
                    await interaction.followup.send(
                        content=f"⏱️ Time's up! Score: {self.score}/{self.max_score}"
                    )
            except Exception as e:
                print(f"Error in timing minigame round: {e}")
            
            # Short pause between rounds
            await asyncio.sleep(1)
    
    async def run_quiz_minigame(self, interaction: discord.Interaction):
        """Run the knowledge quiz minigame"""
        # RPG-themed quiz questions and answers
        quiz_questions = [
            {
                "question": "Which is the most effective strategy against a heavily armored opponent?",
                "answers": ["Use speed to your advantage", "Match strength with strength", "Aim for weak points", "Retreat and heal"],
                "correct": 2
            },
            {
                "question": "What should you prioritize in a long battle?",
                "answers": ["Maximum damage output", "Energy conservation", "Healing items", "Defensive stance"],
                "correct": 1
            },
            {
                "question": "When facing multiple opponents, what's the best approach?",
                "answers": ["Focus on the strongest enemy", "Divide and conquer", "Area attacks", "Defensive position"],
                "correct": 2
            },
            {
                "question": "What's most important for a balanced combat style?",
                "answers": ["Power techniques", "Defensive techniques", "Speed techniques", "Balance of all attributes"],
                "correct": 3
            },
            {
                "question": "Which resource is most critical to manage in extended combat?",
                "answers": ["Health points", "Energy", "Position", "Item usage"],
                "correct": 1
            },
            {
                "question": "What's the best counter to an agile opponent?",
                "answers": ["Match their speed", "Use area attacks", "Predict movement patterns", "Heavy armor"],
                "correct": 2
            },
            {
                "question": "When should you use your strongest ability?",
                "answers": ["At the start of battle", "When your HP is low", "When the enemy is vulnerable", "Save it for emergencies"],
                "correct": 2
            }
        ]
        
        # Shuffle questions
        random.shuffle(quiz_questions)
        
        # Get number of questions from difficulty
        num_questions = min(self.max_score, self.difficulty.get("questions", 3))
        selected_questions = quiz_questions[:num_questions]
        
        for i, question_data in enumerate(selected_questions):
            self.current_step = i + 1
            self.round_complete = False
            
            question = question_data["question"]
            answers = question_data["answers"]
            correct_index = question_data["correct"]
            
            # Save correct answer for feedback
            self.current_correct_answer = answers[correct_index]
            
            # Create quiz view
            quiz_view = View(timeout=15)
            
            # Add answer buttons
            for j, answer in enumerate(answers):
                button = QuizButton(answer=answer, is_correct=(j == correct_index), parent_view=self, row=j)
                quiz_view.add_item(button)
            
            try:
                await interaction.followup.send(
                    content=f"Question {self.current_step}/{num_questions}:\n**{question}**",
                    view=quiz_view
                )
                
                # Wait for answer or timeout
                await asyncio.sleep(15)
                
                if not self.round_complete:
                    await interaction.followup.send(
                        content=f"⏱️ Time's up! The correct answer was: {self.current_correct_answer}\nScore: {self.score}/{self.max_score}"
                    )
            except Exception as e:
                print(f"Error in quiz minigame round: {e}")
            
            # Short pause between rounds
            await asyncio.sleep(1)
    
    async def run_precision_minigame(self, interaction: discord.Interaction):
        """Run the precision targeting minigame"""
        # Get number of targets from difficulty
        num_targets = self.difficulty.get("targets", 5)
        self.max_score = num_targets
        
        for i in range(num_targets):
            self.current_step = i + 1
            self.round_complete = False
            
            # Create a 3x3 grid view
            grid_view = View(timeout=5)
            
            # Randomly position the active target
            active_row = random.randint(0, 2)
            active_col = random.randint(0, 2)
            
            # Add buttons to the grid
            for row in range(3):
                for col in range(3):
                    is_active = (row == active_row and col == active_col)
                    button = MovingTargetButton(
                        is_active=is_active, 
                        position=(row, col),
                        parent_view=self
                    )
                    grid_view.add_item(button)
            
            try:
                await interaction.followup.send(
                    content=f"Target {self.current_step}/{num_targets} - Hit the active target (○)!",
                    view=grid_view
                )
                
                # Wait for this step to complete
                await asyncio.sleep(5)
                
                if not self.round_complete:
                    await interaction.followup.send(
                        content=f"⏱️ Time's up! Score: {self.score}/{self.max_score}"
                    )
            except Exception as e:
                print(f"Error in precision minigame round: {e}")
            
            # Short pause between rounds
            await asyncio.sleep(1)
        
        # Calculate training results
        performance = self.score / self.max_score
        
        # Base attribute gains
        primary_attr = self.training_data["primary_attribute"]
        secondary_attr = self.training_data["secondary_attribute"]
        
        # Calculate attribute gains based on performance
        primary_gain = max(1, int(3 * performance))  # 0-3 points
        secondary_gain = max(0, int(2 * performance))  # 0-2 points
        
        # Handle battle energy training differently - this increases max battle energy capacity
        energy_gain = 0
        if primary_attr == "energy":
            # Get the selected difficulty level from the training data
            difficulty_level = next((d for d in self.training_data["difficulty_levels"] 
                              if d["name"] == self.selected_difficulty), None)
            if difficulty_level and "energy_gain" in difficulty_level:
                # Calculate battle energy gain based on performance and difficulty level
                energy_gain = max(1, int(difficulty_level["energy_gain"] * performance))
        
        # Apply different increases for HP
        if primary_attr == "hp":
            primary_gain *= 5  # 5x multiplier for HP
        if secondary_attr == "hp":
            secondary_gain *= 5  # 5x multiplier for HP
        
        # Calculate exp gain based on performance
        exp_gain = int(self.training_data["base_exp"] * performance)
        
        # Initialize allocated stats if not exists
        if not hasattr(self.player_data, "allocated_stats") or not self.player_data.allocated_stats:
            self.player_data.allocated_stats = {"power": 0, "defense": 0, "speed": 0, "hp": 0}
        
        # Apply attribute gains
        if primary_attr == "energy" and energy_gain > 0:
            # Increase the player's max energy capacity through energy_training field
            if not hasattr(self.player_data, "energy_training"):
                self.player_data.energy_training = 0
            self.player_data.energy_training += energy_gain
            # Also update battle energy to reflect the new maximum
            max_energy = self.player_data.get_max_battle_energy()
            self.player_data.battle_energy = min(max_energy, self.player_data.battle_energy + energy_gain)
            
            secondary_attr_to_apply = secondary_attr
        else:
            # Normal attribute increases
            self.player_data.allocated_stats[primary_attr] += primary_gain
            secondary_attr_to_apply = secondary_attr
            
        # Always apply secondary attribute gain
        self.player_data.allocated_stats[secondary_attr_to_apply] += secondary_gain
        
        # Apply exp gain
        leveled_up = self.player_data.add_exp(exp_gain)
        
        # Update quest progress for training
        from achievements import QuestManager
        quest_manager = QuestManager(self.data_manager)
        
        # Update daily training quests
        completed_daily_quests = quest_manager.update_quest_progress(self.player_data, "daily_training")
        
        # Update weekly advanced training quests
        completed_weekly_quests = quest_manager.update_quest_progress(self.player_data, "weekly_advanced_training")
        
        # Update training cooldowns
        if not hasattr(self.player_data, "training_cooldowns"):
            self.player_data.training_cooldowns = {}
        
        # Set cooldown
        now = datetime.datetime.now()
        self.player_data.training_cooldowns[self.training_type] = (now + datetime.timedelta(hours=self.training_data["cooldown"])).isoformat()
        
        # Update quest progress
        from achievements import QuestManager
        quest_manager = QuestManager(self.data_manager)
        
        # Update daily training quests
        completed_quests = quest_manager.update_quest_progress(self.player_data, "daily_training")
        for quest in completed_quests:
            quest_manager.award_quest_rewards(self.player_data, quest)
        
        # Update weekly training quests
        completed_weekly = quest_manager.update_quest_progress(self.player_data, "weekly_training")
        for quest in completed_weekly:
            quest_manager.award_quest_rewards(self.player_data, quest)
            
        # Save player data
        self.data_manager.save_data()
        
        # Create results embed
        embed = discord.Embed(
            title=f"🏋️ {self.training_type} Training Complete!",
            description=f"Score: {self.score}/{self.max_score} ({int(performance * 100)}%)",
            color=discord.Color.green() if performance >= 0.6 else discord.Color.gold() if performance >= 0.3 else discord.Color.red()
        )
        
        # Add energy gain info if this was energy training
        if primary_attr == "energy" and energy_gain > 0:
            embed.add_field(
                name="⚡ Energy Capacity Increased!",
                value=f"Your maximum battle energy capacity has increased by **{energy_gain}** points!\n"
                      f"New maximum battle energy: **{self.player_data.get_max_battle_energy()}**",
                inline=False
            )
        
        # Add attribute gains
        embed.add_field(
            name="Attribute Gains",
            value=f"**{primary_attr.title()}:** +{primary_gain}\n"
                  f"**{secondary_attr.title()}:** +{secondary_gain}",
            inline=True
        )
        
        # Add exp gain
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
            value=f"This training will be available again in {self.training_data['cooldown']} hours.",
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
                        time_remaining = cooldown_time - now
                        hours, remainder = divmod(time_remaining.seconds, 3600)
                        minutes, _ = divmod(remainder, 60)
                        
                        on_cooldown = True
                        cooldown_text = f" (Cooldown: {hours}h {minutes}m)"
                except (ValueError, TypeError):
                    pass
            
            description = data["description"]
            if on_cooldown:
                description = f"ON COOLDOWN{cooldown_text}"
            
            self.training_select.add_option(
                label=name,
                description=description[:100],  # Discord limit
                value=name,
                emoji=data["emoji"],
                default=False
            )
        
        # Set callback
        self.training_select.callback = self.training_select_callback
        
        # Add select menu
        self.add_item(self.training_select)
        
        # Add cancel button
        cancel_btn = Button(
            label="Cancel",
            style=discord.ButtonStyle.red,
            emoji="❌"
        )
        cancel_btn.callback = self.cancel_callback
        self.add_item(cancel_btn)
    
    def get_available_training(self) -> Dict[str, Dict[str, Any]]:
        """Get all training options available to the player"""
        result = {}
        
        # Add basic training options for everyone
        for name, data in TRAINING_MINIGAMES.items():
            result[name] = data
        
        # Add class-specific training if available
        if self.player_data.class_name in CLASS_TRAINING:
            class_training = CLASS_TRAINING[self.player_data.class_name]
            
            for name, data in class_training.items():
                # Check level requirement
                if self.player_data.class_level >= data.get("level_req", 0):
                    result[name] = data
        
        return result
    
    async def training_select_callback(self, interaction: discord.Interaction):
        """Handle training selection"""
        training_name = self.training_select.values[0]
        training_data = self.training_options[training_name]
        
        # Check cooldown
        if hasattr(self.player_data, "training_cooldowns") and training_name in self.player_data.training_cooldowns:
            try:
                cooldown_time = datetime.datetime.fromisoformat(self.player_data.training_cooldowns[training_name])
                now = datetime.datetime.now()
                
                if cooldown_time > now:
                    time_remaining = cooldown_time - now
                    hours, remainder = divmod(time_remaining.seconds, 3600)
                    minutes, _ = divmod(remainder, 60)
                    
                    await interaction.response.send_message(
                        f"⏳ This training is still on cooldown for {hours}h {minutes}m.",
                        ephemeral=True
                    )
                    return
            except (ValueError, TypeError):
                pass
        
        # Create training minigame view
        training_view = TrainingMinigameView(self.player_data, training_name, training_data, self.data_manager)
        
        # Create training embed
        embed = discord.Embed(
            title=f"🏋️ {training_name} Training",
            description=training_data["description"],
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="Training Focus",
            value=f"Primary: **{training_data['primary_attribute'].title()}**\n"
                  f"Secondary: **{training_data['secondary_attribute'].title()}**",
            inline=True
        )
        
        embed.add_field(
            name="Potential Rewards",
            value=f"Base EXP: **{training_data['base_exp']}**\n"
                  f"Attribute Points: **1-3** (based on performance)",
            inline=True
        )
        
        embed.add_field(
            name="Cooldown",
            value=f"This training has a cooldown of **{training_data['cooldown']} hours** after completion.",
            inline=False
        )
        
        # Show training view
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
    
    # Add level info
    embed.add_field(
        name="📈 Level Information",
        value=f"**Level:** {player_data.class_level}\n"
              f"**EXP:** {player_data.class_exp}/{int(100 * (player_data.class_level ** 1.5))}\n"
              f"**Class:** {player_data.class_name}",
        inline=True
    )
    
    # Send message with embed and view
    await ctx.send(embed=embed, view=view)