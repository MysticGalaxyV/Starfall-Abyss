import discord
from discord.ext import commands
from discord.ui import Button, View, Select
import json
import random
import asyncio
from typing import Dict, List, Any, Optional, Union, Tuple

from data_models import DataManager, PlayerData, Item, InventoryItem

class TradeOffer:
    def __init__(self, 
                 sender_id: int, 
                 receiver_id: int, 
                 offered_items: List[str] = None, 
                 offered_gold: int = 0,
                 requested_items: List[str] = None,
                 requested_gold: int = 0):
        self.sender_id = sender_id
        self.receiver_id = receiver_id
        self.offered_items = offered_items or []  # List of item IDs
        self.offered_gold = offered_gold
        self.requested_items = requested_items or []  # List of item IDs
        self.requested_gold = requested_gold
        self.status = "pending"  # pending, accepted, declined, cancelled
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            "sender_id": self.sender_id,
            "receiver_id": self.receiver_id,
            "offered_items": self.offered_items,
            "offered_gold": self.offered_gold,
            "requested_items": self.requested_items,
            "requested_gold": self.requested_gold,
            "status": self.status
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TradeOffer':
        trade = cls(
            sender_id=data["sender_id"],
            receiver_id=data["receiver_id"],
            offered_items=data.get("offered_items", []),
            offered_gold=data.get("offered_gold", 0),
            requested_items=data.get("requested_items", []),
            requested_gold=data.get("requested_gold", 0)
        )
        trade.status = data.get("status", "pending")
        return trade

class TradeManager:
    def __init__(self, data_manager: DataManager):
        self.data_manager = data_manager
        self.active_trades = {}  # Dict[str, TradeOffer]
        
    def create_trade(self, sender_id: int, receiver_id: int) -> str:
        """Create a new trade and return its ID"""
        trade = TradeOffer(sender_id, receiver_id)
        trade_id = f"{sender_id}_{receiver_id}_{random.randint(1000, 9999)}"
        self.active_trades[trade_id] = trade
        return trade_id
        
    def get_trade(self, trade_id: str) -> Optional[TradeOffer]:
        """Get a trade by its ID"""
        return self.active_trades.get(trade_id)
        
    def cancel_trade(self, trade_id: str) -> bool:
        """Cancel a trade. Returns True if successful"""
        if trade_id in self.active_trades:
            trade = self.active_trades[trade_id]
            trade.status = "cancelled"
            del self.active_trades[trade_id]
            return True
        return False
        
    def complete_trade(self, trade_id: str) -> bool:
        """Execute the trade, transferring items and gold between players"""
        if trade_id not in self.active_trades:
            return False
            
        trade = self.active_trades[trade_id]
        if trade.status != "accepted":
            return False
            
        sender = self.data_manager.get_player(trade.sender_id)
        receiver = self.data_manager.get_player(trade.receiver_id)
        
        # Create maps of item_id -> InventoryItem for faster lookup
        sender_items = {item.item.item_id: item for item in sender.inventory}
        receiver_items = {item.item.item_id: item for item in receiver.inventory}
        
        # Verify sender has the offered items
        for item_id in trade.offered_items:
            if item_id not in sender_items or sender_items[item_id].equipped:
                return False
                
        # Verify receiver has the requested items
        for item_id in trade.requested_items:
            if item_id not in receiver_items or receiver_items[item_id].equipped:
                return False
                
        # Verify gold amounts
        if sender.gold < trade.offered_gold or receiver.gold < trade.requested_gold:
            return False
            
        # All verifications passed, execute the trade
        
        # Transfer items from sender to receiver
        for item_id in trade.offered_items:
            item = sender_items[item_id]
            sender.inventory.remove(item)
            receiver.inventory.append(item)
            
        # Transfer items from receiver to sender
        for item_id in trade.requested_items:
            item = receiver_items[item_id]
            receiver.inventory.remove(item)
            sender.inventory.append(item)
            
        # Transfer gold
        sender.gold -= trade.offered_gold
        receiver.gold += trade.offered_gold
        
        receiver.gold -= trade.requested_gold
        sender.gold += trade.requested_gold
        
        # Save data
        self.data_manager.save_data()
        
        # Remove trade from active trades
        del self.active_trades[trade_id]
        
        return True
        
    def get_player_trades(self, player_id: int) -> List[Tuple[str, TradeOffer]]:
        """Get all active trades involving a player"""
        trades = []
        for trade_id, trade in self.active_trades.items():
            if trade.sender_id == player_id or trade.receiver_id == player_id:
                trades.append((trade_id, trade))
        return trades

