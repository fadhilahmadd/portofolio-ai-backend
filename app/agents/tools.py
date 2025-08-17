from datetime import datetime
import pytz
from langchain_core.tools import tool

@tool
def get_current_time(timezone: str = "Asia/Jakarta") -> str:
    """
    Returns the current date and time for a given timezone.
    Defaults to Jakarta (WIB) if no timezone is provided.
    """
    try:
        tz = pytz.timezone(timezone)
        current_time = datetime.now(tz)
        return f"The current time in {timezone} is {current_time.strftime('%A, %B %d, %Y %I:%M %p')}."
    except pytz.UnknownTimeZoneError:
        return f"Sorry, I don't recognize the timezone '{timezone}'. Please use a valid timezone like 'Asia/Jakarta' or 'America/New_York'."