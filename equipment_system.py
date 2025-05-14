import discord
from discord.ui import View, Button, Select
import random
from typing import Dict, List, Optional

from data_manager import PlayerData
from constants import ITEM_RARITY, SHOP_ITEMS

class EquipmentView(View):
    """View for equipping/unequipping items"""
    def __init__(self, player: PlayerData, timeout=60):
        super().__init__(timeout=timeout)
        self.player = player
        self.result = None
        self.action = None
        
        # Add equip button if player has items
        if player.inventory:
            equip_btn = Button(label="Equip Item", emoji="👕", style=discord.ButtonStyle.primary, custom_id="equip")
            equip_btn.callback = self.equip_callback
            self.add_item(equip_btn)
            
        # Add unequip button if player has equipped items
        has_equipped = any(item is not None for item in player.equipped_items.values())
        if has_equipped:
            unequip_btn = Button(label="Unequip Item", emoji="🧦", style=discord.ButtonStyle.secondary, custom_id="unequip")
            unequip_btn.callback = self.unequip_callback
            self.add_item(unequip_btn)
    
    async def equip_callback(self, interaction):
        self.action = "equip"
        await interaction.response.defer()
        self.stop()
    
    async def unequip_callback(self, interaction):
        self.action = "unequip"
        await interaction.response.defer()
        self.stop()

class ItemSelectView(View):
    """View for selecting an item from inventory"""
    def __init__(self, items: List[Dict], timeout=60):
        super().__init__(timeout=timeout)
        self.selected_item = None
        
        # Create a dropdown for item selection
        options = []
        for item in items:
            emoji = "🗡️"
            if item.get("slot") == "armor":
                emoji = "🛡️"
            elif item.get("slot") == "accessory":
                emoji = "💍"
            elif item.get("slot") == "talisman":
                emoji = "📿"
            
            options.append(discord.SelectOption(
                label=item["name"],
                description=f"{item.get('slot', 'accessory').title()} - Lvl {item.get('level_req', 1)}",
                emoji=emoji,
                value=item["name"]
            ))
        
        # Add a dropdown if we have options
        if options:
            select = Select(
                placeholder="Select an item...",
                options=options[:25],  # Discord limits to 25 options
                custom_id="item_select"
            )
            select.callback = self.select_callback
            self.add_item(select)
        
        # Add a cancel button
        cancel_btn = Button(label="Cancel", emoji="❌", style=discord.ButtonStyle.danger, custom_id="cancel")
        cancel_btn.callback = self.cancel_callback
        self.add_item(cancel_btn)
    
    async def select_callback(self, interaction):
        self.selected_item = interaction.data["values"][0]
        self.stop()
        await interaction.response.defer()
    
    async def cancel_callback(self, interaction):
        self.stop()
        await interaction.response.defer()

class SlotSelectView(View):
    """View for selecting which equipment slot to unequip"""
    def __init__(self, player: PlayerData, timeout=60):
        super().__init__(timeout=timeout)
        self.selected_slot = None
        
        # Create buttons for each equipped slot
        for slot, item in player.equipped_items.items():
            if item:
                btn = Button(
                    label=f"Unequip {item['name']}",
                    custom_id=slot,
                    style=discord.ButtonStyle.secondary
                )
                btn.callback = self.slot_callback
                self.add_item(btn)
        
        # Add cancel button
        cancel_btn = Button(label="Cancel", emoji="❌", style=discord.ButtonStyle.danger, custom_id="cancel")
        cancel_btn.callback = self.cancel_callback
        self.add_item(cancel_btn)
    
    async def slot_callback(self, interaction):
        self.selected_slot = interaction.data["custom_id"]
        self.stop()
        await interaction.response.defer()
    
    async def cancel_callback(self, interaction):
        self.stop()
        await interaction.response.defer()