# Item selection view for trade creation
class ItemSelectView(View):
    def __init__(self, player_data: PlayerData, is_offering: bool = True):
        super().__init__(timeout=180)  # 3 minute timeout
        self.player_data = player_data
        self.is_offering = is_offering
        self.selected_items = []
        self.gold_amount = 0
        
        # Add item selection dropdown
        self.add_item_select()
        
        # Add gold input button
        self.add_gold_button()
        
        # Add control buttons
        self.add_control_buttons()
        
    def add_item_select(self):
        """Add dropdown for item selection"""
        # Only show non-equipped items
        available_items = [item for item in self.player_data.inventory if not item.equipped]
        
        # No items available
        if not available_items:
            return
            
        # Create options for dropdown
        options = []
        for item in available_items:
            already_selected = item.item.item_id in self.selected_items
            option = discord.SelectOption(
                label=f"{item.item.name} (x{item.quantity})",
                description=f"{item.item.description[:50]}...",
                value=item.item.item_id,
                default=already_selected
            )
            options.append(option)
            
        # Create the select menu with up to 25 options (Discord limit)
        select = Select(
            placeholder="Select items to add to the trade",
            options=options[:25],
            max_values=min(len(options), 25)
        )
        
        select.callback = self.item_select_callback
        self.add_item(select)
        
    async def item_select_callback(self, interaction: discord.Interaction):
        """Handle item selection"""
        values = interaction.data.get("values", [])
        self.selected_items = values
        
        # Update the view
        self.clear_items()
        self.add_item_select()
        self.add_gold_button()
        self.add_control_buttons()
        
        action_type = "offering" if self.is_offering else "requesting"
        await interaction.response.edit_message(
            content=f"Currently {action_type}: {len(self.selected_items)} items and {self.gold_amount} gold",
            view=self
        )
        
    def add_gold_button(self):
        """Add button for gold input"""
        gold_button = Button(
            style=discord.ButtonStyle.primary,
            label=f"Set Gold: {self.gold_amount}",
            custom_id="set_gold"
        )
        gold_button.callback = self.gold_button_callback
        self.add_item(gold_button)
        
    async def gold_button_callback(self, interaction: discord.Interaction):
        """Handle gold button click"""
        # Create a modal for gold input
        class GoldInputModal(discord.ui.Modal, title="Enter Gold Amount"):
            gold_input = discord.ui.TextInput(
                label="Gold Amount",
                placeholder="Enter amount of gold",
                default=str(self.gold_amount),
                required=True
            )
            
            async def on_submit(self, modal_interaction: discord.Interaction):
                try:
                    gold_amount = int(self.gold_input.value)
                    
                    # Validate gold amount
                    if gold_amount < 0:
                        await modal_interaction.response.send_message("Gold amount cannot be negative.", ephemeral=True)
                        return
                        
                    if gold_amount > self.parent.player_data.gold and self.parent.is_offering:
                        await modal_interaction.response.send_message(
                            f"You don't have enough gold. You have {self.parent.player_data.gold} gold.", 
                            ephemeral=True
                        )
                        return
                        
                    self.parent.gold_amount = gold_amount
                    
                    # Update the view
                    self.parent.clear_items()
                    self.parent.add_item_select()
                    self.parent.add_gold_button()
                    self.parent.add_control_buttons()
                    
                    action_type = "offering" if self.parent.is_offering else "requesting"
                    await modal_interaction.response.edit_message(
                        content=f"Currently {action_type}: {len(self.parent.selected_items)} items and {self.parent.gold_amount} gold",
                        view=self.parent
                    )
                except ValueError:
                    await modal_interaction.response.send_message("Please enter a valid number.", ephemeral=True)
        
        # Give modal access to view
        modal = GoldInputModal()
        modal.parent = self
        
        # Show the modal
        await interaction.response.send_modal(modal)
        
    def add_control_buttons(self):
        """Add confirm and cancel buttons"""
        confirm_button = Button(
            style=discord.ButtonStyle.success,
            label="Confirm Selection",
            custom_id="confirm"
        )
        confirm_button.callback = self.confirm_callback
        self.add_item(confirm_button)
        
        cancel_button = Button(
            style=discord.ButtonStyle.danger,
            label="Cancel",
            custom_id="cancel"
        )
        cancel_button.callback = self.cancel_callback
        self.add_item(cancel_button)
        
    async def confirm_callback(self, interaction: discord.Interaction):
        """Handle confirm button click"""
        self.stop()
        await interaction.response.defer()
        
    async def cancel_callback(self, interaction: discord.Interaction):
        """Handle cancel button click"""
        self.selected_items = []
        self.gold_amount = 0
        self.stop()
        await interaction.response.defer()

