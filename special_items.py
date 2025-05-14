import discord
from discord.ui import Button, View, Select
import random
import asyncio
import datetime
from typing import Dict, List, Optional, Tuple, Any

from data_models import PlayerData, DataManager, Item, InventoryItem
from utils import GAME_CLASSES, ADVANCED_CLASSES, STARTER_CLASSES

# Special transformation items that can change character abilities
TRANSFORMATION_ITEMS = {
    "Domain Expansion Scroll": {
        "description": "A mystical scroll that teaches the Domain Expansion technique",
        "rarity": "legendary",
        "level_req": 15,
        "effect": "special_ability",
        "ability_name": "Domain Expansion",
        "ability_description": "Create a domain where you control the rules of reality",
        "stats_boost": {"power": 20, "defense": 10, "speed": 5, "hp": 50},
        "cooldown": 72,  # hours
        "value": 10000
    },
    "Limitless Technique Manual": {
        "description": "A manual containing the secrets of the Six Eyes and Limitless technique",
        "rarity": "legendary",
        "level_req": 18,
        "effect": "special_ability",
        "ability_name": "Infinity",
        "ability_description": "Stop attacks at 'infinity' before they reach you",
        "stats_boost": {"power": 15, "defense": 25, "speed": 15, "hp": 25},
        "cooldown": 72,  # hours
        "value": 12000
    },
    "Reverse Cursed Technique Scroll": {
        "description": "A scroll teaching how to use cursed energy to heal",
        "rarity": "epic",
        "level_req": 12,
        "effect": "healing",
        "ability_name": "Reverse Cursed Technique",
        "ability_description": "Use cursed energy to heal yourself and allies",
        "stats_boost": {"hp": 100},
        "cooldown": 24,  # hours
        "value": 5000
    },
    "Ten Shadows Summoning Contract": {
        "description": "A contract allowing the summoning of shadow beasts",
        "rarity": "epic",
        "level_req": 10,
        "effect": "summon",
        "ability_name": "Ten Shadows Technique",
        "ability_description": "Summon shadow beasts to fight alongside you",
        "stats_boost": {"power": 30},
        "cooldown": 48,  # hours
        "value": 7500
    },
    "Black Flash Crystal": {
        "description": "A crystal that teaches the legendary Black Flash technique",
        "rarity": "epic",
        "level_req": 8,
        "effect": "critical",
        "ability_name": "Black Flash",
        "ability_description": "Land critical hits that distort space",
        "stats_boost": {"power": 40, "speed": 10},
        "cooldown": 24,  # hours
        "value": 5000
    }
}

# Rare consumable items with powerful temporary effects
SPECIAL_CONSUMABLES = {
    "Sukuna's Finger": {
        "description": "A cursed object that grants immense power temporarily",
        "rarity": "legendary",
        "level_req": 10,
        "effect": "all_stats_boost",
        "boost_amount": 50,
        "duration": 1,  # battles
        "value": 3000
    },
    "Gojo's Blindfold": {
        "description": "A special blindfold that enhances your perception",
        "rarity": "epic",
        "level_req": 8,
        "effect": "dodge_boost",
        "boost_amount": 75,  # % chance to dodge
        "duration": 2,  # battles
        "value": 2000
    },
    "Cursed Womb": {
        "description": "A strange object that creates a temporary cursed ally",
        "rarity": "epic",
        "level_req": 6,
        "effect": "summon_ally",
        "ally_power": 0.5,  # 50% of player's power
        "duration": 1,  # battles
        "value": 1500
    },
    "Mahito's Soul": {
        "description": "The remnant of Mahito's soul that can reshape your body",
        "rarity": "epic",
        "level_req": 9,
        "effect": "hp_boost",
        "boost_amount": 200,
        "duration": 3,  # battles
        "value": 2500
    },
    "Todo's Clap": {
        "description": "A technique that creates a temporary copy of yourself",
        "rarity": "rare",
        "level_req": 5,
        "effect": "double_attack",
        "chance": 40,  # % chance to attack twice
        "duration": 2,  # battles
        "value": 1000
    }
}

def generate_special_item_id() -> str:
    """Generate a unique ID for special items"""
    import string
    return "SP_" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def create_transformation_item(item_name: str) -> Item:
    """Create a transformation item"""
    item_data = TRANSFORMATION_ITEMS[item_name]
    
    return Item(
        item_id=generate_special_item_id(),
        name=item_name,
        description=item_data["description"],
        item_type="special",
        rarity=item_data["rarity"],
        stats=item_data.get("stats_boost", {}),
        level_req=item_data["level_req"],
        value=item_data["value"]
    )

