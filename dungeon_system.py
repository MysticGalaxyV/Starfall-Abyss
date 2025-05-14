import discord
from discord.ui import View, Button
import random
import asyncio
from typing import Dict, List, Optional, Tuple
import datetime

from data_manager import PlayerData
from constants import DUNGEONS, DUNGEON_COOLDOWN, DUNGEON_ENEMIES, ITEM_RARITY

class DungeonView(View):
    """Interactive view for dungeon combat"""
    def __init__(self, player: PlayerData, enemy: Dict, timeout=30):
        super().__init__(timeout=timeout)
        self.player = player
        self.enemy = enemy
        self.result = None
        
        # Attack Button
        attack_btn = Button(label="Attack", emoji="⚔️", style=discord.ButtonStyle.danger, custom_id="attack")
        attack_btn.callback = self.attack_callback
        self.add_item(attack_btn)
        
        # Defend Button
        defend_btn = Button(label="Defend", emoji="🛡️", style=discord.ButtonStyle.primary, custom_id="defend")
        defend_btn.callback = self.defend_callback
        self.add_item(defend_btn)
        
        # Special Button - class-specific
        if player.class_name:
            ability_name = "Special"
            if player.class_name in ["Spirit Striker", "Domain Tactician", "Flash Rogue"]:
                from constants import CLASSES
                ability_name = CLASSES[player.class_name]["abilities"]["active"]
            
            special_btn = Button(
                label=ability_name, 
                emoji="✨", 
                style=discord.ButtonStyle.success, 
                custom_id="special",
                disabled=player.cursed_energy < 15  # Require some energy to use
            )
            special_btn.callback = self.special_callback
            self.add_item(special_btn)
        
        # Item Button
        has_consumables = any(item.get("type") == "consumable" for item in player.inventory)
        item_btn = Button(
            label="Item", 
            emoji="🎒", 
            style=discord.ButtonStyle.secondary, 
            custom_id="item",
            disabled=not has_consumables
        )
        item_btn.callback = self.item_callback
        self.add_item(item_btn)
        
        # Run Button
        run_btn = Button(label="Run", emoji="💨", style=discord.ButtonStyle.secondary, custom_id="run")
        run_btn.callback = self.run_callback
        self.add_item(run_btn)
    
    async def attack_callback(self, interaction):
        self.result = "attack"
        self.stop()
        await interaction.response.defer()
    
    async def defend_callback(self, interaction):
        self.result = "defend"
        self.stop()
        await interaction.response.defer()
    
    async def special_callback(self, interaction):
        self.result = "special"
        self.stop()
        await interaction.response.defer()
    
    async def item_callback(self, interaction):
        # Create a temporary view to select items
        consumables = [item for item in self.player.inventory if item.get("type") == "consumable"]
        if not consumables:
            await interaction.response.send_message("You don't have any usable items!", ephemeral=True)
            return
        
        view = ItemSelectView(consumables)
        await interaction.response.send_message("Select an item to use:", view=view, ephemeral=True)
        
        # Wait for selection
        await view.wait()
        
        if view.selected_item:
            self.result = f"item:{view.selected_item}"
            self.stop()
        else:
            # If no selection was made, let the player choose another action
            await interaction.followup.send("Item selection canceled. Choose another action.", ephemeral=True)
    
    async def run_callback(self, interaction):
        self.result = "run"
        self.stop()
        await interaction.response.defer()

class ItemSelectView(View):
    """View for selecting an item to use"""
    def __init__(self, items, timeout=30):
        super().__init__(timeout=timeout)
        self.selected_item = None
        
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

class DungeonSelectView(View):
    """View for selecting which dungeon to enter"""
    def __init__(self, player: PlayerData, dungeons: Dict, timeout=60):
        super().__init__(timeout=timeout)
        self.selected_dungeon = None
        
        for name, data in dungeons.items():
            # Determine if the player meets the level requirement
            meets_req = player.class_level >= data["level_req"]
            
            # Friendly description of requirements
            req_text = f"(Lvl {data['level_req']})"
            
            btn = Button(
                label=f"{name} {req_text}", 
                style=discord.ButtonStyle.primary if meets_req else discord.ButtonStyle.secondary,
                custom_id=name,
                emoji="⚔️",
                disabled=not meets_req
            )
            btn.callback = self.dungeon_callback
            self.add_item(btn)
    
    async def dungeon_callback(self, interaction):
        self.selected_dungeon = interaction.data["custom_id"]
        self.stop()
        await interaction.response.defer()

