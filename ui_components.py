import discord
from discord.ui import View, Button, Select
import asyncio
from typing import Dict, List, Optional, Union, Callable

class HelpView(View):
    """Interactive view for help command with page navigation"""
    def __init__(self, help_embeds: List[discord.Embed], timeout: int = 60):
        super().__init__(timeout=timeout)
        self.help_embeds = help_embeds
        self.current_page = 0
        
        # Add navigation buttons
        prev_btn = Button(label="◀️ Previous", style=discord.ButtonStyle.secondary, custom_id="prev")
        prev_btn.callback = self.prev_callback
        self.add_item(prev_btn)
        
        next_btn = Button(label="Next ▶️", style=discord.ButtonStyle.secondary, custom_id="next")
        next_btn.callback = self.next_callback
        self.add_item(next_btn)
    
    async def prev_callback(self, interaction: discord.Interaction):
        """Handle previous page button"""
        self.current_page = (self.current_page - 1) % len(self.help_embeds)
        await interaction.response.edit_message(embed=self.help_embeds[self.current_page])
    
    async def next_callback(self, interaction: discord.Interaction):
        """Handle next page button"""
        self.current_page = (self.current_page + 1) % len(self.help_embeds)
        await interaction.response.edit_message(embed=self.help_embeds[self.current_page])

class ConfirmView(View):
    """View for confirmation dialogs with Yes/No buttons"""
    def __init__(self, target_user: discord.User, timeout: int = 30):
        super().__init__(timeout=timeout)
        self.target_user = target_user
        self.value = None
        
        # Add Yes button
        yes_btn = Button(label="Yes", style=discord.ButtonStyle.success, custom_id="yes", emoji="✅")
        yes_btn.callback = self.yes_callback
        self.add_item(yes_btn)
        
        # Add No button
        no_btn = Button(label="No", style=discord.ButtonStyle.danger, custom_id="no", emoji="❌")
        no_btn.callback = self.no_callback
        self.add_item(no_btn)
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Only allow the target user to interact with this view"""
        return interaction.user.id == self.target_user.id
    
    async def yes_callback(self, interaction: discord.Interaction):
        """Handle Yes button click"""
        self.value = True
        self.stop()
        await interaction.response.defer()
    
    async def no_callback(self, interaction: discord.Interaction):
        """Handle No button click"""
        self.value = False
        self.stop()
        await interaction.response.defer()

class PaginatedView(View):
    """Generic paginated view for any content"""
    def __init__(self, pages: List[Union[discord.Embed, str]], user: discord.User, timeout: int = 60):
        super().__init__(timeout=timeout)
        self.pages = pages
        self.current_page = 0
        self.user = user
        
        # Add navigation buttons
        prev_btn = Button(label="◀️", style=discord.ButtonStyle.secondary, custom_id="prev")
        prev_btn.callback = self.prev_callback
        self.add_item(prev_btn)
        
        page_btn = Button(
            label=f"Page {self.current_page + 1}/{len(pages)}", 
            style=discord.ButtonStyle.primary, 
            custom_id="page", 
            disabled=True
        )
        self.page_btn = page_btn
        self.add_item(page_btn)
        
        next_btn = Button(label="▶️", style=discord.ButtonStyle.secondary, custom_id="next")
        next_btn.callback = self.next_callback
        self.add_item(next_btn)
        
        # Add close button
        close_btn = Button(label="Close", style=discord.ButtonStyle.danger, custom_id="close", emoji="✖️")
        close_btn.callback = self.close_callback
        self.add_item(close_btn)
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Only allow the target user to interact with this view"""
        return interaction.user.id == self.user.id
    
    async def prev_callback(self, interaction: discord.Interaction):
        """Handle previous page button"""
        self.current_page = (self.current_page - 1) % len(self.pages)
        self.update_page_button()
        
        page = self.pages[self.current_page]
        if isinstance(page, discord.Embed):
            await interaction.response.edit_message(embed=page, view=self)
        else:
            await interaction.response.edit_message(content=page, view=self)
    
    async def next_callback(self, interaction: discord.Interaction):
        """Handle next page button"""
        self.current_page = (self.current_page + 1) % len(self.pages)
        self.update_page_button()
        
        page = self.pages[self.current_page]
        if isinstance(page, discord.Embed):
            await interaction.response.edit_message(embed=page, view=self)
        else:
            await interaction.response.edit_message(content=page, view=self)
    
    async def close_callback(self, interaction: discord.Interaction):
        """Handle close button"""
        await interaction.message.delete()
        self.stop()
    
    def update_page_button(self):
        """Update the page indicator button"""
        self.page_btn.label = f"Page {self.current_page + 1}/{len(self.pages)}"