class ShopView(View):
    """View for the shop interface"""
    def __init__(self, player: PlayerData, shop_items: List[Dict], timeout=60):
        super().__init__(timeout=timeout)
        self.player = player
        self.selected_item = None
        
        # Create buttons for each shop item
        for i, item in enumerate(shop_items):
            can_afford = player.currency >= item["price"]
            meets_level = player.class_level >= item.get("level_req", 1)
            
            btn = Button(
                label=f"{item['name']} ({item['price']} 🌀)",
                style=discord.ButtonStyle.primary if (can_afford and meets_level) else discord.ButtonStyle.secondary,
                custom_id=f"item_{i}",
                disabled=not (can_afford and meets_level)
            )
            
            async def make_callback(i=i, item=item):
                async def callback(interaction):
                    self.selected_item = item
                    await interaction.response.defer()
                    self.stop()
                return callback
            
            btn.callback = await make_callback()
            self.add_item(btn)
            
            # Only show up to 5 items at a time (Discord button limit)
            if i >= 4:
                break
        
        # Add a refresh button
        refresh_btn = Button(label="Refresh Shop", emoji="🔄", style=discord.ButtonStyle.secondary, custom_id="refresh")
        refresh_btn.callback = self.refresh_callback
        self.add_item(refresh_btn)
    
    async def refresh_callback(self, interaction):
        # Set a special value to indicate refresh
        self.selected_item = "refresh"
        await interaction.response.defer()
        self.stop()

