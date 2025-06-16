import discord
from discord.ui import Button, View, Select
import random
import asyncio
import datetime
from typing import Dict, List, Optional, Tuple, Any

from data_models import PlayerData, DataManager, Item
from battle_system import BattleEntity, BattleMove, BattleView, generate_enemy_stats, generate_enemy_moves

# Dungeon definitions expanded to cover level 1-100 range
DUNGEONS = {
    # Beginner Dungeons (Levels 1-20)
    "Ancient Forest": {
        "description": "A mysterious forest home to cursed beasts and hidden treasures.",
        "level_req": 1,
        "floors": 3,
        "enemies": ["Cursed Wolf", "Forest Specter", "Ancient Treefolk"],
        "boss": "Elder Treant",
        "max_rewards": 100,
        "exp": 50,
        "rare_drop": 10,  # % chance
        "style": discord.ButtonStyle.green,
        "item_level": 1
    },
    "Forgotten Cave": {
        "description": "Dark caverns filled with dangerous creatures and lost relics.",
        "level_req": 5,
        "floors": 4,
        "enemies": ["Cave Crawler", "Armored Golem", "Crystal Spider"],
        "boss": "Cave Warden",
        "max_rewards": 200,
        "exp": 120,
        "rare_drop": 15,
        "style": discord.ButtonStyle.gray,
        "item_level": 5
    },
    "Cursed Shrine": {
        "description": "An abandoned shrine corrupted by dark energies and vengeful spirits.",
        "level_req": 10,
        "floors": 5,
        "enemies": ["Shrine Guardian", "Cursed Monk", "Vengeful Spirit"],
        "boss": "Shrine Deity",
        "max_rewards": 350,
        "exp": 200,
        "rare_drop": 20,
        "style": discord.ButtonStyle.red,
        "item_level": 10
    },
    "Abyssal Depths": {
        "description": "The deepest part of the ocean, home to nightmarish creatures.",
        "level_req": 15,
        "floors": 6,
        "enemies": ["Deep One", "Abyssal Hunter", "Giant Squid"],
        "boss": "Kraken Lord",
        "max_rewards": 500,
        "exp": 350,
        "rare_drop": 25,
        "style": discord.ButtonStyle.blurple,
        "item_level": 15
    },
    "Infernal Citadel": {
        "description": "A fortress forged in hellfire where only the strongest survive.",
        "level_req": 20,
        "floors": 7,
        "enemies": ["Flame Knight", "Lava Golem", "Fire Drake"],
        "boss": "Infernal Overlord",
        "max_rewards": 750,
        "exp": 500,
        "rare_drop": 30,
        "style": discord.ButtonStyle.red,
        "item_level": 20
    },

    # Intermediate Dungeons (Levels 25-50)
    "Crystal Caverns": {
        "description": "Vast network of crystal caves filled with elementals and golems.",
        "level_req": 25,
        "floors": 8,
        "enemies": ["Crystal Elemental", "Stone Guardian", "Gem Golem"],
        "boss": "Crystal Colossus",
        "max_rewards": 1000,
        "exp": 750,
        "rare_drop": 35,
        "style": discord.ButtonStyle.blurple,
        "item_level": 25
    },
    "Corrupted Sanctum": {
        "description": "Once holy grounds now twisted by forbidden magic.",
        "level_req": 30,
        "floors": 9,
        "enemies": ["Corrupted Cleric", "Shadow Fiend", "Void Walker"],
        "boss": "The Defiled One",
        "max_rewards": 1500,
        "exp": 1000,
        "rare_drop": 40,
        "style": discord.ButtonStyle.red,
        "item_level": 30
    },
    "Sunken Temple": {
        "description": "Ancient temple sunken beneath the waves, harboring powerful relics.",
        "level_req": 35,
        "floors": 10,
        "enemies": ["Temple Guardian", "Deep Cultist", "Abyssal Horror"],
        "boss": "Tidal Ancient",
        "max_rewards": 2000,
        "exp": 1500,
        "rare_drop": 45,
        "style": discord.ButtonStyle.blurple,
        "item_level": 35
    },
    "Forbidden Library": {
        "description": "Repository of forbidden knowledge guarded by magical constructs.",
        "level_req": 40,
        "floors": 11,
        "enemies": ["Living Tome", "Arcane Golem", "Knowledge Devourer"],
        "boss": "The Grand Archivist",
        "max_rewards": 2500,
        "exp": 2000,
        "rare_drop": 50,
        "style": discord.ButtonStyle.gray,
        "item_level": 40
    },
    "Astral Nexus": {
        "description": "Convergence of multiple realms where reality itself is unstable.",
        "level_req": 50,
        "floors": 12,
        "enemies": ["Reality Warper", "Star Spawn", "Cosmic Horror"],
        "boss": "The Boundary Keeper",
        "max_rewards": 3500,
        "exp": 3000,
        "rare_drop": 55,
        "style": discord.ButtonStyle.blurple,
        "item_level": 50
    },

    # Advanced Dungeons (Levels 60-80)
    "Shadow Realm": {
        "description": "A dimension of pure darkness where nightmares manifest.",
        "level_req": 60,
        "floors": 13,
        "enemies": ["Nightmare Entity", "Void Assassin", "Shadow Titan"],
        "boss": "The Darkness Incarnate",
        "max_rewards": 5000,
        "exp": 4500,
        "rare_drop": 60,
        "style": discord.ButtonStyle.gray,
        "item_level": 60
    },
    "Dragon's Lair": {
        "description": "Volcanic caverns home to the most powerful dragons.",
        "level_req": 70,
        "floors": 14,
        "enemies": ["Flame Dragonspawn", "Magma Drake", "Ancient Wyvern"],
        "boss": "The Dragon Emperor",
        "max_rewards": 7500,
        "exp": 6000,
        "rare_drop": 65,
        "style": discord.ButtonStyle.red,
        "item_level": 70
    },
    "Celestial Spire": {
        "description": "A tower reaching the heavens, guarded by celestial beings.",
        "level_req": 80,
        "floors": 15,
        "enemies": ["Celestial Guardian", "Astral Knight", "Divine Enforcer"],
        "boss": "Archangel of Judgment",
        "max_rewards": 10000,
        "exp": 8000,
        "rare_drop": 70,
        "style": discord.ButtonStyle.blurple,
        "item_level": 80
    },

    # Endgame Dungeons (Levels 90-100)
    "Void Citadel": {
        "description": "Fortress at the edge of existence where reality falters.",
        "level_req": 90,
        "floors": 16,
        "enemies": ["Void Monstrosity", "Reality Breaker", "Nullification Entity"],
        "boss": "The Void Emperor",
        "max_rewards": 15000,
        "exp": 12000,
        "rare_drop": 75,
        "style": discord.ButtonStyle.gray,
        "item_level": 90
    },
    "Realm of Eternity": {
        "description": "The final challenge where time and space hold no meaning.",
        "level_req": 95,
        "floors": 20,
        "enemies": ["Eternal Guardian", "Timeless Entity", "Primordial Being"],
        "boss": "The First One",
        "max_rewards": 25000,
        "exp": 20000,
        "rare_drop": 80,
        "style": discord.ButtonStyle.blurple,
        "item_level": 95
    }
}

