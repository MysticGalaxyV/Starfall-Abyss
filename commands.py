import discord
from discord.ext import commands
import asyncio
import datetime
import random
from typing import Dict, List, Optional, Union

from data_manager import DataManager
from battle_system import Battle, handle_battle_rewards
from dungeon_system import DungeonInstance, DungeonSelectView
from player_system import PlayerSystem
from equipment_system import EquipmentSystem
from constants import STARTER_CLASSES, CLASSES, DUNGEONS, SHOP_ITEMS, BATTLE_COOLDOWN
from ui_components import HelpView, ConfirmView

# Command registration
def setup_commands(bot, data_manager: DataManager):
    """Register all commands with the bot"""
    
    @bot.event
    async def on_command_error(ctx, error):
        """Global error handler for command errors"""
        if isinstance(error, commands.CommandNotFound):
            await ctx.send("❌ Command not found. Type `!help` to see available commands.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Missing required argument: {error.param.name}. Check `!help {ctx.command}` for usage.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send(f"❌ Invalid argument. Check `!help {ctx.command}` for usage.")
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"⏳ Command on cooldown. Try again in {error.retry_after:.1f} seconds.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("⛔ You don't have permission to use this command.")
        else:
            await ctx.send(f"❌ An error occurred: {error}")
    
    @bot.command(name="start")
    async def start_command(ctx):
        """Begin your journey and select your class"""
        player = data_manager.get_player(ctx.author.id)
        await PlayerSystem.start_new_character(ctx, player, data_manager)
        data_manager.save_data()
    
    @bot.command(name="profile", aliases=["p", "me"])
    async def profile_command(ctx, member: discord.Member = None):
        """View your stats and progress"""
        target = member or ctx.author
        player = data_manager.get_player(target.id)
        await PlayerSystem.show_profile(ctx, player, target)
    
    @bot.command(name="help", aliases=["h"])
    async def help_command(ctx, category: str = None):
        """Show help message with available commands"""
        from constants import HELP_PAGES
        help_embeds = []
        
        if category:
            if category.title() in HELP_PAGES:
                embed = discord.Embed(
                    title=f"{category.title()} Commands",
                    color=discord.Color.purple()
                )
                
                for cmd, data in HELP_PAGES[category.title()].items():
                    embed.add_field(
                        name=cmd,
                        value=f"{data['description']}\nUsage: {data['usage']}",
                        inline=False
                    )
                help_embeds.append(embed)
            else:
                await ctx.send("❌ Invalid category! Use `!help` to see all categories.")
                return
        else:
            # Create embeds for each category
            for category, commands in HELP_PAGES.items():
                embed = discord.Embed(
                    title=f"{category} Commands",
                    color=discord.Color.purple()
                )
                
                for cmd, data in commands.items():
                    embed.add_field(
                        name=cmd,
                        value=f"{data['description']}\nUsage: {data['usage']}",
                        inline=False
                    )
                
                embed.set_footer(text=f"Page {len(help_embeds) + 1}/{len(HELP_PAGES)}")
                help_embeds.append(embed)
        
        view = HelpView(help_embeds)
        await ctx.send(embed=help_embeds[0], view=view)
    
    @bot.command(name="battle", aliases=["b", "fight"])
    async def battle_command(ctx, opponent: discord.Member = None):
        """Battle another player or an NPC"""
        player = data_manager.get_player(ctx.author.id)
        
        # Check if player has a character
        if not player.class_name:
            await ctx.send("❌ You haven't created a character yet! Use `!start` to begin.")
            return
        
        # Check cooldown
        current_time = datetime.datetime.now()
        if player.last_battle:
            time_since_last_battle = (current_time - player.last_battle).total_seconds()
            if time_since_last_battle < BATTLE_COOLDOWN:
                time_left = BATTLE_COOLDOWN - time_since_last_battle
                minutes = int(time_left // 60)
                seconds = int(time_left % 60)
                await ctx.send(f"⏳ You're still recovering from your last battle. Rest for {minutes}m {seconds}s before battling again.")
                return
        
        # PvP or PvE
        if opponent:
            # Check if opponent is the bot
            if opponent.id == bot.user.id:
                await ctx.send("I'm just a bot, I can't fight you! Try battling without specifying an opponent for an NPC battle.")
                return
            
            # Check if opponent is the player
            if opponent.id == ctx.author.id:
                await ctx.send("You can't battle yourself! Specify another player or leave empty for an NPC battle.")
                return
            
            # Get opponent's data
            opponent_data = data_manager.get_player(opponent.id)
            
            # Check if opponent has a character
            if not opponent_data.class_name:
                await ctx.send(f"❌ {opponent.name} hasn't created a character yet!")
                return
            
            # Check if opponent is within level range (±2 levels)
            level_diff = abs(player.class_level - opponent_data.class_level)
            if level_diff > 2:
                await ctx.send(f"❌ Level difference too high! You can only battle players within 2 levels of your own level ({player.class_level}).")
                return
            
            # Ask opponent if they accept the challenge
            confirm_embed = discord.Embed(
                title="⚔️ Battle Challenge",
                description=f"{ctx.author.name} has challenged {opponent.name} to a battle!",
                color=discord.Color.red()
            )
            confirm_view = ConfirmView(opponent)
            confirm_msg = await ctx.send(content=f"{opponent.mention}", embed=confirm_embed, view=confirm_view)
            
            # Wait for opponent's response
            await confirm_view.wait()
            
            if confirm_view.value is None:
                # Timeout
                await confirm_msg.edit(content=f"{opponent.name} didn't respond to the challenge.", embed=None, view=None)
                return
            elif not confirm_view.value:
                # Declined
                await confirm_msg.edit(content=f"{opponent.name} declined the battle challenge.", embed=None, view=None)
                return
            
            # Start PvP battle
            battle = Battle(player, opponent_data, is_npc=False)
            victory, battle_log = await battle.start_battle(ctx)
            
            # Handle rewards
            await handle_battle_rewards(ctx, player if victory else opponent_data, opponent_data if victory else player, victory, False)
            
            # Update opponent's last battle time
            opponent_data.last_battle = current_time
            
        else:
            # PvE battle against NPC
            battle = Battle(player, is_npc=True)
            victory, battle_log = await battle.start_battle(ctx)
            
            # Handle rewards
            await handle_battle_rewards(ctx, player, battle.opponent, victory, True)
        
        # Save data
        data_manager.save_data()
    
    @bot.command(name="train", aliases=["t"])
    async def train_command(ctx):
        """Train to improve your stats"""
        player = data_manager.get_player(ctx.author.id)
        await PlayerSystem.train_player(ctx, player)
        data_manager.save_data()
    
    @bot.command(name="dungeon", aliases=["d", "explore"])
    async def dungeon_command(ctx, name: str = None):
        """Enter a dungeon"""
        player = data_manager.get_player(ctx.author.id)
        
        # Check if player has a character
        if not player.class_name:
            await ctx.send("❌ You haven't created a character yet! Use `!start` to begin.")
            return
        
        # Check cooldown
        current_time = datetime.datetime.now()
        if player.last_train:
            time_since_last_train = (current_time - player.last_train).total_seconds()
            from constants import DUNGEON_COOLDOWN
            if time_since_last_train < DUNGEON_COOLDOWN:
                time_left = DUNGEON_COOLDOWN - time_since_last_train
                minutes = int(time_left // 60)
                seconds = int(time_left % 60)
                await ctx.send(f"⏳ You're still tired from your last expedition. Rest for {minutes}m {seconds}s before entering a dungeon.")
                return
        
        # If dungeon name is provided, check if it exists
        if name:
            if name.title() not in DUNGEONS:
                await ctx.send(f"❌ Dungeon '{name}' not found! Use `!dungeon` to see available dungeons.")
                return
            
            # Check if player meets level requirement
            dungeon_data = DUNGEONS[name.title()]
            if player.class_level < dungeon_data["level_req"]:
                await ctx.send(f"❌ You need to be level {dungeon_data['level_req']} to enter the {name.title()} dungeon.")
                return
            
            # Enter the specified dungeon
            dungeon_name = name.title()
        else:
            # Show dungeon selection
            embed = discord.Embed(
                title="🗺️ Available Dungeons",
                description="Select a dungeon to explore:",
                color=discord.Color.blue()
            )
            
            # Add each dungeon with details
            for name, data in DUNGEONS.items():
                status = "✅ Available" if player.class_level >= data["level_req"] else f"❌ Requires Level {data['level_req']}"
                completion_count = player.dungeons_completed.get(name, 0)
                
                embed.add_field(
                    name=f"{name} ({data['difficulty']})",
                    value=(
                        f"Floors: {data['floors']}\n"
                        f"XP Reward: {data['exp']}\n"
                        f"Gold: {data['min_rewards']}-{data['max_rewards']} 🌀\n"
                        f"Completed: {completion_count} times\n"
                        f"Status: {status}"
                    ),
                    inline=True
                )
            
            # Send dungeon selection view
            view = DungeonSelectView(player, DUNGEONS)
            message = await ctx.send(embed=embed, view=view)
            
            # Wait for selection
            await view.wait()
            
            if not view.selected_dungeon:
                await message.edit(content="Dungeon selection cancelled.", embed=None, view=None)
                return
            
            dungeon_name = view.selected_dungeon
        
        # Store initial stats to restore afterward if needed
        initial_hp = player.current_stats["hp"]
        initial_energy = player.cursed_energy
        
        # Create and run dungeon instance
        dungeon = DungeonInstance(player, dungeon_name)
        success = await dungeon.run_dungeon(ctx)
        
        # If player died or fled, restore some health and energy
        if not success:
            # Restore 50% of lost HP and energy
            hp_loss = initial_hp - player.current_stats["hp"]
            energy_loss = initial_energy - player.cursed_energy
            
            player.heal(int(hp_loss * 0.5))
            player.restore_energy(int(energy_loss * 0.5))
            
            await ctx.send(
                f"You've recovered some health and energy after your failed dungeon run.\n"
                f"HP: {player.current_stats['hp']}/{player.current_stats['max_hp']}\n"
                f"CE: {player.cursed_energy}/{player.max_cursed_energy}"
            )
        
        # Save data
        data_manager.save_data()
    
    @bot.command(name="inventory", aliases=["i", "inv"])
    async def inventory_command(ctx):
        """View your inventory"""
        player = data_manager.get_player(ctx.author.id)
        await EquipmentSystem.show_inventory(ctx, player)
    
    @bot.command(name="equip", aliases=["e"])
    async def equip_command(ctx, *, item_name: str = None):
        """Equip an item from your inventory"""
        player = data_manager.get_player(ctx.author.id)
        
        # Check if player has a character
        if not player.class_name:
            await ctx.send("❌ You haven't created a character yet! Use `!start` to begin.")
            return
        
        if item_name:
            # Try to equip the specified item
            success = player.equip_item(item_name)
            
            if success:
                await ctx.send(f"✅ Successfully equipped **{item_name}**!")
                data_manager.save_data()
            else:
                await ctx.send(f"❌ Failed to equip **{item_name}**. Make sure it's in your inventory and you meet the requirements.")
        else:
            # Open equipment management UI
            await EquipmentSystem.manage_equipment(ctx, player)
            data_manager.save_data()
    
    @bot.command(name="unequip", aliases=["u"])
    async def unequip_command(ctx, *, slot: str = None):
        """Unequip an item from a specific slot"""
        player = data_manager.get_player(ctx.author.id)
        
        # Check if player has a character
        if not player.class_name:
            await ctx.send("❌ You haven't created a character yet! Use `!start` to begin.")
            return
        
        if slot:
            # Try to unequip from the specified slot
            slot = slot.lower()
            
            # Map some common terms to actual slots
            slot_map = {
                "weapon": "weapon",
                "armor": "armor",
                "accessory": "accessory",
                "talisman": "talisman",
                "neck": "talisman",
                "ring": "accessory",
                "head": "armor",
            }
            
            # Get the correct slot name
            actual_slot = slot_map.get(slot, slot)
            
            if actual_slot not in player.equipped_items:
                await ctx.send(f"❌ Invalid slot: **{slot}**. Valid slots are: weapon, armor, accessory, talisman.")
                return
            
            if not player.equipped_items[actual_slot]:
                await ctx.send(f"❌ Nothing equipped in the **{actual_slot}** slot.")
                return
            
            item_name = player.equipped_items[actual_slot]["name"]
            success = player.unequip_item(actual_slot)
            
            if success:
                await ctx.send(f"✅ Successfully unequipped **{item_name}** from your {actual_slot}.")
                data_manager.save_data()
            else:
                await ctx.send(f"❌ Failed to unequip from **{actual_slot}** slot.")
        else:
            # Open equipment management UI focused on unequipping
            await EquipmentSystem.manage_equipment(ctx, player)
            data_manager.save_data()
    
    @bot.command(name="shop", aliases=["store", "buy"])
    async def shop_command(ctx):
        """Browse and buy items"""
        player = data_manager.get_player(ctx.author.id)
        await EquipmentSystem.show_shop(ctx, player)
        data_manager.save_data()
    
    @bot.command(name="daily", aliases=["claim"])
    async def daily_command(ctx):
        """Claim your daily rewards"""
        player = data_manager.get_player(ctx.author.id)
        await PlayerSystem.daily_reward(ctx, player)
        data_manager.save_data()
    
    @bot.command(name="skills", aliases=["skill", "sp", "skillpoints"])
    async def skills_command(ctx):
        """Allocate skill points"""
        player = data_manager.get_player(ctx.author.id)
        await PlayerSystem.allocate_skill_points(ctx, player)
        data_manager.save_data()
    
    @bot.command(name="heal")
    async def heal_command(ctx):
        """Heal your character (costs currency)"""
        player = data_manager.get_player(ctx.author.id)
        
        # Check if player has a character
        if not player.class_name:
            await ctx.send("❌ You haven't created a character yet! Use `!start` to begin.")
            return
        
        # Check if player needs healing
        if player.current_stats["hp"] >= player.current_stats["max_hp"] and player.cursed_energy >= player.max_cursed_energy:
            await ctx.send("✅ You're already at full health and energy!")
            return
        
        # Calculate cost based on level and how much healing is needed
        hp_percent_missing = 1 - (player.current_stats["hp"] / player.current_stats["max_hp"])
        ce_percent_missing = 1 - (player.cursed_energy / player.max_cursed_energy)
        
        # Higher cost for higher level players and more healing needed
        base_cost = 10 + (player.class_level * 2)
        hp_cost = int(base_cost * hp_percent_missing)
        ce_cost = int(base_cost * ce_percent_missing)
        total_cost = max(5, hp_cost + ce_cost)
        
        # Check if player can afford healing
        if player.currency < total_cost:
            await ctx.send(f"❌ You don't have enough currency to heal! Cost: {total_cost} 🌀, Your currency: {player.currency} 🌀")
            return
        
        # Confirm healing
        confirm_embed = discord.Embed(
            title="💉 Healing",
            description=(
                f"Fully restore your HP and Cursed Energy for {total_cost} 🌀?\n\n"
                f"Current HP: {player.current_stats['hp']}/{player.current_stats['max_hp']}\n"
                f"Current CE: {player.cursed_energy}/{player.max_cursed_energy}\n"
                f"Your currency: {player.currency} 🌀"
            ),
            color=discord.Color.green()
        )
        
        confirm_view = ConfirmView(ctx.author)
        message = await ctx.send(embed=confirm_embed, view=confirm_view)
        
        # Wait for confirmation
        await confirm_view.wait()
        
        if confirm_view.value:
            # Heal player
            player.currency -= total_cost
            player.full_restore()
            
            # Update message
            success_embed = discord.Embed(
                title="✅ Healed Successfully",
                description=(
                    f"You spent {total_cost} 🌀 to fully restore your health and energy.\n\n"
                    f"HP: {player.current_stats['hp']}/{player.current_stats['max_hp']}\n"
                    f"CE: {player.cursed_energy}/{player.max_cursed_energy}\n"
                    f"Remaining currency: {player.currency} 🌀"
                ),
                color=discord.Color.green()
            )
            
            await message.edit(embed=success_embed, view=None)
            data_manager.save_data()
        else:
            # Cancelled
            await message.edit(content="Healing cancelled.", embed=None, view=None)
    
    @bot.command(name="status", aliases=["stats"])
    async def status_command(ctx):
        """Show your current battle status"""
        player = data_manager.get_player(ctx.author.id)
        
        # Check if player has a character
        if not player.class_name:
            await ctx.send("❌ You haven't created a character yet! Use `!start` to begin.")
            return
        
        # Check if on cooldown
        cooldown_status = []
        current_time = datetime.datetime.now()
        
        # Battle cooldown
        if player.last_battle:
            time_since_last_battle = (current_time - player.last_battle).total_seconds()
            if time_since_last_battle < BATTLE_COOLDOWN:
                time_left = BATTLE_COOLDOWN - time_since_last_battle
                minutes = int(time_left // 60)
                seconds = int(time_left % 60)
                cooldown_status.append(f"⏳ Battle: Available in {minutes}m {seconds}s")
            else:
                cooldown_status.append("✅ Battle: Available")
        else:
            cooldown_status.append("✅ Battle: Available")
        
        # Dungeon cooldown
        if player.last_train:
            time_since_last_train = (current_time - player.last_train).total_seconds()
            from constants import DUNGEON_COOLDOWN
            if time_since_last_train < DUNGEON_COOLDOWN:
                time_left = DUNGEON_COOLDOWN - time_since_last_train
                minutes = int(time_left // 60)
                seconds = int(time_left % 60)
                cooldown_status.append(f"⏳ Dungeon: Available in {minutes}m {seconds}s")
            else:
                cooldown_status.append("✅ Dungeon: Available")
        else:
            cooldown_status.append("✅ Dungeon: Available")
        
        # Daily cooldown
        if player.last_daily:
            time_since_last_daily = (current_time - player.last_daily).total_seconds()
            if time_since_last_daily < 86400:  # 24 hours
                next_daily = player.last_daily + datetime.timedelta(days=1)
                time_left = next_daily - current_time
                hours = int(time_left.total_seconds() // 3600)
                minutes = int((time_left.total_seconds() % 3600) // 60)
                cooldown_status.append(f"⏳ Daily: Available in {hours}h {minutes}m")
            else:
                cooldown_status.append("✅ Daily: Available")
        else:
            cooldown_status.append("✅ Daily: Available")
        
        # Create status embed
        embed = discord.Embed(
            title=f"Status: {ctx.author.name}",
            description=f"Class: {player.class_name} | Level: {player.class_level}",
            color=discord.Color.blue()
        )
        
        # HP and Energy bars
        hp_percent = player.current_stats["hp"] / player.current_stats["max_hp"]
        hp_bar = create_bar(hp_percent)
        
        ce_percent = player.cursed_energy / player.max_cursed_energy
        ce_bar = create_bar(ce_percent)
        
        embed.add_field(
            name="Health & Energy",
            value=(
                f"HP: {player.current_stats['hp']}/{player.current_stats['max_hp']} {hp_bar}\n"
                f"CE: {player.cursed_energy}/{player.max_cursed_energy} {ce_bar}"
            ),
            inline=False
        )
        
        # Stats
        embed.add_field(
            name="Stats",
            value=(
                f"Power: {player.current_stats['power']}\n"
                f"Defense: {player.current_stats['defense']}\n"
                f"Speed: {player.current_stats['speed']}"
            ),
            inline=True
        )
        
        # Combat record
        win_rate = 0
        if player.wins + player.losses > 0:
            win_rate = (player.wins / (player.wins + player.losses)) * 100
            
        embed.add_field(
            name="Combat Record",
            value=(
                f"Wins: {player.wins}\n"
                f"Losses: {player.losses}\n"
                f"Win Rate: {win_rate:.1f}%"
            ),
            inline=True
        )
        
        # Cooldowns
        embed.add_field(
            name="Cooldowns",
            value="\n".join(cooldown_status),
            inline=False
        )
        
        if player.skill_points > 0:
            embed.set_footer(text=f"You have {player.skill_points} unspent skill points! Use !skills to allocate them.")
        
        await ctx.send(embed=embed)

    @bot.command(name="rewards", aliases=["drops"])
    async def rewards_command(ctx):
        """View possible dungeon rewards"""
        embed = discord.Embed(
            title="🎁 Dungeon Rewards",
            description="Here are the rewards you can find in each dungeon:",
            color=discord.Color.gold()
        )
        
        for name, data in DUNGEONS.items():
            # Format the rewards info
            rewards_text = (
                f"XP: {data['exp']}\n"
                f"Currency: {data['min_rewards']}-{data['max_rewards']} 🌀\n"
                f"Rare Drop Chance: {data['rare_drop']}%\n"
                f"Level Requirement: {data['level_req']}"
            )
            
            embed.add_field(
                name=f"{name} ({data['difficulty']})",
                value=rewards_text,
                inline=True
            )
        
        embed.add_field(
            name="💡 Tip",
            value=(
                "Defeat more enemies in dungeons for bonus rewards!\n"
                "Higher level dungeons give better items and more XP."
            ),
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @bot.command(name="equipment", aliases=["eq"])
    async def equipment_command(ctx):
        """View your equipped items"""
        player = data_manager.get_player(ctx.author.id)
        
        # Check if player has a character
        if not player.class_name:
            await ctx.send("❌ You haven't created a character yet! Use `!start` to begin.")
            return
        
        # Create equipment embed
        embed = discord.Embed(
            title=f"⚔️ {ctx.author.name}'s Equipment",
            description="Your currently equipped items:",
            color=discord.Color.blue()
        )
        
        # Go through each equipment slot
        has_equipment = False
        for slot, item in player.equipped_items.items():
            if item:
                has_equipment = True
                
                # Get rarity emoji
                from constants import ITEM_RARITY
                rarity_emoji = ITEM_RARITY.get(item.get("rarity", "common"), "⚪")
                
                # Format stats text
                stats_text = ""
                if "stats_boost" in item:
                    stats_text = ", ".join([f"{stat.title()} +{val}" for stat, val in item["stats_boost"].items()])
                
                embed.add_field(
                    name=f"{slot.title()}: {rarity_emoji} {item['name']}",
                    value=f"{item.get('description', '')}\n**Stats:** {stats_text if stats_text else 'None'}",
                    inline=False
                )
        
        if not has_equipment:
            embed.add_field(
                name="No Equipment",
                value="You don't have any items equipped. Use `!shop` to buy items and `!equip` to equip them.",
                inline=False
            )
        else:
            # Show total stats from equipment
            bonus_stats = {"power": 0, "defense": 0, "speed": 0, "hp": 0}
            for slot, item in player.equipped_items.items():
                if item and "stats_boost" in item:
                    for stat, value in item["stats_boost"].items():
                        if stat in bonus_stats:
                            bonus_stats[stat] += value
            
            # Only display stats that have bonuses
            bonus_text = []
            for stat, value in bonus_stats.items():
                if value > 0:
                    bonus_text.append(f"{stat.title()}: +{value}")
            
            if bonus_text:
                embed.add_field(
                    name="Total Equipment Bonuses",
                    value="\n".join(bonus_text),
                    inline=False
                )
        
        # Equipment management instructions
        embed.set_footer(text="Use !equip to equip items and !unequip to unequip items.")
        
        await ctx.send(embed=embed)
    
    @bot.command(name="leaderboard", aliases=["lb", "top"])
    async def leaderboard_command(ctx, category: str = "level"):
        """View the server leaderboard"""
        # Get all players in the current guild
        guild_members = {member.id: member for member in ctx.guild.members}
        
        # Filter players to only include those from this guild and who have characters
        guild_players = []
        for player_id, player_data in data_manager.players.items():
            if int(player_id) in guild_members and player_data.class_name:
                guild_players.append((int(player_id), player_data))
        
        if not guild_players:
            await ctx.send("No players found in the leaderboard yet. Players need to use `!start` to appear here.")
            return
        
        # Sort based on category
        category = category.lower()
        if category in ["level", "lvl"]:
            sorted_players = sorted(guild_players, key=lambda x: (x[1].class_level, x[1].class_exp), reverse=True)
            title = "🏆 Level Leaderboard"
            description = "Top players by level"
        elif category in ["win", "wins"]:
            sorted_players = sorted(guild_players, key=lambda x: x[1].wins, reverse=True)
            title = "🏆 Wins Leaderboard"
            description = "Top players by battle wins"
        elif category in ["winrate", "wr"]:
            # Calculate win rate for each player
            sorted_players = sorted(
                guild_players, 
                key=lambda x: (x[1].wins / max(1, x[1].wins + x[1].losses)), 
                reverse=True
            )
            title = "🏆 Win Rate Leaderboard"
            description = "Top players by battle win percentage"
        elif category in ["dungeon", "dungeons"]:
            sorted_players = sorted(
                guild_players, 
                key=lambda x: sum(x[1].dungeons_completed.values()), 
                reverse=True
            )
            title = "🏆 Dungeon Leaderboard"
            description = "Top players by dungeons completed"
        else:
            await ctx.send(f"❌ Invalid category: {category}. Valid options are: level, wins, winrate, dungeon")
            return
        
        # Create leaderboard embed
        embed = discord.Embed(
            title=title,
            description=description,
            color=discord.Color.gold()
        )
        
        # Add top 10 players
        for i, (player_id, player_data) in enumerate(sorted_players[:10]):
            # Get medal emoji for top 3
            medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"{i+1}."
            
            # Format display value based on category
            if category in ["level", "lvl"]:
                value = f"Level {player_data.class_level} {player_data.class_name}\nXP: {player_data.class_exp}/{player_data.level_requirement}"
            elif category in ["win", "wins"]:
                value = f"{player_data.wins} Wins\nLevel {player_data.class_level} {player_data.class_name}"
            elif category in ["winrate", "wr"]:
                win_rate = 0
                if player_data.wins + player_data.losses > 0:
                    win_rate = (player_data.wins / (player_data.wins + player_data.losses)) * 100
                value = f"{win_rate:.1f}% Win Rate\n{player_data.wins} Wins, {player_data.losses} Losses"
            elif category in ["dungeon", "dungeons"]:
                dungeons_completed = sum(player_data.dungeons_completed.values())
                value = f"{dungeons_completed} Dungeons Completed\nLevel {player_data.class_level} {player_data.class_name}"
            
            # Get member name
            member = guild_members.get(player_id)
            name = member.name if member else f"User {player_id}"
            
            embed.add_field(
                name=f"{medal} {name}",
                value=value,
                inline=False
            )
        
        await ctx.send(embed=embed)

    @bot.command(name="use", aliases=["consume"])
    async def use_command(ctx, *, item_name: str):
        """Use a consumable item"""
        player = data_manager.get_player(ctx.author.id)
        
        # Check if player has a character
        if not player.class_name:
            await ctx.send("❌ You haven't created a character yet! Use `!start` to begin.")
            return
        
        # Find the item in inventory
        item = None
        for inv_item in player.inventory:
            if inv_item.get("name", "").lower() == item_name.lower():
                item = inv_item
                break
        
        if not item:
            await ctx.send(f"❌ Item '{item_name}' not found in your inventory. Use `!inventory` to see your items.")
            return
        
        # Check if it's a consumable
        if item.get("type") != "consumable":
            await ctx.send(f"❌ {item['name']} is not a consumable item. Use `!equip` for equipment items.")
            return
        
        # Use the item
        effects_text = []
        
        if "heal" in item:
            old_hp = player.current_stats["hp"]
            player.heal(item["heal"])
            hp_gain = player.current_stats["hp"] - old_hp
            effects_text.append(f"Restored {hp_gain} HP")
        
        if "energy" in item:
            old_energy = player.cursed_energy
            player.restore_energy(item["energy"])
            energy_gain = player.cursed_energy - old_energy
            effects_text.append(f"Restored {energy_gain} Cursed Energy")
        
        if "effect" in item:
            effect = item["effect"]
            if effect == "strength":
                buff_amount = item.get("buff_amount", 5)
                player.current_stats["power"] += buff_amount
                effects_text.append(f"Increased Power by {buff_amount} (temporary)")
            # Add other effects as needed
        
        # Remove the item from inventory
        player.remove_from_inventory(item["name"])
        
        # Send success message
        embed = discord.Embed(
            title=f"🧪 Used {item['name']}",
            description=f"Effects: {', '.join(effects_text)}",
            color=discord.Color.green()
        )
        
        embed.add_field(
            name="Current Status",
            value=(
                f"HP: {player.current_stats['hp']}/{player.current_stats['max_hp']}\n"
                f"CE: {player.cursed_energy}/{player.max_cursed_energy}"
            ),
            inline=False
        )
        
        await ctx.send(embed=embed)
        data_manager.save_data()
    
    @bot.command(name="gift")
    async def gift_command(ctx, member: discord.Member, amount: int):
        """Gift currency to another player"""
        if member.id == ctx.author.id:
            await ctx.send("❌ You can't gift currency to yourself!")
            return
        
        if amount <= 0:
            await ctx.send("❌ You must gift a positive amount of currency!")
            return
        
        player = data_manager.get_player(ctx.author.id)
        
        # Check if player has a character
        if not player.class_name:
            await ctx.send("❌ You haven't created a character yet! Use `!start` to begin.")
            return
        
        # Check if player has enough currency
        if player.currency < amount:
            await ctx.send(f"❌ You don't have enough currency! You have {player.currency} 🌀, but tried to gift {amount} 🌀.")
            return
        
        # Get recipient player
        recipient = data_manager.get_player(member.id)
        
        # Check if recipient has a character
        if not recipient.class_name:
            await ctx.send(f"❌ {member.name} hasn't created a character yet!")
            return
        
        # Confirm gift
        confirm_embed = discord.Embed(
            title="🎁 Gift Confirmation",
            description=f"Are you sure you want to gift {amount} 🌀 to {member.name}?",
            color=discord.Color.gold()
        )
        
        confirm_view = ConfirmView(ctx.author)
        message = await ctx.send(embed=confirm_embed, view=confirm_view)
        
        # Wait for confirmation
        await confirm_view.wait()
        
        if confirm_view.value:
            # Transfer currency
            player.currency -= amount
            recipient.currency += amount
            
            # Send success message
            success_embed = discord.Embed(
                title="🎁 Gift Sent!",
                description=f"You sent {amount} 🌀 to {member.name}!",
                color=discord.Color.green()
            )
            
            success_embed.add_field(
                name="Your New Balance",
                value=f"{player.currency} 🌀",
                inline=False
            )
            
            await message.edit(embed=success_embed, view=None)
            
            # Notify recipient
            try:
                recipient_embed = discord.Embed(
                    title="🎁 Gift Received!",
                    description=f"You received {amount} 🌀 from {ctx.author.name}!",
                    color=discord.Color.green()
                )
                
                recipient_embed.add_field(
                    name="Your New Balance",
                    value=f"{recipient.currency} 🌀",
                    inline=False
                )
                
                await member.send(embed=recipient_embed)
            except:
                # Couldn't DM the user, just continue
                pass
            
            data_manager.save_data()
        else:
            # Cancelled
            await message.edit(content="Gift cancelled.", embed=None, view=None)

def create_bar(percent: float) -> str:
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
