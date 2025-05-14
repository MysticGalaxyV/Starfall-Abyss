import discord
from discord.ui import View, Button
import random
import asyncio
from typing import Dict, List, Tuple, Optional
import datetime

from data_manager import PlayerData
from constants import BATTLE_COOLDOWN, CRITICAL_MULTIPLIER, ABILITY_COSTS, CLASSES

class BattleButton(discord.ui.Button):
    """Custom button for battle actions"""
    def __init__(self, label: str, emoji: str, style: discord.ButtonStyle, custom_id: str, disabled: bool = False):
        super().__init__(label=label, emoji=emoji, style=style, custom_id=custom_id, disabled=disabled)

class BattleView(View):
    """View for battle interaction buttons"""
    def __init__(self, player: PlayerData, opponent: PlayerData, timeout=30):
        super().__init__(timeout=timeout)
        self.player = player
        self.opponent = opponent
        self.action = None
        self.ability_used = None
        
        # Add basic attack button
        attack_btn = BattleButton(
            label="Attack", 
            emoji="⚔️", 
            style=discord.ButtonStyle.danger, 
            custom_id="attack"
        )
        attack_btn.callback = self.attack_callback
        self.add_item(attack_btn)
        
        # Add defend button
        defend_btn = BattleButton(
            label="Defend", 
            emoji="🛡️", 
            style=discord.ButtonStyle.primary, 
            custom_id="defend"
        )
        defend_btn.callback = self.defend_callback
        self.add_item(defend_btn)
        
        # Add ability button if player has abilities
        if player.class_name and CLASSES.get(player.class_name, {}).get("abilities", {}):
            ability_name = CLASSES[player.class_name]["abilities"]["active"]
            ability_cost = ABILITY_COSTS.get(ability_name, 20)
            
            ability_btn = BattleButton(
                label=ability_name, 
                emoji="✨", 
                style=discord.ButtonStyle.success, 
                custom_id="ability",
                disabled=player.cursed_energy < ability_cost
            )
            ability_btn.callback = self.ability_callback
            self.add_item(ability_btn)
        
        # Add item button
        item_btn = BattleButton(
            label="Use Item", 
            emoji="🎒", 
            style=discord.ButtonStyle.secondary, 
            custom_id="item",
            disabled=len([i for i in player.inventory if i.get("type") == "consumable"]) == 0
        )
        item_btn.callback = self.item_callback
        self.add_item(item_btn)
        
        # Add flee button
        flee_btn = BattleButton(
            label="Flee", 
            emoji="💨", 
            style=discord.ButtonStyle.secondary, 
            custom_id="flee"
        )
        flee_btn.callback = self.flee_callback
        self.add_item(flee_btn)
    
    async def attack_callback(self, interaction: discord.Interaction):
        """Handle basic attack action"""
        self.action = "attack"
        await interaction.response.defer()
        self.stop()
    
    async def defend_callback(self, interaction: discord.Interaction):
        """Handle defend action"""
        self.action = "defend"
        await interaction.response.defer()
        self.stop()
    
    async def ability_callback(self, interaction: discord.Interaction):
        """Handle special ability action"""
        self.action = "ability"
        
        # Get the active ability for this class
        ability_name = CLASSES[self.player.class_name]["abilities"]["active"]
        self.ability_used = ability_name
        
        await interaction.response.defer()
        self.stop()
    
    async def item_callback(self, interaction: discord.Interaction):
        """Handle using an item"""
        # Show a follow-up with consumable items
        consumables = [item for item in self.player.inventory if item.get("type") == "consumable"]
        
        if not consumables:
            await interaction.response.send_message("You don't have any usable items!", ephemeral=True)
            return
        
        # Create a new view for item selection
        view = ItemSelectView(consumables)
        await interaction.response.send_message("Select an item to use:", view=view, ephemeral=True)
        
        # Wait for item selection
        await view.wait()
        
        if view.selected_item:
            self.action = "item"
            self.ability_used = view.selected_item
            self.stop()
        else:
            # No item was selected, let the user choose another action
            await interaction.followup.send("Item selection canceled. Choose another action.", ephemeral=True)
    
    async def flee_callback(self, interaction: discord.Interaction):
        """Handle flee action"""
        self.action = "flee"
        await interaction.response.defer()
        self.stop()

