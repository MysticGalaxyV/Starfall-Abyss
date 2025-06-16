import discord
from discord.ui import Button, View, Select
import random
import string
from typing import Dict, List, Optional, Any

from data_models import PlayerData, DataManager, Item, InventoryItem
from user_restrictions import RestrictedView, get_target_user, create_restricted_embed_footer

# Shop items database - organized by level tiers
SHOP_ITEMS = {
    # Special non-equipment items
    "special": [
        {
            "name": "Guild Charter",
            "description": "An official document required to establish a guild. Provides legal recognition and basic privileges.",
            "item_type": "consumable",
            "rarity": "rare",
            "stats": {},
            "level_req": 20,
            "value": 5000
        },
        {
            "name": "Domain Expansion Scroll",
            "description": "A rare scroll containing ancient knowledge to unlock your domain expansion technique.",
            "item_type": "consumable",
            "rarity": "epic",
            "stats": {},
            "level_req": 40,
            "value": 10000
        },
        {
            "name": "Technique Reset Crystal",
            "description": "A mysterious crystal that allows reallocation of skill points and stats.",
            "item_type": "consumable",
            "rarity": "uncommon",
            "stats": {},
            "level_req": 15,
            "value": 2000
        }
    ],

    # Level 1-3 Shop Items
    "beginner": [
        {
            "name": "Cursed Tool: Novice Staff",
            "description": "A basic staff that channels cursed energy.",
            "item_type": "weapon",
            "rarity": "common",
            "stats": {"power": 3},
            "level_req": 1,
            "value": 50
        },
        {
            "name": "Jujutsu Sorcerer Uniform",
            "description": "Standard uniform worn by jujutsu students.",
            "item_type": "armor",
            "rarity": "common",
            "stats": {"defense": 3},
            "level_req": 1,
            "value": 50
        },
        {
            "name": "Brawler's Boots",
            "description": "Quick-movement footwear for agile fighters.",
            "item_type": "accessory",
            "rarity": "common",
            "stats": {"speed": 3},
            "level_req": 1,
            "value": 50
        },
        {
            "name": "Cursed Armband",
            "description": "An armband that helps control cursed energy flow.",
            "item_type": "accessory",
            "rarity": "common",
            "stats": {"power": 1, "defense": 1},
            "level_req": 1,
            "value": 45
        },
        {
            "name": "Spike Knuckles",
            "description": "Hand protection with offensive spikes.",
            "item_type": "weapon",
            "rarity": "common",
            "stats": {"power": 2, "speed": 1},
            "level_req": 1,
            "value": 45
        },
        {
            "name": "Health Potion",
            "description": "Restores 50 HP during battle.",
            "item_type": "consumable",
            "rarity": "common",
            "stats": {},
            "level_req": 1,
            "value": 30
        },
        {
            "name": "Energy Potion",
            "description": "Restores 40 energy during battle.",
            "item_type": "consumable",
            "rarity": "common",
            "stats": {},
            "level_req": 1,
            "value": 30
        }
    ],

    # Level 4-7 Shop Items
    "intermediate": [
        {
            "name": "Cursed Tool: Binding Threads",
            "description": "Strings imbued with cursed energy that immobilize opponents.",
            "item_type": "weapon",
            "rarity": "uncommon",
            "stats": {"power": 7},
            "level_req": 4,
            "value": 200
        },
        {
            "name": "Grade 2 Sorcerer Robe",
            "description": "Protective garment worn by Grade 2 jujutsu sorcerers.",
            "item_type": "armor",
            "rarity": "uncommon",
            "stats": {"defense": 7},
            "level_req": 4,
            "value": 200
        },
        {
            "name": "Brawler's Combat Gloves",
            "description": "Enhances reflexes and striking power.",
            "item_type": "accessory",
            "rarity": "uncommon",
            "stats": {"speed": 5, "power": 2},
            "level_req": 4,
            "value": 200
        },
        {
            "name": "Cursed Energy Conductor",
            "description": "A bracelet that helps channel cursed energy more efficiently.",
            "item_type": "accessory",
            "rarity": "uncommon",
            "stats": {"power": 4, "defense": 3},
            "level_req": 4,
            "value": 210
        },
        {
            "name": "Star Power Charm",
            "description": "A lucky charm that enhances your natural abilities.",
            "item_type": "accessory",
            "rarity": "uncommon",
            "stats": {"hp": 15, "speed": 3},
            "level_req": 5,
            "value": 225
        },
        {
            "name": "Greater Health Potion",
            "description": "Restores 120 HP during battle.",
            "item_type": "consumable",
            "rarity": "uncommon",
            "stats": {},
            "level_req": 4,
            "value": 100
        },
        {
            "name": "Greater Energy Potion",
            "description": "Restores 80 energy during battle.",
            "item_type": "consumable",
            "rarity": "uncommon",
            "stats": {},
            "level_req": 4,
            "value": 100
        },
        {
            "name": "Strength Elixir",
            "description": "Increases strength for 3 turns during battle.",
            "item_type": "consumable",
            "rarity": "uncommon",
            "stats": {},
            "level_req": 5,
            "value": 150
        }
    ],

    # Level 8-12 Shop Items
    "advanced": [
        {
            "name": "Cursed Tool: Malevolent Blade",
            "description": "A special-grade weapon that amplifies cursed techniques.",
            "item_type": "weapon",
            "rarity": "rare",
            "stats": {"power": 12, "speed": 3},
            "level_req": 8,
            "value": 500
        },
        {
            "name": "Grade 1 Sorcerer Attire",
            "description": "Battle garment worn by elite Grade 1 jujutsu sorcerers.",
            "item_type": "armor",
            "rarity": "rare",
            "stats": {"defense": 15, "hp": 30},
            "level_req": 8,
            "value": 500
        },
        {
            "name": "Domain Amplifier",
            "description": "A rare accessory that strengthens your domain abilities.",
            "item_type": "accessory",
            "rarity": "rare",
            "stats": {"power": 5, "speed": 5},
            "level_req": 8,
            "value": 500
        },
        {
            "name": "Brawler's Gadget",
            "description": "A specialized device that enhances combat efficiency.",
            "item_type": "accessory",
            "rarity": "rare",
            "stats": {"defense": 6, "speed": 6},
            "level_req": 9,
            "value": 550
        },
        {
            "name": "Cursed Technique Enhancer",
            "description": "A device that amplifies the user's innate cursed technique.",
            "item_type": "weapon",
            "rarity": "rare",
            "stats": {"power": 10, "defense": 5},
            "level_req": 10,
            "value": 600
        },
        {
            "name": "Superior Health Potion",
            "description": "Restores 200 HP during battle.",
            "item_type": "consumable",
            "rarity": "rare",
            "stats": {},
            "level_req": 8,
            "value": 250
        },
        {
            "name": "Superior Energy Potion",
            "description": "Restores 150 energy during battle.",
            "item_type": "consumable",
            "rarity": "rare",
            "stats": {},
            "level_req": 8,
            "value": 250
        },
        {
            "name": "Guardian Shield Potion",
            "description": "Creates a defensive shield for 3 turns during battle.",
            "item_type": "consumable",
            "rarity": "rare",
            "stats": {},
            "level_req": 10,
            "value": 300
        }
    ],

    # Level 13+ Shop Items
    "elite": [
        {
            "name": "Special Grade Cursed Tool",
            "description": "A legendary weapon used by the most powerful jujutsu sorcerers.",
            "item_type": "weapon",
            "rarity": "epic",
            "stats": {"power": 20, "speed": 5},
            "level_req": 13,
            "value": 1200
        },
        {
            "name": "Domain Barrier Attire",
            "description": "Special armor that strengthens your domain and provides exceptional protection.",
            "item_type": "armor",
            "rarity": "epic",
            "stats": {"defense": 25, "hp": 60},
            "level_req": 13,
            "value": 1200
        },
        {
            "name": "Reverse Cursed Technique Amplifier",
            "description": "A powerful accessory that enhances healing and offensive capabilities.",
            "item_type": "accessory",
            "rarity": "epic",
            "stats": {"power": 10, "defense": 10, "speed": 10},
            "level_req": 13,
            "value": 1200
        },
        {
            "name": "Brawler's Legendary Gadget",
            "description": "The ultimate combat enhancement device used by champion brawlers.",
            "item_type": "accessory",
            "rarity": "epic",
            "stats": {"power": 8, "speed": 15, "defense": 8},
            "level_req": 14,
            "value": 1350
        },
        {
            "name": "Limitless Technique Vessel",
            "description": "A rare artifact that grants aspects of the legendary Limitless Technique.",
            "item_type": "weapon",
            "rarity": "epic",
            "stats": {"power": 25, "hp": 30},
            "level_req": 15,
            "value": 1500
        },
        {
            "name": "Master Health Potion",
            "description": "Restores 400 HP during battle.",
            "item_type": "consumable",
            "rarity": "epic",
            "stats": {},
            "level_req": 13,
            "value": 500
        },
        {
            "name": "Master Energy Potion",
            "description": "Restores 300 energy during battle.",
            "item_type": "consumable",
            "rarity": "epic",
            "stats": {},
            "level_req": 13,
            "value": 500
        },
        {
            "name": "Ultimate Combat Elixir",
            "description": "Increases all combat stats for 3 turns during battle.",
            "item_type": "consumable",
            "rarity": "epic",
            "stats": {},
            "level_req": 15,
            "value": 800
        }
    ]
}