class EquipmentSystem:
    """Handles equipment-related functionality"""
    @staticmethod
    async def show_inventory(ctx, player: PlayerData):
        """Display a player's inventory"""
        if not player.class_name:
            await ctx.send("❌ You haven't created a character yet! Use `!start` to begin.")
            return
        
        # Create inventory embed
        embed = discord.Embed(
            title=f"🎒 {ctx.author.name}'s Inventory",
            description=f"Currency: {player.currency} 🌀",
            color=discord.Color.gold()
        )
        
        # Group items by type
        equipment = [item for item in player.inventory if item.get("type") == "equipment"]
        consumables = [item for item in player.inventory if item.get("type") == "consumable"]
        other_items = [item for item in player.inventory if item.get("type") not in ["equipment", "consumable"]]
        
        # Display equipped items
        equipped_text = ""
        for slot, item in player.equipped_items.items():
            if item:
                rarity_emoji = ITEM_RARITY.get(item.get("rarity", "common"), "⚪")
                equipped_text += f"{rarity_emoji} **{slot.title()}:** {item['name']}\n"
        
        if equipped_text:
            embed.add_field(name="📦 Equipped Items", value=equipped_text, inline=False)
        else:
            embed.add_field(name="📦 Equipped Items", value="No items equipped", inline=False)
        
        # Display equipment
        if equipment:
            equipment_text = ""
            for item in equipment:
                rarity_emoji = ITEM_RARITY.get(item.get("rarity", "common"), "⚪")
                equipment_text += f"{rarity_emoji} {item['name']} ({item.get('slot', 'accessory').title()})\n"
            
            embed.add_field(name="⚔️ Equipment", value=equipment_text, inline=False)
        
        # Display consumables
        if consumables:
            consumable_text = ""
            for item in consumables:
                effects = []
                if "heal" in item:
                    effects.append(f"Heal {item['heal']} HP")
                if "energy" in item:
                    effects.append(f"Restore {item['energy']} CE")
                if "effect" in item:
                    effects.append(f"{item['effect'].title()} effect")
                
                effect_str = " • ".join(effects)
                consumable_text += f"🧪 {item['name']} - {effect_str}\n"
            
            embed.add_field(name="🧪 Consumables", value=consumable_text, inline=False)
        
        # Display other items
        if other_items:
            other_text = ""
            for item in other_items:
                other_text += f"📦 {item['name']}\n"
            
            embed.add_field(name="📦 Other Items", value=other_text, inline=False)
        
        # Show empty inventory message if no items
        if not player.inventory and not any(player.equipped_items.values()):
            embed.add_field(
                name="Empty Inventory",
                value="You don't have any items yet. Find items in dungeons or buy them from the shop!",
                inline=False
            )
        
        # Add instructions
        embed.set_footer(text="Use !equip to equip items, !unequip to unequip items, and !shop to buy new items.")
        
        await ctx.send(embed=embed)
    
    @staticmethod
    async def manage_equipment(ctx, player: PlayerData):
        """Manage equipment (equip/unequip)"""
        if not player.class_name:
            await ctx.send("❌ You haven't created a character yet! Use `!start` to begin.")
            return
        
        # Create equipment management embed
        embed = discord.Embed(
            title="⚔️ Equipment Management",
            description="Manage your character's equipment:",
            color=discord.Color.blue()
        )
        
        # Show current equipment
        equipment_text = ""
        for slot, item in player.equipped_items.items():
            if item:
                equipment_text += f"**{slot.title()}:** {item['name']}\n"
            else:
                equipment_text += f"**{slot.title()}:** None\n"
        
        embed.add_field(name="Currently Equipped", value=equipment_text, inline=False)
        
        # Show inventory count
        equipment_count = len([item for item in player.inventory if item.get("type") == "equipment"])
        embed.add_field(name="Inventory", value=f"{equipment_count} equipment items available", inline=False)
        
        # Equipment management buttons
        view = EquipmentView(player)
        message = await ctx.send(embed=embed, view=view)
        
        # Wait for user action
        await view.wait()
        
        if view.action == "equip":
            # Show equippable items
            equipment = [item for item in player.inventory if item.get("type") == "equipment"]
            
            if not equipment:
                await message.edit(content="❌ You don't have any equipment to equip!", embed=None, view=None)
                return
            
            # Create item selection view
            item_view = ItemSelectView(equipment)
            item_embed = discord.Embed(
                title="👕 Equip Item",
                description="Select an item to equip:",
                color=discord.Color.blue()
            )
            
            await message.edit(embed=item_embed, view=item_view)
            
            # Wait for item selection
            await item_view.wait()
            
            if item_view.selected_item:
                # Equip the selected item
                success = player.equip_item(item_view.selected_item)
                
                if success:
                    # Find the equipped item for details
                    equipped_item = None
                    for slot, item in player.equipped_items.items():
                        if item and item["name"] == item_view.selected_item:
                            equipped_item = item
                            break
                    
                    if equipped_item:
                        # Show success message with item details
                        success_embed = discord.Embed(
                            title="✅ Item Equipped!",
                            description=f"You equipped **{equipped_item['name']}**!",
                            color=discord.Color.green()
                        )
                        
                        # Item details
                        stats_text = ""
                        for stat, value in equipped_item.get("stats_boost", {}).items():
                            stats_text += f"{stat.title()}: +{value}\n"
                        
                        success_embed.add_field(
                            name="Item Stats",
                            value=stats_text if stats_text else "No stat bonuses",
                            inline=True
                        )
                        
                        if "description" in equipped_item:
                            success_embed.add_field(
                                name="Description",
                                value=equipped_item["description"],
                                inline=True
                            )
                        
                        await message.edit(embed=success_embed, view=None)
                    else:
                        await message.edit(content="✅ Item equipped successfully!", embed=None, view=None)
                else:
                    await message.edit(
                        content="❌ Failed to equip the item. You may not meet the level requirement.",
                        embed=None,
                        view=None
                    )
            else:
                await message.edit(content="❌ Equipment selection cancelled.", embed=None, view=None)
        
        elif view.action == "unequip":
            # Show unequip options
            slot_view = SlotSelectView(player)
            slot_embed = discord.Embed(
                title="🧦 Unequip Item",
                description="Select an item to unequip:",
                color=discord.Color.blue()
            )
            
            await message.edit(embed=slot_embed, view=slot_view)
            
            # Wait for slot selection
            await slot_view.wait()
            
            if slot_view.selected_slot:
                # Get item before unequipping
                item_name = player.equipped_items[slot_view.selected_slot]["name"]
                
                # Unequip the selected slot
                success = player.unequip_item(slot_view.selected_slot)
                
                if success:
                    await message.edit(
                        content=f"✅ Successfully unequipped **{item_name}** from your {slot_view.selected_slot}.",
                        embed=None,
                        view=None
                    )
                else:
                    await message.edit(
                        content="❌ Failed to unequip the item.",
                        embed=None,
                        view=None
                    )
            else:
                await message.edit(content="❌ Unequip cancelled.", embed=None, view=None)
        else:
            await message.edit(content="❌ Equipment management cancelled.", embed=None, view=None)
    
    @staticmethod
    async def show_shop(ctx, player: PlayerData):
        """Display and interact with the shop"""
        if not player.class_name:
            await ctx.send("❌ You haven't created a character yet! Use `!start` to begin.")
            return
        
        # Generate shop items based on player level
        from constants import generate_shop_items
        
        # Continue showing the shop until player exits
        while True:
            shop_items = generate_shop_items(player.class_level)
            
            # Create shop embed
            embed = discord.Embed(
                title="🛒 Item Shop",
                description=f"Your currency: **{player.currency}** 🌀",
                color=discord.Color.gold()
            )
            
            # Add each shop item
            for item in shop_items:
                # Determine if player can afford/use the item
                can_afford = player.currency >= item["price"]
                meets_level = player.class_level >= item.get("level_req", 1)
                
                # Format the item details
                item_name = item["name"]
                rarity_emoji = ITEM_RARITY.get(item.get("rarity", "common"), "⚪")
                
                # Format price with affordability indicator
                price_text = f"Price: {item['price']} 🌀 {'✅' if can_afford else '❌'}"
                
                # Create item description
                description = item.get("description", "")
                
                # Add level requirement if applicable
                level_text = f"Required Level: {item.get('level_req', 1)} {'✅' if meets_level else '❌'}"
                
                # Add stats for equipment
                stats_text = ""
                if item.get("type") == "equipment" and "stats_boost" in item:
                    stats_text = "\nStats: " + ", ".join([f"{stat.title()} +{val}" for stat, val in item["stats_boost"].items()])
                
                # Add effects for consumables
                effects_text = ""
                if item.get("type") == "consumable":
                    effects = []
                    if "heal" in item:
                        effects.append(f"Heal {item['heal']} HP")
                    if "energy" in item:
                        effects.append(f"Restore {item['energy']} CE")
                    if "effect" in item:
                        effects.append(f"{item['effect'].title()} effect")
                    
                    if effects:
                        effects_text = "\nEffects: " + " • ".join(effects)
                
                # Full item description
                full_description = f"{description}{stats_text}{effects_text}\n{level_text}\n{price_text}"
                
                embed.add_field(
                    name=f"{rarity_emoji} {item_name}",
                    value=full_description,
                    inline=True
                )
            
            # Add instructions
            embed.set_footer(text="Select an item to purchase, or refresh to see different items.")
            
            # Create the shop view
            view = ShopView(player, shop_items)
            message = await ctx.send(embed=embed, view=view)
            
            # Wait for selection
            await view.wait()
            
            if view.selected_item:
                if view.selected_item == "refresh":
                    # User wants to refresh the shop
                    await message.delete()
                    continue
                
                # User wants to buy an item
                item = view.selected_item
                
                # Verify player can still afford it
                if player.currency < item["price"]:
                    await message.edit(content="❌ You don't have enough currency to buy this item!", embed=None, view=None)
                    break
                
                # Verify level requirement
                if player.class_level < item.get("level_req", 1):
                    await message.edit(content="❌ You don't meet the level requirement for this item!", embed=None, view=None)
                    break
                
                # Purchase the item
                player.currency -= item["price"]
                player.add_to_inventory(item)
                
                # Create purchase confirmation
                purchase_embed = discord.Embed(
                    title="🛍️ Item Purchased!",
                    description=f"You bought **{item['name']}** for {item['price']} 🌀.",
                    color=discord.Color.green()
                )
                
                purchase_embed.add_field(
                    name="Item Details",
                    value=item.get("description", ""),
                    inline=False
                )
                
                purchase_embed.add_field(
                    name="Current Balance",
                    value=f"{player.currency} 🌀",
                    inline=False
                )
                
                # Add equip button if it's equipment
                if item.get("type") == "equipment":
                    purchase_embed.set_footer(text="Use !equip to equip your new item.")
                
                await message.edit(embed=purchase_embed, view=None)
                break
            else:
                # User closed the shop
                await message.edit(content="Shop closed. Come back soon!", embed=None, view=None)
                break