class ItemSelectView(View):
    """View for selecting an item during battle"""
    def __init__(self, items: List[Dict], timeout=30):
        super().__init__(timeout=timeout)
        self.selected_item = None
        
        # Add a button for each item
        for i, item in enumerate(items):
            btn = Button(
                label=item["name"], 
                emoji="🧪", 
                style=discord.ButtonStyle.secondary,
                custom_id=f"item_{i}"
            )
            
            # Create a callback for this button
            async def make_callback(i=i, item=item):
                async def callback(interaction):
                    self.selected_item = item["name"]
                    await interaction.response.defer()
                    self.stop()
                return callback
            
            btn.callback = await make_callback()
            self.add_item(btn)

class Battle:
    """Handles battle logic between two players or a player and NPC"""
    def __init__(self, player: PlayerData, opponent: Optional[PlayerData] = None, is_npc: bool = False):
        self.player = player
        self.opponent = opponent
        self.is_npc = is_npc
        self.player_defending = False
        self.opponent_defending = False
        self.turn = 0  # 0 for player, 1 for opponent
        self.battle_log = []
        
        # If opponent is NPC, create stats based on player level
        if is_npc and not opponent:
            from constants import generate_npc_opponent
            self.opponent = generate_npc_opponent(player.class_level)
    
    async def start_battle(self, ctx) -> Tuple[bool, str]:
        """
        Begin the battle sequence
        Returns: (victory, battle_log_summary)
        """
        # Display initial battle state
        embed = self.create_battle_embed()
        message = await ctx.send(embed=embed)
        
        # Determine who goes first based on speed
        if self.player.current_stats["speed"] >= self.opponent.current_stats["speed"]:
            self.turn = 0  # Player goes first
            self.battle_log.append(f"**{ctx.author.name}** goes first due to higher speed!")
        else:
            self.turn = 1  # Opponent goes first
            self.battle_log.append(f"**{self.opponent.class_name}** goes first due to higher speed!")
        
        # Update the embed with turn info
        embed = self.create_battle_embed()
        await message.edit(embed=embed)
        
        # Main battle loop
        battle_active = True
        while battle_active:
            # Reset defending status at the start of each round
            if self.turn == 0:
                self.opponent_defending = False
            else:
                self.player_defending = False
                
            if self.turn == 0:  # Player's turn
                # Create battle view for player's action selection
                view = BattleView(self.player, self.opponent, timeout=30)
                await message.edit(embed=self.create_battle_embed(), view=view)
                
                # Wait for player's action
                await view.wait()
                
                # If the view timed out (no response)
                if view.action is None:
                    self.battle_log.append(f"**{ctx.author.name}** took too long to decide and missed their turn!")
                    action = "timeout"
                else:
                    action = view.action
                    ability_used = view.ability_used
                
                # Process player's action
                battle_active = await self.process_player_action(ctx, action, ability_used)
            else:  # Opponent's turn
                if self.is_npc:
                    # AI opponent selects an action
                    action = self.get_npc_action()
                    await asyncio.sleep(1)  # Add a delay to make it feel more natural
                    battle_active = await self.process_opponent_action(ctx, action)
                else:
                    # For PvP, the other player would take their turn here
                    # This is simplified for the AI opponent version
                    pass
            
            # Update the battle display
            embed = self.create_battle_embed()
            await message.edit(embed=embed, view=None)
            
            # Check if battle should end
            if self.player.current_stats["hp"] <= 0:
                self.battle_log.append(f"**{ctx.author.name}** has been defeated!")
                victory = False
                battle_active = False
            elif self.opponent.current_stats["hp"] <= 0:
                self.battle_log.append(f"**{self.opponent.class_name}** has been defeated!")
                victory = True
                battle_active = False
            
            # Switch turns if battle continues
            if battle_active:
                self.turn = 1 - self.turn  # Toggle between 0 and 1
        
        # Update player's last battle timestamp
        self.player.last_battle = datetime.datetime.now()
        
        # Return the battle result and log
        battle_log_summary = "\n".join(self.battle_log[-10:])  # Last 10 lines for summary
        return victory, battle_log_summary
    
    async def process_player_action(self, ctx, action: str, ability_used: str = None) -> bool:
        """
        Process the player's chosen action
        Returns: bool indicating if battle should continue
        """
        player_name = ctx.author.name
        
        if action == "attack":
            # Calculate damage
            damage, critical = self.calculate_damage(
                self.player.current_stats["power"], 
                self.opponent.current_stats["defense"],
                self.opponent_defending
            )
            
            # Apply damage to opponent
            self.opponent.current_stats["hp"] -= damage
            
            # Add to battle log
            if critical:
                self.battle_log.append(f"**{player_name}** lands a critical hit for **{damage}** damage! 💥")
            else:
                self.battle_log.append(f"**{player_name}** attacks for **{damage}** damage.")
            
            # Use some energy for the attack
            self.player.cursed_energy = max(0, self.player.cursed_energy - 5)
            
        elif action == "defend":
            self.player_defending = True
            self.battle_log.append(f"**{player_name}** takes a defensive stance. 🛡️")
            
            # Restore some energy while defending
            energy_restored = random.randint(10, 20)
            self.player.restore_energy(energy_restored)
            self.battle_log.append(f"**{player_name}** regains **{energy_restored}** cursed energy.")
            
        elif action == "ability":
            # Get ability details
            ability_name = ability_used
            ability_cost = ABILITY_COSTS.get(ability_name, 20)
            
            # Check if player has enough energy
            if self.player.cursed_energy < ability_cost:
                self.battle_log.append(f"**{player_name}** doesn't have enough cursed energy to use {ability_name}!")
                return True
            
            # Use the ability
            self.player.cursed_energy -= ability_cost
            
            # Apply ability effects based on name
            if ability_name == "Cursed Combo":
                # Multiple hits with lower accuracy
                hits = random.randint(2, 4)
                total_damage = 0
                
                for i in range(hits):
                    hit_damage, critical = self.calculate_damage(
                        self.player.current_stats["power"] * 0.6,  # Lower damage per hit
                        self.opponent.current_stats["defense"],
                        self.opponent_defending,
                        accuracy=0.8  # Lower accuracy
                    )
                    
                    if hit_damage > 0:
                        total_damage += hit_damage
                        self.battle_log.append(f"**{player_name}**'s Cursed Combo hits for **{hit_damage}** damage!")
                    else:
                        self.battle_log.append(f"**{player_name}**'s Cursed Combo misses!")
                
                self.opponent.current_stats["hp"] -= total_damage
                self.battle_log.append(f"**{player_name}**'s Cursed Combo dealt a total of **{total_damage}** damage!")
                
            elif ability_name == "Barrier Pulse":
                # Defensive ability that also deals damage
                self.player_defending = True
                
                # Calculate defensive pulse damage
                damage, critical = self.calculate_damage(
                    self.player.current_stats["defense"] * 0.8,  # Damage based on defense
                    self.opponent.current_stats["defense"] * 0.5,  # Less affected by opponent's defense
                    self.opponent_defending
                )
                
                self.opponent.current_stats["hp"] -= damage
                self.battle_log.append(f"**{player_name}** creates a barrier that pulses for **{damage}** damage!")
                self.battle_log.append(f"**{player_name}** is protected by the barrier. 🛡️")
                
            elif ability_name == "Shadowstep":
                # High damage attack with chance to avoid next attack
                damage, critical = self.calculate_damage(
                    self.player.current_stats["power"] * 1.5,  # Higher damage multiplier
                    self.opponent.current_stats["defense"],
                    self.opponent_defending
                )
                
                self.opponent.current_stats["hp"] -= damage
                self.battle_log.append(f"**{player_name}** uses Shadowstep and strikes for **{damage}** damage!")
                
                # Chance to dodge next attack
                if random.random() < 0.5:
                    self.player_defending = True
                    self.battle_log.append(f"**{player_name}** fades into the shadows, making it harder to be hit! 👻")
            
            # Add custom abilities for other classes here
            
        elif action == "item":
            # Find the item in inventory
            item_name = ability_used
            item = None
            for inv_item in self.player.inventory:
                if inv_item["name"] == item_name:
                    item = inv_item
                    break
            
            if not item:
                self.battle_log.append(f"**{player_name}** couldn't find the item!")
                return True
            
            # Apply item effects
            if item["type"] == "consumable":
                if "heal" in item:
                    heal_amount = item["heal"]
                    self.player.heal(heal_amount)
                    self.battle_log.append(f"**{player_name}** uses **{item_name}** and heals for **{heal_amount}** HP!")
                
                if "energy" in item:
                    energy_amount = item["energy"]
                    self.player.restore_energy(energy_amount)
                    self.battle_log.append(f"**{player_name}** uses **{item_name}** and restores **{energy_amount}** cursed energy!")
                
                if "effect" in item:
                    effect = item["effect"]
                    if effect == "strength":
                        buff_amount = item.get("buff_amount", 5)
                        # Temporary buff for this battle only
                        self.player.current_stats["power"] += buff_amount
                        self.battle_log.append(f"**{player_name}** uses **{item_name}** and gains **{buff_amount}** power!")
                    
                    # Add other effects as needed
            
            # Remove the item from inventory
            self.player.remove_from_inventory(item_name)
            
        elif action == "flee":
            # Chance to flee based on speed difference
            flee_chance = 0.3 + max(0, (self.player.current_stats["speed"] - self.opponent.current_stats["speed"]) * 0.05)
            fled = random.random() < flee_chance
            
            if fled:
                self.battle_log.append(f"**{player_name}** successfully fled from battle! 💨")
                return False  # End battle
            else:
                self.battle_log.append(f"**{player_name}** tried to flee but couldn't escape!")
        
        elif action == "timeout":
            # Player took too long, already logged in the battle loop
            pass
        
        # Check if opponent is defeated
        if self.opponent.current_stats["hp"] <= 0:
            self.opponent.current_stats["hp"] = 0
            return False  # End battle
            
        return True  # Continue battle
    
    async def process_opponent_action(self, ctx, action: str) -> bool:
        """
        Process the opponent's action
        Returns: bool indicating if battle should continue
        """
        if action == "attack":
            # Calculate damage
            damage, critical = self.calculate_damage(
                self.opponent.current_stats["power"], 
                self.player.current_stats["defense"],
                self.player_defending
            )
            
            # Apply damage to player
            self.player.current_stats["hp"] -= damage
            
            # Add to battle log
            if critical:
                self.battle_log.append(f"**{self.opponent.class_name}** lands a critical hit for **{damage}** damage! 💥")
            else:
                self.battle_log.append(f"**{self.opponent.class_name}** attacks for **{damage}** damage.")
                
        elif action == "defend":
            self.opponent_defending = True
            self.battle_log.append(f"**{self.opponent.class_name}** takes a defensive stance. 🛡️")
            
        elif action == "ability":
            # NPC uses a generic ability based on their class
            ability_name = "Special Attack"
            
            # Calculate ability damage
            damage = int(self.opponent.current_stats["power"] * 1.3)
            if self.player_defending:
                damage = int(damage * 0.6)
                
            self.player.current_stats["hp"] -= damage
            self.battle_log.append(f"**{self.opponent.class_name}** uses **{ability_name}** for **{damage}** damage!")
            
        # Check if player is defeated
        if self.player.current_stats["hp"] <= 0:
            self.player.current_stats["hp"] = 0
            return False  # End battle
            
        return True  # Continue battle
    
    def get_npc_action(self) -> str:
        """Determine the AI opponent's action based on the battle state"""
        # Simple AI decision making
        if self.opponent.current_stats["hp"] < self.opponent.current_stats["max_hp"] * 0.3:
            # Low health, high chance to defend
            if random.random() < 0.6:
                return "defend"
            
        if not self.player_defending and random.random() < 0.2:
            # Player isn't defending, chance to use ability
            return "ability"
            
        # Default to attack
        return "attack"
    
    def calculate_damage(self, attacker_power: float, defender_defense: float, 
                         is_defending: bool, accuracy: float = 0.95) -> Tuple[int, bool]:
        """
        Calculate damage for an attack
        Returns: (damage_amount, is_critical)
        """
        # Check if attack hits based on accuracy
        if random.random() > accuracy:
            return 0, False
            
        # Base damage calculation
        base_damage = max(1, attacker_power - defender_defense * 0.5)
        
        # Add randomness
        damage = random.uniform(base_damage * 0.8, base_damage * 1.2)
        
        # Critical hit chance (10%)
        critical = random.random() < 0.1
        if critical:
            damage *= CRITICAL_MULTIPLIER
            
        # Reduce damage if defending
        if is_defending:
            damage *= 0.5
            
        return int(damage), critical
    
    def create_battle_embed(self) -> discord.Embed:
        """Create an embed displaying the current battle state"""
        embed = discord.Embed(
            title="⚔️ Battle",
            description="Turn-based battle in progress",
            color=discord.Color.red()
        )
        
        # Player information
        player_hp_percent = self.player.current_stats["hp"] / self.player.current_stats["max_hp"]
        player_hp_bar = self.create_health_bar(player_hp_percent)
        player_ce_percent = self.player.cursed_energy / self.player.max_cursed_energy
        player_ce_bar = self.create_energy_bar(player_ce_percent)
        
        embed.add_field(
            name=f"Your Character: {self.player.class_name}",
            value=(
                f"HP: {self.player.current_stats['hp']}/{self.player.current_stats['max_hp']} {player_hp_bar}\n"
                f"CE: {self.player.cursed_energy}/{self.player.max_cursed_energy} {player_ce_bar}\n"
                f"State: {'🛡️ Defending' if self.player_defending else '⚔️ Combat Ready'}"
            ),
            inline=False
        )
        
        # Opponent information
        opponent_hp_percent = self.opponent.current_stats["hp"] / self.opponent.current_stats["max_hp"]
        opponent_hp_bar = self.create_health_bar(opponent_hp_percent)
        
        embed.add_field(
            name=f"Opponent: {self.opponent.class_name}",
            value=(
                f"HP: {self.opponent.current_stats['hp']}/{self.opponent.current_stats['max_hp']} {opponent_hp_bar}\n"
                f"State: {'🛡️ Defending' if self.opponent_defending else '⚔️ Combat Ready'}"
            ),
            inline=False
        )
        
        # Battle log (last 5 entries)
        if self.battle_log:
            log_text = "\n".join(self.battle_log[-5:])
            embed.add_field(name="Battle Log", value=log_text, inline=False)
        
        # Turn indicator
        if len(self.battle_log) > 0:  # Only show after battle has started
            turn_text = "**Your turn!**" if self.turn == 0 else f"**{self.opponent.class_name}'s turn!**"
            embed.set_footer(text=turn_text)
            
        return embed
    
    def create_health_bar(self, percent: float) -> str:
        """Create a visual health bar"""
        filled = "█" * int(percent * 10)
        empty = "░" * (10 - int(percent * 10))
        
        # Color based on health percentage
        if percent > 0.7:
            return f"[{filled}{empty}] 🟢"
        elif percent > 0.3:
            return f"[{filled}{empty}] 🟡"
        else:
            return f"[{filled}{empty}] 🔴"
    
    def create_energy_bar(self, percent: float) -> str:
        """Create a visual energy bar"""
        filled = "█" * int(percent * 10)
        empty = "░" * (10 - int(percent * 10))
        return f"[{filled}{empty}] ✨"

