        """
        Enhanced Battle System for Discord RPG Bot

        This module contains an improved battle system with:
        1. Dynamic energy scaling based on player level and training
        2. Better potion detection and usage in battles
        3. Improved battle display with correct energy values
        """

        from typing import Optional, Dict, List, Tuple, Any
        import random
        import discord
        from discord.ui import Button, View
        import asyncio
        import datetime
        from data_models import PlayerData, Item, DataManager

        class BattleMove:
            def __init__(self, name: str, damage_multiplier: float, energy_cost: int, 
                         effect: Optional[str] = None, description: Optional[str] = None):
                self.name = name
                self.damage_multiplier = damage_multiplier
                self.energy_cost = energy_cost
                self.effect = effect
                self.description = description or f"Deal {damage_multiplier}x damage for {energy_cost} energy"

        class BattleEntity:
            def __init__(self, name: str, stats: Dict[str, int], moves: Optional[List[BattleMove]] = None, 
                         is_player: bool = False, player_data: Optional[PlayerData] = None):
                self.name = name
                self.stats = stats.copy()
                self.current_hp = stats["hp"]

                # Use dynamic energy scaling for players based on level and training
                if player_data and is_player and hasattr(player_data, "get_max_battle_energy"):
                    self.max_energy = player_data.get_max_battle_energy()
                    self.current_energy = min(player_data.battle_energy, self.max_energy)
                else:
                    self.max_energy = stats.get("energy", 100)
                    self.current_energy = self.max_energy

                self.moves = moves or []
                self.is_player = is_player
                self.player_data = player_data
                self.status_effects = {}  # Effect name -> (turns remaining, effect strength)

                # Process active effects from special items
                if is_player and player_data and hasattr(player_data, "active_effects"):
                    # Apply any HP boosts from active effects
                    for effect_name, effect_data in player_data.active_effects.items():
                        if effect_data.get("effect") == "hp_boost":
                            boost_amount = effect_data.get("boost_amount", 0)
                            self.stats["hp"] += boost_amount
                            self.current_hp += boost_amount
                        elif effect_data.get("effect") == "all_stats_boost":
                            boost_amount = effect_data.get("boost_amount", 0)
                            for stat in ["power", "defense", "speed", "hp"]:
                                if stat in self.stats:
                                    self.stats[stat] += boost_amount
                                    if stat == "hp":
                                        self.current_hp += boost_amount

            def is_alive(self) -> bool:
                return self.current_hp > 0

            def calculate_damage(self, move: BattleMove, target: 'BattleEntity') -> int:
                """Calculate damage for a move against a target"""
                base_damage = int(self.stats["power"] * move.damage_multiplier)
                # Apply defense reduction (defense reduces damage by a percentage)
                damage_reduction = target.stats["defense"] / 100
                damage = int(base_damage * (1 - min(0.75, damage_reduction)))  # Cap reduction at 75%

                # Apply critical hit (10% chance for 1.5x damage)
                if random.random() < 0.1:
                    damage = int(damage * 1.5)

                # Ensure minimum damage of 1
                return max(1, damage)

            def apply_move(self, move: BattleMove, target: 'BattleEntity') -> Tuple[int, str]:
                """Apply a move to a target and return damage dealt and effect message"""
                # Subtract energy cost
                self.current_energy -= move.energy_cost

                # Calculate and apply damage
                damage = self.calculate_damage(move, target)
                target.current_hp -= damage
                target.current_hp = max(0, target.current_hp)  # Prevent negative HP

                effect_msg = ""

                # Apply any special effects
                if move.effect:
                    if move.effect == "stun":
                        # 30% chance to stun for 1 turn
                        if random.random() < 0.3:
                            target.status_effects["stunned"] = (1, 1)
                            effect_msg = "\n🌀 Target is stunned for 1 turn!"
                    elif move.effect == "bleed":
                        # Apply bleeding for 3 turns
                        bleed_strength = int(self.stats["power"] * 0.15)  # 15% of power per turn
                        target.status_effects["bleeding"] = (3, bleed_strength)
                        effect_msg = f"\n🩸 Target is bleeding for 3 turns! (-{bleed_strength} HP/turn)"
                    elif move.effect == "energy_drain":
                        # Drain 20 energy
                        drain_amount = 20
                        target.current_energy = max(0, target.current_energy - drain_amount)
                        effect_msg = f"\n⚡ Drained {drain_amount} energy from target!"

                return damage, effect_msg

            def update_status_effects(self) -> str:
                """Update status effects at the end of turn. Return status message."""
                status_msg = ""
                expired_effects = []

                for effect_name, (turns_remaining, effect_strength) in self.status_effects.items():
                    if effect_name == "bleeding":
                        self.current_hp -= effect_strength
                        self.current_hp = max(0, self.current_hp)
                        status_msg += f"\n🩸 {self.name} takes {effect_strength} bleeding damage!"

                    # Decrement turns remaining
                    turns_remaining -= 1
                    if turns_remaining <= 0:
                        expired_effects.append(effect_name)
                        status_msg += f"\n✨ {effect_name.capitalize()} effect expired on {self.name}!"
                    else:
                        self.status_effects[effect_name] = (turns_remaining, effect_strength)

                # Remove expired effects
                for effect in expired_effects:
                    del self.status_effects[effect]

                return status_msg

        class BattleMoveButton(Button):
            def __init__(self, move: BattleMove, row: int = 0):
                # Choose button style based on move type
                if "heal" in (move.effect or ""):
                    style = discord.ButtonStyle.success  # Green
                    emoji = "💚"
                elif "energy" in (move.effect or ""):
                    style = discord.ButtonStyle.primary  # Blue
                    emoji = "⚡"
                elif "shield" in (move.effect or ""):
                    style = discord.ButtonStyle.secondary  # Gray
                    emoji = "🛡️"
                else:
                    style = discord.ButtonStyle.danger  # Red
                    emoji = "⚔️"

                # Keep label short to avoid button rendering issues
                label = move.name
                if len(label) > 10:
                    label = label[:10]  # Truncate long names

                super().__init__(
                    style=style,
                    label=f"{label} ({move.energy_cost}⚡)",
                    emoji=emoji,
                    row=row
                )
                self.move = move

            async def callback(self, interaction: discord.Interaction):
                view = self.view
                if view is not None and hasattr(view, 'on_move_selected'):
                    await view.on_move_selected(interaction, self.move)
                else:
                    await interaction.response.send_message("This battle has expired. Please start a new one.", ephemeral=True)

        class ItemButton(Button):
            def __init__(self, item_name: str, item_effect: str, row: int = 0):
                # Truncate the item name if it's too long for a button
                display_name = item_name
                if len(display_name) > 10:
                    display_name = display_name[:8] + ".."

                # Choose style and emoji based on item effect
                if "heal" in item_effect.lower():
                    style = discord.ButtonStyle.success  # Green
                    emoji = "🧪"
                elif "energy" in item_effect.lower():
                    style = discord.ButtonStyle.primary  # Blue
                    emoji = "⚡"
                elif "strength" in item_effect.lower() or "power" in item_effect.lower():
                    style = discord.ButtonStyle.danger  # Red
                    emoji = "💪"
                elif "defense" in item_effect.lower() or "shield" in item_effect.lower():
                    style = discord.ButtonStyle.secondary  # Gray
                    emoji = "🛡️"
                else:
                    style = discord.ButtonStyle.primary  # Blue
                    emoji = "🔮"

                super().__init__(
                    style=style,
                    label=display_name,
                    emoji=emoji,
                    row=row
                )
                self.item_name = item_name
                self.item_effect = item_effect

            async def callback(self, interaction: discord.Interaction):
                view = self.view
                if view is not None and hasattr(view, 'on_item_selected'):
                    await view.on_item_selected(interaction, self.item_name, self.item_effect)
                else:
                    await interaction.response.send_message("This battle has expired. Please start a new one.", ephemeral=True)

        class BattleView(View):
            def __init__(self, player: BattleEntity, enemy: BattleEntity, timeout: int = 30):
                super().__init__(timeout=timeout)
                self.player = player
                self.enemy = enemy
                self.update_buttons()

            def get_safe_message_content(self, interaction: discord.Interaction) -> str:
                """Safely extract message content from interaction, returning empty string if not possible"""
                try:
                    if hasattr(interaction, 'message') and interaction.message:
                        if hasattr(interaction.message, 'content') and interaction.message.content:
                            return interaction.message.content.split("\n\n")[0]
                except:
                    pass

                return ""

            def update_buttons(self):
                # Clear existing buttons
                self.clear_items()

                # Add move buttons
                # Organize them in 2 rows (up to 5 per row) if needed
                row_index = 0

                # Sort moves by energy cost
                sorted_moves = sorted(self.player.moves, key=lambda m: m.energy_cost)

                # Check if player has enough energy for ANY move
                has_usable_move = any(self.player.current_energy >= move.energy_cost for move in sorted_moves)

                # If player has no usable moves, add a Rest button
                if not has_usable_move:
                    rest_button = Button(
                        style=discord.ButtonStyle.primary,
                        label="Rest (Recover Energy)",
                        emoji="🔄",
                        row=0
                    )

                    # Set the callback for the rest button
                    async def rest_callback(interaction):
                        await self.rest_to_recover_energy(interaction)

                    rest_button.callback = rest_callback
                    self.add_item(rest_button)
                else:
                    # Add normal move buttons if player has enough energy
                    for i, move in enumerate(sorted_moves):
                        # Check if player has enough energy for the move
                        disabled = self.player.current_energy < move.energy_cost

                        # Place buttons in proper rows (max 5 per row)
                        if i >= 5:
                            row_index = 1

                        button = BattleMoveButton(move, row=row_index)
                        button.disabled = disabled
                        self.add_item(button)

                # Add Items button (row 2)
                items_button = Button(
                    style=discord.ButtonStyle.success,
                    label="Items",
                    emoji="🎒",
                    row=2
                )

                # Set the callback
                items_button.callback = self.show_items
                self.add_item(items_button)

            async def rest_to_recover_energy(self, interaction: discord.Interaction):
                """Handle player resting to recover energy when they can't make any moves"""
                # Calculate energy recovery amount (30% of max energy)
                recovery_amount = max(30, int(self.player.max_energy * 0.3))
                old_energy = self.player.current_energy
                self.player.current_energy = min(self.player.max_energy, old_energy + recovery_amount)

                # Update the view with the results
                await interaction.response.edit_message(
                    content=f"🔄 You rest to recover energy! (+{recovery_amount} energy)\n" 
                           f"Energy: {old_energy} → {self.player.current_energy}/{self.player.max_energy} ⚡",
                    view=self
                )

                # Enemy turn
                await asyncio.sleep(1)

                # Choose enemy move (prioritize moves they have energy for)
                available_moves = [m for m in self.enemy.moves if self.enemy.current_energy >= m.energy_cost]
                if not available_moves:
                    # If no moves available, enemy also skips turn to regain energy
                    energy_gain = max(30, int(self.enemy.max_energy * 0.3))
                    self.enemy.current_energy = min(self.enemy.max_energy, self.enemy.current_energy + energy_gain)

                    await interaction.edit_original_response(
                        content=f"🔄 You rest to recover energy! (+{recovery_amount} energy)\n" 
                               f"🔄 {self.enemy.name} is also exhausted and regains {energy_gain} energy!",
                        view=self
                    )
                else:
                    enemy_move = random.choice(available_moves)
                    enemy_damage, enemy_effect_msg = self.enemy.apply_move(enemy_move, self.player)

                    await interaction.edit_original_response(
                        content=f"🔄 You rest to recover energy! (+{recovery_amount} energy)\n" 
                               f"⚔️ {self.enemy.name} used {enemy_move.name} for {enemy_damage} damage!{enemy_effect_msg}",
                        view=self
                    )

                    # Check if player is defeated
                    if not self.player.is_alive():
                        # Battle lost
                        self.stop()
                        await asyncio.sleep(1)
                        await interaction.edit_original_response(
                            content=f"💀 Defeat! You were defeated by {self.enemy.name}!",
                            view=None
                        )
                        return

                # Update status effects, buttons, and battle stats
                player_status_msg = self.player.update_status_effects()
                enemy_status_msg = self.enemy.update_status_effects()
                self.update_buttons()

                battle_stats = (
                    f"Your HP: {self.player.current_hp}/{self.player.stats['hp']} ❤️ | "
                    f"Energy: {self.player.current_energy}/{self.player.max_energy} ⚡\n"
                    f"{self.enemy.name}'s HP: {self.enemy.current_hp}/{self.enemy.stats['hp']} ❤️ | "
                    f"Energy: {self.enemy.current_energy}/{self.enemy.max_energy} ⚡"
                    f"{player_status_msg}{enemy_status_msg}"
                )

                message_content = self.get_safe_message_content(interaction)
                await interaction.edit_original_response(
                    content=message_content + f"\n\n{battle_stats}",
                    view=self
                )

            async def on_move_selected(self, interaction: discord.Interaction, move: BattleMove):
                # Apply the player's move
                damage, effect_msg = self.player.apply_move(move, self.enemy)

                # Update the view with the results
                await interaction.response.edit_message(
                    content=f"⚔️ You used {move.name} for {damage} damage!{effect_msg}",
                    view=self
                )

                # Check if enemy is defeated
                if not self.enemy.is_alive():
                    # Battle won
                    self.stop()
                    await asyncio.sleep(1)
                    await interaction.edit_original_response(
                        content=f"🎉 Victory! You defeated {self.enemy.name}!\n"
                               f"Your HP: {self.player.current_hp}/{self.player.stats['hp']} ❤️ | "
                               f"Energy: {self.player.current_energy}/{self.player.max_energy} ⚡",
                        view=None
                    )

                    # Update player energy in their data object
                    if self.player.player_data:
                        self.player.player_data.battle_energy = self.player.current_energy

                    return

                # Enemy turn
                await asyncio.sleep(1)

                # Choose enemy move (prioritize moves they have energy for)
                available_moves = [m for m in self.enemy.moves if self.enemy.current_energy >= m.energy_cost]
                if not available_moves:
                    # If no moves available, enemy skips turn to regain energy
                    self.enemy.current_energy = min(self.enemy.max_energy, 
                                                   self.enemy.current_energy + 30)
                    await interaction.edit_original_response(
                        content=f"⚔️ You used {move.name} for {damage} damage!{effect_msg}\n"
                               f"🔄 {self.enemy.name} is exhausted and regains 30 energy!",
                        view=self
                    )
                else:
                    enemy_move = random.choice(available_moves)
                    enemy_damage, enemy_effect_msg = self.enemy.apply_move(enemy_move, self.player)

                    await interaction.edit_original_response(
                        content=f"⚔️ You used {move.name} for {damage} damage!{effect_msg}\n"
                               f"⚔️ {self.enemy.name} used {enemy_move.name} for {enemy_damage} damage!{enemy_effect_msg}",
                        view=self
                    )

                    # Check if player is defeated
                    if not self.player.is_alive():
                        # Battle lost
                        self.stop()
                        await asyncio.sleep(1)
                        await interaction.edit_original_response(
                            content=f"💀 Defeat! You were defeated by {self.enemy.name}!",
                            view=None
                        )
                        return

                # Update status effects
                player_status_msg = self.player.update_status_effects()
                enemy_status_msg = self.enemy.update_status_effects()

                # Update buttons for next turn
                self.update_buttons()

                # Show battle status with dynamic maximum energy values
                battle_stats = (
                    f"Your HP: {self.player.current_hp}/{self.player.stats['hp']} ❤️ | "
                    f"Energy: {self.player.current_energy}/{self.player.max_energy} ⚡\n"
                    f"{self.enemy.name}'s HP: {self.enemy.current_hp}/{self.enemy.stats['hp']} ❤️ | "
                    f"Energy: {self.enemy.current_energy}/{self.enemy.max_energy} ⚡"
                    f"{player_status_msg}{enemy_status_msg}"
                )

                message_content = self.get_safe_message_content(interaction)
                await interaction.edit_original_response(
                    content=message_content + f"\n\n{battle_stats}",
                    view=self
                )

            async def show_items(self, interaction: discord.Interaction):
                """Display usable items in player's inventory"""
                # Get usable items from player's inventory
                if hasattr(self.player, 'player_data') and self.player.player_data:
                    player_data = self.player.player_data
                    usable_items = []

                    # Look for potions or usable items in inventory
                    if hasattr(player_data, 'inventory'):
                        for item in player_data.inventory:
                            # Check if item is a potion or battle item
                            if hasattr(item, 'type') and item.type in ["potion", "battle_item"]:
                                usable_items.append(item)
                            # Also check item description for keywords
                            elif hasattr(item, 'description'):
                                desc_lower = item.description.lower()
                                if ("heal" in desc_lower or 
                                    "hp" in desc_lower or 
                                    "health" in desc_lower or
                                    "energy" in desc_lower or
                                    "potion" in desc_lower):
                                    usable_items.append(item)

                    if usable_items:
                        # Create a view for item selection
                        items_view = View(timeout=30)

                        # Add a back button to return to battle view
                        back_button = Button(
                            style=discord.ButtonStyle.secondary,
                            label="Back",
                            emoji="↩️",
                            row=0
                        )

                        async def back_button_callback(b_interaction: discord.Interaction):
                            await b_interaction.response.edit_message(content="Returning to battle...", view=None)
                            # Delete this message after a short delay
                            await asyncio.sleep(1)
                            try:
                                await b_interaction.delete_original_response()
                            except:
                                pass

                        back_button.callback = back_button_callback
                        items_view.add_item(back_button)

                        # Add item buttons (up to 5 per row)
                        for i, item in enumerate(usable_items[:15]):  # Limit to 15 items
                            row_num = (i // 5) + 1  # Start at row 1 (after back button)

                            # Extract effect from item description
                            effect = item.description if hasattr(item, 'description') else "Unknown effect"

                            item_button = ItemButton(item.name, effect, row=row_num)
                            items_view.add_item(item_button)

                        # Display the items view
                        await interaction.response.send_message(
                            content="Select an item to use:",
                            view=items_view,
                            ephemeral=True
                        )
                    else:
                        await interaction.response.send_message(
                            "No items available!",
                            ephemeral=True
                        )

            async def on_item_selected(self, interaction: discord.Interaction, item_name: str, item_effect: str):
                # Process item use
                try:
                    player_data = self.player.player_data
                    if not player_data:
                        await interaction.response.send_message("Error accessing player data!", ephemeral=True)
                        return

                    # Find the item in inventory
                    item_index = None
                    used_inv_item = None

                    for i, item in enumerate(player_data.inventory):
                        if hasattr(item, 'name') and item.name == item_name:
                            item_index = i
                            used_inv_item = item
                            break

                    if item_index is None or used_inv_item is None:
                        await interaction.response.send_message(f"Couldn't find {item_name} in your inventory!", ephemeral=True)
                        return

                    # Apply item effects
                    effect_message = f"You used {item_name}!"

                    # Process different item types
                    if "heal" in item_effect.lower() or "health" in item_effect.lower() or "hp" in item_effect.lower():
                        # Healing potion
                        heal_amount = 50  # Default

                        # Try to extract amount from description
                        import re
                        heal_match = re.search(r'(\d+)\s*hp', item_effect.lower())
                        if heal_match:
                            heal_amount = int(heal_match.group(1))

                        # Apply healing
                        old_hp = self.player.current_hp
                        self.player.current_hp = min(self.player.stats["hp"], self.player.current_hp + heal_amount)
                        actual_heal = self.player.current_hp - old_hp

                        effect_message = f"You used {item_name} and recovered {actual_heal} HP! 💚"

                    elif "energy" in item_effect.lower():
                        # Energy potion
                        energy_amount = 30  # Default

                        # Try to extract amount from description
                        import re
                        energy_match = re.search(r'(\d+)\s*energy', item_effect.lower())
                        if energy_match:
                            energy_amount = int(energy_match.group(1))

                        # Apply energy recovery
                        old_energy = self.player.current_energy
                        self.player.current_energy = min(self.player.max_energy, self.player.current_energy + energy_amount)
                        actual_energy = self.player.current_energy - old_energy

                        effect_message = f"You used {item_name} and recovered {actual_energy} energy! ⚡"

                    elif "strength" in item_effect.lower() or "power" in item_effect.lower():
                        # Strength boost
                        boost_amount = 10  # Default
                        boost_turns = 3  # Default

                        # Apply temporary boost
                        self.player.status_effects["strength_boost"] = (boost_turns, boost_amount)
                        self.player.stats["power"] += boost_amount

                        effect_message = f"You used {item_name} and boosted your power by {boost_amount} for {boost_turns} turns! 💪"

                    elif "defense" in item_effect.lower() or "shield" in item_effect.lower():
                        # Defense boost
                        boost_amount = 10  # Default
                        boost_turns = 3  # Default

                        # Apply temporary boost
                        self.player.status_effects["defense_boost"] = (boost_turns, boost_amount)
                        self.player.stats["defense"] += boost_amount

                        effect_message = f"You used {item_name} and boosted your defense by {boost_amount} for {boost_turns} turns! 🛡️"

                    # Remove item from inventory
                    if hasattr(used_inv_item, 'quantity') and used_inv_item.quantity > 1:
                        used_inv_item.quantity -= 1
                    else:
                        player_data.inventory.pop(item_index)

                    # Save player data
                    try:
                        from data_models import data_manager
                        data_manager.save_data()
                    except Exception as e:
                        print(f"Error saving data after item use: {e}")

                    # Update battle view
                    self.update_buttons()

                    # Show battle status with dynamic maximum energy
                    battle_stats = (
                        f"Your HP: {self.player.current_hp}/{self.player.stats['hp']} ❤️ | "
                        f"Energy: {self.player.current_energy}/{self.player.max_energy} ⚡\n"
                        f"{self.enemy.name}'s HP: {self.enemy.current_hp}/{self.enemy.stats['hp']} ❤️ | "
                        f"Energy: {self.enemy.current_energy}/{self.enemy.max_energy} ⚡"
                    )

                    # Send message about item use
                    await interaction.response.edit_message(content=f"{effect_message}\n\n{battle_stats}", view=None)

                    # Delete this message after a short delay to return to battle
                    await asyncio.sleep(2)
                    try:
                        await interaction.delete_original_response()
                    except:
                        pass

                except Exception as e:
                    # If anything goes wrong, just send a simple error message
                    try:
                        await interaction.response.send_message(f"Error using item: {str(e)}", ephemeral=True)
                    except:
                        try:
                            await interaction.followup.send(f"Error using item", ephemeral=True)
                        except:
                            pass

                    # We should have already processed the item above, no need for this code
                    return

        async def start_battle(ctx, player_data: PlayerData, enemy_name: str, enemy_level: int, data_manager: DataManager):
            """Start a battle between the player and an enemy"""
            # Generate enemy stats and moves based on name and level
            enemy_stats = generate_enemy_stats(enemy_name, enemy_level, player_data.class_level)
            enemy_moves = generate_enemy_moves(enemy_name)

            # Create player entity - get stats from class data
            from main import STARTER_CLASSES
            player_stats = player_data.get_stats(STARTER_CLASSES)

            player_entity = BattleEntity(
                ctx.author.display_name,
                player_stats,
                [
                    BattleMove("Quick Strike", 0.8, 10, description="A fast attack that costs little energy"),
                    BattleMove("Shadow Step", 1.3, 20, effect="stun", description="A swift attack that can stun the enemy"),
                    BattleMove("Heavy Blow", 1.5, 25, description="A powerful strike with high damage"),
                    BattleMove("Focused Attack", 1.2, 15, effect="bleed", description="Causes bleeding damage over time"),
                    BattleMove("Energy Drain", 0.6, 20, effect="energy_drain", description="Drains enemy energy")
                ],
                is_player=True,
                player_data=player_data
            )

            # Create enemy entity
            enemy_entity = BattleEntity(
                enemy_name,
                enemy_stats,
                enemy_moves
            )

            # Create battle embed
            embed = discord.Embed(
                title=f"⚔️ Battle: {ctx.author.display_name} vs {enemy_name} (Level {enemy_level})",
                description="Select moves to battle your opponent!",
                color=discord.Color.red()
            )

            # Add player stats
            embed.add_field(
                name=f"{ctx.author.display_name} (Level {player_data.class_level})",
                value=f"HP: {player_entity.current_hp}/{player_entity.stats['hp']} ❤️\n"
                      f"Battle Energy: {player_entity.current_energy}/{player_entity.max_energy} ⚡\n"
                      f"Power: {player_entity.stats['power']} ⚔️\n"
                      f"Defense: {player_entity.stats['defense']} 🛡️",
                inline=True
            )

            # Add enemy stats
            embed.add_field(
                name=f"{enemy_name} (Level {enemy_level})",
                value=f"HP: {enemy_entity.current_hp}/{enemy_entity.stats['hp']} ❤️\n"
                      f"Battle Energy: {enemy_entity.current_energy}/{enemy_entity.max_energy} ⚡\n"
                      f"Power: {enemy_entity.stats['power']} ⚔️\n"
                      f"Defense: {enemy_entity.stats['defense']} 🛡️",
                inline=True
            )

            # Create and send battle view
            battle_view = BattleView(player_entity, enemy_entity)
            message = await ctx.send(embed=embed, view=battle_view)

            # Wait for the battle to complete
            result = await battle_view.wait()

            # Update player data - only track current energy during battle, don't regenerate yet
            player_data.battle_energy = player_entity.current_energy

            # Save data
            data_manager.save_data()

            # Check result
            if result:  # Timeout
                await message.edit(content="Battle timed out!", view=None)
            elif player_entity.is_alive():
                # Player won
                exp_reward = calculate_exp_reward(enemy_level, player_data.class_level)
                gold_reward = calculate_gold_reward(enemy_level)

                # Award rewards
                # Add rewards - ensure we're adding all rewards properly
                player_data.add_exp(exp_reward)
                player_data.add_gold(gold_reward)

                # No need to manually track gold_earned since add_gold already does this

                # Update battle stats
                player_data.wins += 1

                # Regenerate health and energy after battle victory - full regeneration
                from utils import GAME_CLASSES
                player_data.regenerate_health_and_energy(GAME_CLASSES, 1.0)  # 100% regeneration

                # Make absolutely sure data is properly saved after rewards
                data_manager.save_data()
                # Double-check that data is saved by forcing another save
                data_manager.players[player_data.user_id] = player_data
                data_manager.save_data()

                # Create rewards embed
                rewards_embed = discord.Embed(
                    title="🎉 Battle Victory!",
                    description=f"You defeated {enemy_name} (Level {enemy_level})!",
                    color=discord.Color.green()
                )

                rewards_embed.add_field(
                    name="Rewards",
                    value=f"Experience: {exp_reward} XP 📊\n"
                          f"Gold: {gold_reward} 💰",
                    inline=False
                )

                # Check for level up
                old_level = player_data.class_level
                # Calculate XP needed for next level
                xp_needed = int(100 * (old_level ** 1.5))

                # Check if player has enough XP to level up
                if player_data.class_exp >= xp_needed and old_level < 50:  # Max level cap at 50
                    # Level up!
                    player_data.class_level += 1
                    player_data.class_exp -= xp_needed
                    player_data.skill_points += 2  # Award 2 skill points per level

                    # Add level up message
                    rewards_embed.add_field(
                        name="🎊 Level Up!",
                        value=f"You are now level {player_data.class_level}!\n"
                              f"You received 2 skill points!",
                        inline=False
                    )

                    # Add extra rewards for level up
                    level_bonus_gold = player_data.class_level * 20
                    player_data.add_gold(level_bonus_gold)
                    data_manager.save_data()

                    rewards_embed.add_field(
                        name="Level Up Bonus",
                        value=f"Gold: {level_bonus_gold} 💰",
                        inline=False
                    )

                await ctx.send(embed=rewards_embed)
            else:
                # Player lost
                # Update battle stats
                player_data.losses += 1

                # Give some consolation rewards
                consolation_exp = int(calculate_exp_reward(enemy_level, player_data.class_level) * 0.25)
                player_data.add_exp(consolation_exp)

                # Regenerate health and energy after battle defeat - partial recovery
                from utils import GAME_CLASSES
                player_data.regenerate_health_and_energy(GAME_CLASSES, 0.5)  # 50% regeneration

                # Save data with updated stats
                data_manager.save_data()

                # Create defeat embed
                defeat_embed = discord.Embed(
                    title="💀 Battle Defeat",
                    description=f"You were defeated by {enemy_name} (Level {enemy_level})!",
                    color=discord.Color.red()
                )

                defeat_embed.add_field(
                    name="Consolation Reward",
                    value=f"Experience: {consolation_exp} XP 📊",
                    inline=False
                )

                defeat_embed.add_field(
                    name="Recovery",
                    value=f"Your HP and Energy have partially recovered (50%).",
                    inline=False
                )

                await ctx.send(embed=defeat_embed)

        def generate_enemy_stats(enemy_name: str, enemy_level: int, player_level: int) -> Dict[str, int]:
            """Generate enemy stats based on name and level"""
            # Base stats
            base_stats = {
                "hp": 50,
                "power": 10,
                "defense": 10,
                "speed": 10,
                "energy": 100
            }

            # Apply level scaling
            for stat in base_stats:
                if stat == "hp":
                    base_stats[stat] = int(base_stats[stat] + (enemy_level * 15))
                elif stat == "energy":
                    # Energy doesn't scale with level
                    pass
                else:
                    base_stats[stat] = int(base_stats[stat] + (enemy_level * 2))

            # Apply enemy-specific modifiers
            if "Goblin" in enemy_name:
                base_stats["hp"] -= 10
                base_stats["defense"] -= 2
                base_stats["speed"] += 5
            elif "Troll" in enemy_name:
                base_stats["hp"] += 30
                base_stats["power"] += 5
                base_stats["speed"] -= 3
            elif "Dragon" in enemy_name:
                base_stats["hp"] += 50
                base_stats["power"] += 10
                base_stats["defense"] += 8
            elif "Slime" in enemy_name:
                base_stats["hp"] += 20
                base_stats["defense"] += 5
                base_stats["power"] -= 3
            elif "Skeleton" in enemy_name:
                base_stats["defense"] -= 5
                base_stats["speed"] += 3
            elif "Boss" in enemy_name:
                # Boss enemies are much stronger
                for stat in base_stats:
                    if stat != "energy":
                        base_stats[stat] = int(base_stats[stat] * 1.5)

            # Adjust based on player level to avoid huge disparities
            if player_level > enemy_level + 5:
                # If player is much higher level, buff the enemy
                level_diff = player_level - enemy_level
                modifier = min(1.5, 1 + (level_diff * 0.05))

                for stat in base_stats:
                    if stat != "energy":
                        base_stats[stat] = int(base_stats[stat] * modifier)

            return base_stats

        def generate_enemy_moves(enemy_name: str) -> List[BattleMove]:
            """Generate enemy moves based on their name"""
            # Default moves that all enemies have
            moves = [
                BattleMove("Strike", 0.8, 10, description="A basic attack"),
                BattleMove("Power Attack", 1.3, 20, description="A stronger attack")
            ]

            # Add enemy-specific moves
            if "Goblin" in enemy_name:
                moves.append(BattleMove("Sneak Attack", 1.1, 15, effect="bleed", 
                                        description="Causes bleeding damage over time"))
            elif "Troll" in enemy_name:
                moves.append(BattleMove("Smash", 1.8, 30, description="A devastating attack"))
            elif "Dragon" in enemy_name:
                moves.append(BattleMove("Fire Breath", 1.5, 25, effect="bleed",
                                        description="Deals fire damage over time"))
                moves.append(BattleMove("Tail Sweep", 1.2, 20, description="Hits with massive tail"))
            elif "Slime" in enemy_name:
                moves.append(BattleMove("Acid Splash", 0.9, 15, effect="bleed",
                                        description="Deals acid damage over time"))
            elif "Skeleton" in enemy_name:
                moves.append(BattleMove("Bone Throw", 0.7, 10, description="Throws a bone"))
            elif "Boss" in enemy_name:
                moves.append(BattleMove("Ultimate Attack", 2.0, 35, description="A devastating attack"))
                moves.append(BattleMove("Energy Drain", 0.6, 20, effect="energy_drain", 
                                        description="Drains opponent's energy"))

            return moves

        def calculate_exp_reward(enemy_level: int, player_level: int) -> int:
            """Calculate experience reward based on enemy and player levels"""
            # Increase base XP reward to make progression faster
            base_exp = 30 + (enemy_level * 15)  # Increased from 20 + (enemy_level * 10)

            # Apply level difference modifier with better rewards
            level_diff = enemy_level - player_level

            if level_diff >= 5:  # Enemy is much stronger
                modifier = 1.8  # Increased from 1.5
            elif level_diff >= 2:  # Enemy is stronger
                modifier = 1.4  # Increased from 1.2
            elif level_diff <= -5:  # Enemy is much weaker
                modifier = 0.6  # Increased from 0.5
            elif level_diff <= -2:  # Enemy is weaker
                modifier = 0.9  # Increased from 0.8
            else:  # Enemy is close to player level
                modifier = 1.2  # Increased from 1.0

            # Apply an additional scaling bonus for higher player levels
            # This helps counteract the increased XP requirements at higher levels
            level_scaling = 1.0
            if player_level > 20:
                level_scaling = 1.0 + min(0.5, (player_level - 20) * 0.02)  # Up to +50% at level 45+

            return int(base_exp * modifier * level_scaling)

        def calculate_gold_reward(enemy_level: int) -> int:
            """Calculate gold reward based on enemy level"""
            base_gold = 10 + (enemy_level * 5)

            # Add some randomness
            variance = random.uniform(0.8, 1.2)

            return int(base_gold * variance)

        # Removed the legacy cursed_energy reward function as we now use gold

        async def start_pvp_battle(ctx, target_member, player_data, target_data, data_manager):
            """Start a PvP battle between two players"""
            # Create player entities from player data
            from main import STARTER_CLASSES
            player_stats = player_data.get_stats(STARTER_CLASSES)

            player_entity = BattleEntity(
                ctx.author.display_name,
                player_stats,
                [
                    BattleMove("Quick Strike", 0.8, 10, description="A fast attack that costs little energy"),
                    BattleMove("Heavy Blow", 1.5, 25, description="A powerful strike with high damage"),
                    BattleMove("Focused Attack", 1.2, 15, effect="bleed", description="Causes bleeding damage over time"),
                    BattleMove("Energy Drain", 0.6, 20, effect="energy_drain", description="Drains enemy energy")
                ],
                is_player=True,
                player_data=player_data
            )

            target_stats = {
                "hp": target_data.hp,
                "power": target_data.strength,
                "defense": target_data.defense,
                "speed": target_data.dexterity
            }

            target_entity = BattleEntity(
                target_member.display_name,
                target_stats,
                [
                    BattleMove("Quick Strike", 0.8, 10, description="A fast attack that costs little energy"),
                    BattleMove("Heavy Blow", 1.5, 25, description="A powerful strike with high damage"),
                    BattleMove("Focused Attack", 1.2, 15, effect="bleed", description="Causes bleeding damage over time"),
                    BattleMove("Energy Drain", 0.6, 20, effect="energy_drain", description="Drains enemy energy")
                ],
                is_player=True,
                player_data=target_data
            )

            # Create battle embed
            embed = discord.Embed(
                title=f"⚔️ PvP Battle: {ctx.author.display_name} vs {target_member.display_name}",
                description=f"{ctx.author.mention} has challenged {target_member.mention} to a battle!",
                color=discord.Color.gold()
            )

            # Add player stats
            embed.add_field(
                name=f"{ctx.author.display_name} (Level {player_data.class_level})",
                value=f"HP: {player_entity.current_hp}/{player_entity.stats['hp']} ❤️\n"
                      f"Battle Energy: {player_entity.current_energy}/{player_entity.max_energy} ⚡\n"
                      f"Power: {player_entity.stats['power']} ⚔️\n"
                      f"Defense: {player_entity.stats['defense']} 🛡️",
                inline=True
            )

            # Add target stats
            embed.add_field(
                name=f"{target_member.display_name} (Level {target_data.class_level})",
                value=f"HP: {target_entity.current_hp}/{target_entity.stats['hp']} ❤️\n"
                      f"Battle Energy: {target_entity.current_energy}/{target_entity.max_energy} ⚡\n"
                      f"Power: {target_entity.stats['power']} ⚔️\n"
                      f"Defense: {target_entity.stats['defense']} 🛡️",
                inline=True
            )

            # Create battle view and send message
            battle_view = BattleView(player_entity, target_entity)
            message = await ctx.send(embed=embed, view=battle_view)

            # Wait for battle to complete
            result = await battle_view.wait()

            # Update battle energy
            player_data.battle_energy = player_entity.current_energy

            # Save data
            data_manager.save_data()

            # Check result
            if result:  # Timeout
                await message.edit(content="PvP battle timed out!", view=None)
            elif player_entity.is_alive():
                # Player won
                # Update PvP stats
                if not hasattr(player_data, "pvp_wins"):
                    player_data.pvp_wins = 0
                if not hasattr(target_data, "pvp_losses"):
                    target_data.pvp_losses = 0

                player_data.pvp_wins += 1
                target_data.pvp_losses += 1

                # Award rewards
                gold_reward = 50 + (target_data.class_level * 5)
                exp_reward = 30 + (target_data.class_level * 8)

                player_data.add_exp(exp_reward)
                player_data.add_gold(gold_reward)

                # Award small consolation reward to loser
                consolation_exp = int(exp_reward * 0.2)
                target_data.add_exp(consolation_exp)

                # Save updated data
                data_manager.save_data()

                # Create victory embed
                victory_embed = discord.Embed(
                    title="🏆 PvP Victory!",
                    description=f"{ctx.author.display_name} defeated {target_member.display_name} in battle!",
                    color=discord.Color.green()
                )

                victory_embed.add_field(
                    name="Rewards",
                    value=f"Experience: {exp_reward} XP 📊\n"
                          f"Gold: {gold_reward} 💰",
                    inline=False
                )

                # Add PvP stats
                victory_embed.add_field(
                    name="PvP Stats",
                    value=f"{ctx.author.display_name}: {player_data.pvp_wins} wins\n"
                          f"{target_member.display_name}: {target_data.pvp_losses} losses",
                    inline=False
                )

                # Check for level up
                if player_data.check_level_up():
                    victory_embed.add_field(
                        name="🎊 Level Up!",
                        value=f"{ctx.author.display_name} is now level {player_data.class_level}!\n"
                              f"You received 2 skill points!",
                        inline=False
                    )

                await ctx.send(embed=victory_embed)
            else:
                # Player lost
                # Update PvP stats
                if not hasattr(player_data, "pvp_losses"):
                    player_data.pvp_losses = 0
                if not hasattr(target_data, "pvp_wins"):
                    target_data.pvp_wins = 0

                player_data.pvp_losses += 1
                target_data.pvp_wins += 1

                # Award rewards to winner
                gold_reward = 50 + (player_data.class_level * 5)
                exp_reward = 30 + (player_data.class_level * 8)

                target_data.add_exp(exp_reward)
                target_data.add_gold(gold_reward)

                # Award small consolation reward to loser
                consolation_exp = int(exp_reward * 0.2)
                player_data.add_exp(consolation_exp)

                # Save updated data
                data_manager.save_data()

                # Create defeat embed
                defeat_embed = discord.Embed(
                    title="💀 PvP Defeat",
                    description=f"{ctx.author.display_name} was defeated by {target_member.display_name} in battle!",
                    color=discord.Color.red()
                )

                defeat_embed.add_field(
                    name="Consolation",
                    value=f"Experience: {consolation_exp} XP 📊",
                    inline=False
                )

                # Add PvP stats
                defeat_embed.add_field(
                    name="PvP Stats",
                    value=f"{ctx.author.display_name}: {player_data.pvp_losses} losses\n"
                          f"{target_member.display_name}: {target_data.pvp_wins} wins",
                    inline=False
                )

                # Check for level up on opponent
                if target_data.check_level_up():
                    defeat_embed.add_field(
                        name="🎊 Level Up!",
                        value=f"{target_member.display_name} is now level {target_data.class_level}!",
                        inline=False
                    )

                await ctx.send(embed=defeat_embed)