# Rare and unique items that can drop from dungeons
RARE_ITEMS = [
    {
        "name": "Cursed Spirit Blade",
        "description": "A blade that channels cursed spirits.",
        "item_type": "weapon",
        "rarity": "rare",
        "stats": {"power": 10, "speed": 5},
        "level_req": 5,
        "value": 600
    },
    {
        "name": "Domain Essence Armor",
        "description": "Armor infused with domain energy.",
        "item_type": "armor",
        "rarity": "rare",
        "stats": {"defense": 12, "hp": 40},
        "level_req": 5,
        "value": 600
    },
    {
        "name": "Limitless Pendant",
        "description": "Enhances your natural abilities.",
        "item_type": "accessory",
        "rarity": "rare",
        "stats": {"power": 6, "defense": 6, "speed": 6},
        "level_req": 5,
        "value": 600
    },
    {
        "name": "Sukuna's Finger",
        "description": "A powerful cursed object that enhances attacks.",
        "item_type": "weapon",
        "rarity": "epic",
        "stats": {"power": 15, "speed": 8},
        "level_req": 8,
        "value": 1500
    },
    {
        "name": "Infinity Curse Armor",
        "description": "Legendary armor with unmatched protection.",
        "item_type": "armor",
        "rarity": "epic",
        "stats": {"defense": 20, "hp": 60},
        "level_req": 8,
        "value": 1500
    },
    {
        "name": "Ten Shadows Talisman",
        "description": "A talisman that grants shadow abilities.",
        "item_type": "accessory",
        "rarity": "epic",
        "stats": {"power": 10, "defense": 8, "speed": 10},
        "level_req": 8,
        "value": 1500
    },
    {
        "name": "Mahoraga Wheel",
        "description": "A divine item that adapts to any situation.",
        "item_type": "accessory",
        "rarity": "legendary",
        "stats": {"power": 15, "defense": 15, "speed": 15, "hp": 50},
        "level_req": 12,
        "value": 5000
    },
    {
        "name": "Star Power: Dynamike's Demolition",
        "description": "Legendary Brawler power that amplifies all explosive techniques.",
        "item_type": "accessory",
        "rarity": "legendary",
        "stats": {"power": 20, "speed": 10, "defense": 5},
        "level_req": 12,
        "value": 5000
    },
    {
        "name": "Domain Expansion Core",
        "description": "Legendary armor that creates its own domain.",
        "item_type": "armor",
        "rarity": "legendary",
        "stats": {"defense": 30, "hp": 100, "power": 10},
        "level_req": 12,
        "value": 5000
    },
    {
        "name": "Star Power: Bull's Berserker",
        "description": "Legendary Brawler armor that becomes stronger as you take damage.",
        "item_type": "armor",
        "rarity": "legendary",
        "stats": {"defense": 25, "hp": 120, "speed": 5},
        "level_req": 12,
        "value": 5000
    },
    {
        "name": "Black Flash Sword",
        "description": "A legendary weapon that cuts through reality.",
        "item_type": "weapon",
        "rarity": "legendary",
        "stats": {"power": 30, "speed": 20, "defense": 5},
        "level_req": 12,
        "value": 5000
    },
    {
        "name": "Star Power: Shelly's Shell Shock",
        "description": "The most powerful brawler weapon, causes massive damage and slows opponents.",
        "item_type": "weapon",
        "rarity": "legendary",
        "stats": {"power": 28, "speed": 15, "defense": 10},
        "level_req": 12,
        "value": 5000
    }
]