def create_special_consumable(item_name: str) -> Item:
    """Create a special consumable item"""
    item_data = SPECIAL_CONSUMABLES[item_name]
    
    return Item(
        item_id=generate_special_item_id(),
        name=item_name,
        description=item_data["description"],
        item_type="special_consumable",
        rarity=item_data["rarity"],
        stats={},  # consumables don't have permanent stat boosts
        level_req=item_data["level_req"],
        value=item_data["value"]
    )

class SpecialItemView(View):
    def __init__(self, player_data: PlayerData, item_name: str, data_manager: DataManager):
        super().__init__(timeout=60)
        self.player_data = player_data
        self.item_name = item_name
        self.data_manager = data_manager
        
        # Check if it's a transformation or consumable
        self.is_transformation = item_name in TRANSFORMATION_ITEMS
        self.is_consumable = item_name in SPECIAL_CONSUMABLES
        
        if not self.is_transformation and not self.is_consumable:
            raise ValueError(f"Unknown special item: {item_name}")
        
        # Add Use button
        use_btn = Button(
            label="Use Item",
            style=discord.ButtonStyle.green,
            emoji="✨"
        )
        use_btn.callback = self.use_callback
        self.add_item(use_btn)
        
        # Add Cancel button
        cancel_btn = Button(
            label="Cancel",
            style=discord.ButtonStyle.red,
            emoji="❌"
        )
        cancel_btn.callback = self.cancel_callback
        self.add_item(cancel_btn)
    
    async def use_callback(self, interaction: discord.Interaction):
        """Handle using the special item"""
        # Process based on item type
        if self.is_transformation:
            await self.use_transformation_item(interaction)
        elif self.is_consumable:
            await self.use_consumable_item(interaction)
    
    async def use_transformation_item(self, interaction: discord.Interaction):
        """Use a transformation item that grants special abilities"""
        item_data = TRANSFORMATION_ITEMS[self.item_name]
        
        # Check level requirement
        if self.player_data.class_level < item_data["level_req"]:
            await interaction.response.send_message(
                f"❌ You need to be level {item_data['level_req']} to use this item!",
                ephemeral=True
            )
            return
        
        # Check if the player already has this special ability
        player_abilities = self.player_data.__dict__.get("special_abilities", {})
        if item_data["ability_name"] in player_abilities:
            await interaction.response.send_message(
                f"❌ You already know the {item_data['ability_name']} ability!",
                ephemeral=True
            )
            return
        
        # Confirm the use
        confirm_view = View(timeout=30)
        
        confirm_btn = Button(
            label="Confirm",
            style=discord.ButtonStyle.green,
            emoji="✅"
        )
        
        cancel_btn = Button(
            label="Cancel",
            style=discord.ButtonStyle.red,
            emoji="❌"
        )
        
        async def confirm_callback(confirm_interaction):
            # Initialize special abilities if it doesn't exist
            if not hasattr(self.player_data, "special_abilities"):
                self.player_data.special_abilities = {}
            
            # Apply permanent stat boosts
            stats_boost = item_data.get("stats_boost", {})
            for stat, boost in stats_boost.items():
                if stat in self.player_data.allocated_stats:
                    self.player_data.allocated_stats[stat] += boost
                else:
                    self.player_data.allocated_stats[stat] = boost
            
            # Add special ability
            self.player_data.special_abilities[item_data["ability_name"]] = {
                "description": item_data["ability_description"],
                "effect": item_data["effect"],
                "cooldown": item_data["cooldown"],
                "last_used": None
            }
            
            # Remove the item from inventory
            for i, inv_item in enumerate(self.player_data.inventory):
                if inv_item.item.name == self.item_name:
                    if inv_item.quantity > 1:
                        inv_item.quantity -= 1
                    else:
                        self.player_data.inventory.pop(i)
                    break
            
            # Save player data
            self.data_manager.save_data()
            
            # Create result embed
            embed = discord.Embed(
                title="✨ Special Item Used!",
                description=f"You have learned the **{item_data['ability_name']}** ability!",
                color=discord.Color.gold()
            )
            
            embed.add_field(
                name="Ability Description",
                value=item_data["ability_description"],
                inline=False
            )
            
            # Add stat boosts
            stat_text = ""
            for stat, boost in stats_boost.items():
                stat_text += f"**{stat.title()}:** +{boost}\n"
            
            if stat_text:
                embed.add_field(
                    name="Permanent Stat Boosts",
                    value=stat_text,
                    inline=False
                )
            
            embed.add_field(
                name="Cooldown",
                value=f"This ability can be used once every {item_data['cooldown']} hours.",
                inline=False
            )
            
            await confirm_interaction.response.edit_message(
                content=None,
                embed=embed,
                view=None
            )
            
            # Stop the view
            self.stop()
        
        async def cancel_callback(cancel_interaction):
            await cancel_interaction.response.edit_message(
                content="❌ Cancelled using the special item.",
                view=None
            )
            
            # Stop the view
            self.stop()
        
        # Set callbacks
        confirm_btn.callback = confirm_callback
        cancel_btn.callback = cancel_callback
        
        # Add buttons
        confirm_view.add_item(confirm_btn)
        confirm_view.add_item(cancel_btn)
        
        # Show confirmation
        await interaction.response.send_message(
            f"⚠️ You're about to use **{self.item_name}** to learn the **{item_data['ability_name']}** ability.\n\n"
            f"This will permanently consume the item. Are you sure?",
            view=confirm_view
        )
    
    async def use_consumable_item(self, interaction: discord.Interaction):
        """Use a special consumable with temporary effects"""
        item_data = SPECIAL_CONSUMABLES[self.item_name]
        
        # Check level requirement
        if self.player_data.class_level < item_data["level_req"]:
            await interaction.response.send_message(
                f"❌ You need to be level {item_data['level_req']} to use this item!",
                ephemeral=True
            )
            return
        
        # Confirm the use
        confirm_view = View(timeout=30)
        
        confirm_btn = Button(
            label="Confirm",
            style=discord.ButtonStyle.green,
            emoji="✅"
        )
        
        cancel_btn = Button(
            label="Cancel",
            style=discord.ButtonStyle.red,
            emoji="❌"
        )
        
        async def confirm_callback(confirm_interaction):
            # Initialize active effects if it doesn't exist
            if not hasattr(self.player_data, "active_effects"):
                self.player_data.active_effects = {}
            
            # Add the effect
            self.player_data.active_effects[self.item_name] = {
                "effect": item_data["effect"],
                "duration": item_data["duration"],
                "boost_amount": item_data.get("boost_amount", 0),
                "ally_power": item_data.get("ally_power", 0),
                "chance": item_data.get("chance", 0)
            }
            
            # Remove the item from inventory
            for i, inv_item in enumerate(self.player_data.inventory):
                if inv_item.item.name == self.item_name:
                    if inv_item.quantity > 1:
                        inv_item.quantity -= 1
                    else:
                        self.player_data.inventory.pop(i)
                    break
            
            # Save player data
            self.data_manager.save_data()
            
            # Create result embed
            embed = discord.Embed(
                title="🧪 Special Consumable Used!",
                description=f"You have used **{self.item_name}**!",
                color=discord.Color.purple()
            )
            
            embed.add_field(
                name="Effect",
                value=item_data["description"],
                inline=False
            )
            
            embed.add_field(
                name="Duration",
                value=f"This effect will last for the next {item_data['duration']} battles.",
                inline=False
            )
            
            await confirm_interaction.response.edit_message(
                content=None,
                embed=embed,
                view=None
            )
            
            # Stop the view
            self.stop()
        
        async def cancel_callback(cancel_interaction):
            await cancel_interaction.response.edit_message(
                content="❌ Cancelled using the consumable.",
                view=None
            )
            
            # Stop the view
            self.stop()
        
        # Set callbacks
        confirm_btn.callback = confirm_callback
        cancel_btn.callback = cancel_callback
        
        # Add buttons
        confirm_view.add_item(confirm_btn)
        confirm_view.add_item(cancel_btn)
        
        # Show confirmation
        await interaction.response.send_message(
            f"⚠️ You're about to use **{self.item_name}**.\n\n"
            f"This will give you a temporary effect for {item_data['duration']} battles. Are you sure?",
            view=confirm_view
        )
    
    async def cancel_callback(self, interaction: discord.Interaction):
        """Handle cancellation"""
        await interaction.response.send_message("❌ Cancelled using the item.", ephemeral=True)
        self.stop()

