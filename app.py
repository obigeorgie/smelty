import os
from flask import Flask, render_template
from config import DISCORD_TOKEN

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev_key_123")

@app.route('/')
def home():
    """Landing page route."""
    features = [
        {
            "icon": "🎭",
            "title": "Multiple Personas",
            "description": "Chat with different AI personalities - from a cynical VC to an excited teen!"
        },
        {
            "icon": "🏆",
            "title": "Streak Rewards",
            "description": "Keep using the bot to unlock special modes and hidden features!"
        },
        {
            "icon": "🚀",
            "title": "Smart Fallback",
            "description": "Automatically switches between APIs to ensure 24/7 uptime"
        },
        {
            "icon": "⚡",
            "title": "Rate Limited",
            "description": "Built-in rate limiting to keep things running smoothly"
        }
    ]
    
    personas = [
        {
            "name": "Cynical VC",
            "description": "Questions everything's scalability with a dash of startup jargon",
            "example": "Oh sure, another 'revolutionary' idea that'll disrupt the market. What's your burn rate looking like? *adjusts Patagonia vest*"
        },
        {
            "name": "TikTok Teen",
            "description": "Super excited about everything with plenty of emojis",
            "example": "OMG bestie! 🌟 That's literally 💫 the most amazing 🎯 thing ever!!!"
        },
        {
            "name": "Conspiracy Theorist",
            "description": "Connects everything to the Illuminati or UFOs",
            "example": "Wake up sheeple! The Illuminati is clearly behind this. I have documents from Area 51 that PROVE it!"
        }
    ]
    
    rewards = [
        {
            "unlock": "5 uses",
            "reward": "Meme Lord Mode",
            "description": "Master of internet culture and memes"
        },
        {
            "unlock": "10 uses",
            "reward": "Dank Memer Mode",
            "description": "The original chaotic personality"
        },
        {
            "unlock": "25 uses",
            "reward": "Chaos Agent Mode",
            "description": "Pure randomness and surreal humor"
        },
        {
            "unlock": "50 uses",
            "reward": "Elite Status",
            "description": "Fancy formatting and theatrical responses"
        },
        {
            "unlock": "100 uses",
            "reward": "Legendary Mode",
            "description": "The ultimate AI personality"
        }
    ]
    
    return render_template('index.html', 
                         features=features,
                         personas=personas,
                         rewards=rewards)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