class DungeonProgressView(View):
    def __init__(self, player_data: PlayerData, dungeon_data: Dict[str, Any], data_manager: DataManager, dungeon_name: str = None, guild=None, guild_bonus=None, team_player_data=None):
        super().__init__(timeout=180)
        # Handle both single player and team modes
        self.is_team_dungeon = team_player_data is not None and len(team_player_data) > 0

        if self.is_team_dungeon:
            # Team dungeon mode
            self.team_player_data = team_player_data  # List of PlayerData objects
            self.player_data = team_player_data[0]  # Team leader is first player
        else:
            # Solo dungeon mode
            self.team_player_data = [player_data]
            self.player_data = player_data

        self.dungeon_data = dungeon_data
        self.data_manager = data_manager
        self.current_floor = 0
        self.max_floors = dungeon_data["floors"]
        self.dungeon_name = dungeon_name if dungeon_name else dungeon_data.get("name", "Unknown Dungeon")
        self.enemies_defeated = 0
        self.battles_won = True  # Track if player has won all battles
        self.messages = []  # Store message references for cleanup

        # Guild-related data
        self.guild = guild
        self.guild_bonus = guild_bonus or {}

        # Track player stats for cumulative damage
        from utils import GAME_CLASSES

        # Initialize team stats
        self.team_max_hp = {}
        self.team_current_hp = {}
        self.team_current_energy = {}

        # Set up stats for all team members
        for team_member in self.team_player_data:
            member_id = team_member.user_id
            member_stats = team_member.get_stats(GAME_CLASSES)
            self.team_max_hp[member_id] = member_stats["hp"]
            self.team_current_hp[member_id] = member_stats["hp"]
            self.team_current_energy[member_id] = team_member.cursed_energy

        # For compatibility with existing code
        self.player_max_hp = self.team_max_hp.get(self.player_data.user_id, 0)
        self.player_current_hp = self.team_current_hp.get(self.player_data.user_id, 0)
        self.player_current_energy = self.team_current_energy.get(self.player_data.user_id, 0)

        # Add continue button
        self.continue_btn = Button(
            label="Proceed to Next Floor", 
            style=discord.ButtonStyle.green,
            emoji="➡️"
        )
        self.continue_btn.callback = self.next_floor_callback
        self.add_item(self.continue_btn)

        # Add use item button
        self.item_btn = Button(
            label="Use Item",
            style=discord.ButtonStyle.blurple,
            emoji="🧪"
        )
        self.item_btn.callback = self.use_item_callback
        self.add_item(self.item_btn)

        # Add retreat button
        self.retreat_btn = Button(
            label="Retreat",
            style=discord.ButtonStyle.red,
            emoji="🏃"
        )
        self.retreat_btn.callback = self.retreat_callback
        self.add_item(self.retreat_btn)

    async def next_floor_callback(self, interaction: discord.Interaction):
        """Handle moving to the next floor"""
        # Increment floor
        self.current_floor += 1

        await interaction.response.defer()

        # Clear previous message content
        if hasattr(interaction, 'message'):
            try:
                await interaction.message.edit(content=f"🗺️ Proceeding to floor {self.current_floor}/{self.max_floors}...", view=None)
            except:
                pass

        # Check if we've reached the boss floor
        if self.current_floor == self.max_floors:
            # Boss encounter
            await self.boss_encounter(interaction)
        else:
            # Regular floor encounter
            await self.floor_encounter(interaction)

    async def use_item_callback(self, interaction: discord.Interaction):
        """Handle using an item between dungeon floors"""
        # Get list of usable healing/buff items
        usable_items = []

        # Check if player has inventory and items
        if hasattr(self.player_data, 'inventory') and self.player_data.inventory:
            for i, inv_item in enumerate(self.player_data.inventory):
                # Handle both InventoryItem objects and dictionary items
                if hasattr(inv_item, 'item'):
                    # InventoryItem object
                    item_type = inv_item.item.item_type if hasattr(inv_item.item, 'item_type') else ''
                    quantity = inv_item.quantity
                    item_name = inv_item.item.name if hasattr(inv_item.item, 'name') else f"Item #{i+1}"
                    item_desc = inv_item.item.description if hasattr(inv_item.item, 'description') else 'A usable item'
                else:
                    # Dictionary item (legacy support)
                    item_type = inv_item.get('item_type', inv_item.get('type', ''))
                    quantity = inv_item.get('quantity', 0)
                    item_name = inv_item.get('name', f"Item #{i+1}")
                    item_desc = inv_item.get('description', 'A usable item')

                # Only show consumable items that can be used in dungeons
                if (item_type == "consumable" or 
                    item_type == "potion") and quantity > 0:

                    usable_items.append({
                        'name': item_name,
                        'description': item_desc,
                        'index': i
                    })

        if not usable_items:
            await interaction.response.send_message("❌ You don't have any usable items in your inventory!", ephemeral=True)
            return

        # Create a class for the item selection view
        class ItemSelectView(discord.ui.View):
            def __init__(self, dungeon_view, items):
                super().__init__(timeout=30)
                self.dungeon_view = dungeon_view
                self.items = items

                # Add item selection dropdown
                select = discord.ui.Select(
                    placeholder="Select an item to use...",
                    options=[
                        discord.SelectOption(
                            label=item['name'][:25],  # Limit to 25 chars
                            description=item['description'][:50] + "..." if len(item['description']) > 50 else item['description'],
                            value=str(item['index'])
                        ) for item in items[:25]  # Discord limits to 25 options
                    ]
                )

                select.callback = self.select_callback
                self.add_item(select)

                # Add cancel button
                cancel_btn = discord.ui.Button(label="Cancel", style=discord.ButtonStyle.secondary)
                cancel_btn.callback = self.cancel_callback
                self.add_item(cancel_btn)

            async def select_callback(self, select_interaction):
                try:
                    selected_index = int(select_interaction.data['values'][0])
                    item_data = self.dungeon_view.player_data.inventory[selected_index]

                    # Apply effect based on item type
                    effect_msg = f"You used {item_data.get('name', 'an item')}!"
                    item_used = False

                    # Get player stats for reference
                    from utils import GAME_CLASSES
                    player_stats = self.dungeon_view.player_data.get_stats(GAME_CLASSES)
                    max_hp = player_stats.get("hp", 100)
                    max_energy = player_stats.get("energy", 100)

                    # Check item description for effect hints
                    item_desc = item_data.get('description', '').lower()

                    # Health potions
                    if any(word in item_desc for word in ['health', 'healing', 'hp', 'potion', 'heal']):
                        # Calculate healing amount based on item quality
                        if 'minor' in item_desc:
                            heal_percent = 0.2  # 20% of max HP
                        elif 'major' in item_desc:
                            heal_percent = 0.5  # 50% of max HP
                        elif 'full' in item_desc or 'complete' in item_desc:
                            heal_percent = 1.0  # Full heal
                        else:
                            heal_percent = 0.3  # Default to 30%

                        heal_amount = int(max_hp * heal_percent)

                        # Apply healing
                        if hasattr(self.dungeon_view, 'player_current_hp'):
                            prev_hp = self.dungeon_view.player_current_hp
                            self.dungeon_view.player_current_hp = min(max_hp, prev_hp + heal_amount)
                            effect_msg = f"✅ Restored {heal_amount} HP! ({self.dungeon_view.player_current_hp}/{max_hp} HP)"
                        else:
                            # If no HP tracking, create it
                            self.dungeon_view.player_current_hp = max_hp
                            effect_msg = f"✅ Fully restored your HP! ({max_hp}/{max_hp} HP)"

                        item_used = True

                    # Energy potions
                    elif any(word in item_desc for word in ['energy', 'stamina', 'mana']):
                        # Calculate energy amount based on item quality
                        if 'minor' in item_desc:
                            energy_amount = 30  # Small energy restore
                        elif 'major' in item_desc:
                            energy_amount = 60  # Medium energy restore
                        elif 'full' in item_desc or 'complete' in item_desc:
                            energy_amount = max_energy  # Full energy
                        else:
                            energy_amount = 40  # Default

                        # Apply energy
                        if hasattr(self.dungeon_view, 'player_current_energy'):
                            prev_energy = self.dungeon_view.player_current_energy
                            self.dungeon_view.player_current_energy = min(max_energy, prev_energy + energy_amount)
                            effect_msg = f"✅ Restored {energy_amount} energy! ({self.dungeon_view.player_current_energy}/{max_energy} energy)"
                        else:
                            # If no energy tracking, create it
                            self.dungeon_view.player_current_energy = max_energy
                            effect_msg = f"✅ Fully restored your energy! ({max_energy}/{max_energy} energy)"

                        item_used = True

                    # Buff potions
                    elif any(word in item_desc for word in ['buff', 'boost', 'strength', 'power', 'defense']):
                        # Track active buffs
                        if not hasattr(self.dungeon_view.player_data, 'active_effects'):
                            self.dungeon_view.player_data.active_effects = {}

                        # Determine buff type based on description
                        buff_type = "power"  # Default
                        buff_amount = 10     # Default

                        if 'power' in item_desc or 'strength' in item_desc or 'attack' in item_desc:
                            buff_type = "power"
                            buff_amount = 15
                        elif 'defense' in item_desc or 'shield' in item_desc or 'armor' in item_desc:
                            buff_type = "defense"
                            buff_amount = 15
                        elif 'speed' in item_desc or 'quick' in item_desc or 'agility' in item_desc:
                            buff_type = "speed"
                            buff_amount = 10
                        elif 'all' in item_desc or 'stat' in item_desc:
                            # Apply all buffs
                            self.dungeon_view.player_data.active_effects["power"] = 10
                            self.dungeon_view.player_data.active_effects["defense"] = 10
                            self.dungeon_view.player_data.active_effects["speed"] = 5
                            effect_msg = f"✅ Applied a boost to all stats for the next battle!"
                            item_used = True

                        if not item_used:
                            # Apply single stat buff
                            self.dungeon_view.player_data.active_effects[buff_type] = buff_amount
                            effect_msg = f"✅ Applied a {buff_amount}% boost to your {buff_type} for the next battle!"
                            item_used = True

                    # If no specific effect was applied
                    if not item_used:
                        # Generic effect - apply a small HP restore as a fallback
                        if hasattr(self.dungeon_view, 'player_current_hp'):
                            heal_amount = int(max_hp * 0.15)  # 15% heal
                            prev_hp = self.dungeon_view.player_current_hp
                            self.dungeon_view.player_current_hp = min(max_hp, prev_hp + heal_amount)
                            effect_msg = f"✅ Used {item_data.get('name', 'the item')} and restored {heal_amount} HP."
                        else:
                            effect_msg = f"✅ Used {item_data.get('name', 'the item')} and feel somewhat refreshed."

                        item_used = True

                    # Consume the item if successfully used
                    if item_used:
                        # Decrement item quantity
                        item_data['quantity'] = max(0, item_data.get('quantity', 1) - 1)

                        # Remove item if quantity is 0
                        if item_data['quantity'] <= 0:
                            self.dungeon_view.player_data.inventory = [
                                item for i, item in enumerate(self.dungeon_view.player_data.inventory) 
                                if i != selected_index
                            ]

                        # Save player data
                        self.dungeon_view.data_manager.save_data()

                        # Show success message with effect
                        await select_interaction.response.send_message(effect_msg, ephemeral=False)
                    else:
                        await select_interaction.response.send_message("❌ Could not use that item here.", ephemeral=True)

                except Exception as e:
                    await select_interaction.response.send_message(f"❌ Error using item: {str(e)}", ephemeral=True)

            async def cancel_callback(self, cancel_interaction):
                await cancel_interaction.response.send_message("Item selection canceled.", ephemeral=True)

        # Create and show the item select view
        item_view = ItemSelectView(self, usable_items)
        await interaction.response.send_message(
            "Select an item to use before the next floor:", 
            view=item_view,
            ephemeral=False
        )


    async def retreat_callback(self, interaction: discord.Interaction):
        """Handle player retreat from dungeon"""
        self.battles_won = False

        # Calculate partial rewards
        progress_percent = (self.current_floor / self.max_floors) * 0.5  # Max 50% of rewards for retreat
        gold_reward = int(self.dungeon_data["max_rewards"] * progress_percent)
        exp_reward = int(self.dungeon_data["exp"] * progress_percent)

        await interaction.response.send_message(
            f"🏃 You retreat from the {self.dungeon_name} dungeon!\n"
            f"Made it to floor {self.current_floor}/{self.max_floors}\n"
            f"Partial rewards: {gold_reward} 🌀 and {exp_reward} EXP",
            ephemeral=True
        )

        # Award partial rewards
        self.player_data.cursed_energy += gold_reward  # Changed from gold to cursed_energy
        self.player_data.add_exp(exp_reward)

        # Save player data
        self.data_manager.save_data()

        # Close this view
        self.stop()

    async def floor_encounter(self, interaction: discord.Interaction):
        """Handle a regular floor encounter"""
        channel = interaction.channel

        # Determine if floor has combat, trap, or treasure
        encounter_type = random.choices(
            ["combat", "trap", "treasure"],
            weights=[0.7, 0.15, 0.15],
            k=1
        )[0]

        if encounter_type == "combat":
            # Combat encounter
            enemy_pool = self.dungeon_data["enemies"]
            enemy_name = random.choice(enemy_pool)
            enemy_level = self.dungeon_data["level_req"] + random.randint(0, 2)

            # Create enemy
            enemy_stats = generate_enemy_stats(enemy_name, enemy_level, self.player_data.class_level)
            enemy_moves = generate_enemy_moves(enemy_name)

            enemy_entity = BattleEntity(
                enemy_name,
                enemy_stats,
                enemy_moves
            )

            # Create embed for encounter
            embed = discord.Embed(
                title=f"⚔️ Combat Encounter - Floor {self.current_floor}",
                description=f"A {enemy_name} (Level {enemy_level}) blocks your path!",
                color=discord.Color.red()
            )

            # Start battle
            from battle_system import start_battle
            battle_result = await self.battle_encounter(interaction, enemy_name, enemy_level)

            if not battle_result:
                # Player lost the battle
                self.battles_won = False

                # Calculate partial rewards
                progress_percent = ((self.current_floor - 1) / self.max_floors) * 0.4  # Max 40% of rewards for defeat
                cursed_energy_reward = int(self.dungeon_data["max_rewards"] * progress_percent)
                exp_reward = int(self.dungeon_data["exp"] * progress_percent)

                # Award partial rewards
                self.player_data.add_cursed_energy(cursed_energy_reward)
                self.player_data.add_exp(exp_reward)

                # Send defeat message
                defeat_embed = discord.Embed(
                    title="💀 Dungeon Defeat",
                    description=f"You were defeated by {enemy_name} on floor {self.current_floor}!",
                    color=discord.Color.red()
                )

                defeat_embed.add_field(
                    name="Partial Rewards",
                    value=f"EXP: +{exp_reward} 📊\n"
                          f"Cursed Energy: +{cursed_energy_reward} 🔮",
                    inline=False
                )

                await channel.send(embed=defeat_embed)

                # Reset accumulated dungeon damage and restore health
                from utils import GAME_CLASSES
                self.player_data.reset_dungeon_damage(GAME_CLASSES, True)

                # Save player data
                self.data_manager.save_data()

                # Close this view
                self.stop()
                return

            # Increment enemies defeated counter
            self.enemies_defeated += 1

        elif encounter_type == "trap":
            # Trap encounter
            trap_types = [
                {"name": "Poison Darts", "damage": 0.15, "color": discord.Color.purple()},
                {"name": "Floor Spikes", "damage": 0.2, "color": discord.Color.red()},
                {"name": "Cave-in", "damage": 0.25, "color": discord.Color.dark_grey()},
                {"name": "Flame Jets", "damage": 0.18, "color": discord.Color.orange()}
            ]

            trap = random.choice(trap_types)

            # Calculate damage based on player's max HP
            from utils import GAME_CLASSES
            player_stats = self.player_data.get_stats(GAME_CLASSES)
            max_hp = player_stats["hp"]
            damage = int(max_hp * trap["damage"])

            # Add accumulated damage and update player's current HP
            self.player_data.add_dungeon_damage(damage, GAME_CLASSES)

            # Get current HP after damage for display
            current_hp = self.player_data.current_hp

            # Create embed for trap
            embed = discord.Embed(
                title=f"⚠️ Trap Encountered - Floor {self.current_floor}",
                description=f"You triggered a {trap['name']} trap!",
                color=trap["color"]
            )

            embed.add_field(
                name="Damage",
                value=f"You took {damage} damage! 💥\nRemaining HP: {current_hp}/{max_hp}",
                inline=False
            )

            await channel.send(embed=embed)
            await asyncio.sleep(2)

        else:  # treasure
            # Treasure encounter
            treasure_types = [
                {"name": "Cursed Energy Vessel", "cursed_energy": 0.3, "exp": 0.1, "color": discord.Color.dark_purple()},
                {"name": "Experience Shrine", "cursed_energy": 0.1, "exp": 0.3, "color": discord.Color.blue()},
                {"name": "Ancient Relic", "cursed_energy": 0.2, "exp": 0.2, "color": discord.Color.teal()}
            ]

            treasure = random.choice(treasure_types)

            # Calculate rewards
            bonus_cursed_energy = int(self.dungeon_data["max_rewards"] * treasure["cursed_energy"])
            bonus_exp = int(self.dungeon_data["exp"] * treasure["exp"])

            # Award bonuses
            self.player_data.cursed_energy += bonus_cursed_energy
            self.player_data.add_exp(bonus_exp)

            # Create embed for treasure
            embed = discord.Embed(
                title=f"💎 Treasure Found - Floor {self.current_floor}",
                description=f"You discovered a {treasure['name']}!",
                color=treasure["color"]
            )

            embed.add_field(
                name="Rewards",
                value=f"Cursed Energy: +{bonus_cursed_energy} 🔮\n"
                      f"EXP: +{bonus_exp} 📊",
                inline=False
            )

            # Check for item find
            if random.random() < 0.3:  # 30% chance
                from equipment import generate_random_item

                # Generate item with level appropriate to dungeon
                item_level = min(self.player_data.class_level, self.dungeon_data["item_level"])
                new_item = generate_random_item(item_level)

                # Add to inventory
                from equipment import add_item_to_inventory
                add_item_to_inventory(self.player_data, new_item)

                embed.add_field(
                    name="Item Found!",
                    value=f"You found: **{new_item.name}**\n"
                          f"{new_item.description}",
                    inline=False
                )

            await channel.send(embed=embed)
            await asyncio.sleep(2)

        # Show the continue/retreat buttons
        continue_view = View()
        continue_view.add_item(self.continue_btn)
        continue_view.add_item(self.retreat_btn)

        status_msg = await channel.send(
            f"🗺️ You are on floor {self.current_floor}/{self.max_floors} of {self.dungeon_name}.\n"
            f"What would you like to do?",
            view=continue_view
        )

        self.messages.append(status_msg)

    async def battle_encounter(self, interaction: discord.Interaction, enemy_name: str, enemy_level: int) -> bool:
        """Handle a battle encounter, returns True if player won, False if lost"""
        from utils import GAME_CLASSES
        ctx = await interaction.client.get_context(interaction.message)

        # Get player class data
        if self.player_data.class_name not in GAME_CLASSES:
            await ctx.send("❌ Invalid player class. Please use !start to choose a class.")
            return False

        class_data = GAME_CLASSES[self.player_data.class_name]

        # Calculate player stats including equipment and level
        player_stats = self.player_data.get_stats(GAME_CLASSES)

        # Store max HP separately and use current HP for battle continuity
        max_hp = player_stats["hp"]
        if hasattr(self, 'player_current_hp'):
            current_hp = min(max_hp, self.player_current_hp)
        else:
            current_hp = max_hp

        # Get player moves based on class
        player_moves = []

        # Basic moves for everyone
        player_moves.append(BattleMove("Basic Attack", 1.0, 10))
        player_moves.append(BattleMove("Heavy Strike", 1.5, 25))

        # Class-specific special moves
        if self.player_data.class_name == "Spirit Striker":
            player_moves.append(BattleMove("Cursed Combo", 2.0, 35, "weakness", "Deal damage and weaken enemy"))
            player_moves.append(BattleMove("Soul Siphon", 1.2, 20, "energy_restore", "Deal damage and restore energy"))
        elif self.player_data.class_name == "Domain Tactician":
            player_moves.append(BattleMove("Barrier Pulse", 0.8, 30, "shield", "Deal damage and gain a shield"))
            player_moves.append(BattleMove("Tactical Heal", 0.5, 25, "heal", "Deal damage and heal yourself"))
        elif self.player_data.class_name == "Flash Rogue":
            player_moves.append(BattleMove("Shadowstep", 1.7, 30, "strength", "Deal damage and gain increased damage"))
            player_moves.append(BattleMove("Quick Strikes", 0.7, 15, None, "Deal multiple quick strikes"))

        # Create player entity
        player_entity = BattleEntity(
            interaction.user.display_name,
            player_stats,
            player_moves,
            is_player=True,
            player_data=self.player_data
        )
        
        # Set current HP to maintain battle continuity while preserving max HP
        player_entity.current_hp = current_hp

        # Create enemy entity
        enemy_stats = generate_enemy_stats(enemy_name, enemy_level, self.player_data.class_level)
        enemy_moves = generate_enemy_moves(enemy_name)

        enemy_entity = BattleEntity(
            enemy_name,
            enemy_stats,
            enemy_moves
        )

        # Create battle embed
        embed = discord.Embed(
            title=f"⚔️ Dungeon Battle: {interaction.user.display_name} vs {enemy_name}",
            description=f"A {enemy_name} (Level {enemy_level}) appears!",
            color=discord.Color.red()
        )

        # Add player stats - always show max HP from stats, current HP from entity
        embed.add_field(
            name=f"{interaction.user.display_name} (Level {self.player_data.class_level})",
            value=f"HP: {player_entity.current_hp}/{max_hp} ❤️\n"
                  f"Energy: {player_entity.current_energy}/{self.player_data.get_max_battle_energy()} ✨\n"
                  f"Power: {player_entity.stats['power']} ⚔️\n"
                  f"Defense: {player_entity.stats['defense']} 🛡️",
            inline=True
        )

        # Add enemy stats
        embed.add_field(
            name=f"{enemy_name} (Level {enemy_level})",
            value=f"HP: {enemy_entity.current_hp}/{enemy_entity.stats['hp']} ❤️\n"
                  f"Energy: {enemy_entity.current_energy}/{enemy_entity.stats.get('energy', 100)} ✨\n"
                  f"Power: {enemy_entity.stats['power']} ⚔️\n"
                  f"Defense: {enemy_entity.stats['defense']} 🛡️",
            inline=True
        )

        # Create battle view
        battle_view = BattleView(player_entity, enemy_entity, interaction.user, timeout=180)
        battle_view.data_manager = self.data_manager

        battle_msg = await interaction.channel.send(embed=embed, view=battle_view)
        self.messages.append(battle_msg)

        # Wait for battle to end
        await battle_view.wait()

        # Process battle results
        if not enemy_entity.is_alive():
            # Player won
            # Store player's current HP for next fights
            self.player_current_hp = player_entity.current_hp

            # Small reward for each enemy defeated
            minor_gold = int(self.dungeon_data["max_rewards"] * 0.1)
            minor_exp = int(self.dungeon_data["exp"] * 0.1)

            self.player_data.add_gold(minor_gold)
            self.player_data.add_exp(minor_exp)

            win_embed = discord.Embed(
                title="✅ Enemy Defeated",
                description=f"You defeated the {enemy_name}!",
                color=discord.Color.green()
            )

            win_embed.add_field(
                name="Minor Rewards",
                value=f"Gold: +{minor_gold} 💰\n"
                      f"EXP: +{minor_exp} 📊",
                inline=False
            )

            # Show remaining HP
            win_embed.add_field(
                name="Status",
                value=f"HP: {self.player_current_hp}/{max_hp} ❤️\n"
                      f"Energy: {player_entity.current_energy} ✨",
                inline=False
            )

            await interaction.channel.send(embed=win_embed)
            return True
        else:
            # Player lost
            # Set remaining HP to minimal (1) since they lost
            self.player_current_hp = 1
            return False

    async def boss_encounter(self, interaction: discord.Interaction):
        """Handle the boss encounter"""
        channel = interaction.channel

        boss_name = self.dungeon_data["boss"]
        boss_level = self.dungeon_data["level_req"] + 3  # Boss is harder

        # Show boss intro
        boss_intro = discord.Embed(
            title=f"🔥 BOSS FLOOR - {boss_name}",
            description=f"You've reached the final floor of {self.dungeon_name}!\n"
                       f"The dungeon boss, {boss_name} (Level {boss_level}), awaits you!",
            color=discord.Color.dark_red()
        )

        intro_msg = await channel.send(embed=boss_intro)
        self.messages.append(intro_msg)

        await asyncio.sleep(2)

        # Start boss battle
        boss_result = await self.battle_encounter(interaction, boss_name, boss_level)

        if not boss_result:
            # Player lost to boss
            self.battles_won = False

            # Calculate partial rewards (higher for making it to boss)
            progress_percent = 0.6  # 60% of rewards for reaching but losing to boss
            gold_reward = int(self.dungeon_data["max_rewards"] * progress_percent)
            exp_reward = int(self.dungeon_data["exp"] * progress_percent)

            # Award partial rewards
            self.player_data.add_gold(gold_reward)
            self.player_data.add_exp(exp_reward)

            # Send defeat message
            defeat_embed = discord.Embed(
                title="💀 Dungeon Defeat",
                description=f"You were defeated by {boss_name}, the dungeon boss!",
                color=discord.Color.red()
            )

            defeat_embed.add_field(
                name="Partial Rewards",
                value=f"EXP: +{exp_reward} 📊\n"
                      f"Gold: +{gold_reward} 💰",
                inline=False
            )

            await channel.send(embed=defeat_embed)

            # Save player data
            self.data_manager.save_data()
        else:
            # Player defeated boss - complete the dungeon!

            # Calculate full rewards
            gold_reward = self.dungeon_data["max_rewards"]
            exp_reward = self.dungeon_data["exp"]

            # Add bonus based on enemies defeated
            bonus_percent = min(0.3, self.enemies_defeated * 0.05)  # Max 30% bonus
            bonus_gold = int(gold_reward * bonus_percent)
            bonus_exp = int(exp_reward * bonus_percent)

            total_gold = gold_reward + bonus_gold
            total_exp = exp_reward + bonus_exp

            # Award rewards
            self.player_data.add_gold(total_gold)
            leveled_up = self.player_data.add_exp(total_exp)

            # Update dungeon clear count
            if self.dungeon_name not in self.player_data.dungeon_clears:
                self.player_data.dungeon_clears[self.dungeon_name] = 1
            else:
                self.player_data.dungeon_clears[self.dungeon_name] += 1

            # Update quest progress for dungeons
            from achievements import QuestManager
            quest_manager = QuestManager(self.data_manager)

            # Update daily dungeon quests
            completed_daily_quests = quest_manager.update_quest_progress(self.player_data, "daily_dungeons")

            # Update long-term dungeon quests
            completed_longterm_quests = quest_manager.update_quest_progress(self.player_data, "total_dungeons")

            # Send victory message
            victory_embed = discord.Embed(
                title="🎉 Dungeon Completed!",
                description=f"You defeated {boss_name} and completed the {self.dungeon_name} dungeon!",
                color=discord.Color.gold()
            )

            victory_embed.add_field(
                name="Rewards",
                value=f"Base Gold: {gold_reward} 💰\n"
                      f"Bonus Gold: +{bonus_gold} 💰\n"
                      f"Base EXP: {exp_reward} 📊\n"
                      f"Bonus EXP: +{bonus_exp} 📊\n"
                      f"Total: {total_gold} 💰 and {total_exp} EXP",
                inline=False
            )

            # Check for level up
            if leveled_up:
                victory_embed.add_field(
                    name="Level Up!",
                    value=f"🆙 You reached Level {self.player_data.class_level}!\n"
                          f"You gained 2 skill points! Use !skills to allocate them.",
                    inline=False
                )

            # Check for special item drop (rare equipment, transformation items, etc.)
            special_drop = False
            special_drop_msg = ""

            # First check for rare equipment drop
            if random.random() < (self.dungeon_data["rare_drop"] / 100):
                from equipment import generate_rare_item

                # Generate rare item appropriate to dungeon
                rare_item = generate_rare_item(self.dungeon_data["item_level"])

                # Add to inventory
                from equipment import add_item_to_inventory
                add_item_to_inventory(self.player_data, rare_item)

                special_drop = True
                special_drop_msg = f"The boss dropped: **{rare_item.name}**\n{rare_item.description}"

                victory_embed.add_field(
                    name="✨ Rare Item Found! ✨",
                    value=special_drop_msg,
                    inline=False
                )

            # Check for special transformation item (lower chance, but increases with dungeon level)
            special_item_chance = (self.dungeon_data["item_level"] * 0.5) / 100  # 0.5% per dungeon level
            if random.random() < special_item_chance:
                from special_items import create_transformation_item, get_random_special_drop

                # Get special item based on player level
                special_item = await get_random_special_drop(self.player_data.class_level)

                if special_item:
                    # Add to inventory
                    from equipment import add_item_to_inventory
                    add_item_to_inventory(self.player_data, special_item)

                    special_drop = True
                    spec_msg = f"You found a mythical item: **{special_item.name}**\n{special_item.description}"

                    # If we already have a special drop, add this as a separate field
                    if special_drop_msg:
                        victory_embed.add_field(
                            name="🌟 Mythical Item Found! 🌟",
                            value=spec_msg,
                            inline=False
                        )
                    else:
                        special_drop_msg = spec_msg
                        victory_embed.add_field(
                            name="🌟 Mythical Item Found! 🌟",
                            value=special_drop_msg,
                            inline=False
                        )

            # If no special drops, give regular item
            if not special_drop:
                # Regular item drop
                from equipment import generate_random_item

                item_level = self.dungeon_data["item_level"]
                new_item = generate_random_item(item_level)

                # Add to inventory
                from equipment import add_item_to_inventory
                add_item_to_inventory(self.player_data, new_item)

                victory_embed.add_field(
                    name="Item Found!",
                    value=f"The boss dropped: **{new_item.name}**\n"
                          f"{new_item.description}",
                    inline=False
                )

            await channel.send(embed=victory_embed)

            # Handle quest progression
            # Update quest progress for all participants
            from achievements import QuestManager
            quest_manager = QuestManager(self.data_manager)

            if self.is_team_dungeon:
                # Update for all team members
                for player in self.team_player_data:
                    completed_quests = quest_manager.update_quest_progress(player, "daily_dungeons")
                    for quest in completed_quests:
                        quest_manager.award_quest_rewards(player, quest)

                    # Also update for weekly_dungeons if applicable
                    completed_weekly = quest_manager.update_quest_progress(player, "weekly_dungeons")
                    for quest in completed_weekly:
                        quest_manager.award_quest_rewards(player, quest)
            else:
                # Solo player
                completed_quests = quest_manager.update_quest_progress(self.player_data, "daily_dungeons")
                for quest in completed_quests:
                    quest_manager.award_quest_rewards(self.player_data, quest)

                # Also update for weekly_dungeons if applicable
                completed_weekly = quest_manager.update_quest_progress(self.player_data, "weekly_dungeons")
                for quest in completed_weekly:
                    quest_manager.award_quest_rewards(self.player_data, quest)

            # Reset accumulated dungeon damage and restore full health
            from utils import GAME_CLASSES
            self.player_data.reset_dungeon_damage(GAME_CLASSES, True)

            # Save player data
            self.data_manager.save_data()

        # Close this view
        self.stop()

