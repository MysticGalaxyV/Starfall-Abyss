import discord
from discord.ui import Button, View, Select
import random
import asyncio
import datetime
from typing import Dict, List, Optional, Tuple, Any

from data_models import PlayerData, DataManager
from utils import GAME_CLASSES, ADVANCED_CLASSES, STARTER_CLASSES

class ClassChangeView(View):
    def __init__(self, player_data: PlayerData, data_manager: DataManager):
        super().__init__(timeout=60)
        self.player_data = player_data
        self.data_manager = data_manager
        
        # Create class selection dropdown
        self.class_select = Select(
            placeholder="Select a class to change to",
            min_values=1,
            max_values=1
        )
        
        # Get available classes for the player
        available_classes = self.get_available_classes()
        
        # Add options to dropdown
        for class_name, requirements in available_classes.items():
            # Skip current class
            if class_name == player_data.class_name:
                continue
                
            # Add option
            self.class_select.add_option(
                label=class_name,
                description=f"{GAME_CLASSES[class_name]['role']} - {requirements['status']}",
                value=class_name,
                emoji="✅" if requirements["available"] else "❌",
                default=False
            )
        
        # Set callback
        self.class_select.callback = self.class_select_callback
        
        # Add to view
        self.add_item(self.class_select)
        
        # Add cancel button
        cancel_btn = Button(
            label="Cancel",
            style=discord.ButtonStyle.red,
            emoji="❌"
        )
        cancel_btn.callback = self.cancel_callback
        self.add_item(cancel_btn)
    
    def get_available_classes(self) -> Dict[str, Dict[str, Any]]:
        """Get available classes for the player with requirements status"""
        result = {}
        
        # Add starter classes - always available if unlocked
        for class_name in STARTER_CLASSES.keys():
            if class_name in self.player_data.unlocked_classes:
                result[class_name] = {
                    "available": True,
                    "status": "Unlocked"
                }
            else:
                result[class_name] = {
                    "available": False,
                    "status": "Locked - Complete starter quest"
                }
        
        # Add advanced classes with requirements
        for class_name, class_data in ADVANCED_CLASSES.items():
            requirements = class_data.get("requirements", {})
            available = True
            status_parts = []
            
            # Check base class requirement
            base_class = requirements.get("base_class")
            if base_class and base_class not in self.player_data.unlocked_classes:
                available = False
                status_parts.append(f"Need {base_class} class")
            
            # Check level requirement
            level_req = requirements.get("level", 0)
            if self.player_data.class_level < level_req:
                available = False
                status_parts.append(f"Need level {level_req}")
            
            # Check dungeon clears requirement
            dungeon_req = requirements.get("dungeon_clears", 0)
            total_clears = sum(self.player_data.dungeon_clears.values())
            if total_clears < dungeon_req:
                available = False
                status_parts.append(f"Need {dungeon_req} dungeon clears")
            
            # Check if already unlocked
            if class_name in self.player_data.unlocked_classes:
                status = "Unlocked"
            else:
                if available:
                    status = "Available to unlock"
                else:
                    status = "Locked - " + ", ".join(status_parts)
            
            result[class_name] = {
                "available": class_name in self.player_data.unlocked_classes or available,
                "status": status
            }
        
        return result
    
    async def class_select_callback(self, interaction: discord.Interaction):
        """Handle class selection"""
        selected_class = self.class_select.values[0]
        available_classes = self.get_available_classes()
        
        if not available_classes[selected_class]["available"]:
            await interaction.response.send_message(
                f"❌ You can't change to {selected_class} yet. Requirements: {available_classes[selected_class]['status']}",
                ephemeral=True
            )
            return
        
        # Check if this is a new class to unlock
        if selected_class not in self.player_data.unlocked_classes:
            # Create confirmation view
            confirm_view = View(timeout=30)
            
            confirm_btn = Button(
                label=f"Unlock {selected_class}",
                style=discord.ButtonStyle.green,
                emoji="✅"
            )
            
            cancel_btn = Button(
                label="Cancel",
                style=discord.ButtonStyle.red,
                emoji="❌"
            )
            
            async def confirm_callback(confirm_interaction):
                # Unlock the class
                self.player_data.unlocked_classes.append(selected_class)
                
                # Change to the new class
                old_class = self.player_data.class_name
                self.player_data.class_name = selected_class
                
                # Save data
                self.data_manager.save_data()
                
                # Create result embed
                embed = discord.Embed(
                    title="🔄 Class Changed!",
                    description=f"You have unlocked and changed to the **{selected_class}** class!",
                    color=discord.Color.green()
                )
                
                # Add class info
                class_data = GAME_CLASSES[selected_class]
                stats_text = "\n".join([f"{stat.title()}: {value}" for stat, value in class_data["stats"].items()])
                
                embed.add_field(
                    name=f"{selected_class} ({class_data['role']})",
                    value=f"**Active Ability:** {class_data['abilities']['active']}\n"
                          f"**Passive Ability:** {class_data['abilities']['passive']}\n"
                          f"**Stats:**\n{stats_text}",
                    inline=False
                )
                
                embed.add_field(
                    name="Note",
                    value="Your level and experience have been preserved.\n"
                          "Use the `!skills` command to allocate your skill points with your new class!",
                    inline=False
                )
                
                await confirm_interaction.response.edit_message(
                    content=None,
                    embed=embed,
                    view=None
                )
                
                # Stop the original view
                self.stop()
            
            async def cancel_callback(cancel_interaction):
                await cancel_interaction.response.edit_message(
                    content="❌ Class change cancelled.",
                    embed=None,
                    view=None
                )
                
                # Stop both views
                confirm_view.stop()
                self.stop()
            
            # Set callbacks
            confirm_btn.callback = confirm_callback
            cancel_btn.callback = cancel_callback
            
            # Add buttons to view
            confirm_view.add_item(confirm_btn)
            confirm_view.add_item(cancel_btn)
            
            # Show confirmation
            await interaction.response.send_message(
                f"⚠️ You're about to unlock the **{selected_class}** class for the first time. This will change your current class from **{self.player_data.class_name}** to **{selected_class}**.\n\n"
                f"Are you sure you want to proceed?",
                view=confirm_view
            )
            
        else:
            # Already unlocked, just change class
            # Create confirmation view
            confirm_view = View(timeout=30)
            
            confirm_btn = Button(
                label=f"Change to {selected_class}",
                style=discord.ButtonStyle.green,
                emoji="✅"
            )
            
            cancel_btn = Button(
                label="Cancel",
                style=discord.ButtonStyle.red,
                emoji="❌"
            )
            
            async def confirm_callback(confirm_interaction):
                # Change to the new class
                old_class = self.player_data.class_name
                self.player_data.class_name = selected_class
                
                # Save data
                self.data_manager.save_data()
                
                # Create result embed
                embed = discord.Embed(
                    title="🔄 Class Changed!",
                    description=f"You have changed from **{old_class}** to **{selected_class}**!",
                    color=discord.Color.green()
                )
                
                # Add class info
                class_data = GAME_CLASSES[selected_class]
                stats_text = "\n".join([f"{stat.title()}: {value}" for stat, value in class_data["stats"].items()])
                
                embed.add_field(
                    name=f"{selected_class} ({class_data['role']})",
                    value=f"**Active Ability:** {class_data['abilities']['active']}\n"
                          f"**Passive Ability:** {class_data['abilities']['passive']}\n"
                          f"**Stats:**\n{stats_text}",
                    inline=False
                )
                
                embed.add_field(
                    name="Note",
                    value="Your level and experience have been preserved.\n"
                          "Use the `!skills` command to allocate your skill points with your new class!",
                    inline=False
                )
                
                await confirm_interaction.response.edit_message(
                    content=None,
                    embed=embed,
                    view=None
                )
                
                # Stop the original view
                self.stop()
                
            async def cancel_callback(cancel_interaction):
                await cancel_interaction.response.edit_message(
                    content="❌ Class change cancelled.",
                    embed=None,
                    view=None
                )
                
                # Stop both views
                confirm_view.stop()
                self.stop()
            
            # Set callbacks
            confirm_btn.callback = confirm_callback
            cancel_btn.callback = cancel_callback
            
            # Add buttons to view
            confirm_view.add_item(confirm_btn)
            confirm_view.add_item(cancel_btn)
            
            # Show confirmation
            await interaction.response.send_message(
                f"⚠️ You're about to change your class from **{self.player_data.class_name}** to **{selected_class}**.\n\n"
                f"Your level and experience will be preserved, but you may want to reallocate your skill points for the new class.\n\n"
                f"Are you sure you want to proceed?",
                view=confirm_view
            )
    
    async def cancel_callback(self, interaction: discord.Interaction):
        """Handle cancellation"""
        await interaction.response.send_message("❌ Class change cancelled.", ephemeral=True)
        self.stop()