class SelectOptionView(View):
    """View for selecting options from a dropdown menu"""
    def __init__(self, options: List[Dict], placeholder: str, callback: Callable, timeout: int = 60):
        super().__init__(timeout=timeout)
        
        # Create select menu with options
        select_options = []
        for option in options:
            select_options.append(discord.SelectOption(
                label=option["label"],
                value=option["value"],
                description=option.get("description", ""),
                emoji=option.get("emoji", None)
            ))
        
        # Add select menu
        select = Select(
            placeholder=placeholder,
            options=select_options[:25],  # Discord limits to 25 options
            custom_id="option_select"
        )
        select.callback = callback
        self.add_item(select)
        
        # Add cancel button
        cancel_btn = Button(label="Cancel", style=discord.ButtonStyle.secondary, custom_id="cancel", emoji="❌")
        cancel_btn.callback = self.cancel_callback
        self.add_item(cancel_btn)
    
    async def cancel_callback(self, interaction: discord.Interaction):
        """Handle cancel button"""
        await interaction.response.defer()
        self.stop()

class ItemDetailsView(View):
    """View for displaying item details with action buttons"""
    def __init__(self, item: Dict, player, timeout: int = 60):
        super().__init__(timeout=timeout)
        self.item = item
        self.player = player
        self.action = None
        
        # Add buttons based on item type
        if item.get("type") == "equipment":
            # Add equip button
            equip_btn = Button(label="Equip", style=discord.ButtonStyle.primary, custom_id="equip", emoji="👕")
            equip_btn.callback = self.equip_callback
            self.add_item(equip_btn)
        elif item.get("type") == "consumable":
            # Add use button
            use_btn = Button(label="Use", style=discord.ButtonStyle.success, custom_id="use", emoji="🧪")
            use_btn.callback = self.use_callback
            self.add_item(use_btn)
        
        # Add close button
        close_btn = Button(label="Close", style=discord.ButtonStyle.secondary, custom_id="close", emoji="❌")
        close_btn.callback = self.close_callback
        self.add_item(close_btn)
    
    async def equip_callback(self, interaction: discord.Interaction):
        """Handle equip button"""
        self.action = "equip"
        await interaction.response.defer()
        self.stop()
    
    async def use_callback(self, interaction: discord.Interaction):
        """Handle use button"""
        self.action = "use"
        await interaction.response.defer()
        self.stop()
    
    async def close_callback(self, interaction: discord.Interaction):
        """Handle close button"""
        await interaction.response.defer()
        self.stop()

