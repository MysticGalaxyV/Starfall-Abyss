"""
User interaction restriction system for Discord RPG Bot
Ensures only authorized users can interact with command interfaces
"""

import discord
from discord.ui import View
from typing import Optional, Union


class RestrictedView(View):
    """
    Base view class that restricts interactions to specific users
    """

    def __init__(self, authorized_user: Union[discord.User, discord.Member],
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.authorized_user_id = authorized_user.id
        self.authorized_user_name = str(authorized_user)

    async def interaction_check(self,
                                interaction: discord.Interaction) -> bool:
        """
        Check if the user is authorized to use this interface
        Returns True if authorized, False otherwise
        """
        if interaction.user.id != self.authorized_user_id:
            await interaction.response.send_message(
                f"❌ This interface is for {self.authorized_user_name} only! "
                f"Use your own command to access this feature.",
                ephemeral=True)
            return False
        return True


def get_target_user(
        ctx,
        mentioned_users: list = None) -> Union[discord.User, discord.Member]:
    """
    Determine the target user for a command
    Returns mentioned user if any, otherwise the command author
    """
    if mentioned_users and len(mentioned_users) > 0:
        return mentioned_users[0]
    return ctx.author


def create_restricted_embed_footer(
        authorized_user: Union[discord.User, discord.Member]) -> str:
    """
    Create a footer text indicating who can use the interface
    """
    return f"🔒 Interface restricted to {authorized_user.display_name}"
