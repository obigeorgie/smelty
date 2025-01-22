import discord
from discord import app_commands
from config import DISCORD_TOKEN, logger
from database import Database
from personas import PERSONAS, RICKROLL_RESPONSES
from utils import call_llm, handle_long_response
import asyncio

# Initialize Discord client with all intents
intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# Initialize database
db = Database()

# Add reconnection handling
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

# Updated help command
@tree.command(name="help", description="Show available modes and features of the bot")
async def help_command(interaction):
    """Display help information about the bot."""
    try:
        help_text = """
🤖 **AI Personality Bot - Your Companion with Multiple Personalities!**

🎭 **Available Modes:**
• `cynical_vc` - A sarcastic Silicon Valley VC who questions everything
• `starry_teen` - An overly excited TikTok teen who can't stop using emojis
• `conspiracy_nut` - A paranoid theorist who sees patterns everywhere

🎮 **How to Use:**
```
/smelty mode:[choose_mode] question:[your_question]
```

📝 **Example:**
`/smelty mode:cynical_vc question:What's your take on AI startups?`

🌟 **Special Features:**
• 🎯 Build your streak by using the bot regularly
• 🎉 Secret mode unlocks at 10 uses!
• 🎵 Try asking about rickroll in any mode for a surprise!

⚡ **Rate Limits:**
• 5 requests per minute to keep things running smoothly
• Watch for the streak counter after each response!

Need more help? Just ask away! 🚀"""

        await interaction.response.send_message(help_text)
        logger.info(f"Help command used by {interaction.user.name}")
    except Exception as e:
        logger.error(f"Error displaying help: {e}", exc_info=True)
        await interaction.response.send_message(
            "❌ Sorry, couldn't display help right now. Please try again later!"
        )

@tree.command(
    name="smelty",
    description="Ask AI in a specific personality mode!"
)
@app_commands.describe(
    mode="The personality mode (cynical_vc, starry_teen, conspiracy_nut)",
    question="Your question or prompt for the AI"
)
async def smelty(interaction, mode: str, question: str):
    try:
        logger.info(f"Received command from {interaction.user.name} (ID: {interaction.user.id})")
        logger.info(f"Mode: {mode}, Question: {question}")

        # Check if it's a rickroll request
        if question.lower().strip() == "rickroll":
            response = RICKROLL_RESPONSES.get(mode, RICKROLL_RESPONSES["dank_memer"])
            logger.info("Processing rickroll request")
            await interaction.response.send_message(response)
            return

        # Update user streak
        user_id = interaction.user.id
        streak = db.update_user_streak(user_id)
        logger.info(f"User {user_id} streak updated to: {streak}")

        # Check if user unlocked dank_memer mode
        if streak >= 10 and mode == "dank_memer":
            persona = PERSONAS["dank_memer"]
            logger.info("Using dank_memer persona (unlocked)")
        elif mode not in PERSONAS:
            available_modes = ", ".join(f"`{m}`" for m in PERSONAS.keys() if m != "dank_memer")
            logger.warning(f"Invalid mode requested: {mode}")
            await interaction.response.send_message(
                f"❌ Invalid mode! Available modes: {available_modes}\n"
                f"💡 Use `/help` to see all features and examples!"
            )
            return
        else:
            persona = PERSONAS[mode]
            logger.info(f"Using persona: {mode}")

        # Defer the response to show "thinking" state
        await interaction.response.defer(thinking=True)

        try:
            # Get AI response with improved error handling
            logger.info("Calling LLM API...")
            response = call_llm(persona["prompt"], question)
            logger.info("Received response from LLM")

            # Format response with mode and streak info
            formatted_response = f"**[{mode}]** {response}\n"

            # Show streak milestone messages
            streak_message = f"\n🎯 Current Streak: {streak}"
            if streak == 10:
                streak_message += "\n🎉 **Achievement Unlocked!** You've discovered the secret 'dank_memer' mode!"
                logger.info(f"User {interaction.user.name} unlocked dank_memer mode!")
            elif streak > 10:
                streak_message += "\n🎭 Pro tip: Try the 'dank_memer' mode for extra spice! 🌶️"
            elif streak >= 5:
                streak_message += "\n👀 Getting close to unlocking something special..."

            formatted_response += streak_message

            await interaction.followup.send(formatted_response)
            logger.info("Response sent successfully with streak info")

        except Exception as e:
            error_msg = str(e)
            if "Rate limit exceeded" in error_msg:
                await interaction.followup.send(
                    "🚫 Whoa there, speed racer! You're moving too fast!\n"
                    "⏳ Take a quick breather (about 60 seconds) before your next wild take.\n"
                    "🤔 Perfect time to review your previous chaos or check `/help` for more modes!"
                )
            else:
                await interaction.followup.send(
                    "🤖 Oops! My circuits are a bit tangled right now.\n"
                    "🔄 Give me a moment to recalibrate and try again!\n"
                    "💡 Tip: Try a different mode or question if this persists."
                )
            logger.error(f"Error getting response: {e}", exc_info=True)

    except Exception as e:
        logger.error(f"Error processing command: {e}", exc_info=True)
        if not interaction.response.is_done():
            await interaction.response.send_message(
                "⚠️ Something went sideways! Don't worry, it's not you - it's me.\n"
                "🔄 Please try again in a moment!"
            )
        else:
            await interaction.followup.send(
                "⚠️ Something went sideways! Don't worry, it's not you - it's me.\n"
                "🔄 Please try again in a moment!"
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

if __name__ == "__main__":
    asyncio.run(start_bot())