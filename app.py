import os
from flask import Flask, render_template
from config import DISCORD_TOKEN
from personas import PERSONAS, REWARD_PERSONAS

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev_key_123")

@app.route('/')
def home():
    """Landing page route."""
    features = [
        {
            "icon": "🎭",
            "title": "Multiple Personas",
            "description": "Chat with different AI personalities - from a cynical VC to a medieval knight!"
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

    # Show first 6 base personas
    persona_list = list(PERSONAS.items())[:6]
    personas = [
        {
            "name": name.replace('_', ' ').title(),
            "description": details["prompt"].split('\n')[0].strip(),
            "example": details["example"]
        }
        for name, details in persona_list
    ]

    # Show all reward tiers
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
            "unlock": "15 uses",
            "reward": "Poetry Master",
            "description": "Responses flow like beautiful verses"
        },
        {
            "unlock": "25 uses",
            "reward": "Chaos Agent Mode",
            "description": "Pure randomness and surreal humor"
        },
        {
            "unlock": "35 uses",
            "reward": "Quantum Physicist",
            "description": "Scientific and quantum-inspired responses"
        },
        {
            "unlock": "50 uses",
            "reward": "Elite Status",
            "description": "Fancy formatting and theatrical responses"
        },
        {
            "unlock": "75 uses",
            "reward": "Shakespearean Dramatist",
            "description": "Dramatic and theatrical responses"
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