def generate_item_id() -> str:
    """Generate a unique item ID"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=8))

def generate_random_item(level: int) -> Item:
    """Generate a random item appropriate for the given level"""
    # Determine item tier based on level
    if level <= 3:
        tier = "beginner"
    elif level <= 7:
        tier = "intermediate"
    elif level <= 12:
        tier = "advanced"
    else:
        tier = "elite"

    # Get item pool from shop items
    item_pool = SHOP_ITEMS[tier]

    # Choose a random item
    item_data = random.choice(item_pool)

    # Create and return the item
    return Item(
        item_id=generate_item_id(),
        name=item_data["name"],
        description=item_data["description"],
        item_type=item_data["item_type"],
        rarity=item_data["rarity"],
        stats=item_data["stats"],
        level_req=item_data["level_req"],
        value=item_data["value"]
    )

def generate_rare_item(level: int) -> Item:
    """Generate a rare item from dungeon drops"""
    # Filter items by level requirement
    eligible_items = [item for item in RARE_ITEMS if item["level_req"] <= level]

    if not eligible_items:
        # Fallback to regular item if no eligible rare items
        return generate_random_item(level)

    # Choose a random item
    item_data = random.choice(eligible_items)

    # Create and return the item
    return Item(
        item_id=generate_item_id(),
        name=item_data["name"],
        description=item_data["description"],
        item_type=item_data["item_type"],
        rarity=item_data["rarity"],
        stats=item_data["stats"],
        level_req=item_data["level_req"],
        value=item_data["value"]
    )

def add_item_to_inventory(player: PlayerData, item: Item) -> None:
    """Add an item to player's inventory, stacking consumables"""
    # For consumables, check if we already have this item
    if item.item_type == "consumable":
        for inv_item in player.inventory:
            if inv_item.item.name == item.name:
                # Stack consumables
                inv_item.quantity += 1
                return

    # Otherwise, add as new item
    player.inventory.append(InventoryItem(item=item, quantity=1, equipped=False))

