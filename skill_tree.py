import discord
from discord.ext import commands
from discord.ui import Button, View, Select
import json
import random
import asyncio
from typing import Dict, List, Any, Optional, Union

from data_models import DataManager, PlayerData

class SkillTreeView(View):
    def __init__(self, player_data: PlayerData, data_manager: DataManager):
        super().__init__(timeout=180)  # 3 minute timeout
        self.player_data = player_data
        self.data_manager = data_manager
        self.current_tree = self.get_default_tree()
        
        # Add tree selection dropdown
        self.add_tree_select()
        
        # Add node buttons
        self.add_node_buttons()
        
    def get_default_tree(self) -> str:
        """Get the default skill tree based on player's class"""
        class_name = self.player_data.class_name.lower() if self.player_data.class_name else "warrior"
        
        # Map classes to their primary skill trees
        class_tree_map = {
            "warrior": "strength",
            "mage": "intelligence",
            "ranger": "dexterity",
            "cleric": "wisdom",
            "rogue": "agility",
            "paladin": "vitality"
        }
        
        # Return the appropriate tree or default to strength
        return class_tree_map.get(class_name, "strength")
        
    def add_tree_select(self):
        """Add dropdown for selecting skill tree"""
        # Define all available skill trees
        tree_options = [
            discord.SelectOption(
                label="Strength Tree",
                description="Focus on physical power and damage",
                value="strength",
                emoji="💪",
                default=self.current_tree == "strength"
            ),
            discord.SelectOption(
                label="Dexterity Tree",
                description="Focus on speed and precision",
                value="dexterity",
                emoji="🏹",
                default=self.current_tree == "dexterity"
            ),
            discord.SelectOption(
                label="Intelligence Tree",
                description="Focus on magical power and spells",
                value="intelligence",
                emoji="🧠",
                default=self.current_tree == "intelligence"
            ),
            discord.SelectOption(
                label="Wisdom Tree",
                description="Focus on support and healing",
                value="wisdom",
                emoji="📚",
                default=self.current_tree == "wisdom"
            ),
            discord.SelectOption(
                label="Vitality Tree",
                description="Focus on health and defense",
                value="vitality",
                emoji="❤️",
                default=self.current_tree == "vitality"
            ),
            discord.SelectOption(
                label="Agility Tree",
                description="Focus on evasion and critical hits",
                value="agility",
                emoji="💨",
                default=self.current_tree == "agility"
            )
        ]
        
        select = Select(
            placeholder="Select a skill tree",
            options=tree_options,
            custom_id="tree_select"
        )
        
        select.callback = self.tree_select_callback
        self.add_item(select)
        
    async def tree_select_callback(self, interaction: discord.Interaction):
        """Handle tree selection"""
        self.current_tree = interaction.data.get("values", [])[0]
        
        # Clear and rebuild the view
        self.clear_items()
        self.add_tree_select()
        self.add_node_buttons()
        
        await interaction.response.edit_message(
            embed=self.create_skill_tree_embed(),
            view=self
        )
        
    def add_node_buttons(self):
        """Add buttons for skill tree nodes"""
        # Define nodes for each tree
        tree_nodes = {
            "strength": [
                ("Power Strike", "Increases physical damage by 5% per level", 1, 5),
                ("Brute Force", "Chance to ignore defense", 2, 5),
                ("Weapon Mastery", "Increases weapon damage", 3, 5),
                ("Smashing Blow", "Deals heavy damage with a chance to stun", 4, 3),
                ("Titan's Grip", "Can use two-handed weapons in one hand", 5, 1)
            ],
            "dexterity": [
                ("Precise Shot", "Increases accuracy by 5% per level", 1, 5),
                ("Quick Draw", "Chance for an extra attack", 2, 5),
                ("Evasive Maneuvers", "Increases dodge chance", 3, 5),
                ("Critical Eye", "Increases critical hit chance", 4, 3),
                ("Sniper's Focus", "Guaranteed critical hit after aiming for a turn", 5, 1)
            ],
            "intelligence": [
                ("Arcane Mind", "Increases magical damage by 5% per level", 1, 5),
                ("Spell Mastery", "Reduces energy cost of spells", 2, 5),
                ("Elemental Affinity", "Increases elemental damage", 3, 5),
                ("Counterspell", "Chance to nullify enemy spell effects", 4, 3),
                ("Archmage's Presence", "Spells have a chance to cost no energy", 5, 1)
            ],
            "wisdom": [
                ("Healing Touch", "Increases healing effect by 5% per level", 1, 5),
                ("Spirit Link", "Shared healing between allies", 2, 5),
                ("Protective Aura", "Provides damage reduction to allies", 3, 5),
                ("Divine Intervention", "Chance to prevent fatal damage", 4, 3),
                ("Resurrection", "Can revive fallen allies in dungeon runs", 5, 1)
            ],
            "vitality": [
                ("Iron Skin", "Increases defense by 5% per level", 1, 5),
                ("Endurance", "Increases max health", 2, 5),
                ("Regeneration", "Recover health over time", 3, 5),
                ("Unbreakable", "Chance to resist status effects", 4, 3),
                ("Undying Will", "Survive fatal damage once per battle", 5, 1)
            ],
            "agility": [
                ("Quick Reflexes", "Increases action speed by 5% per level", 1, 5),
                ("Dual Wielding", "Improves damage when using two weapons", 2, 5),
                ("Shadow Step", "Chance to dodge attacks completely", 3, 5),
                ("Exploit Weakness", "Increased critical damage", 4, 3),
                ("Assassination", "Chance for instant kill on weak enemies", 5, 1)
            ]
        }
        
        # Get player's current skill tree progress
        player_tree_progress = self.player_data.skill_tree.get(self.current_tree, {})
        
        # Get corresponding nodes
        nodes = tree_nodes.get(self.current_tree, [])
        
        # Add buttons for each node
        for i, (name, desc, tier, max_level) in enumerate(nodes):
            # Get current level of this node
            current_level = player_tree_progress.get(name, 0)
            
            # Check if this node can be leveled up
            # Tier 1 nodes are always available
            # Higher tier nodes require at least 1 point in a previous tier node
            can_level = False
            
            if tier == 1:
                can_level = True
            else:
                # Check if player has points in previous tier
                for prev_name, prev_desc, prev_tier, prev_max in nodes:
                    if prev_tier == tier - 1 and player_tree_progress.get(prev_name, 0) > 0:
                        can_level = True
                        break
            
            # Also check if player has skill points and hasn't maxed this node
            can_level = can_level and self.player_data.skill_points > 0 and current_level < max_level
            
            # Create button
            button = Button(
                style=discord.ButtonStyle.primary if can_level else discord.ButtonStyle.secondary,
                label=f"{name} ({current_level}/{max_level})",
                custom_id=f"node_{i}",
                disabled=not can_level
            )
            
            button.callback = self.node_button_callback
            self.add_item(button)
        
    async def node_button_callback(self, interaction: discord.Interaction):
        """Handle node selection"""
        # Extract node index from button component data
        custom_id = interaction.data.get('custom_id', '')
        if not custom_id:
            await interaction.response.send_message("Error processing skill selection. Please try again.", ephemeral=True)
            return
            
        node_index = int(custom_id.split("_")[1])
        
        # Get the node info
        tree_nodes = {
            "strength": [
                ("Power Strike", "Increases physical damage by 5% per level", 1, 5),
                ("Brute Force", "Chance to ignore defense", 2, 5),
                ("Weapon Mastery", "Increases weapon damage", 3, 5),
                ("Smashing Blow", "Deals heavy damage with a chance to stun", 4, 3),
                ("Titan's Grip", "Can use two-handed weapons in one hand", 5, 1)
            ],
            "dexterity": [
                ("Precise Shot", "Increases accuracy by 5% per level", 1, 5),
                ("Quick Draw", "Chance for an extra attack", 2, 5),
                ("Evasive Maneuvers", "Increases dodge chance", 3, 5),
                ("Critical Eye", "Increases critical hit chance", 4, 3),
                ("Sniper's Focus", "Guaranteed critical hit after aiming for a turn", 5, 1)
            ],
            "intelligence": [
                ("Arcane Mind", "Increases magical damage by 5% per level", 1, 5),
                ("Spell Mastery", "Reduces energy cost of spells", 2, 5),
                ("Elemental Affinity", "Increases elemental damage", 3, 5),
                ("Counterspell", "Chance to nullify enemy spell effects", 4, 3),
                ("Archmage's Presence", "Spells have a chance to cost no energy", 5, 1)
            ],
            "wisdom": [
                ("Healing Touch", "Increases healing effect by 5% per level", 1, 5),
                ("Spirit Link", "Shared healing between allies", 2, 5),
                ("Protective Aura", "Provides damage reduction to allies", 3, 5),
                ("Divine Intervention", "Chance to prevent fatal damage", 4, 3),
                ("Resurrection", "Can revive fallen allies in dungeon runs", 5, 1)
            ],
            "vitality": [
                ("Iron Skin", "Increases defense by 5% per level", 1, 5),
                ("Endurance", "Increases max health", 2, 5),
                ("Regeneration", "Recover health over time", 3, 5),
                ("Unbreakable", "Chance to resist status effects", 4, 3),
                ("Undying Will", "Survive fatal damage once per battle", 5, 1)
            ],
            "agility": [
                ("Quick Reflexes", "Increases action speed by 5% per level", 1, 5),
                ("Dual Wielding", "Improves damage when using two weapons", 2, 5),
                ("Shadow Step", "Chance to dodge attacks completely", 3, 5),
                ("Exploit Weakness", "Increased critical damage", 4, 3),
                ("Assassination", "Chance for instant kill on weak enemies", 5, 1)
            ]
        }
        nodes = tree_nodes.get(self.current_tree, [])
        
        # If node is out of range, do nothing
        if node_index >= len(nodes):
            await interaction.response.send_message("Invalid skill node.", ephemeral=True)
            return
            
        node_name, _, _, max_level = nodes[node_index]
        
        # Initialize the skill tree dictionary if it doesn't exist
        if self.current_tree not in self.player_data.skill_tree:
            self.player_data.skill_tree[self.current_tree] = {}
            
        # Initialize the skill points spent counter if it doesn't exist
        if self.current_tree not in self.player_data.skill_points_spent:
            self.player_data.skill_points_spent[self.current_tree] = 0
        
        # Get current level and increment it
        current_level = self.player_data.skill_tree[self.current_tree].get(node_name, 0)
        
        # Check if we can level up this node
        if current_level >= max_level:
            await interaction.response.send_message(f"{node_name} is already at maximum level.", ephemeral=True)
            return
            
        if self.player_data.skill_points <= 0:
            await interaction.response.send_message("You don't have any skill points to spend.", ephemeral=True)
            return
            
        # Apply the skill point
        self.player_data.skill_tree[self.current_tree][node_name] = current_level + 1
        self.player_data.skill_points -= 1
        self.player_data.skill_points_spent[self.current_tree] = self.player_data.skill_points_spent.get(self.current_tree, 0) + 1
        
        # Save the data
        self.data_manager.save_data()
        
        # Clear and rebuild the view
        self.clear_items()
        self.add_tree_select()
        self.add_node_buttons()
        
        # Show a success message
        await interaction.response.edit_message(
            content=f"Skill point allocated to {node_name}! New level: {current_level + 1}/{max_level}",
            embed=self.create_skill_tree_embed(),
            view=self
        )
        
    def create_skill_tree_embed(self) -> discord.Embed:
        """Create the skill tree embed"""
        # Get tree display name
        tree_display_names = {
            "strength": "Strength 💪",
            "dexterity": "Dexterity 🏹",
            "intelligence": "Intelligence 🧠",
            "wisdom": "Wisdom 📚",
            "vitality": "Vitality ❤️",
            "agility": "Agility 💨"
        }
        
        tree_display_name = tree_display_names.get(self.current_tree, "Unknown Tree")
        
        # Create the base embed
        embed = discord.Embed(
            title=f"Skill Tree: {tree_display_name}",
            description=f"You have {self.player_data.skill_points} skill points to spend.",
            color=discord.Color.blue()
        )
        
        # Get tree nodes
        tree_nodes = {
            "strength": [
                ("Power Strike", "Increases physical damage by 5% per level", 1, 5),
                ("Brute Force", "Chance to ignore defense", 2, 5),
                ("Weapon Mastery", "Increases weapon damage", 3, 5),
                ("Smashing Blow", "Deals heavy damage with a chance to stun", 4, 3),
                ("Titan's Grip", "Can use two-handed weapons in one hand", 5, 1)
            ],
            "dexterity": [
                ("Precise Shot", "Increases accuracy by 5% per level", 1, 5),
                ("Quick Draw", "Chance for an extra attack", 2, 5),
                ("Evasive Maneuvers", "Increases dodge chance", 3, 5),
                ("Critical Eye", "Increases critical hit chance", 4, 3),
                ("Sniper's Focus", "Guaranteed critical hit after aiming for a turn", 5, 1)
            ],
            "intelligence": [
                ("Arcane Mind", "Increases magical damage by 5% per level", 1, 5),
                ("Spell Mastery", "Reduces energy cost of spells", 2, 5),
                ("Elemental Affinity", "Increases elemental damage", 3, 5),
                ("Counterspell", "Chance to nullify enemy spell effects", 4, 3),
                ("Archmage's Presence", "Spells have a chance to cost no energy", 5, 1)
            ],
            "wisdom": [
                ("Healing Touch", "Increases healing effect by 5% per level", 1, 5),
                ("Spirit Link", "Shared healing between allies", 2, 5),
                ("Protective Aura", "Provides damage reduction to allies", 3, 5),
                ("Divine Intervention", "Chance to prevent fatal damage", 4, 3),
                ("Resurrection", "Can revive fallen allies in dungeon runs", 5, 1)
            ],
            "vitality": [
                ("Iron Skin", "Increases defense by 5% per level", 1, 5),
                ("Endurance", "Increases max health", 2, 5),
                ("Regeneration", "Recover health over time", 3, 5),
                ("Unbreakable", "Chance to resist status effects", 4, 3),
                ("Undying Will", "Survive fatal damage once per battle", 5, 1)
            ],
            "agility": [
                ("Quick Reflexes", "Increases action speed by 5% per level", 1, 5),
                ("Dual Wielding", "Improves damage when using two weapons", 2, 5),
                ("Shadow Step", "Chance to dodge attacks completely", 3, 5),
                ("Exploit Weakness", "Increased critical damage", 4, 3),
                ("Assassination", "Chance for instant kill on weak enemies", 5, 1)
            ]
        }
        
        nodes = tree_nodes.get(self.current_tree, [])
        player_tree_progress = self.player_data.skill_tree.get(self.current_tree, {})
        
        # Group nodes by tier
        tier_nodes = {}
        for name, desc, tier, max_level in nodes:
            if tier not in tier_nodes:
                tier_nodes[tier] = []
            tier_nodes[tier].append((name, desc, max_level, player_tree_progress.get(name, 0)))
        
        # Add fields for each tier
        for tier in sorted(tier_nodes.keys()):
            tier_text = []
            for name, desc, max_level, current_level in tier_nodes[tier]:
                progress = f"[{current_level}/{max_level}]"
                tier_text.append(f"**{name}** {progress}\n*{desc}*")
            
            embed.add_field(
                name=f"Tier {tier}",
                value="\n\n".join(tier_text),
                inline=False
            )
        
        # Add total points spent in this tree
        total_points = self.player_data.skill_points_spent.get(self.current_tree, 0)
        embed.set_footer(text=f"Total points spent in {tree_display_name}: {total_points}")
        
        return embed

async def skill_tree_command(ctx, data_manager: DataManager):
    """View and allocate points in your skill tree"""
    player = data_manager.get_player(ctx.author.id)
    
    if not player.class_name:
        await ctx.send("You need to start your adventure before you can access the skill tree! Use the `!start` command.")
        return
    
    # Create the skill tree view
    view = SkillTreeView(player, data_manager)
    
    # Send the initial message
    await ctx.send(
        content=f"Skill Tree for {ctx.author.display_name}",
        embed=view.create_skill_tree_embed(),
        view=view
    )

async def skills_tree_command(ctx, data_manager: DataManager):
    """Alias for skill_tree command"""
    await skill_tree_command(ctx, data_manager)