class DungeonSelectView(View):
    def __init__(self, player_data: PlayerData, data_manager: DataManager):
        super().__init__(timeout=60)
        self.player_data = player_data
        self.data_manager = data_manager
        self.selected_dungeon = None

        # Collect dungeons and sort by requirements
        available_dungeons = []
        locked_dungeons = []

        for name, data in data_manager.dungeons.items():
            dungeon_data = data.copy()
            dungeon_data["name"] = name

            # Check if player meets level requirement
            meets_req = player_data.class_level >= data["level_req"]

            if meets_req:
                available_dungeons.append((name, dungeon_data))
            else:
                locked_dungeons.append((name, dungeon_data))

        # Sort by level requirement
        available_dungeons.sort(key=lambda x: x[1]["level_req"])
        locked_dungeons.sort(key=lambda x: x[1]["level_req"])

        # Limit to maximum number of buttons that can fit (5 buttons per row, 5 rows max = 25 buttons)
        # We'll use 3 rows for available and 2 rows for locked
        available_limit = min(len(available_dungeons), 15)  # 3 rows x 5 buttons
        locked_limit = min(len(locked_dungeons), 10)        # 2 rows x 5 buttons

        # Add available dungeon buttons (first 3 rows)
        for i, (name, data) in enumerate(available_dungeons[:available_limit]):
            row = i // 5  # Calculate row (0-2)

            btn = Button(
                label=f"{name} (Lvl {data['level_req']})",
                style=data["style"],
                emoji="⚔️",
                disabled=False,
                row=row
            )

            # Store the dungeon data in the button for access in callback
            btn.dungeon_data = data

            # Set the callback
            btn.callback = self.dungeon_callback

            self.add_item(btn)

        # Add locked dungeon buttons (rows 3-4)
        for i, (name, data) in enumerate(locked_dungeons[:locked_limit]):
            row = 3 + (i // 5)  # Start from row 3

            btn = Button(
                label=f"{name} (Lvl {data['level_req']})",
                style=discord.ButtonStyle.gray,
                emoji="🔒",
                disabled=True,
                row=row
            )

            # Store the dungeon data in the button
            btn.dungeon_data = data

            # Set the callback (won't be triggered due to disabled=True)
            btn.callback = self.dungeon_callback

            self.add_item(btn)

    async def dungeon_callback(self, interaction: discord.Interaction):
        # Get the dungeon data from the clicked button
        for item in self.children:
            if isinstance(item, Button) and item.custom_id == interaction.data["custom_id"]:
                dungeon_data = item.dungeon_data
                break
        else:
            await interaction.response.send_message("❌ Error: Dungeon not found!", ephemeral=True)
            return

        # Check level requirement again (redundant but safe)
        if self.player_data.class_level < dungeon_data["level_req"]:
            await interaction.response.send_message(
                f"❌ You need to be level {dungeon_data['level_req']} to enter this dungeon!", 
                ephemeral=True
            )
            return

        # Check if player has sufficient energy and restore if too low
        from utils import GAME_CLASSES
        max_energy = self.player_data.get_max_battle_energy()
        min_energy_needed = 30  # Dungeons need more energy than regular battles

        if hasattr(self.player_data, 'battle_energy') and self.player_data.battle_energy < min_energy_needed:
            # Restore energy to full
            self.player_data.battle_energy = max_energy
            self.data_manager.save_data()

            # Notify player about energy restoration
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="⚡ Energy Restored!",
                    description=f"Your energy was too low to explore a dungeon effectively. It has been restored to full ({max_energy}/{max_energy}).",
                    color=discord.Color.blue()
                )
            )

            # Wait a moment before proceeding
            await asyncio.sleep(1)

            # Send dungeon entry message as a follow-up
            await interaction.followup.send(
                f"⚔️ Entering {dungeon_data['name']}...\n"
                f"This dungeon has {dungeon_data['floors']} floors with increasingly difficult challenges.\n"
                f"Prepare yourself!"
            )
        else:
            # Start the dungeon with normal energy
            await interaction.response.send_message(
                f"⚔️ Entering {dungeon_data['name']}...\n"
                f"This dungeon has {dungeon_data['floors']} floors with increasingly difficult challenges.\n"
                f"Prepare yourself!"
            )

        # Create progress view for the dungeon
        progress_view = DungeonProgressView(self.player_data, dungeon_data, self.data_manager)

        # Start at floor 0 (entrance) with a more detailed embed
        entrance_embed = discord.Embed(
            title=f"🗺️ Entering {dungeon_data['name']}",
            description=f"{dungeon_data['description']}",
            color=discord.Color.dark_purple()
        )

        # Add dungeon details
        entrance_embed.add_field(
            name="Dungeon Stats",
            value=f"Level: {dungeon_data['level_req']}+\n"
                  f"Floors: {dungeon_data['floors']}\n"
                  f"Boss: {dungeon_data['boss']}",
            inline=True
        )

        entrance_embed.add_field(
            name="Potential Rewards",
            value=f"Gold: Up to {dungeon_data['max_rewards']}\n"
                  f"EXP: Up to {dungeon_data['exp']}\n"
                  f"Rare Drop Chance: {dungeon_data['rare_drop']}%",
            inline=True
        )

        # Add enemies information
        enemies_list = ", ".join(dungeon_data['enemies'])
        entrance_embed.add_field(
            name="Enemies",
            value=f"{enemies_list}",
            inline=False
        )

        # Add player information
        from utils import GAME_CLASSES
        player_stats = self.player_data.get_stats(GAME_CLASSES)
        entrance_embed.add_field(
            name="Your Stats",
            value=f"Level: {self.player_data.class_level}\n"
                  f"Class: {self.player_data.class_name}\n"
                  f"HP: {player_stats.get('hp', 0)}\n"
                  f"Power: {player_stats.get('power', 0)}\n"
                  f"Defense: {player_stats.get('defense', 0)}\n"
                  f"Speed: {player_stats.get('speed', 0)}",
            inline=True
        )

        entrance_embed.set_footer(text="Are you ready to proceed?")

        await interaction.followup.send(embed=entrance_embed, view=progress_view)

        # Stop this view since we're starting the dungeon
        self.stop()