class ItemActionView(View):
    def __init__(self, player_data: PlayerData, inventory_item: InventoryItem, data_manager: DataManager):
        super().__init__(timeout=60)
        self.player_data = player_data
        self.inventory_item = inventory_item
        self.data_manager = data_manager
        self.result = None

        # Add appropriate buttons based on item type
        if inventory_item.item.item_type != "consumable":
            # Equipment items can be equipped or sold
            equip_label = "Unequip" if inventory_item.equipped else "Equip"
            equip_btn = Button(
                label=equip_label, 
                style=discord.ButtonStyle.green if not inventory_item.equipped else discord.ButtonStyle.red,
                emoji="🔄"
            )
            equip_btn.callback = self.equip_callback
            self.add_item(equip_btn)

        # All items can be sold
        sell_btn = Button(
            label=f"Sell (${inventory_item.item.value})",
            style=discord.ButtonStyle.gray,
            emoji="💰"
        )
        sell_btn.callback = self.sell_callback
        self.add_item(sell_btn)

        # Cancel button
        cancel_btn = Button(
            label="Cancel",
            style=discord.ButtonStyle.red,
            emoji="❌"
        )
        cancel_btn.callback = self.cancel_callback
        self.add_item(cancel_btn)

    async def equip_callback(self, interaction: discord.Interaction):
        """Handle equipping/unequipping an item"""
        if self.inventory_item.equipped:
            # Unequip
            self.inventory_item.equipped = False

            # Also remove from equipped_items dictionary
            for slot, item_id in self.player_data.equipped_items.items():
                if item_id == self.inventory_item.item.item_id:
                    self.player_data.equipped_items[slot] = None

            await interaction.response.edit_message(
                content=f"✅ {self.inventory_item.item.name} has been unequipped.",
                view=None
            )
        else:
            # Determine the slot based on item type
            slot = None
            if self.inventory_item.item.item_type == "weapon":
                # Check for dual wielding capability
                from utils import can_dual_wield
                
                if self.player_data.class_name and can_dual_wield(self.player_data.class_name):
                    # For dual wielding classes, check both weapon slots
                    if not self.player_data.equipped_items["weapon"]:
                        slot = "weapon"
                    elif not self.player_data.equipped_items["weapon2"]:
                        slot = "weapon2"
                    else:
                        # Both slots full, replace main hand weapon
                        slot = "weapon"
                else:
                    # Single weapon slot for non-dual wielding classes
                    slot = "weapon"
            elif self.inventory_item.item.item_type == "armor":
                slot = "armor"
            elif self.inventory_item.item.item_type == "accessory":
                slot = "accessory"

            if slot:
                # Unequip any previous item in this slot
                if self.player_data.equipped_items[slot]:
                    # Find the equipped item and unequip it
                    for inv_item in self.player_data.inventory:
                        if hasattr(inv_item.item, "item_id") and inv_item.item.item_id == self.player_data.equipped_items[slot]:
                            inv_item.equipped = False

                # Equip this item
                self.inventory_item.equipped = True
                self.player_data.equipped_items[slot] = self.inventory_item.item.item_id

                # Display appropriate slot name
                slot_display = "main hand" if slot == "weapon" else ("off hand" if slot == "weapon2" else slot)
                await interaction.response.edit_message(
                    content=f"✅ {self.inventory_item.item.name} has been equipped as your {slot_display}.",
                    view=None
                )
            else:
                await interaction.response.edit_message(
                    content=f"❌ Cannot equip {self.inventory_item.item.name} - unknown item type.",
                    view=None
                )
                return

        # Save player data
        self.data_manager.save_data()
        self.result = "equipped" if self.inventory_item.equipped else "unequipped"
        self.stop()

    async def sell_callback(self, interaction: discord.Interaction):
        """Handle selling an item"""
        item_name = self.inventory_item.item.name
        item_value = self.inventory_item.item.value

        # Can't sell equipped items
        if self.inventory_item.equipped:
            await interaction.response.edit_message(
                content="❌ You can't sell an equipped item. Please unequip it first.",
                view=self
            )
            return

        # Process sale - earn gold from selling items
        self.player_data.gold += item_value

        # Remove from inventory (or decrease quantity for consumables)
        if self.inventory_item.item.item_type == "consumable" and self.inventory_item.quantity > 1:
            self.inventory_item.quantity -= 1
            await interaction.response.edit_message(
                content=f"💰 Sold 1x {item_name} for {item_value} gold. {self.inventory_item.quantity}x remaining.",
                view=None
            )
        else:
            self.player_data.inventory.remove(self.inventory_item)
            await interaction.response.edit_message(
                content=f"💰 Sold {item_name} for {item_value} gold.",
                view=None
            )

        # Save player data
        self.data_manager.save_data()
        self.result = "sold"
        self.stop()

    async def cancel_callback(self, interaction: discord.Interaction):
        """Handle canceling the action"""
        await interaction.response.edit_message(
            content="❌ Action canceled.",
            view=None
        )
        self.result = "canceled"
        self.stop()

