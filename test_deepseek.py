import os
import requests
import logging
import time
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
API_KEY = os.getenv('DEEPSEEK_API_KEY')
API_URL = "https://api.deepseek.com/v1/chat/completions"

def test_api_call():
    """Test the DeepSeek API with a simple request."""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    # Test payload following DeepSeek's format
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say hello!"}
        ],
        "max_tokens": 50,
        "temperature": 0.7,
        "stream": False
    }

    try:
        logger.info("Making test API call to DeepSeek...")
        logger.debug(f"Using API URL: {API_URL}")
        logger.debug("API Key format check - First 4 chars: " + API_KEY[:4] if API_KEY else "No API key found")

        response = requests.post(
            API_URL,
            headers=headers,
            json=payload,
            timeout=10,
            verify=True  # Ensure SSL verification is enabled
        )

        logger.info(f"Response Status Code: {response.status_code}")
        logger.debug(f"Response Headers: {response.headers}")
        logger.debug("Raw Response Content: %s", response.text[:500] if response.text else "No content")

        if response.status_code == 200:
            result = response.json()
            logger.info("API call successful!")
            logger.debug(f"Response structure: {list(result.keys())}")
            return result
        else:
            error_content = response.json() if response.content else "No error content"
            logger.error(f"API error: Status {response.status_code}")
            logger.error(f"Error Content: {error_content}")
            logger.error(f"Request URL: {API_URL}")
            logger.error(f"Request Headers: {headers}")
            return None

    except requests.exceptions.Timeout:
        logger.error("Request timed out")
        return None
    except Exception as e:
        logger.error(f"Error making API call: {str(e)}")
        return None

def test_rate_limiting():
    """Test rate limiting by making multiple rapid requests."""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    # Base payload
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say hello!"}
        ],
        "max_tokens": 50,
        "temperature": 0.7,
        "stream": False
    }

    logger.info("Starting rate limit test - making 6 rapid requests...")
    results = []

    for i in range(6):
        try:
            logger.info(f"Making request {i+1}/6...")
            response = requests.post(
                API_URL,
                headers=headers,
                json=payload,
                timeout=10
            )

            logger.info(f"Response {i+1} Status Code: {response.status_code}")

            if response.status_code == 429:
                logger.warning(f"Request {i+1}: Rate limit hit!")
                results.append("RATE_LIMITED")
            elif response.status_code == 200:
                result = response.json()
                content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
                results.append(f"SUCCESS: {content[:30]}...")
                logger.info(f"Request {i+1}: Success")
            else:
                logger.error(f"Request {i+1}: Unexpected status {response.status_code}")
                results.append(f"ERROR: Status {response.status_code}")

            # Small delay to see rate limiting in action
            time.sleep(0.5)

        except Exception as e:
            logger.error(f"Error in request {i+1}: {str(e)}")
            results.append(f"ERROR: {str(e)}")

    return results

if __name__ == "__main__":
    print("\nTesting API Call...")
    print("-" * 50)
    result = test_api_call()
    if result:
        print("\nTest successful! API is working.")
        print("Response received:", result.get('choices', [{}])[0].get('message', {}).get('content', ''))
    else:
        print("\nTest failed! Check the logs above for details.")

    print("\nTesting Rate Limiting...")
    print("-" * 50)
    results = test_rate_limiting()
    print("\nResults:")
    for i, result in enumerate(results, 1):
        print(f"Request {i}: {result}")