async def class_change_command(ctx, data_manager: DataManager):
    """Change your character's class to another unlocked class"""
    player_data = data_manager.get_player(ctx.author.id)
    
    # Check if player has started
    if not player_data.class_name:
        await ctx.send("❌ You haven't started your adventure yet! Use `!start` to choose a class.")
        return
    
    # Create embed for class change
    embed = discord.Embed(
        title="🔄 Class Change",
        description="Change your character's class to another available class.\n"
                   "Your level and experience will be preserved, but you may want to reallocate your skill points for the new class.",
        color=discord.Color.blue()
    )
    
    # Add current class info
    class_data = GAME_CLASSES[player_data.class_name]
    embed.add_field(
        name=f"Current Class: {player_data.class_name} ({class_data['role']})",
        value=f"**Level:** {player_data.class_level}\n"
              f"**EXP:** {player_data.class_exp}/{int(100 * (player_data.class_level ** 1.5))}\n"
              f"**Active Ability:** {class_data['abilities']['active']}\n"
              f"**Passive Ability:** {class_data['abilities']['passive']}",
        inline=False
    )
    
    # Add unlocked classes info
    unlocked = "\n".join([f"• {cls}" for cls in player_data.unlocked_classes]) if player_data.unlocked_classes else "None"
    embed.add_field(
        name="Unlocked Classes",
        value=unlocked,
        inline=False
    )
    
    # Create view for class change
    view = ClassChangeView(player_data, data_manager)
    
    # Send message with embed and view
    message = await ctx.send(embed=embed, view=view)
    
    # Wait for selection
    await view.wait()