async def dungeon_command(ctx, data_manager: DataManager):
    """Handle the dungeon command - shows available dungeons and lets player select one"""
    player_data = data_manager.get_player(ctx.author.id)

    # Check if player has a class
    if not player_data.class_name:
        await ctx.send("❌ You need to choose a class first! Use `!start` to begin your journey.")
        return

    # Create dungeon select embed
    embed = discord.Embed(
        title="🗺️ Available Dungeons",
        description="Choose a dungeon to explore. Higher level dungeons offer better rewards but are more challenging.",
        color=discord.Color.dark_purple()
    )

    # Add dungeon info
    for name, data in DUNGEONS.items():
        # Check if player meets level requirement
        meets_req = player_data.class_level >= data["level_req"]
        status = "✅ Available" if meets_req else f"🔒 Locked (Requires Level {data['level_req']})"

        # Add clear count if player has cleared this dungeon
        clears = player_data.dungeon_clears.get(name, 0)
        clear_text = f"\nTimes cleared: {clears}" if clears > 0 else ""

        embed.add_field(
            name=f"{name} {status}",
            value=f"{data['description']}\n"
                  f"Floors: {data['floors']}\n"
                  f"Rewards: Up to {data['max_rewards']} Cursed Energy and {data['exp']} EXP{clear_text}",
            inline=False
        )

    # Create and send the view
    dungeon_view = DungeonSelectView(player_data, data_manager)
    await ctx.send(embed=embed, view=dungeon_view)

    # Wait for selection
    await dungeon_view.wait()
