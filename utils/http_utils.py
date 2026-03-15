# utils/http_utils.py
"""
Resilient HTTP helpers shared by weather_api.py (and any future API module).
"""

import time
import requests
from utils.logger import get_logger

logger = get_logger(__name__)


def get_with_retry(
    url: str,
    params: dict,
    timeout: int = 10,
    max_retries: int = 3,
    backoff: float = 1.5,
) -> requests.Response:
    """
    GET request with exponential backoff retry.
    Only retries on network errors and 5xx responses.
    Raises immediately on 4xx (client errors — retrying won't help).
    
    Args:
        url (str): OpenWeatherMap url
        params (dict): dictionary of request parameters
        timeout (int): 10 seconds by default
        max_retries (int): 3 times by default
        backoff (float)L 1.5 by default
    
    Returns:
        requests.Response: respose of the request or any error msg if any error happens
    """
    last_error = None

    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(url, params=params, timeout=timeout)

            # 4xx → don't retry, raise immediately
            if 400 <= response.status_code < 500:
                response.raise_for_status()

            # 5xx → retry
            if response.status_code >= 500:
                raise requests.exceptions.HTTPError(
                    f"Server error: {response.status_code}", response=response
                )

            return response   # success

        except (requests.exceptions.ConnectionError,
                requests.exceptions.Timeout,
                requests.exceptions.HTTPError) as e:
            last_error = e
            wait = backoff ** attempt
            logger.warning(
                "Attempt %d/%d failed (%s). Retrying in %.1fs…",
                attempt, max_retries, e, wait,
            )
            if attempt < max_retries:
                time.sleep(wait)

    raise last_error   # re-raise after all retries exhausted