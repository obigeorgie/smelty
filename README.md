# Discord Personality Bot (Smelty)

A fun Discord bot that responds to queries with different personalities using DeepSeek-R1 API. The bot features multiple personas including a cynical Silicon Valley VC, an enthusiastic TikTok teen, and a conspiracy theorist.

## Features

- 🎭 Multiple AI Personalities
  - Cynical Silicon Valley VC
  - Enthusiastic TikTok Teen
  - Conspiracy Theorist
  - Secret "Dank Memer" mode (unlocked at streak 10)
- 🎯 User Streak System
- 🚀 Rate Limiting Protection
- 💾 Persistent User Data
- 🔄 API Fallback System (DeepSeek → HuggingFace)

## Commands

- `/smelty mode:[personality] question:[your_question]` - Get AI responses in different personalities
- `/help` - Show available modes and features

## Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file with the following variables:
   ```
   DISCORD_TOKEN=your_discord_token
   DEEPSEEK_API_KEY=your_deepseek_api_key
   HUGGINGFACE_TOKEN=your_huggingface_token
   ```
4. Run the bot:
   ```bash
   python bot.py
   ```

## Personalities

- **Cynical VC**: Sarcastic Silicon Valley investor who questions everything
- **Starry Teen**: Overly excited TikTok teen who loves emojis
- **Conspiracy Nut**: Paranoid theorist who connects everything to conspiracies
- **Dank Memer**: Special mode unlocked after 10 uses (Hidden)

## Rate Limits

- 5 requests per minute per user
- Built-in cooldown system
- Automatic fallback to HuggingFace when DeepSeek is unavailable

## License

MIT License - See LICENSE file for details
