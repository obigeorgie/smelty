import discord
from discord import app_commands
from config import DISCORD_TOKEN, logger
from database import Database
from personas import PERSONAS, REWARD_PERSONAS, RICKROLL_RESPONSES, get_unlock_message, get_persona
from utils import call_llm, handle_long_response
import asyncio
import json

# Initialize Discord client with all intents
intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# Initialize database
db = Database()

@tree.command(name="help", description="Show available modes and features of the bot")
async def help_command(interaction):
    """Display help information about the bot."""
    try:
        # Get user's unlocked rewards
        _, _, unlocked_rewards = db.get_user_streak(interaction.user.id)

        # Build help text based on available features
        base_modes = ", ".join(f"`{m}`" for m in PERSONAS.keys())
        unlocked_modes = ", ".join(f"`{m}`" for m in REWARD_PERSONAS.keys() if m in unlocked_rewards)

        # Build the special modes section only if there are unlocked modes
        special_modes_section = ""
        if unlocked_modes:
            special_modes_section = f"🌟 **Unlocked Special Modes:**\n• {unlocked_modes}\n\n"

        help_text = (
            "🤖 **AI Personality Bot - Your Companion with Multiple Personalities!**\n\n"
            f"🎭 **Available Modes:**\n• {base_modes}\n\n"
            f"{special_modes_section}"
            "🎮 **How to Use:**\n"
            "/smelty mode:[choose_mode] question:[your_question]\n"
            "/prefs - Set your default personality mode\n\n"
            "📝 **Example:**\n"
            "/smelty mode:cynical_vc question:What's your take on AI startups?\n\n"
            "🌟 **Streak Rewards:**\n"
            "• 5 uses: Unlock Meme Lord mode\n"
            "• 10 uses: Unlock Dank Memer mode\n"
            "• 25 uses: Unlock Chaos Agent mode\n"
            "• 50 uses: Unlock Elite Status\n"
            "• 100 uses: Unlock Legendary status\n\n"
            "⚡ **Rate Limits:**\n"
            "• 5 requests per minute to keep things running smoothly\n\n"
            "Need more help? Just ask away! 🚀"
        )

        await interaction.response.send_message(help_text)
        logger.info(f"Help command used by {interaction.user.name}")
    except Exception as e:
        logger.error(f"Error displaying help: {e}", exc_info=True)
        await interaction.response.send_message(
            "❌ Sorry, couldn't display help right now. Please try again later!"
        )

@tree.command(
    name="prefs",
    description="Set your preferences for the bot!"
)
@app_commands.describe(
    default_mode="Your preferred personality mode",
)
async def preferences(interaction, default_mode: str = None):
    """Set user preferences."""
    try:
        if default_mode:
            # Verify the mode exists and user has access
            streak, _, unlocked_rewards = db.get_user_streak(interaction.user.id)

            if default_mode in REWARD_PERSONAS and default_mode not in unlocked_rewards:
                await interaction.response.send_message(
                    f"❌ You haven't unlocked the {default_mode} mode yet!\n"
                    f"Keep using the bot to unlock more personalities!"
                )
                return

            if default_mode not in PERSONAS and default_mode not in REWARD_PERSONAS:
                available_modes = list(PERSONAS.keys()) + [r for r in unlocked_rewards if r in REWARD_PERSONAS]
                await interaction.response.send_message(
                    f"❌ Invalid mode! Available modes: {', '.join(available_modes)}"
                )
                return

            # Save preference
            if db.save_user_preference(interaction.user.id, default_mode):
                await interaction.response.send_message(
                    f"✅ Your default mode has been set to: `{default_mode}`!\n"
                    "This will be used when you don't specify a mode."
                )
            else:
                await interaction.response.send_message(
                    "❌ Couldn't save your preference. Please try again later!"
                )
        else:
            # Show current preferences
            default_persona, custom_settings = db.get_user_preferences(interaction.user.id)
            if default_persona:
                await interaction.response.send_message(
                    f"🎭 Your current default mode is: `{default_persona}`\n"
                    "Use `/prefs default_mode:[mode]` to change it!"
                )
            else:
                await interaction.response.send_message(
                    "You haven't set any preferences yet!\n"
                    "Use `/prefs default_mode:[mode]` to set your default personality."
                )

    except Exception as e:
        logger.error(f"Error handling preferences: {e}", exc_info=True)
        await interaction.response.send_message(
            "❌ Something went wrong with preferences. Please try again later!"
        )