class SpecialAbilitiesView(View):
    def __init__(self, player_data: PlayerData, data_manager: DataManager):
        super().__init__(timeout=60)
        self.player_data = player_data
        self.data_manager = data_manager
        
        # Get special abilities
        self.abilities = getattr(player_data, "special_abilities", {})
        
        if not self.abilities:
            # No abilities, so just add a cancel button
            cancel_btn = Button(
                label="Close",
                style=discord.ButtonStyle.red,
                emoji="❌"
            )
            cancel_btn.callback = self.cancel_callback
            self.add_item(cancel_btn)
        else:
            # Add buttons for each ability
            for ability_name in self.abilities.keys():
                # Check cooldown
                ability_data = self.abilities[ability_name]
                on_cooldown = False
                
                if ability_data["last_used"]:
                    # Calculate time since last use
                    now = datetime.datetime.now()
                    last_used = datetime.datetime.fromisoformat(ability_data["last_used"]) 
                    hours_since = (now - last_used).total_seconds() / 3600
                    
                    # Check if still on cooldown
                    if hours_since < ability_data["cooldown"]:
                        on_cooldown = True
                
                # Create button
                ability_btn = Button(
                    label=ability_name,
                    style=discord.ButtonStyle.green if not on_cooldown else discord.ButtonStyle.gray,
                    emoji="✨" if not on_cooldown else "⏳",
                    disabled=on_cooldown
                )
                ability_btn.custom_id = ability_name
                ability_btn.callback = self.ability_callback
                self.add_item(ability_btn)
            
            # Add cancel button
            cancel_btn = Button(
                label="Close",
                style=discord.ButtonStyle.red,
                emoji="❌"
            )
            cancel_btn.callback = self.cancel_callback
            self.add_item(cancel_btn)
    
    async def ability_callback(self, interaction: discord.Interaction):
        """Handle using a special ability"""
        ability_name = interaction.data["custom_id"]
        ability_data = self.abilities[ability_name]
        
        # Update last used time
        now = datetime.datetime.now()
        self.abilities[ability_name]["last_used"] = now.isoformat()
        
        # Save player data
        self.data_manager.save_data()
        
        # Create result embed
        embed = discord.Embed(
            title=f"✨ {ability_name} Activated!",
            description=f"You have activated the **{ability_name}** ability!",
            color=discord.Color.gold()
        )
        
        embed.add_field(
            name="Effect",
            value=ability_data["description"],
            inline=False
        )
        
        embed.add_field(
            name="Cooldown",
            value=f"This ability will be available again in {ability_data['cooldown']} hours.",
            inline=False
        )
        
        # Disable buttons and update message
        for item in self.children:
            if isinstance(item, Button) and item.custom_id == ability_name:
                item.disabled = True
                item.emoji = "⏳"
                item.style = discord.ButtonStyle.gray
        
        await interaction.response.edit_message(
            content=f"✨ You've activated **{ability_name}**!",
            embed=embed,
            view=self
        )
    
    async def cancel_callback(self, interaction: discord.Interaction):
        """Handle cancellation"""
        await interaction.response.edit_message(
            content="Closed abilities menu.",
            embed=None,
            view=None
        )
        self.stop()

