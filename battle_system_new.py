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
        super().__init__(
            style=discord.ButtonStyle.primary,
            label=f"{move.name} ({move.energy_cost} ⚡)",
            row=row,
            disabled=False
        )
        self.move = move
        
    async def callback(self, interaction: discord.Interaction):
        await self.view.on_move_selected(interaction, self.move)

class ItemButton(Button):
    def __init__(self, item_name: str, item_effect: str, row: int = 0):
        super().__init__(
            style=discord.ButtonStyle.success,
            label=item_name,
            row=row,
            disabled=False
        )
        self.item_name = item_name
        self.item_effect = item_effect
        
    async def callback(self, interaction: discord.Interaction):
        await self.view.on_item_selected(interaction, self.item_name, self.item_effect)

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
        for i, move in enumerate(self.player.moves):
            # Check if player has enough energy for the move
            disabled = self.player.current_energy < move.energy_cost
            button = BattleMoveButton(move, row=0)
            button.disabled = disabled
            self.add_item(button)
            
        # Check for usable items (potions)
        if self.player.is_player and self.player.player_data:
            player_data = self.player.player_data
            
            # Look for potions in inventory
            potions = []
            for inv_item in player_data.inventory:
                item = inv_item.item
                # Check if it's a potion (potions typically have healing or energy restore effects)
                if (item.item_type.lower() == "potion" or 
                    "potion" in item.name.lower() or 
                    "elixir" in item.name.lower()):
                    effect = "healing" if "heal" in item.description.lower() else "energy"
                    potions.append((item.name, effect))
            
            # Add potion buttons (up to 3)
            for i, (potion_name, effect) in enumerate(potions[:3]):
                self.add_item(ItemButton(potion_name, effect, row=1))
            
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
    
    async def on_item_selected(self, interaction: discord.Interaction, item_name: str, item_effect: str):
        # Process item use
        player_data = self.player.player_data
        
        # Find the actual item in inventory
        used_item = None
        used_inv_item = None
        for inv_item in player_data.inventory:
            if inv_item.item.name == item_name:
                used_item = inv_item.item
                used_inv_item = inv_item
                break
        
        if not used_item:
            await interaction.response.edit_message(
                content=f"❌ Item {item_name} not found in inventory!",
                view=self
            )
            return
        
        # Apply item effect
        effect_message = ""
        if item_effect == "healing":
            # Healing potions restore a percentage of max HP
            heal_amount = int(self.player.stats["hp"] * 0.3)  # 30% of max HP
            self.player.current_hp = min(self.player.stats["hp"], self.player.current_hp + heal_amount)
            effect_message = f"🧪 Used {item_name} to restore {heal_amount} HP!"
        elif item_effect == "energy":
            # Energy potions restore a percentage of max energy
            energy_amount = int(self.player.max_energy * 0.4)  # 40% of max energy
            self.player.current_energy = min(self.player.max_energy, self.player.current_energy + energy_amount)
            effect_message = f"⚡ Used {item_name} to restore {energy_amount} energy!"
        
        # Remove one of the item from inventory
        if used_inv_item.quantity > 1:
            used_inv_item.quantity -= 1
        else:
            player_data.inventory.remove(used_inv_item)
        
        # Update the view with the results
        await interaction.response.edit_message(
            content=effect_message,
            view=self
        )
        
        # Enemy turn after item use
        await asyncio.sleep(1)
        
        # Choose enemy move
        available_moves = [m for m in self.enemy.moves if self.enemy.current_energy >= m.energy_cost]
        if not available_moves:
            self.enemy.current_energy = min(self.enemy.max_energy, 
                                           self.enemy.current_energy + 30)
            await interaction.edit_original_response(
                content=f"{effect_message}\n"
                       f"🔄 {self.enemy.name} is exhausted and regains 30 energy!",
                view=self
            )
        else:
            enemy_move = random.choice(available_moves)
            enemy_damage, enemy_effect_msg = self.enemy.apply_move(enemy_move, self.player)
            
            await interaction.edit_original_response(
                content=f"{effect_message}\n"
                       f"⚔️ {self.enemy.name} used {enemy_move.name} for {enemy_damage} damage!{enemy_effect_msg}",
                view=self
            )
            
            if not self.player.is_alive():
                self.stop()
                await asyncio.sleep(1)
                await interaction.edit_original_response(
                    content=f"💀 Defeat! You were defeated by {self.enemy.name}!",
                    view=None
                )
                return
        
        # Update status effects and buttons
        player_status_msg = self.player.update_status_effects()
        enemy_status_msg = self.enemy.update_status_effects()
        self.update_buttons()
        
        # Show battle status with dynamic maximum energy
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