@tree.command(
    name="smelty",
    description="Ask AI in a specific personality mode!"
)
@app_commands.describe(
    mode="The personality mode (use /help to see available modes)",
    question="Your question or prompt for the AI"
)
async def smelty(interaction, question: str, mode: str = None):
    try:
        logger.info(f"Command received - User: {interaction.user.name} (ID: {interaction.user.id})")

        # If no mode specified, use user's preferred mode
        if not mode:
            default_mode, _ = db.get_user_preferences(interaction.user.id)
            if default_mode:
                mode = default_mode
                logger.info(f"Using default mode {mode} for user {interaction.user.name}")
            else:
                mode = "cynical_vc"  # Fallback to default

        logger.info(f"Parameters - Mode: {mode}, Question: {question}")

        # Check if it's a rickroll request
        if question.lower().strip() == "rickroll":
            response = RICKROLL_RESPONSES.get(mode, RICKROLL_RESPONSES["dank_memer"])
            logger.info(f"Rickroll request processed for mode: {mode}")
            await interaction.response.send_message(response)
            return

        # Update user streak with more logging
        previous_streak = db.get_user_streak(interaction.user.id)[0]
        streak, highest_streak, unlocked_rewards = db.update_user_streak(interaction.user.id)
        logger.info(f"User streak updated - Previous: {previous_streak}, New: {streak}")

        # Check for new rewards
        new_rewards = [r for r in unlocked_rewards if r not in json.loads(db.get_user_streak(interaction.user.id)[2])]

        # Get appropriate persona based on mode and unlocked rewards
        persona = get_persona(mode, unlocked_rewards)
        if not persona:
            available_modes = (
                list(PERSONAS.keys()) +
                [r for r in unlocked_rewards if r in REWARD_PERSONAS]
            )
            modes_str = ", ".join(f"`{m}`" for m in available_modes)
            logger.warning(f"Invalid mode requested: {mode} by user {interaction.user.name}")
            await interaction.response.send_message(
                f"❌ Invalid mode! Available modes: {modes_str}\n"
                f"💡 Use `/help` to see all features and examples!"
            )
            return

        # Defer response with logging
        await interaction.response.defer(thinking=True)
        logger.info("Response deferred, initiating API call")

        try:
            # Get AI response with enhanced logging
            logger.info(f"Calling LLM API for user {interaction.user.name} with persona {mode}")
            response = call_llm(persona["prompt"], question)
            logger.info("Received LLM API response successfully")

            # Format response with mode and streak info
            formatted_response = f"**[{mode}]** {response}\n"

            # Add streak and reward information
            streak_message = f"\n🎯 Current Streak: {streak}"
            if highest_streak > streak:
                streak_message += f" (Highest: {highest_streak})"

            # Add new reward notifications
            if new_rewards:
                streak_message += "\n\n🎉 **New Rewards Unlocked!**"
                for reward in new_rewards:
                    streak_message += f"\n{get_unlock_message(reward)}"
            elif streak >= 5:
                next_tier = next((tier for tier in [5, 10, 25, 50, 100] if tier > streak), None)
                if next_tier:
                    streak_message += f"\n👀 Next reward at {next_tier} streak!"

            formatted_response += streak_message

            await interaction.followup.send(formatted_response)
            logger.info(f"Response sent successfully to user {interaction.user.name}")

        except Exception as e:
            error_msg = str(e)
            if "Rate limit exceeded" in error_msg:
                logger.warning(f"Rate limit hit for user {interaction.user.name}")
                await interaction.followup.send(
                    "🚫 Whoa there, speed racer! You're moving too fast!\n"
                    "⏳ Take a quick breather (about 60 seconds) before your next wild take.\n"
                    "🤔 Perfect time to review your previous chaos or check `/help` for more modes!"
                )
            else:
                logger.error(f"Error getting response: {e}", exc_info=True)
                await interaction.followup.send(
                    "🤖 Oops! My circuits are a bit tangled right now.\n"
                    "🔄 Give me a moment to recalibrate and try again!\n"
                    "💡 Tip: Try a different mode or question if this persists."
                )

    except Exception as e:
        logger.error(f"Error processing command: {e}", exc_info=True)
        error_response = (
            "⚠️ Something went sideways! Don't worry, it's not you - it's me.\n"
            "🔄 Please try again in a moment!"
        )
        if not interaction.response.is_done():
            await interaction.response.send_message(error_response)
        else:
            await interaction.followup.send(error_response)

@tree.command(name="invite", description="Get the bot's invite link!")
async def invite_command(interaction):
    """Provides the bot's invite link."""
    try:
        # Create invite link with minimal required permissions
        permissions = discord.Permissions(
            send_messages=True,
            use_application_commands=True
        )

        invite_url = discord.utils.oauth_url(
            client.user.id,
            permissions=permissions,
            scopes=["bot", "applications.commands"]
        )

        await interaction.response.send_message(
            f"🎉 **Add me to your server!**\n"
            f"Click here to invite me: {invite_url}\n\n"
            f"*I only need basic permissions to send messages and use commands!*"
        )
        logger.info(f"Invite command used by {interaction.user.name}")
    except Exception as e:
        logger.error(f"Error generating invite link: {e}")
        await interaction.response.send_message(
            "❌ Oops! Something went wrong generating the invite link. "
            "Please try again later!"
        )

@client.event
async def on_ready():
    """Called when the bot is ready."""
    try:
        await tree.sync()
        logger.info(f"Logged in as {client.user} (ID: {client.user.id})")
        logger.info("Bot is ready and commands are synced!")
        logger.info("------")
    except Exception as e:
        logger.error(f"Error during startup: {e}", exc_info=True)

async def start_bot():
    """Start the Discord bot with reconnection handling."""
    retry_count = 0
    max_retries = 5
    base_delay = 1

    while retry_count < max_retries:
        try:
            async with client:
                await client.start(DISCORD_TOKEN)
        except discord.errors.HTTPException as e:
            if e.status == 429:  # Too Many Requests
                delay = base_delay * (2 ** retry_count)  # Exponential backoff
                logger.warning(f"Rate limited. Retrying in {delay} seconds...")
                await asyncio.sleep(delay)
                retry_count += 1
            else:
                logger.error(f"HTTP Error: {e}")
                break
        except Exception as e:
            logger.error(f"Error during bot execution: {e}")
            break

if __name__ == "__main__":
    asyncio.run(start_bot())