async def special_items_command(ctx, data_manager: DataManager):
    """View and use your special items"""
    player_data = data_manager.get_player(ctx.author.id)
    
    # Check if player has started
    if not player_data.class_name:
        await ctx.send("❌ You haven't started your adventure yet! Use `!start` to choose a class.")
        return
    
    # Get special items from inventory
    special_items = []
    special_consumables = []
    
    for inv_item in player_data.inventory:
        if inv_item.item.item_type == "special":
            special_items.append(inv_item)
        elif inv_item.item.item_type == "special_consumable":
            special_consumables.append(inv_item)
    
    # Create embed for special items
    embed = discord.Embed(
        title="✨ Special Items",
        description="View and use your special items and abilities.",
        color=discord.Color.gold()
    )
    
    # Add info about transformation items
    if special_items:
        items_text = ""
        for inv_item in special_items:
            items_text += f"**{inv_item.item.name}** (x{inv_item.quantity}) - {inv_item.item.description}\n"
        
        embed.add_field(
            name="Transformation Items",
            value=items_text,
            inline=False
        )
    else:
        embed.add_field(
            name="Transformation Items",
            value="You don't have any transformation items.",
            inline=False
        )
    
    # Add info about special consumables
    if special_consumables:
        consumables_text = ""
        for inv_item in special_consumables:
            consumables_text += f"**{inv_item.item.name}** (x{inv_item.quantity}) - {inv_item.item.description}\n"
        
        embed.add_field(
            name="Special Consumables",
            value=consumables_text,
            inline=False
        )
    else:
        embed.add_field(
            name="Special Consumables",
            value="You don't have any special consumables.",
            inline=False
        )
    
    # Add info about unlocked special abilities
    abilities = getattr(player_data, "special_abilities", {})
    if abilities:
        abilities_text = ""
        for ability_name, ability_data in abilities.items():
            # Check cooldown
            status = "Ready"
            if ability_data["last_used"]:
                # Calculate time since last use
                now = datetime.datetime.now()
                try:
                    last_used = datetime.datetime.fromisoformat(ability_data["last_used"])
                    hours_since = (now - last_used).total_seconds() / 3600
                    
                    # Check if still on cooldown
                    if hours_since < ability_data["cooldown"]:
                        hours_left = ability_data["cooldown"] - hours_since
                        status = f"On cooldown ({int(hours_left)} hours remaining)"
                except (ValueError, TypeError):
                    status = "Ready"
            
            abilities_text += f"**{ability_name}** - {ability_data['description']} ({status})\n"
        
        embed.add_field(
            name="Special Abilities",
            value=abilities_text,
            inline=False
        )
    else:
        embed.add_field(
            name="Special Abilities",
            value="You haven't unlocked any special abilities yet.",
            inline=False
        )
    
    # Create view with options
    view = View(timeout=60)
    
    # Add dropdown for using items if available
    if special_items or special_consumables:
        item_select = Select(
            placeholder="Select an item to use",
            min_values=1,
            max_values=1
        )
        
        # Add options for all special items
        for inv_item in special_items + special_consumables:
            item_select.add_option(
                label=inv_item.item.name,
                description=f"{inv_item.item.description[:50]}...",
                value=inv_item.item.name
            )
        
        async def item_select_callback(interaction):
            # Get selected item
            item_name = item_select.values[0]
            
            # Create special item view
            item_view = SpecialItemView(player_data, item_name, data_manager)
            
            # Show item view
            await interaction.response.send_message(
                f"You selected **{item_name}**.",
                view=item_view,
                ephemeral=True
            )
        
        item_select.callback = item_select_callback
        view.add_item(item_select)
    
    # Add button for using abilities if available
    if abilities:
        abilities_btn = Button(
            label="Use Special Abilities",
            style=discord.ButtonStyle.primary,
            emoji="✨"
        )
        
        async def abilities_callback(interaction):
            # Create abilities view
            abilities_view = SpecialAbilitiesView(player_data, data_manager)
            
            # Show abilities view
            await interaction.response.send_message(
                "Select an ability to use:",
                view=abilities_view,
                ephemeral=True
            )
        
        abilities_btn.callback = abilities_callback
        view.add_item(abilities_btn)
    
    # Add close button
    close_btn = Button(
        label="Close",
        style=discord.ButtonStyle.red,
        emoji="❌"
    )
    
    async def close_callback(interaction):
        await interaction.response.edit_message(
            content="Closed special items menu.",
            embed=None,
            view=None
        )
    
    close_btn.callback = close_callback
    view.add_item(close_btn)
    
    # Send message with embed and view
    await ctx.send(embed=embed, view=view)