async def start_battle(ctx, player_data: PlayerData, enemy_name: str, enemy_level: int, data_manager: DataManager):
    """Start a battle between the player and an enemy"""
    # Get player class
    class_data = data_manager.class_data
    player_class = class_data.get(player_data.class_name, {"name": "Unknown", "base_stats": {}})
    
    # Generate player stats
    player_stats = player_data.get_stats(class_data)
    
    # Generate player battle moves from skills
    player_moves = []
    for skill_id, skill_data in data_manager.skills.items():
        if skill_data["class"] == player_data.class_name or skill_data.get("universal", False):
            if player_data.class_level >= skill_data["level_req"]:
                # Check if the skill is on cooldown
                if skill_id in player_data.skill_cooldowns:
                    cooldown_end = player_data.skill_cooldowns[skill_id]
                    if cooldown_end > datetime.datetime.now().isoformat():
                        continue  # Skip this skill, it's on cooldown
                
                player_moves.append(BattleMove(
                    name=skill_data["name"],
                    damage_multiplier=skill_data["damage_multiplier"],
                    energy_cost=skill_data["energy_cost"],
                    effect=skill_data.get("effect"),
                    description=skill_data.get("description")
                ))
    
    # If no player moves, add basic attack
    if not player_moves:
        player_moves.append(BattleMove("Basic Attack", 1.0, 10))
    
    # Create player battle entity
    player_entity = BattleEntity(
        name=f"{ctx.author.name}'s {player_data.class_name}",
        stats=player_stats,
        moves=player_moves,
        is_player=True,
        player_data=player_data
    )
    
    # Generate enemy stats and moves based on level
    enemy_stats = generate_enemy_stats(enemy_name, enemy_level, player_data.class_level)
    enemy_moves = generate_enemy_moves(enemy_name)
    
    # Create enemy battle entity
    enemy_entity = BattleEntity(
        name=f"Lvl {enemy_level} {enemy_name}",
        stats=enemy_stats,
        moves=enemy_moves
    )
    
    # Create battle embed
    embed = discord.Embed(
        title=f"⚔️ Battle: {player_entity.name} vs {enemy_entity.name}",
        description=f"**Your Stats:**\nHP: {player_stats['hp']}\nPower: {player_stats['power']}\nDefense: {player_stats['defense']}\nSpeed: {player_stats['speed']}\n\n"
                   f"**Enemy Stats:**\nHP: {enemy_stats['hp']}\nPower: {enemy_stats['power']}\nDefense: {enemy_stats['defense']}\nSpeed: {enemy_stats['speed']}",
        color=0xFF5500
    )
    
    # Create battle view
    battle_view = BattleView(player_entity, enemy_entity)
    
    # Start battle
    sent_message = await ctx.send(embed=embed, view=battle_view)
    
    # Wait for battle to finish or time out
    await battle_view.wait()
    
    # If battle was won, update player data
    if not enemy_entity.is_alive():
        # Calculate rewards
        exp_reward = calculate_exp_reward(enemy_level, player_data.class_level)
        gold_reward = calculate_gold_reward(enemy_level)
        cursed_energy = calculate_cursed_energy_reward(enemy_level)
        
        # Apply rewards
        level_up = player_data.add_exp(exp_reward)
        player_data.add_cursed_energy(cursed_energy)
        
        # Save updated energy to player data
        player_data.battle_energy = player_entity.current_energy
        
        # Update win count
        player_data.wins += 1
        
        # Save data
        data_manager.save_data()
        
        # Send rewards message
        rewards_embed = discord.Embed(
            title="🎁 Battle Rewards",
            description=f"You defeated a Lvl {enemy_level} {enemy_name}!",
            color=0x00FF00
        )
        rewards_embed.add_field(name="Experience", value=f"+{exp_reward} XP" + (" (Level Up!)" if level_up else ""), inline=True)
        rewards_embed.add_field(name="Cursed Energy", value=f"+{cursed_energy} ⚡", inline=True)
        
        await ctx.send(embed=rewards_embed)
        
        # Update quest progress (daily wins)
        if hasattr(data_manager, 'quest_manager'):
            completed_quests = data_manager.quest_manager.update_quest_progress(player_data, "daily_wins")
            for quest in completed_quests:
                quest_embed = discord.Embed(
                    title="✅ Quest Completed!",
                    description=f"**{quest['name']}**\n{quest['description']}",
                    color=0xFFD700
                )
                quest_embed.add_field(name="Rewards", value=f"XP: {quest['rewards'].get('xp', 0)}\nCursed Energy: {quest['rewards'].get('cursed_energy', 0)}")
                await ctx.send(embed=quest_embed)
    
    elif not player_entity.is_alive():
        # Update loss count
        player_data.losses += 1
        
        # Save updated energy to player data
        player_data.battle_energy = player_entity.current_energy
        
        # Save data
        data_manager.save_data()
        
        await ctx.send(f"😔 You were defeated by the {enemy_name}. Better luck next time!")

