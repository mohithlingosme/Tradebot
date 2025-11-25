"""
Time utility functions for market data processing.
"""

from datetime import datetime, timedelta
from typing import List, Tuple


def generate_time_chunks(start_time: datetime, end_time: datetime,
                        chunk_size: timedelta) -> List[Tuple[datetime, datetime]]:
    """
    Generate time chunks for backfill processing.

    Args:
        start_time: Start of the time range
        end_time: End of the time range
        chunk_size: Size of each chunk

    Returns:
        List of (chunk_start, chunk_end) tuples
    """
    chunks = []
    current_time = start_time

    while current_time < end_time:
        chunk_end = min(current_time + chunk_size, end_time)
        chunks.append((current_time, chunk_end))
        current_time = chunk_end

    return chunks


def align_to_granularity(dt: datetime, granularity_minutes: int) -> datetime:
    """
    Align a datetime to the start of a granularity bucket.

    Args:
        dt: Datetime to align
        granularity_minutes: Granularity in minutes

    Returns:
        Aligned datetime
    """
    # Calculate total minutes since epoch
    epoch = datetime(1970, 1, 1)
    total_minutes = int((dt - epoch).total_seconds() / 60)

    # Align to granularity
    aligned_minutes = (total_minutes // granularity_minutes) * granularity_minutes

    return epoch + timedelta(minutes=aligned_minutes)


def get_candle_bucket_start(dt: datetime, granularity: str) -> datetime:
    """
    Get the bucket start time for a candle based on granularity.

    Args:
        dt: Datetime
        granularity: Granularity string (e.g., '1m', '5m', '1h', '1d')

    Returns:
        Bucket start datetime
    """
    if granularity.endswith('m'):
        minutes = int(granularity[:-1])
        return align_to_granularity(dt, minutes)
    elif granularity.endswith('h'):
        hours = int(granularity[:-1])
        # Align to hour boundary first, then to hour multiple
        aligned_hour = dt.replace(minute=0, second=0, microsecond=0)
        hour_diff = aligned_hour.hour % hours
        aligned_hour = aligned_hour - timedelta(hours=hour_diff)
        return aligned_hour
    elif granularity.endswith('d'):
        # Align to start of day
        return dt.replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        # For unsupported granularity, return the original datetime unchanged
        return dt


def parse_granularity(granularity: str) -> timedelta:
    """
    Parse granularity string to timedelta.

    Args:
        granularity: Granularity string (e.g., '1m', '5m', '1h', '1d')

    Returns:
        Timedelta representing the granularity
    """
    if granularity.endswith('m'):
        return timedelta(minutes=int(granularity[:-1]))
    elif granularity.endswith('h'):
        return timedelta(hours=int(granularity[:-1]))
    elif granularity.endswith('d'):
        return timedelta(days=int(granularity[:-1]))
    else:
        raise ValueError(f"Unsupported granularity: {granularity}")


def is_market_hours(dt: datetime, timezone: str = 'America/New_York') -> bool:
    """
    Check if a datetime is during market hours (9:30 AM - 4:00 PM ET).

    Args:
        dt: Datetime to check
        timezone: Timezone string

    Returns:
        True if during market hours
    """
    # This is a simplified check - in production you'd use proper timezone handling
    # For now, just check if it's a weekday between 9:30 and 16:00
    if dt.weekday() >= 5:  # Saturday = 5, Sunday = 6
        return False

    # Simplified time check (assuming UTC for now)
    hour = dt.hour
    minute = dt.minute

    if hour < 14 or hour > 21:  # 9:30 AM ET = 14:30 UTC, 4:00 PM ET = 21:00 UTC
        return False

    if hour == 14 and minute < 30:
        return False

    return True
