import discord
from discord.ui import Button, View, Select
from typing import Dict, List, Any, Optional
import operator
from data_models import PlayerData, DataManager


class LeaderboardView(View):

    def __init__(self, data_manager: DataManager, category: str = "level", bot=None):
        super().__init__(timeout=60)
        self.data_manager = data_manager
        self.category = category
        self.page = 0
        self.per_page = 5
        self.bot = bot  # Store the bot instance to look up usernames

        self.add_category_select()
        self.add_navigation_buttons()

    def add_category_select(self):
        """Add dropdown for leaderboard categories"""
        options = [
            discord.SelectOption(label="Level",
                                 value="level",
                                 description="Sort by player level",
                                 default=self.category == "level"),
            discord.SelectOption(label="Gold",
                                 value="gold",
                                 description="Sort by gold amount",
                                 default=self.category == "gold"),
            discord.SelectOption(label="Battle Wins",
                                 value="wins",
                                 description="Sort by PvE battle wins",
                                 default=self.category == "wins"),
            discord.SelectOption(label="PvP Wins",
                                 value="pvp_wins",
                                 description="Sort by PvP battle wins",
                                 default=self.category == "pvp_wins"),
            discord.SelectOption(
                label="Dungeons Completed",
                value="dungeons_completed",
                description="Sort by dungeons completed",
                default=self.category == "dungeons_completed"),
            discord.SelectOption(label="Bosses Defeated",
                                 value="bosses_defeated",
                                 description="Sort by bosses defeated",
                                 default=self.category == "bosses_defeated"),
            discord.SelectOption(label="Combat Rating",
                                 value="combat_rating",
                                 description="Sort by overall combat performance",
                                 default=self.category == "combat_rating"),
            discord.SelectOption(label="Guild Contribution",
                                 value="guild_contribution",
                                 description="Sort by guild activity points",
                                 default=self.category == "guild_contribution"),
            discord.SelectOption(label="Achievement Points",
                                 value="achievement_points",
                                 description="Sort by total achievement points",
                                 default=self.category == "achievement_points"),
            discord.SelectOption(label="Weekly Active",
                                 value="weekly_active",
                                 description="Most active players this week",
                                 default=self.category == "weekly_active")
        ]

        category_select = Select(placeholder="Select category",
                                 options=options)
        category_select.callback = self.category_callback
        self.add_item(category_select)

    def add_navigation_buttons(self):
        """Add prev/next page buttons"""
        prev_button = Button(label="⬅️ Previous",
                             style=discord.ButtonStyle.secondary)
        prev_button.callback = self.prev_page_callback
        self.add_item(prev_button)

        next_button = Button(label="Next ➡️",
                             style=discord.ButtonStyle.secondary)
        next_button.callback = self.next_page_callback
        self.add_item(next_button)

    async def category_callback(self, interaction: discord.Interaction):
        """Handle category selection"""
        # Safely get the selected value
        if hasattr(interaction, 'data') and interaction.data:
            values = interaction.data.get('values')
            if values and len(values) > 0:
                self.category = values[0]
                self.page = 0  # Reset to first page on category change

        embed = await self.create_leaderboard_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    async def prev_page_callback(self, interaction: discord.Interaction):
        """Handle previous page button"""
        if self.page > 0:
            self.page -= 1
        embed = await self.create_leaderboard_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    async def next_page_callback(self, interaction: discord.Interaction):
        """Handle next page button"""
        total_players = len(self.get_sorted_players())
        max_pages = (total_players + self.per_page - 1) // self.per_page

        if self.page < max_pages - 1:
            self.page += 1
        embed = await self.create_leaderboard_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    def get_sorted_players(self) -> List[tuple]:
        """Get players sorted by the selected category"""
        players = []
        for user_id, player in self.data_manager.players.items():
            if self.category == "level":
                value = player.class_level  # Fixed: changed from user_level to class_level
            elif self.category == "gold":
                value = player.gold
            elif self.category == "wins":
                value = player.wins
            elif self.category == "pvp_wins":
                value = player.pvp_wins
            elif self.category == "dungeons_completed":
                value = player.dungeons_completed
            elif self.category == "bosses_defeated":
                value = player.bosses_defeated
            else:
                value = 0

            players.append((user_id, player, value))

        # Sort in descending order by the value
        return sorted(players, key=operator.itemgetter(2), reverse=True)

    async def create_leaderboard_embed(self) -> discord.Embed:
        """Create the leaderboard embed"""
        category_display = {
            "level": "Level",
            "gold": "Gold",
            "wins": "Battle Wins",
            "pvp_wins": "PvP Wins",
            "dungeons_completed": "Dungeons Completed",
            "bosses_defeated": "Bosses Defeated"
        }

        sorted_players = self.get_sorted_players()

        embed = discord.Embed(
            title=
            f"📊 {category_display.get(self.category, 'Level')} Leaderboard",
            description="Top players in the realm!",
            color=discord.Color.gold())

        # Calculate start and end indices for the current page
        start_idx = self.page * self.per_page
        end_idx = min(start_idx + self.per_page, len(sorted_players))

        if not sorted_players:
            embed.add_field(name="No Data",
                            value="No players found.",
                            inline=False)
            return embed

        for i in range(start_idx, end_idx):
            user_id, player, value = sorted_players[i]

            # Get medal for top 3
            medal = ""
            if i == 0:
                medal = "🥇 "
            elif i == 1:
                medal = "🥈 "
            elif i == 2:
                medal = "🥉 "

            rank = i + 1
            # The line below was causing an error - removed it as it seems redundant

            # Format value based on category
            if self.category == "gold":
                value_display = f"{value:,} 💰"
            else:
                value_display = str(value)

            # Try to get username from discord, or fall back to player ID
            username = f"Player {user_id}"
            try:
                if self.bot:
                    # Convert user_id to int if it's a string
                    user_id_int = int(user_id) if isinstance(user_id, str) else user_id
                    user = self.bot.get_user(user_id_int)
                    if user:
                        username = user.display_name or user.name
                    else:
                        # Try to fetch user if not in cache
                        try:
                            user = await self.bot.fetch_user(user_id_int)
                            if user:
                                username = user.display_name or user.name
                        except:
                            # If fetch fails, keep the fallback name
                            pass
            except (ValueError, TypeError, AttributeError):
                # If there's any error converting user_id or finding the user, keep fallback
                pass

            # Build the value string conditionally
            value_parts = [f"**{category_display.get(self.category, 'Level')}:** {value_display}"]
            value_parts.append(f"**Class:** {player.class_name or 'None'}")
            
            # Only show level if we're not already sorting by level
            if self.category != "level":
                value_parts.append(f"**Level:** {player.class_level}")
            
            embed.add_field(
                name=f"{medal}Rank #{rank}: {username}",
                value="\n".join(value_parts),
                inline=False)

        total_players = len(sorted_players)
        max_pages = (total_players + self.per_page - 1) // self.per_page

        embed.set_footer(
            text=
            f"Page {self.page + 1}/{max_pages} • Total Players: {total_players}"
        )
        return embed


async def leaderboard_command(ctx,
                              data_manager: DataManager,
                              category: str = "level"):
    """View the top players leaderboard"""
    # Validate category
    valid_categories = [
        "level", "gold", "wins", "pvp_wins", "dungeons_completed",
        "bosses_defeated"
    ]
    if category and category.lower() not in valid_categories:
        category = "level"  # Default to level if invalid category

    # Pass the bot instance to the view so it can look up usernames
    view = LeaderboardView(data_manager, category=category.lower(), bot=ctx.bot)
    embed = await view.create_leaderboard_embed()

    await ctx.send(embed=embed, view=view)