class TradeView(View):
    def __init__(self, trade_manager: TradeManager, trade_id: str):
        super().__init__(timeout=300)  # 5 minute timeout
        self.trade_manager = trade_manager
        self.trade_id = trade_id
        self.trade = trade_manager.get_trade(trade_id)
        
        # Add accept/decline buttons
        self.add_action_buttons()
        
    def add_action_buttons(self):
        """Add accept, decline, and cancel buttons"""
        accept_button = Button(
            style=discord.ButtonStyle.success,
            label="Accept Trade",
            custom_id="accept"
        )
        accept_button.callback = self.accept_callback
        self.add_item(accept_button)
        
        decline_button = Button(
            style=discord.ButtonStyle.danger,
            label="Decline Trade",
            custom_id="decline"
        )
        decline_button.callback = self.decline_callback
        self.add_item(decline_button)
        
        cancel_button = Button(
            style=discord.ButtonStyle.secondary,
            label="Cancel Trade",
            custom_id="cancel"
        )
        cancel_button.callback = self.cancel_callback
        self.add_item(cancel_button)
        
    async def accept_callback(self, interaction: discord.Interaction):
        """Handle trade acceptance"""
        # Only the receiver can accept
        if interaction.user.id != self.trade.receiver_id:
            await interaction.response.send_message(
                "Only the trade recipient can accept the trade.",
                ephemeral=True
            )
            return
            
        # Mark trade as accepted
        self.trade.status = "accepted"
        
        # Execute the trade
        success = self.trade_manager.complete_trade(self.trade_id)
        
        if success:
            # Inform both users
            sender = self.trade_manager.data_manager.get_player(self.trade.sender_id)
            receiver = self.trade_manager.data_manager.get_player(self.trade.receiver_id)
            
            # Create detailed message of what was traded
            offered_items_text = "No items" if not self.trade.offered_items else ", ".join(
                [get_item_name_by_id(item_id, self.trade_manager.data_manager) for item_id in self.trade.offered_items]
            )
            
            requested_items_text = "No items" if not self.trade.requested_items else ", ".join(
                [get_item_name_by_id(item_id, self.trade_manager.data_manager) for item_id in self.trade.requested_items]
            )
            
            embed = discord.Embed(
                title="Trade Completed!",
                description="The trade has been successfully completed.",
                color=discord.Color.green()
            )
            
            embed.add_field(
                name=f"{interaction.client.get_user(self.trade.sender_id)} sent:",
                value=f"{offered_items_text}\n{self.trade.offered_gold} gold",
                inline=True
            )
            
            embed.add_field(
                name=f"{interaction.client.get_user(self.trade.receiver_id)} sent:",
                value=f"{requested_items_text}\n{self.trade.requested_gold} gold",
                inline=True
            )
            
            await interaction.response.edit_message(embed=embed, view=None)
        else:
            await interaction.response.send_message(
                "There was an error completing the trade. Make sure all items are still available and not equipped, and that both players have enough gold.",
                ephemeral=True
            )
            
    async def decline_callback(self, interaction: discord.Interaction):
        """Handle trade decline"""
        # Only the receiver can decline
        if interaction.user.id != self.trade.receiver_id:
            await interaction.response.send_message(
                "Only the trade recipient can decline the trade.",
                ephemeral=True
            )
            return
            
        # Mark trade as declined and remove from active trades
        self.trade.status = "declined"
        self.trade_manager.cancel_trade(self.trade_id)
        
        # Create decline message
        embed = discord.Embed(
            title="Trade Declined",
            description=f"{interaction.user.name} has declined the trade.",
            color=discord.Color.red()
        )
        
        await interaction.response.edit_message(embed=embed, view=None)
        
    async def cancel_callback(self, interaction: discord.Interaction):
        """Handle trade cancellation"""
        # Only the sender can cancel
        if interaction.user.id != self.trade.sender_id:
            await interaction.response.send_message(
                "Only the trade creator can cancel the trade.",
                ephemeral=True
            )
            return
            
        # Mark trade as cancelled and remove from active trades
        self.trade.status = "cancelled"
        self.trade_manager.cancel_trade(self.trade_id)
        
        # Create cancellation message
        embed = discord.Embed(
            title="Trade Cancelled",
            description=f"{interaction.user.name} has cancelled the trade.",
            color=discord.Color.orange()
        )
        
        await interaction.response.edit_message(embed=embed, view=None)
        
    def create_trade_embed(self) -> discord.Embed:
        """Create an embed displaying the trade details"""
        sender = self.trade_manager.data_manager.get_player(self.trade.sender_id)
        receiver = self.trade_manager.data_manager.get_player(self.trade.receiver_id)
        
        # Get item names
        offered_items = [
            get_item_by_id(item_id, self.trade_manager.data_manager) 
            for item_id in self.trade.offered_items
        ]
        requested_items = [
            get_item_by_id(item_id, self.trade_manager.data_manager)
            for item_id in self.trade.requested_items
        ]
        
        # Create embed
        embed = discord.Embed(
            title="Trade Offer",
            description="Review the trade offer below.",
            color=discord.Color.blue()
        )
        
        # Add sender's offer
        sender_name = f"<@{self.trade.sender_id}>"
        offered_items_text = "No items" if not offered_items else "\n".join(
            [f"• {item.name} - {item.description}" for item in offered_items if item]
        )
        
        embed.add_field(
            name=f"{sender_name} is offering:",
            value=f"{offered_items_text}\n{self.trade.offered_gold} gold",
            inline=False
        )
        
        # Add what sender is requesting
        requested_items_text = "No items" if not requested_items else "\n".join(
            [f"• {item.name} - {item.description}" for item in requested_items if item]
        )
        
        embed.add_field(
            name=f"{sender_name} is requesting:",
            value=f"{requested_items_text}\n{self.trade.requested_gold} gold",
            inline=False
        )
        
        # Add instructions
        receiver_name = f"<@{self.trade.receiver_id}>"
        embed.add_field(
            name="Instructions",
            value=f"{receiver_name} can Accept or Decline this trade.\n{sender_name} can Cancel this trade.",
            inline=False
        )
        
        return embed

