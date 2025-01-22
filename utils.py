import time
import requests
from functools import lru_cache
import asyncio
from config import (
    HUGGINGFACE_API_URL, 
    HUGGINGFACE_TOKEN,
    DEEPSEEK_API_KEY,
    MAX_REQUESTS_PER_MINUTE,
    DEEPSEEK_API_URL,
    logger
)

# Rate limiting
request_timestamps = []

def check_rate_limit():
    """Check if we've exceeded our rate limit."""
    current_time = time.time()
    # Remove timestamps older than 1 minute
    global request_timestamps
    request_timestamps = [ts for ts in request_timestamps 
                        if current_time - ts < 60]

    remaining_requests = MAX_REQUESTS_PER_MINUTE - len(request_timestamps)
    if remaining_requests <= 0:
        wait_time = 60 - (current_time - request_timestamps[0])
        logger.warning(f"Rate limit exceeded. Next reset in {wait_time:.1f}s")
        return f"🚫 Rate limit reached! Please wait {wait_time:.0f} seconds before trying again."

    logger.debug(f"Rate limit check passed. {remaining_requests} requests remaining")
    return None

def call_llm(system_message: str, user_message: str) -> str:
    """Call the LLM API with fallback support and improved error handling."""
    rate_limit_msg = check_rate_limit()
    if rate_limit_msg:
        return rate_limit_msg

    try:
        # Try DeepSeek API first
        if DEEPSEEK_API_KEY:
            logger.info("Attempting DeepSeek API call...")
            response = call_deepseek_api(system_message, user_message)
            if response:
                request_timestamps.append(time.time())
                logger.info("DeepSeek API call successful")
                return response
            logger.warning("DeepSeek API call failed, falling back to HuggingFace")

        # Fallback to HuggingFace
        if HUGGINGFACE_TOKEN:
            logger.info("Attempting HuggingFace API call...")
            response = call_huggingface_api(system_message, user_message)
            if response:
                request_timestamps.append(time.time())
                logger.info("HuggingFace API call successful")
                return response
            logger.error("HuggingFace API call failed")

        return "😕 All API attempts failed. Our systems are taking a short break. Please try again in a minute! 🔄"

    except Exception as e:
        logger.error(f"Unexpected error in LLM call: {str(e)}", exc_info=True)
        return "🔧 Oops! Our AI had a slight hiccup. Our engineers are looking into it! Please try again. 🛠️"

def call_deepseek_api(system_message: str, user_message: str) -> str:
    """Call the DeepSeek API with enhanced error handling and detailed logging."""
    try:
        logger.info("Preparing DeepSeek API call...")

        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            "max_tokens": 150,  # Increased for longer responses
            "temperature": 0.7,
            "top_p": 0.9,
            "stream": False
        }

        logger.debug(f"Making request to DeepSeek API: {DEEPSEEK_API_URL}")
        logger.debug(f"Payload length: {len(str(payload))} characters")

        response = requests.post(
            DEEPSEEK_API_URL,
            headers=headers,
            json=payload,
            timeout=10
        )

        logger.debug(f"DeepSeek API Response Status: {response.status_code}")
        logger.debug(f"Response Headers: {response.headers}")

        if response.status_code == 429:
            logger.warning("DeepSeek API rate limit hit")
            return "🚫 Our primary AI is taking a quick break. Switching to backup system... 🔄"

        if response.status_code == 401:
            logger.error("DeepSeek API authentication failed")
            return None

        if response.status_code == 400:
            logger.error(f"DeepSeek API bad request: {response.text}")
            return None

        if response.status_code != 200:
            error_content = response.json() if response.content else "No error content"
            logger.error(f"DeepSeek API error: Status {response.status_code}, Content: {error_content}")
            return None

        result = response.json()
        logger.info("Successfully received DeepSeek API response")
        logger.debug(f"Response tokens used: {result.get('usage', {}).get('total_tokens', 'unknown')}")

        try:
            return result['choices'][0]['message']['content'].strip()
        except (KeyError, IndexError) as e:
            logger.error(f"Unexpected API response format: {e}")
            logger.debug(f"API Response: {result}")
            return None

    except requests.exceptions.Timeout:
        logger.error("DeepSeek API timeout")
        return "⏱️ Request took too long. Let's try that again!"

    except requests.exceptions.RequestException as e:
        logger.error(f"Network error calling DeepSeek API: {str(e)}")
        return "🌐 Having trouble connecting. Please check your internet and try again!"

    except Exception as e:
        logger.error(f"Unexpected error in DeepSeek API call: {str(e)}", exc_info=True)
        return "🤖 Looks like I'm having a moment. Let's try that again!"

def call_huggingface_api(system_message: str, user_message: str) -> str:
    """Call the HuggingFace API as fallback with improved error handling."""
    try:
        headers = {"Authorization": f"Bearer {HUGGINGFACE_TOKEN}"}

        payload = {
            "inputs": f"<|system|>{system_message}</s><|user|>{user_message}</s><|assistant|>",
            "parameters": {
                "max_new_tokens": 150,
                "temperature": 0.7,
                "top_p": 0.9,
                "do_sample": True
            }
        }

        logger.debug("Making HuggingFace API request")

        response = requests.post(
            HUGGINGFACE_API_URL,
            headers=headers,
            json=payload,
            timeout=10
        )

        if response.status_code == 429:
            logger.warning("HuggingFace API rate limit hit")
            return "🚫 Our backup system needs a break too! Please try again in a minute. ⏳"

        if response.status_code != 200:
            logger.error(f"HuggingFace API error: Status {response.status_code}")
            logger.debug(f"Error response: {response.text}")
            return "🤖 Our backup brain needs a quick restart. Please try again!"

        result = response.json()
        generated_text = result[0]['generated_text']
        # Extract only the assistant's response
        assistant_response = generated_text.split("<|assistant|>")[-1].strip()
        return assistant_response

    except Exception as e:
        logger.error(f"Error calling HuggingFace API: {e}", exc_info=True)
        return "🔧 Our backup system isn't responding right now. Please try again!"

async def handle_long_response(interaction, content: str):
    """Handle responses that might be too long for Discord."""
    try:
        if len(content) > 2000:
            chunks = [content[i:i + 1994] for i in range(0, len(content), 1994)]
            await interaction.response.send_message(f"{chunks[0]} (1/{len(chunks)})")
            for i, chunk in enumerate(chunks[1:], 2):
                await interaction.followup.send(f"{chunk} ({i}/{len(chunks)})")
        else:
            await interaction.response.send_message(content)
    except Exception as e:
        logger.error(f"Error handling long response: {e}", exc_info=True)
        await interaction.response.send_message("❌ Something went wrong while sending the response. Please try again!")