class DungeonInstance:
    """Manages a dungeon run instance"""
    def __init__(self, player: PlayerData, dungeon_name: str):
        self.player = player
        self.dungeon_name = dungeon_name
        self.dungeon_data = DUNGEONS[dungeon_name]
        self.current_floor = 0
        self.max_floors = self.dungeon_data["floors"]
        self.enemies_defeated = 0
        self.loot_collected = []
        self.player_defending = False
        
        # Save initial stats to restore after dungeon
        self.initial_hp = player.current_stats["hp"]
        self.initial_energy = player.cursed_energy
    
    async def run_dungeon(self, ctx) -> bool:
        """
        Run through the dungeon
        Returns: bool indicating success (True) or failure (False)
        """
        # Start dungeon
        embed = discord.Embed(
            title=f"⚔️ Entering {self.dungeon_name}",
            description=f"A {self.dungeon_data['difficulty']} level dungeon with {self.max_floors} floors.",
            color=discord.Color.dark_gold()
        )
        embed.add_field(name="Prepare yourself", value="Your journey begins...", inline=False)
        message = await ctx.send(embed=embed)
        
        # Run through each floor
        for floor in range(1, self.max_floors + 1):
            self.current_floor = floor
            
            # Update the message
            embed = self.create_floor_embed()
            await message.edit(embed=embed)
            await asyncio.sleep(1)
            
            # Determine if this floor has an enemy
            has_enemy = random.random() < 0.8  # 80% chance of enemy
            
            if has_enemy:
                # Generate an enemy for this floor
                enemy = self.generate_enemy()
                
                # Fight the enemy
                result = await self.battle_enemy(ctx, message, enemy)
                
                if not result:
                    # Player died or ran away
                    return False
            else:
                # No enemy, just a treasure room or rest area
                room_type = random.choice(["treasure", "rest"])
                
                if room_type == "treasure":
                    await self.treasure_room(ctx, message)
                else:
                    await self.rest_room(ctx, message)
                
                await asyncio.sleep(2)
        
        # Player completed the dungeon!
        return await self.complete_dungeon(ctx, message)
    
    async def battle_enemy(self, ctx, message, enemy: Dict) -> bool:
        """
        Handle a battle with an enemy
        Returns: bool indicating if player won (True) or lost/ran (False)
        """
        # Setup battle
        enemy_hp = enemy["hp"]
        enemy_max_hp = enemy["hp"]
        battle_log = []
        
        # Initial battle message
        embed = discord.Embed(
            title=f"⚔️ Battle: Floor {self.current_floor}",
            description=f"You encounter a {enemy['name']}!",
            color=discord.Color.red()
        )
        
        # Add enemy and player info
        embed.add_field(
            name=f"Enemy: {enemy['name']}",
            value=f"HP: {enemy_hp}/{enemy_max_hp}\nPower: {enemy['power']}\nDefense: {enemy['defense']}",
            inline=True
        )
        
        embed.add_field(
            name=f"Your Character: {self.player.class_name}",
            value=(
                f"HP: {self.player.current_stats['hp']}/{self.player.current_stats['max_hp']}\n"
                f"CE: {self.player.cursed_energy}/{self.player.max_cursed_energy}"
            ),
            inline=True
        )
        
        await message.edit(embed=embed)
        await asyncio.sleep(1)
        
        # Battle loop
        battle_active = True
        player_turn = True  # Player goes first
        
        while battle_active:
            # Reset defending status at the start of each turn
            if player_turn:
                enemy_defending = False
            else:
                self.player_defending = False
                
            if player_turn:
                # Player's turn
                view = DungeonView(self.player, enemy, timeout=30)
                
                # Update message with battle state
                embed = self.create_battle_embed(enemy, enemy_hp, enemy_max_hp, battle_log)
                await message.edit(embed=embed, view=view)
                
                # Wait for player's action
                await view.wait()
                
                if view.result is None:
                    # Timeout - player loses turn
                    battle_log.append("You took too long and missed your turn!")
                elif view.result == "attack":
                    # Basic attack
                    damage = self.calculate_damage(
                        self.player.current_stats["power"],
                        enemy["defense"],
                        critical_chance=0.1
                    )
                    enemy_hp -= damage
                    battle_log.append(f"You attack for {damage} damage.")
                    
                    # Use some energy
                    self.player.cursed_energy = max(0, self.player.cursed_energy - 5)
                    
                elif view.result == "defend":
                    # Defend to reduce incoming damage
                    self.player_defending = True
                    battle_log.append("You take a defensive stance. 🛡️")
                    
                    # Restore some energy while defending
                    energy_restored = random.randint(10, 20)
                    self.player.restore_energy(energy_restored)
                    battle_log.append(f"You regain {energy_restored} cursed energy.")
                    
                elif view.result == "special":
                    # Use special ability based on class
                    ability_cost = 15
                    
                    if self.player.cursed_energy < ability_cost:
                        battle_log.append("Not enough cursed energy!")
                    else:
                        self.player.cursed_energy -= ability_cost
                        
                        # Use ability based on class
                        if self.player.class_name == "Spirit Striker":
                            # Cursed Combo - multiple hits
                            hits = random.randint(2, 4)
                            total_damage = 0
                            
                            for i in range(hits):
                                hit_damage = self.calculate_damage(
                                    self.player.current_stats["power"] * 0.6,
                                    enemy["defense"],
                                    critical_chance=0.05
                                )
                                enemy_hp -= hit_damage
                                total_damage += hit_damage
                                
                            battle_log.append(f"Your Cursed Combo hits {hits} times for {total_damage} total damage!")
                            
                        elif self.player.class_name == "Domain Tactician":
                            # Barrier Pulse - damage + defense
                            self.player_defending = True
                            damage = self.calculate_damage(
                                self.player.current_stats["defense"] * 0.8,
                                enemy["defense"] * 0.5
                            )
                            enemy_hp -= damage
                            battle_log.append(f"Your Barrier Pulse deals {damage} damage and protects you! 🛡️")
                            
                        elif self.player.class_name == "Flash Rogue":
                            # Shadowstep - high damage + evasion
                            damage = self.calculate_damage(
                                self.player.current_stats["power"] * 1.5,
                                enemy["defense"],
                                critical_chance=0.15
                            )
                            enemy_hp -= damage
                            battle_log.append(f"Your Shadowstep strikes for {damage} damage!")
                            
                            # Chance to dodge next attack
                            if random.random() < 0.5:
                                self.player_defending = True
                                battle_log.append("You fade into the shadows, making it harder to be hit! 👻")
                        
                        else:
                            # Generic special attack
                            damage = self.calculate_damage(
                                self.player.current_stats["power"] * 1.3,
                                enemy["defense"]
                            )
                            enemy_hp -= damage
                            battle_log.append(f"Your special attack deals {damage} damage!")
                
                elif view.result.startswith("item:"):
                    # Use an item
                    item_name = view.result.split(":", 1)[1]
                    
                    # Find the item
                    item = None
                    for inv_item in self.player.inventory:
                        if inv_item["name"] == item_name:
                            item = inv_item
                            break
                    
                    if item:
                        # Apply item effects
                        if "heal" in item:
                            heal_amount = item["heal"]
                            self.player.heal(heal_amount)
                            battle_log.append(f"You use {item_name} and heal for {heal_amount} HP!")
                        
                        if "energy" in item:
                            energy_amount = item["energy"]
                            self.player.restore_energy(energy_amount)
                            battle_log.append(f"You use {item_name} and restore {energy_amount} cursed energy!")
                        
                        if "effect" in item:
                            # Apply special effects
                            effect = item["effect"]
                            if effect == "strength":
                                buff_amount = item.get("buff_amount", 5)
                                self.player.current_stats["power"] += buff_amount
                                battle_log.append(f"You use {item_name} and gain {buff_amount} power!")
                        
                        # Remove the item
                        self.player.remove_from_inventory(item_name)
                    else:
                        battle_log.append(f"Item {item_name} not found!")
                
                elif view.result == "run":
                    # Try to run away
                    escape_chance = 0.3
                    
                    # Higher chance to escape on lower floors
                    escape_chance += (self.max_floors - self.current_floor) * 0.05
                    
                    if random.random() < escape_chance:
                        battle_log.append("You successfully escaped from the dungeon!")
                        embed = self.create_battle_embed(enemy, enemy_hp, enemy_max_hp, battle_log)
                        await message.edit(embed=embed, view=None)
                        
                        # Escape penalty - lose some progress
                        await asyncio.sleep(2)
                        embed = discord.Embed(
                            title="🏃‍♂️ Dungeon Escape",
                            description=f"You escaped from the {self.dungeon_name} dungeon.",
                            color=discord.Color.blue()
                        )
                        await message.edit(embed=embed)
                        return False
                    else:
                        battle_log.append("You failed to escape!")
            
            else:
                # Enemy's turn
                await asyncio.sleep(1)  # Pause for effect
                
                # Simple AI for enemy
                if enemy_hp < enemy_max_hp * 0.3 and random.random() < 0.4:
                    # Low health, chance to defend
                    enemy_defending = True
                    battle_log.append(f"The {enemy['name']} takes a defensive stance. 🛡️")
                else:
                    # Attack
                    damage_modifier = 1.0
                    if self.player_defending:
                        damage_modifier = 0.5  # Reduce damage when player is defending
                    
                    damage = self.calculate_damage(
                        enemy["power"],
                        self.player.current_stats["defense"],
                        damage_modifier
                    )
                    
                    self.player.current_stats["hp"] -= damage
                    battle_log.append(f"The {enemy['name']} attacks you for {damage} damage!")
            
            # Update battle embed
            embed = self.create_battle_embed(enemy, enemy_hp, enemy_max_hp, battle_log)
            await message.edit(embed=embed, view=None)
            
            # Check win/loss conditions
            if enemy_hp <= 0:
                battle_log.append(f"You defeated the {enemy['name']}!")
                embed = self.create_battle_embed(enemy, 0, enemy_max_hp, battle_log)
                await message.edit(embed=embed)
                
                # Battle won
                self.enemies_defeated += 1
                await asyncio.sleep(1)
                return True
                
            if self.player.current_stats["hp"] <= 0:
                battle_log.append("You have been defeated!")
                embed = self.create_battle_embed(enemy, enemy_hp, enemy_max_hp, battle_log)
                await message.edit(embed=embed)
                
                # Battle lost
                await asyncio.sleep(1)
                
                # Create defeat embed
                embed = discord.Embed(
                    title="⚰️ Dungeon Defeat",
                    description=f"You were defeated in the {self.dungeon_name} dungeon on floor {self.current_floor}.",
                    color=discord.Color.dark_red()
                )
                
                # Add some info about what was lost
                embed.add_field(
                    name="Consequences",
                    value="You lost some progress and items collected in this dungeon run.",
                    inline=False
                )
                
                await message.edit(embed=embed)
                return False
            
            # Switch turns
            player_turn = not player_turn
            
            # Keep battle log a reasonable size
            if len(battle_log) > 6:
                battle_log = battle_log[-6:]
    
    def generate_enemy(self) -> Dict:
        """Generate an appropriate enemy for the current floor"""
        # Get list of possible enemies for this dungeon
        dungeon_level = self.dungeon_data["level_req"]
        possible_enemies = [e for e in DUNGEON_ENEMIES if dungeon_level - 2 <= e["level"] <= dungeon_level + 2]
        
        if not possible_enemies:
            # Fallback if no enemies match
            possible_enemies = DUNGEON_ENEMIES
        
        # Select a random enemy
        base_enemy = random.choice(possible_enemies)
        
        # Scale the enemy based on floor number
        floor_scaling = 1.0 + (self.current_floor / self.max_floors) * 0.5
        
        enemy = {
            "name": base_enemy["name"],
            "hp": int(base_enemy["hp"] * floor_scaling),
            "power": int(base_enemy["power"] * floor_scaling),
            "defense": int(base_enemy["defense"] * floor_scaling),
            "level": base_enemy["level"]
        }
        
        # Chance for elite enemy
        if random.random() < 0.2:
            enemy["name"] = f"Elite {enemy['name']}"
            enemy["hp"] = int(enemy["hp"] * 1.5)
            enemy["power"] = int(enemy["power"] * 1.2)
            enemy["defense"] = int(enemy["defense"] * 1.2)
        
        return enemy
    
    async def treasure_room(self, ctx, message):
        """Handle a treasure room encounter"""
        embed = discord.Embed(
            title="🗝️ Treasure Room",
            description=f"You found a treasure room on floor {self.current_floor}!",
            color=discord.Color.gold()
        )
        
        # Generate random loot
        loot_type = random.choices(
            ["gold", "item", "energy"],
            weights=[0.6, 0.3, 0.1],
            k=1
        )[0]
        
        if loot_type == "gold":
            # Gold/currency
            gold_amount = random.randint(
                self.dungeon_data["level_req"] * 10,
                self.dungeon_data["level_req"] * 20
            )
            self.player.currency += gold_amount
            embed.add_field(
                name="Gold Found",
                value=f"You found {gold_amount} 🌀 cursed energy fragments!",
                inline=False
            )
            
        elif loot_type == "item":
            # Generate a random item
            from constants import generate_random_item
            item = generate_random_item(self.player.class_level)
            self.player.add_to_inventory(item)
            self.loot_collected.append(item["name"])
            
            embed.add_field(
                name="Item Found",
                value=f"You found a **{item['name']}**!\n{item['description']}",
                inline=False
            )
            
        elif loot_type == "energy":
            # Restore energy
            energy_amount = random.randint(30, 50)
            self.player.restore_energy(energy_amount)
            embed.add_field(
                name="Energy Source",
                value=f"You found a source of cursed energy and restored {energy_amount} CE!",
                inline=False
            )
        
        await message.edit(embed=embed)
    
    async def rest_room(self, ctx, message):
        """Handle a rest area encounter"""
        embed = discord.Embed(
            title="🏕️ Rest Area",
            description=f"You found a safe area to rest on floor {self.current_floor}.",
            color=discord.Color.green()
        )
        
        # Heal the player
        heal_amount = int(self.player.current_stats["max_hp"] * 0.3)
        self.player.heal(heal_amount)
        
        # Restore some energy
        energy_amount = int(self.player.max_cursed_energy * 0.3)
        self.player.restore_energy(energy_amount)
        
        embed.add_field(
            name="Rest Benefits",
            value=(
                f"You recovered {heal_amount} HP and {energy_amount} cursed energy.\n"
                f"Current HP: {self.player.current_stats['hp']}/{self.player.current_stats['max_hp']}\n"
                f"Current CE: {self.player.cursed_energy}/{self.player.max_cursed_energy}"
            ),
            inline=False
        )
        
        await message.edit(embed=embed)
    
    async def complete_dungeon(self, ctx, message) -> bool:
        """Handle successful dungeon completion"""
        # Calculate rewards
        xp_reward = self.dungeon_data["exp"]
        gold_reward = random.randint(
            self.dungeon_data["min_rewards"],
            self.dungeon_data["max_rewards"]
        )
        
        # Bonus for defeating enemies
        enemy_bonus_xp = self.enemies_defeated * 10
        enemy_bonus_gold = self.enemies_defeated * 5
        
        total_xp = xp_reward + enemy_bonus_xp
        total_gold = gold_reward + enemy_bonus_gold
        
        # Apply rewards
        level_up = self.player.add_exp(total_xp)
        self.player.currency += total_gold
        
        # Record completion
        if self.dungeon_name not in self.player.dungeons_completed:
            self.player.dungeons_completed[self.dungeon_name] = 1
        else:
            self.player.dungeons_completed[self.dungeon_name] += 1
        
        # Create completion embed
        embed = discord.Embed(
            title="🎉 Dungeon Completed!",
            description=f"You successfully cleared all {self.max_floors} floors of the {self.dungeon_name}!",
            color=discord.Color.gold()
        )
        
        # Add reward info
        embed.add_field(
            name="Rewards",
            value=(
                f"XP: {xp_reward} (+ {enemy_bonus_xp} enemy bonus) = {total_xp}\n"
                f"Currency: {gold_reward} (+ {enemy_bonus_gold} enemy bonus) = {total_gold} 🌀\n"
                f"Enemies Defeated: {self.enemies_defeated}"
            ),
            inline=False
        )
        
        # Add level up message if applicable
        if level_up:
            embed.add_field(
                name="Level Up!",
                value=(
                    f"You reached level {self.player.class_level}!\n"
                    f"You gained 3 skill points!"
                ),
                inline=False
            )
        
        # Add loot summary
        if self.loot_collected:
            embed.add_field(
                name="Items Collected",
                value="\n".join([f"- {item}" for item in self.loot_collected]),
                inline=False
            )
        
        # Check for rare drop
        if random.random() < (self.dungeon_data["rare_drop"] / 100):
            from constants import generate_rare_item
            rare_item = generate_rare_item(self.player.class_level, self.dungeon_name)
            self.player.add_to_inventory(rare_item)
            
            embed.add_field(
                name="✨ Rare Find!",
                value=f"You found a **{rare_item['name']}**!\n{rare_item['description']}",
                inline=False
            )
        
        await message.edit(embed=embed)
        
        # Set last dungeon timestamp
        self.player.last_train = datetime.datetime.now()
        
        return True
    
    def calculate_damage(self, attacker_power: float, defender_defense: float, 
                         damage_modifier: float = 1.0, critical_chance: float = 0.1) -> int:
        """Calculate damage for an attack"""
        # Base damage
        damage = max(1, (attacker_power - defender_defense * 0.5) * damage_modifier)
        
        # Random variation
        damage *= random.uniform(0.9, 1.1)
        
        # Critical hit
        if random.random() < critical_chance:
            damage *= 1.5
        
        return int(damage)
    
    def create_floor_embed(self) -> discord.Embed:
        """Create an embed displaying the current floor information"""
        embed = discord.Embed(
            title=f"🗺️ {self.dungeon_name} - Floor {self.current_floor}/{self.max_floors}",
            description="Exploring the dungeon...",
            color=discord.Color.blue()
        )
        
        # Add player status
        hp_percent = self.player.current_stats["hp"] / self.player.current_stats["max_hp"]
        hp_bar = self.create_bar(hp_percent)
        
        ce_percent = self.player.cursed_energy / self.player.max_cursed_energy
        ce_bar = self.create_bar(ce_percent)
        
        embed.add_field(
            name="Your Status",
            value=(
                f"HP: {self.player.current_stats['hp']}/{self.player.current_stats['max_hp']} {hp_bar}\n"
                f"CE: {self.player.cursed_energy}/{self.player.max_cursed_energy} {ce_bar}"
            ),
            inline=False
        )
        
        # Add dungeon progress
        progress_percent = (self.current_floor - 1) / self.max_floors
        progress_bar = self.create_bar(progress_percent)
        
        embed.add_field(
            name="Dungeon Progress",
            value=f"Floor: {self.current_floor}/{self.max_floors} {progress_bar}",
            inline=False
        )
        
        embed.set_footer(text=f"Enemies defeated: {self.enemies_defeated} | Items found: {len(self.loot_collected)}")
        
        return embed
    
    def create_battle_embed(self, enemy: Dict, enemy_hp: int, enemy_max_hp: int, battle_log: List[str]) -> discord.Embed:
        """Create an embed displaying the current battle state"""
        embed = discord.Embed(
            title=f"⚔️ Battle: Floor {self.current_floor}",
            description=f"Fighting a {enemy['name']}",
            color=discord.Color.red()
        )
        
        # Enemy status
        enemy_hp_percent = max(0, enemy_hp / enemy_max_hp)
        enemy_hp_bar = self.create_bar(enemy_hp_percent)
        
        embed.add_field(
            name=f"Enemy: {enemy['name']}",
            value=(
                f"HP: {max(0, enemy_hp)}/{enemy_max_hp} {enemy_hp_bar}\n"
                f"Power: {enemy['power']} | Defense: {enemy['defense']}"
            ),
            inline=False
        )
        
        # Player status
        player_hp_percent = self.player.current_stats["hp"] / self.player.current_stats["max_hp"]
        player_hp_bar = self.create_bar(player_hp_percent)
        
        player_ce_percent = self.player.cursed_energy / self.player.max_cursed_energy
        player_ce_bar = self.create_bar(player_ce_percent)
        
        embed.add_field(
            name=f"Your Character: {self.player.class_name}",
            value=(
                f"HP: {self.player.current_stats['hp']}/{self.player.current_stats['max_hp']} {player_hp_bar}\n"
                f"CE: {self.player.cursed_energy}/{self.player.max_cursed_energy} {player_ce_bar}\n"
                f"Power: {self.player.current_stats['power']} | Defense: {self.player.current_stats['defense']}"
            ),
            inline=False
        )
        
        # Battle log
        if battle_log:
            log_text = "\n".join(battle_log[-5:])  # Show most recent 5 lines
            embed.add_field(name="Battle Log", value=log_text, inline=False)
        
        return embed
    
    def create_bar(self, percent: float) -> str:
        """Create a visual bar based on percentage"""
        blocks = 10
        filled = "█" * int(blocks * percent)
        empty = "░" * (blocks - len(filled))
        
        if percent > 0.7:
            return f"[{filled}{empty}] 🟢"
        elif percent > 0.3:
            return f"[{filled}{empty}] 🟡"
        else:
            return f"[{filled}{empty}] 🔴"