class CountdownView(View):
    """View with a countdown timer that updates automatically"""
    def __init__(self, user: discord.User, seconds: int, message: str = "Countdown:", timeout: int = 300):
        super().__init__(timeout=timeout)
        self.seconds = seconds
        self.message = message
        self.user = user
        self.counter = None
        self.cancelled = False
        
        # Add a disabled button that shows the time
        self.time_btn = Button(
            label=f"{seconds}s", 
            style=discord.ButtonStyle.primary, 
            custom_id="time", 
            disabled=True
        )
        self.add_item(self.time_btn)
        
        # Add cancel button
        cancel_btn = Button(label="Cancel", style=discord.ButtonStyle.danger, custom_id="cancel", emoji="❌")
        cancel_btn.callback = self.cancel_callback
        self.add_item(cancel_btn)
    
    async def start(self, ctx):
        """Start the countdown and update the message"""
        message = await ctx.send(f"{self.message} {self.seconds}s", view=self)
        
        # Create a task to update the countdown
        self.counter = asyncio.create_task(self.update_countdown(message))
        
        # Wait for view to finish
        await self.wait()
        
        if not self.counter.done():
            self.counter.cancel()
            
        return self.cancelled
    
    async def update_countdown(self, message):
        """Update the countdown timer"""
        try:
            while self.seconds > 0 and not self.cancelled:
                await asyncio.sleep(1)
                self.seconds -= 1
                self.time_btn.label = f"{self.seconds}s"
                await message.edit(content=f"{self.message} {self.seconds}s", view=self)
                
            if not self.cancelled:
                # Time ran out
                self.stop()
                await message.edit(content=f"{self.message} Completed!", view=None)
        except asyncio.CancelledError:
            # Task was cancelled
            pass
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Only allow the target user to interact with this view"""
        return interaction.user.id == self.user.id
    
    async def cancel_callback(self, interaction: discord.Interaction):
        """Handle cancel button"""
        self.cancelled = True
        await interaction.response.edit_message(content=f"{self.message} Cancelled!", view=None)
        self.stop()

class BattleWagerView(View):
    """View for setting up battle wagers"""
    def __init__(self, challenger: discord.User, opponent: discord.User, timeout: int = 60):
        super().__init__(timeout=timeout)
        self.challenger = challenger
        self.opponent = opponent
        self.wager_amount = 0
        self.challenger_confirmed = False
        self.opponent_confirmed = False
        
        # Add wager amount buttons
        for amount in [0, 10, 50, 100, 500]:
            btn = Button(
                label=f"{amount} 🌀",
                style=discord.ButtonStyle.primary if amount == 0 else discord.ButtonStyle.secondary,
                custom_id=f"wager_{amount}"
            )
            btn.callback = self.wager_callback
            self.add_item(btn)
        
        # Add confirm buttons
        self.challenger_btn = Button(
            label="Challenger: Waiting...",
            style=discord.ButtonStyle.danger,
            custom_id="confirm_challenger",
            emoji="⏳"
        )
        self.challenger_btn.callback = self.challenger_callback
        self.add_item(self.challenger_btn)
        
        self.opponent_btn = Button(
            label="Opponent: Waiting...",
            style=discord.ButtonStyle.danger,
            custom_id="confirm_opponent",
            emoji="⏳"
        )
        self.opponent_btn.callback = self.opponent_callback
        self.add_item(self.opponent_btn)
    
    async def wager_callback(self, interaction: discord.Interaction):
        """Handle wager amount button clicks"""
        # Check if user is either challenger or opponent
        if interaction.user.id not in [self.challenger.id, self.opponent.id]:
            await interaction.response.send_message("You're not part of this battle!", ephemeral=True)
            return
        
        # Reset confirmations when wager changes
        self.challenger_confirmed = False
        self.opponent_confirmed = False
        
        # Update wager amount
        amount = int(interaction.data["custom_id"].split("_")[1])
        self.wager_amount = amount
        
        # Update buttons
        self.challenger_btn.label = "Challenger: Waiting..."
        self.challenger_btn.style = discord.ButtonStyle.danger
        self.challenger_btn.emoji = "⏳"
        
        self.opponent_btn.label = "Opponent: Waiting..."
        self.opponent_btn.style = discord.ButtonStyle.danger
        self.opponent_btn.emoji = "⏳"
        
        # Update the message
        embed = discord.Embed(
            title="⚔️ Battle Wager",
            description=(
                f"Set a wager for this battle!\n\n"
                f"Current wager: **{self.wager_amount}** 🌀\n\n"
                f"Both players must confirm to start the battle."
            ),
            color=discord.Color.gold()
        )
        
        await interaction.response.edit_message(embed=embed, view=self)
    
    async def challenger_callback(self, interaction: discord.Interaction):
        """Handle challenger confirm button"""
        if interaction.user.id != self.challenger.id:
            await interaction.response.send_message("Only the challenger can use this button!", ephemeral=True)
            return
        
        # Toggle confirmation
        self.challenger_confirmed = not self.challenger_confirmed
        
        # Update button
        if self.challenger_confirmed:
            self.challenger_btn.label = "Challenger: Confirmed"
            self.challenger_btn.style = discord.ButtonStyle.success
            self.challenger_btn.emoji = "✅"
        else:
            self.challenger_btn.label = "Challenger: Waiting..."
            self.challenger_btn.style = discord.ButtonStyle.danger
            self.challenger_btn.emoji = "⏳"
        
        # Check if both confirmed
        if self.challenger_confirmed and self.opponent_confirmed:
            self.stop()
        
        await interaction.response.edit_message(view=self)
    
    async def opponent_callback(self, interaction: discord.Interaction):
        """Handle opponent confirm button"""
        if interaction.user.id != self.opponent.id:
            await interaction.response.send_message("Only the opponent can use this button!", ephemeral=True)
            return
        
        # Toggle confirmation
        self.opponent_confirmed = not self.opponent_confirmed
        
        # Update button
        if self.opponent_confirmed:
            self.opponent_btn.label = "Opponent: Confirmed"
            self.opponent_btn.style = discord.ButtonStyle.success
            self.opponent_btn.emoji = "✅"
        else:
            self.opponent_btn.label = "Opponent: Waiting..."
            self.opponent_btn.style = discord.ButtonStyle.danger
            self.opponent_btn.emoji = "⏳"
        
        # Check if both confirmed
        if self.challenger_confirmed and self.opponent_confirmed:
            self.stop()
        
        await interaction.response.edit_message(view=self)