class InventoryView(RestrictedView):
    def __init__(self, player_data: PlayerData, data_manager: DataManager, authorized_user):
        super().__init__(authorized_user, timeout=180)
        self.player_data = player_data
        self.data_manager = data_manager
        self.current_page = 0
        self.items_per_page = 5

        # Create select menu for item types
        self.type_select = Select(
            placeholder="Filter by item type",
            options=[
                discord.SelectOption(label="All Items", value="all", default=True),
                discord.SelectOption(label="Weapons", value="weapon"),
                discord.SelectOption(label="Armor", value="armor"),
                discord.SelectOption(label="Accessories", value="accessory"),
                discord.SelectOption(label="Consumables", value="consumable")
            ]
        )
        self.type_select.callback = self.filter_callback
        self.add_item(self.type_select)

        # Add navigation buttons
        self.prev_btn = Button(label="◀️ Previous", style=discord.ButtonStyle.gray)
        self.prev_btn.callback = self.prev_callback

        self.next_btn = Button(label="Next ▶️", style=discord.ButtonStyle.gray)
        self.next_btn.callback = self.next_callback

        self.add_item(self.prev_btn)
        self.add_item(self.next_btn)

        # Add item select buttons (will be populated in update_buttons)
        self.selected_type = "all"
        self.update_buttons()

    def get_filtered_items(self):
        """Get items filtered by selected type"""
        if self.selected_type == "all":
            return self.player_data.inventory
        else:
            return [item for item in self.player_data.inventory if item.item.item_type == self.selected_type]

    def update_buttons(self):
        """Update item buttons based on current page and filter"""
        # Remove old item buttons
        for item in list(self.children):
            if isinstance(item, Button) and item not in [self.prev_btn, self.next_btn]:
                self.remove_item(item)

        # Get filtered items
        filtered_items = self.get_filtered_items()

        # Calculate page bounds
        total_pages = max(1, (len(filtered_items) + self.items_per_page - 1) // self.items_per_page)
        self.current_page = min(self.current_page, total_pages - 1)

        # Update navigation button states
        self.prev_btn.disabled = self.current_page == 0
        self.next_btn.disabled = self.current_page >= total_pages - 1

        # Calculate slice for current page
        start_idx = self.current_page * self.items_per_page
        end_idx = start_idx + self.items_per_page
        current_items = filtered_items[start_idx:end_idx]

        # Add item buttons
        for i, inv_item in enumerate(current_items):
            # Choose emoji and style based on item type and equipped status
            if inv_item.item.item_type == "weapon":
                emoji = "⚔️"
            elif inv_item.item.item_type == "armor":
                emoji = "🛡️"
            elif inv_item.item.item_type == "accessory":
                emoji = "💍"
            else:  # consumable
                emoji = "🧪"

            # Add quantity label for consumables
            label = inv_item.item.name
            if inv_item.item.item_type == "consumable" and inv_item.quantity > 1:
                label = f"{label} (x{inv_item.quantity})"

            # Add equipped indicator
            if inv_item.equipped:
                label = f"[E] {label}"
                style = discord.ButtonStyle.green
            else:
                style = discord.ButtonStyle.gray

            # Create button
            btn = Button(
                label=label,
                emoji=emoji,
                style=style,
                row=1 + (i // 2)  # Use multiple rows for layout
            )

            # Store item reference in button
            btn.inv_item = inv_item
            btn.callback = self.item_callback

            self.add_item(btn)

    async def filter_callback(self, interaction: discord.Interaction):
        """Handle item type filter selection"""
        self.selected_type = self.type_select.values[0]
        self.current_page = 0
        self.update_buttons()

        # Update message with inventory embed
        embed = self.create_inventory_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    async def prev_callback(self, interaction: discord.Interaction):
        """Handle previous page button"""
        self.current_page = max(0, self.current_page - 1)
        self.update_buttons()

        # Update message with inventory embed
        embed = self.create_inventory_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    async def next_callback(self, interaction: discord.Interaction):
        """Handle next page button"""
        filtered_items = self.get_filtered_items()
        total_pages = max(1, (len(filtered_items) + self.items_per_page - 1) // self.items_per_page)

        self.current_page = min(total_pages - 1, self.current_page + 1)
        self.update_buttons()

        # Update message with inventory embed
        embed = self.create_inventory_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    async def item_callback(self, interaction: discord.Interaction):
        """Handle item selection"""
        # Get selected item
        for item in self.children:
            if isinstance(item, Button) and item.custom_id == interaction.data["custom_id"]:
                inventory_item = item.inv_item
                break
        else:
            await interaction.response.send_message("❌ Error: Item not found!", ephemeral=True)
            return

        # Show item details embed
        embed = discord.Embed(
            title=f"{inventory_item.item.name}",
            description=inventory_item.item.description,
            color=self.get_rarity_color(inventory_item.item.rarity)
        )

        # Add item details
        embed.add_field(
            name="Type",
            value=inventory_item.item.item_type.title(),
            inline=True
        )

        embed.add_field(
            name="Rarity",
            value=inventory_item.item.rarity.title(),
            inline=True
        )

        embed.add_field(
            name="Level Requirement",
            value=str(inventory_item.item.level_req),
            inline=True
        )

        # Add stats
        stats_text = "None"
        if inventory_item.item.stats:
            stats_text = "\n".join([f"**{stat.title()}:** +{value}" for stat, value in inventory_item.item.stats.items()])

        embed.add_field(
            name="Stats",
            value=stats_text,
            inline=False
        )

        embed.add_field(
            name="Status",
            value="Equipped" if inventory_item.equipped else "Not Equipped",
            inline=True
        )

        embed.add_field(
            name="Value",
            value=f"{inventory_item.item.value} Gold",
            inline=True
        )

        # Create item action view
        action_view = ItemActionView(self.player_data, inventory_item, self.data_manager)

        await interaction.response.send_message(embed=embed, view=action_view)

        # Wait for action to complete
        await action_view.wait()

        if action_view.result in ["equipped", "unequipped", "sold"]:
            # Update inventory view
            self.update_buttons()

            try:
                original_message = interaction.message
                embed = self.create_inventory_embed()
                await original_message.edit(embed=embed, view=self)
            except:
                pass

    def create_inventory_embed(self):
        """Create inventory embed based on current page and filter"""
        # Get filtered items
        filtered_items = self.get_filtered_items()

        # Calculate pagination info
        total_pages = max(1, (len(filtered_items) + self.items_per_page - 1) // self.items_per_page)
        start_idx = self.current_page * self.items_per_page
        end_idx = min(start_idx + self.items_per_page, len(filtered_items))

        # Create embed
        embed = discord.Embed(
            title=f"🎒 {self.player_data.class_name}'s Inventory",
            description=f"Gold: {self.player_data.gold} 💰\nItems: {len(self.player_data.inventory)}\n"
                       f"Filter: {self.selected_type.title()}",
            color=discord.Color.gold()
        )

        # Add item list
        for i, inv_item in enumerate(filtered_items[start_idx:end_idx], start=1):
            # Format item name with equipped status and rarity color
            rarity_emoji = self.get_rarity_emoji(inv_item.item.rarity)
            equipped_text = " [Equipped]" if inv_item.equipped else ""

            # Add quantity for consumables
            quantity_text = f" (x{inv_item.quantity})" if inv_item.item.item_type == "consumable" and inv_item.quantity > 1 else ""

            # Format item stats
            stats_text = ""
            if inv_item.item.stats:
                stats_list = [f"{stat.title()}: +{value}" for stat, value in inv_item.item.stats.items()]
                stats_text = f" ({', '.join(stats_list)})"

            embed.add_field(
                name=f"{i}. {rarity_emoji} {inv_item.item.name}{equipped_text}{quantity_text}",
                value=f"Type: {inv_item.item.item_type.title()}{stats_text}\n"
                      f"Level Req: {inv_item.item.level_req} | Value: {inv_item.item.value} Gold",
                inline=False
            )

        # Add equipped items summary with dual weapon support
        from utils import can_dual_wield
        
        equipped_text_lines = []
        
        # Display weapons with dual wield support
        main_weapon_id = self.player_data.equipped_items.get("weapon")
        off_weapon_id = self.player_data.equipped_items.get("weapon2")
        
        if main_weapon_id:
            for item in self.player_data.inventory:
                if hasattr(item.item, "item_id") and item.item.item_id == main_weapon_id:
                    equipped_text_lines.append(f"**Main Hand**: {item.item.name}")
                    break
        
        if self.player_data.class_name and can_dual_wield(self.player_data.class_name) and off_weapon_id:
            for item in self.player_data.inventory:
                if hasattr(item.item, "item_id") and item.item.item_id == off_weapon_id:
                    equipped_text_lines.append(f"**Off Hand**: {item.item.name}")
                    break
        
        # Display other equipment
        armor_id = self.player_data.equipped_items.get("armor")
        accessory_id = self.player_data.equipped_items.get("accessory")
        
        if armor_id:
            for item in self.player_data.inventory:
                if hasattr(item.item, "item_id") and item.item.item_id == armor_id:
                    equipped_text_lines.append(f"**Armor**: {item.item.name}")
                    break
        
        if accessory_id:
            for item in self.player_data.inventory:
                if hasattr(item.item, "item_id") and item.item.item_id == accessory_id:
                    equipped_text_lines.append(f"**Accessory**: {item.item.name}")
                    break
        
        equipped_text = "\n".join(equipped_text_lines) if equipped_text_lines else "None"

        embed.add_field(
            name="🔆 Equipped Items",
            value=equipped_text,
            inline=False
        )

        embed.set_footer(text=f"Page {self.current_page + 1}/{total_pages}")
        return embed

    def get_rarity_color(self, rarity: str) -> discord.Color:
        """Get color for item rarity"""
        rarity_colors = {
            "common": discord.Color.light_grey(),
            "uncommon": discord.Color.green(),
            "rare": discord.Color.blue(),
            "epic": discord.Color.purple(),
            "legendary": discord.Color.gold()
        }
        return rarity_colors.get(rarity.lower(), discord.Color.default())

    def get_rarity_emoji(self, rarity: str) -> str:
        """Get emoji for item rarity"""
        rarity_emojis = {
            "common": "⚪",
            "uncommon": "🟢",
            "rare": "🔵",
            "epic": "🟣",
            "legendary": "🟠"
        }
        return rarity_emojis.get(rarity.lower(), "⚪")

class ShopView(RestrictedView):
    def __init__(self, player_data: PlayerData, data_manager: DataManager, authorized_user):
        super().__init__(authorized_user, timeout=180)
        self.player_data = player_data
        self.data_manager = data_manager
        self.current_page = 0
        self.items_per_page = 5

        # Create select menu for shop categories
        self.category_select = Select(
            placeholder="Select shop category",
            options=[
                discord.SelectOption(label="All Items", value="all", default=True),
                discord.SelectOption(label="Weapons", value="weapon"),
                discord.SelectOption(label="Armor", value="armor"),
                discord.SelectOption(label="Accessories", value="accessory"),
                discord.SelectOption(label="Consumables", value="consumable")
            ]
        )
        self.category_select.callback = self.category_callback
        self.add_item(self.category_select)

        # Add navigation buttons
        self.prev_btn = Button(label="◀️ Previous", style=discord.ButtonStyle.gray)
        self.prev_btn.callback = self.prev_callback

        self.next_btn = Button(label="Next ▶️", style=discord.ButtonStyle.gray)
        self.next_btn.callback = self.next_callback

        self.add_item(self.prev_btn)
        self.add_item(self.next_btn)

        # Initialize
        self.selected_category = "all"
        self.shop_items = self.get_available_shop_items()
        self.update_buttons()

    def get_available_shop_items(self):
        """Get all shop items available to the player based on level"""
        player_level = self.player_data.class_level
        available_items = []

        # Iterate through all tiers
        for tier, items in SHOP_ITEMS.items():
            for item_data in items:
                # Check level requirement
                if item_data["level_req"] <= player_level:
                    # Filter by category if needed
                    if self.selected_category == "all" or item_data["item_type"] == self.selected_category:
                        # Convert to Item object
                        item = Item(
                            item_id=generate_item_id(),
                            name=item_data["name"],
                            description=item_data["description"],
                            item_type=item_data["item_type"],
                            rarity=item_data["rarity"],
                            stats=item_data["stats"],
                            level_req=item_data["level_req"],
                            value=item_data["value"]
                        )
                        available_items.append(item)

        # Sort by level requirement and then by value
        available_items.sort(key=lambda x: (x.level_req, x.value))
        return available_items

    def update_buttons(self):
        """Update shop item buttons based on current page and filter"""
        # Remove old item buttons
        for item in list(self.children):
            if isinstance(item, Button) and item not in [self.prev_btn, self.next_btn]:
                self.remove_item(item)

        # Calculate page bounds
        total_pages = max(1, (len(self.shop_items) + self.items_per_page - 1) // self.items_per_page)
        self.current_page = min(self.current_page, total_pages - 1)

        # Update navigation button states
        self.prev_btn.disabled = self.current_page == 0
        self.next_btn.disabled = self.current_page >= total_pages - 1

        # Calculate slice for current page
        start_idx = self.current_page * self.items_per_page
        end_idx = start_idx + self.items_per_page
        current_items = self.shop_items[start_idx:end_idx]

        # Add item buttons
        for i, item in enumerate(current_items):
            # Choose emoji based on item type
            if item.item_type == "weapon":
                emoji = "⚔️"
            elif item.item_type == "armor":
                emoji = "🛡️"
            elif item.item_type == "accessory":
                emoji = "💍"
            else:  # consumable
                emoji = "🧪"

            # Check if player can afford it
            can_afford = self.player_data.gold >= item.value

            # Create button
            btn = Button(
                label=f"{item.name} ({item.value} 💰)",
                emoji=emoji,
                style=discord.ButtonStyle.green if can_afford else discord.ButtonStyle.gray,
                disabled=not can_afford,
                row=1 + (i // 2)  # Use multiple rows for layout
            )

            # Store item reference in button
            btn.shop_item = item
            btn.callback = self.buy_callback

            self.add_item(btn)

    async def category_callback(self, interaction: discord.Interaction):
        """Handle category filter selection"""
        self.selected_category = self.category_select.values[0]
        self.current_page = 0
        self.shop_items = self.get_available_shop_items()
        self.update_buttons()

        # Update message with shop embed
        embed = self.create_shop_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    async def prev_callback(self, interaction: discord.Interaction):
        """Handle previous page button"""
        self.current_page = max(0, self.current_page - 1)
        self.update_buttons()

        # Update message with shop embed
        embed = self.create_shop_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    async def next_callback(self, interaction: discord.Interaction):
        """Handle next page button"""
        total_pages = max(1, (len(self.shop_items) + self.items_per_page - 1) // self.items_per_page)

        self.current_page = min(total_pages - 1, self.current_page + 1)
        self.update_buttons()

        # Update message with shop embed
        embed = self.create_shop_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    async def buy_callback(self, interaction: discord.Interaction):
        """Handle item purchase"""
        # Get selected item
        for item in self.children:
            if isinstance(item, Button) and item.custom_id == interaction.data["custom_id"]:
                shop_item = item.shop_item
                break
        else:
            await interaction.response.send_message("❌ Error: Item not found!", ephemeral=True)
            return

        # Check if player can afford the item
        if self.player_data.gold < shop_item.value:
            await interaction.response.send_message(
                f"❌ You can't afford this item! It costs {shop_item.value} gold 💰, but you only have {self.player_data.gold} 💰.",
                ephemeral=True
            )
            return

        # Process purchase
        self.player_data.remove_gold(shop_item.value)
        add_item_to_inventory(self.player_data, shop_item)

        # Save player data
        self.data_manager.save_data()

        # Update buttons (player may no longer be able to afford some items)
        self.update_buttons()

        # Send confirmation
        await interaction.response.send_message(
            f"✅ You purchased {shop_item.name} for {shop_item.value} gold! 💰",
            ephemeral=True
        )

        # Update shop view
        embed = self.create_shop_embed()
        await interaction.message.edit(embed=embed, view=self)

    def create_shop_embed(self):
        """Create shop embed based on current page and filter"""
        # Calculate pagination info
        total_pages = max(1, (len(self.shop_items) + self.items_per_page - 1) // self.items_per_page)
        start_idx = self.current_page * self.items_per_page
        end_idx = min(start_idx + self.items_per_page, len(self.shop_items))

        # Create embed
        embed = discord.Embed(
            title="🛒 Jujutsu Supplies Shop",
            description=f"Gold: {self.player_data.gold} 💰\n"
                       f"Filter: {self.selected_category.title() if self.selected_category != 'all' else 'All Items'}\n"
                       f"Click on an item to purchase it.",
            color=discord.Color.dark_purple()
        )

        # Add shop items
        for i, item in enumerate(self.shop_items[start_idx:end_idx], start=1):
            # Format item with rarity emoji
            rarity_emoji = self.get_rarity_emoji(item.rarity)

            # Format item stats
            stats_text = ""
            if item.stats:
                stats_list = [f"{stat.title()}: +{value}" for stat, value in item.stats.items()]
                stats_text = f" ({', '.join(stats_list)})"

            # Add affordability indicator
            affordable = "✅" if self.player_data.gold >= item.value else "❌"

            embed.add_field(
                name=f"{i}. {rarity_emoji} {item.name} - {item.value} 💰 {affordable}",
                value=f"Type: {item.item_type.title()}{stats_text}\n"
                      f"Level Req: {item.level_req}\n{item.description}",
                inline=False
            )

        embed.set_footer(text=f"Page {self.current_page + 1}/{total_pages}")
        return embed

    def get_rarity_emoji(self, rarity: str) -> str:
        """Get emoji for item rarity"""
        rarity_emojis = {
            "common": "⚪",
            "uncommon": "🟢",
            "rare": "🔵",
            "epic": "🟣",
            "legendary": "🟠"
        }
        return rarity_emojis.get(rarity.lower(), "⚪")

async def equipment_command(ctx, data_manager: DataManager):
    """View and manage your equipment"""
    # Only the command author can interact with their own equipment interface
    player_data = data_manager.get_player(ctx.author.id)

    # Check if player has started
    if not player_data.class_name:
        await ctx.send("❌ You haven't started your adventure yet! Use `!start` to choose a class.")
        return

    # Create inventory view
    inventory_view = InventoryView(player_data, data_manager, ctx.author)
    embed = inventory_view.create_inventory_embed()

    # Add footer to indicate who can use this interface
    embed.set_footer(text=f"🔒 Only {ctx.author.display_name} can interact with this interface")

    await ctx.send(embed=embed, view=inventory_view)

async def shop_command(ctx, data_manager: DataManager):
    """Browse the item shop"""
    # Only the command author can interact with their own shop interface
    player_data = data_manager.get_player(ctx.author.id)

    # Check if player has started
    if not player_data.class_name:
        await ctx.send("❌ You haven't started your adventure yet! Use `!start` to choose a class.")
        return

    # Create shop view
    shop_view = ShopView(player_data, data_manager, ctx.author)
    embed = shop_view.create_shop_embed()

    # Add footer to indicate who can use this interface
    embed.set_footer(text=f"🔒 Only {ctx.author.display_name} can interact with this interface")

    await ctx.send(embed=embed, view=shop_view)

async def buy_command(ctx, item_name: str, data_manager: DataManager):
    """Buy an item by name"""
    if not item_name:
        await ctx.send("❌ Please specify an item name. Use `!shop` to see available items.")
        return

    player_data = data_manager.get_player(ctx.author.id)

    # Check if player has started
    if not player_data.class_name:
        await ctx.send("❌ You haven't started your adventure yet! Use `!start` to choose a class.")
        return

    # Get all available shop items
    available_items = []
    player_level = player_data.class_level

    for tier, items in SHOP_ITEMS.items():
        for item_data in items:
            if item_data["level_req"] <= player_level:
                available_items.append(item_data)

    # Find the matching item
    matching_items = [item for item in available_items if item["name"].lower() == item_name.lower()]

    if not matching_items:
        # Try partial match
        matching_items = [item for item in available_items if item_name.lower() in item["name"].lower()]

    if not matching_items:
        await ctx.send(f"❌ Item '{item_name}' not found in the shop. Use `!shop` to see available items.")
        return

    # If multiple matches, pick the first one
    item_data = matching_items[0]

    # Check if player can afford it
    if player_data.gold < item_data["value"]:
        await ctx.send(f"❌ You can't afford this item! It costs {item_data['value']} gold 💰, but you only have {player_data.gold} 💰.")
        return

    # Process purchase
    player_data.remove_gold(item_data["value"])

    # Create and add item to inventory
    new_item = Item(
        item_id=generate_item_id(),
        name=item_data["name"],
        description=item_data["description"],
        item_type=item_data["item_type"],
        rarity=item_data["rarity"],
        stats=item_data["stats"],
        level_req=item_data["level_req"],
        value=item_data["value"]
    )

    add_item_to_inventory(player_data, new_item)

    # Save player data
    data_manager.save_data()

    # Create confirmation embed
    embed = discord.Embed(
        title="✅ Purchase Successful",
        description=f"You have purchased {new_item.name} for {new_item.value} gold! 💰",
        color=discord.Color.dark_purple()
    )

    # Add item details
    embed.add_field(
        name="Item Details",
        value=f"**Type:** {new_item.item_type.title()}\n"
              f"**Rarity:** {new_item.rarity.title()}\n"
              f"**Description:** {new_item.description}",
        inline=False
    )

    # Add stats if any
    if new_item.stats:
        stats_text = "\n".join([f"**{stat.title()}:** +{value}" for stat, value in new_item.stats.items()])
        embed.add_field(
            name="Stats",
            value=stats_text,
            inline=False
        )

    # Add remaining gold
    embed.add_field(
        name="Remaining Gold",
        value=f"{player_data.gold} 💰",
        inline=False
    )

    await ctx.send(embed=embed)
