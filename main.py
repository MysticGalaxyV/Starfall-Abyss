import discord
from discord.ext import commands
import os
import asyncio
import logging

# Local imports
from data_manager import DataManager
from commands import setup_commands
from constants import ACTIVITY_STATUS, LOG_FORMAT

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('jujutsu_rpg')

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

def get_prefix(bot, message):
    prefixes = ['!', f'<@{bot.user.id}> ', f'<@!{bot.user.id}> ']
    return prefixes

bot = commands.Bot(command_prefix=get_prefix, intents=intents, activity=discord.Game(name=ACTIVITY_STATUS))
bot.remove_command('help')  # Remove default help command to use our custom one

# Initialize the data manager
data_manager = DataManager()

@bot.event
async def on_ready():
    """Event triggered when bot is connected and ready"""
    logger.info(f'Logged in as {bot.user.name} ({bot.user.id})')
    logger.info(f'Connected to {len(bot.guilds)} guilds')
    logger.info(f'Bot is ready!')

@bot.event
async def on_message(message):
    """Event triggered when a message is received"""
    # Prevent the bot from responding to itself
    if message.author == bot.user:
        return
    
    # Respond to just the bot mention
    if message.content.strip() == f'<@{bot.user.id}>' or message.content.strip() == f'<@!{bot.user.id}>':
        ctx = await bot.get_context(message)
        from commands import help_command
        await help_command(ctx)
    
    await bot.process_commands(message)

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
        logger.error(f"Command error: {error}", exc_info=True)
        await ctx.send(f"❌ An error occurred: {error}")

@bot.event
async def on_disconnect():
    """Event triggered when bot disconnects - save data before exit"""
    logger.info("Bot disconnecting, saving data...")
    data_manager.save_data()

async def auto_save_data():
    """Background task to periodically save player data"""
    await bot.wait_until_ready()
    logger.info("Starting auto-save task")
    while not bot.is_closed():
        await asyncio.sleep(300)  # Save every 5 minutes
        logger.info("Auto-saving player data...")
        data_manager.save_data()

def main():
    """Main entry point to start the bot"""
    # Register all commands
    setup_commands(bot, data_manager)
    
    # Start the auto-save background task
    bot.loop.create_task(auto_save_data())
    
    # Start the bot
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        logger.error("No Discord token found. Set the DISCORD_TOKEN environment variable.")
        return
    
    try:
        bot.run(token)
    except discord.errors.LoginFailure:
        logger.error("Invalid token. Please check your Discord token.")
    except Exception as e:
        logger.error(f"Error starting bot: {e}", exc_info=True)
    finally:
        # Make sure to save data when the bot shuts down
        data_manager.save_data()
        logger.info("Bot shut down, data saved.")

if __name__ == "__main__":
    main()