# Helper functions
def get_item_by_id(item_id: str, data_manager: DataManager) -> Optional[Item]:
    """Find an item by its ID across all player inventories"""
    for player_id, player in data_manager.players.items():
        for inv_item in player.inventory:
            if inv_item.item.item_id == item_id:
                return inv_item.item
    return None

def get_item_name_by_id(item_id: str, data_manager: DataManager) -> str:
    """Get item name by ID, returning 'Unknown Item' if not found"""
    item = get_item_by_id(item_id, data_manager)
    return item.name if item else "Unknown Item"

# Command function
async def trade_command(ctx, target_member: discord.Member, data_manager: DataManager):
    """Start a trade with another player"""
    # Check if both users exist in the database
    sender = data_manager.get_player(ctx.author.id)
    
    if not sender.class_name:
        await ctx.send("You need to start your adventure before you can trade! Use the `!start` command.")
        return
    
    # Initialize receiver
    receiver = data_manager.get_player(target_member.id)
    
    if not receiver.class_name:
        await ctx.send(f"{target_member.mention} hasn't started their adventure yet!")
        return
        
    # Check if trading with self
    if ctx.author.id == target_member.id:
        await ctx.send("You can't trade with yourself!")
        return
        
    # Create trade manager if it doesn't exist
    if not hasattr(data_manager, 'trade_manager'):
        data_manager.trade_manager = TradeManager(data_manager)
        
    # Start trade process
    await ctx.send(f"{ctx.author.mention} is initiating a trade with {target_member.mention}...")
    
    # First, select what the sender wants to offer
    offer_message = await ctx.send("Select the items you want to offer:")
    offer_view = ItemSelectView(sender, is_offering=True)
    await offer_message.edit(view=offer_view)
    
    # Wait for sender to select offered items
    await offer_view.wait()
    
    if not offer_view.selected_items and offer_view.gold_amount == 0:
        await ctx.send("Trade cancelled: You didn't offer any items or gold.")
        return
        
    # Now, select what the sender wants in return
    request_message = await ctx.send("Select the items you want in return:")
    request_view = ItemSelectView(sender, is_offering=False)
    await request_message.edit(view=request_view)
    
    # Wait for sender to select requested items
    await request_view.wait()
    
    # Create the trade
    trade_id = data_manager.trade_manager.create_trade(ctx.author.id, target_member.id)
    trade = data_manager.trade_manager.get_trade(trade_id)
    
    # Set trade details
    trade.offered_items = offer_view.selected_items
    trade.offered_gold = offer_view.gold_amount
    trade.requested_items = request_view.selected_items
    trade.requested_gold = request_view.gold_amount
    
    # Send trade offer to receiver
    trade_view = TradeView(data_manager.trade_manager, trade_id)
    embed = trade_view.create_trade_embed()
    
    await ctx.send(f"{target_member.mention}, you've received a trade offer!", embed=embed, view=trade_view)

# Slash command version
async def slash_trade(interaction: discord.Interaction, target_member: discord.Member, data_manager: DataManager):
    """Start a trade with another player"""
    ctx = await interaction.client.get_context(interaction)
    await trade_command(ctx, target_member, data_manager)

# Command aliases
async def t_command(ctx, target_member: discord.Member, data_manager: DataManager):
    """Alias for trade command"""
    await trade_command(ctx, target_member, data_manager)