def generate_enemy_stats(enemy_name: str, enemy_level: int, player_level: int) -> Dict[str, int]:
    """Generate enemy stats based on name and level"""
    # Base stats that scale with level
    base_hp = 50 + (enemy_level * 10)
    base_power = 10 + (enemy_level * 2)
    base_defense = 5 + (enemy_level * 1.5)
    base_speed = 8 + (enemy_level * 1.2)
    base_energy = 100  # Base energy
    
    # Adjust stats based on enemy type
    if "curse" in enemy_name.lower():
        # Cursed enemies have more power but less defense
        base_power *= 1.2
        base_defense *= 0.8
    elif "tank" in enemy_name.lower() or "golem" in enemy_name.lower():
        # Tanks have more HP and defense but less speed
        base_hp *= 1.5
        base_defense *= 1.3
        base_speed *= 0.7
    elif "speed" in enemy_name.lower() or "ninja" in enemy_name.lower():
        # Fast enemies have more speed and power but less HP
        base_speed *= 1.5
        base_power *= 1.1
        base_hp *= 0.8
    
    # Bosses have significantly enhanced stats
    if "boss" in enemy_name.lower():
        base_hp *= 2.0
        base_power *= 1.5
        base_defense *= 1.3
        base_energy = 150
    
    # Make enemies scale a bit with player level to avoid trivial battles
    if player_level > enemy_level + 5:
        level_diff = player_level - (enemy_level + 5)
        scaling_factor = 1.0 + (level_diff * 0.05)  # 5% increase per level difference
        base_hp *= scaling_factor
        base_power *= scaling_factor
        base_defense *= scaling_factor
    
    return {
        "hp": int(base_hp),
        "power": int(base_power),
        "defense": int(base_defense),
        "speed": int(base_speed),
        "energy": int(base_energy)
    }

def generate_enemy_moves(enemy_name: str) -> List[BattleMove]:
    """Generate enemy moves based on their name"""
    moves = []
    
    # All enemies have a basic attack
    moves.append(BattleMove("Attack", 1.0, 10))
    
    # Add specialized moves based on enemy type
    if "curse" in enemy_name.lower():
        moves.append(BattleMove("Curse Strike", 1.3, 20, effect="energy_drain"))
    elif "tank" in enemy_name.lower() or "golem" in enemy_name.lower():
        moves.append(BattleMove("Heavy Blow", 1.5, 25))
    elif "speed" in enemy_name.lower() or "ninja" in enemy_name.lower():
        moves.append(BattleMove("Quick Strike", 0.8, 15, effect="stun"))
    
    # Bosses get an extra powerful move
    if "boss" in enemy_name.lower():
        moves.append(BattleMove("Devastating Attack", 2.0, 40, effect="bleed"))
    
    return moves

def calculate_exp_reward(enemy_level: int, player_level: int) -> int:
    """Calculate experience reward based on enemy and player levels"""
    base_exp = 10 + (enemy_level * 5)
    
    # Reduce XP if player is higher level than the enemy
    if player_level > enemy_level:
        level_diff = player_level - enemy_level
        exp_reduction = 0.1 * level_diff  # 10% reduction per level difference
        exp_reduction = min(0.9, exp_reduction)  # Cap at 90% reduction
        base_exp *= (1.0 - exp_reduction)
    
    # Bonus XP if player is lower level than the enemy
    elif player_level < enemy_level:
        level_diff = enemy_level - player_level
        exp_bonus = 0.2 * level_diff  # 20% bonus per level difference
        base_exp *= (1.0 + exp_bonus)
    
    return max(1, int(base_exp))

def calculate_gold_reward(enemy_level: int) -> int:
    """Calculate cursed energy reward based on enemy level"""
    return calculate_cursed_energy_reward(enemy_level)

def calculate_cursed_energy_reward(enemy_level: int) -> int:
    """Calculate cursed energy reward based on enemy level"""
    base_reward = 5 + (enemy_level * 3)
    
    # Add some randomness
    variance = random.uniform(0.8, 1.2)
    
    return max(1, int(base_reward * variance))

async def start_pvp_battle(ctx, target_member, player_data, target_data, data_manager):
    """Start a PvP battle between two players"""
    # Implementation for PvP battle would be similar to PvE but with two player entities
    pass