async def get_random_special_drop(player_level: int) -> Optional[Item]:
    """Get a random special item drop based on player level and luck"""
    # Determine drop chance based on level
    # Higher level = higher chance for better items
    legendary_chance = min(2 + (player_level * 0.1), 5)  # Max 5% at level 30
    epic_chance = min(5 + (player_level * 0.2), 15)      # Max 15% at level 50
    rare_chance = min(10 + (player_level * 0.5), 30)     # Max 30% at level 40
    
    # Roll for rarity
    roll = random.random() * 100
    
    # Determine item type (transformation or consumable)
    is_transformation = random.random() < 0.3  # 30% chance for transformation item
    
    if roll < legendary_chance:
        # Legendary drop
        rarity = "legendary"
    elif roll < (legendary_chance + epic_chance):
        # Epic drop
        rarity = "epic"
    elif roll < (legendary_chance + epic_chance + rare_chance):
        # Rare drop
        rarity = "rare"
    else:
        # No special drop
        return None
    
    # Get items of the selected rarity
    if is_transformation:
        possible_items = [name for name, data in TRANSFORMATION_ITEMS.items() 
                         if data["rarity"] == rarity and data["level_req"] <= player_level]
    else:
        possible_items = [name for name, data in SPECIAL_CONSUMABLES.items() 
                         if data["rarity"] == rarity and data["level_req"] <= player_level]
    
    # If no items match the criteria, return None
    if not possible_items:
        return None
    
    # Choose a random item
    item_name = random.choice(possible_items)
    
    # Create and return the item
    if is_transformation:
        return create_transformation_item(item_name)
    else:
        return create_special_consumable(item_name)