async def handle_battle_rewards(ctx, player: PlayerData, opponent: PlayerData, victory: bool, is_npc: bool):
    """Handle rewards after a battle"""
    if victory:
        # Calculate XP reward
        xp_reward = int(opponent.class_level * 15 * random.uniform(0.8, 1.2))
        
        # Calculate currency reward
        currency_reward = int(opponent.class_level * 10 * random.uniform(0.8, 1.2))
        
        # Apply rewards
        level_up = player.add_exp(xp_reward)
        player.currency += currency_reward
        player.wins += 1
        
        # Create reward embed
        embed = discord.Embed(
            title="🎉 Victory!",
            description=f"You defeated {opponent.class_name}!",
            color=discord.Color.green()
        )
        
        embed.add_field(
            name="Rewards",
            value=(
                f"XP: +{xp_reward}\n"
                f"Currency: +{currency_reward} 🌀\n"
            ),
            inline=False
        )
        
        if level_up:
            embed.add_field(
                name="Level Up!",
                value=(
                    f"You reached level {player.class_level}!\n"
                    f"You gained 3 skill points!\n"
                    f"Use !skills to allocate them."
                ),
                inline=False
            )
        
        # Chance for item drop from NPC
        if is_npc and random.random() < 0.3:
            from constants import generate_random_item
            item = generate_random_item(player.class_level)
            player.add_to_inventory(item)
            
            embed.add_field(
                name="Item Drop!",
                value=f"You found: **{item['name']}**\n{item['description']}",
                inline=False
            )
        
        await ctx.send(embed=embed)
    else:
        # Handle defeat
        player.losses += 1
        
        embed = discord.Embed(
            title="😞 Defeat",
            description=f"You were defeated by {opponent.class_name}.",
            color=discord.Color.red()
        )
        
        # Small consolation prize
        consolation_xp = int(opponent.class_level * 5 * random.uniform(0.8, 1.2))
        player.add_exp(consolation_xp)
        
        embed.add_field(
            name="Consolation",
            value=f"You still gained {consolation_xp} XP from the experience.",
            inline=False
        )
        
        await ctx.send(embed=embed)
