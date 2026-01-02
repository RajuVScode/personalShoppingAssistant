import re
from datetime import datetime, timedelta
from typing import Optional, Tuple

def get_upcoming_weekend(current_date: datetime) -> Tuple[datetime, datetime]:
    """
    Get the upcoming weekend (Saturday-Sunday).
    If today is Saturday or Sunday, returns this weekend.
    """
    current_weekday = current_date.weekday()
    
    if current_weekday == 5:
        saturday = current_date
    elif current_weekday == 6:
        saturday = current_date - timedelta(days=1)
    else:
        days_until_saturday = (5 - current_weekday) % 7
        if days_until_saturday == 0:
            days_until_saturday = 7
        saturday = current_date + timedelta(days=days_until_saturday)
    
    sunday = saturday + timedelta(days=1)
    return saturday, sunday

def get_next_weekend(current_date: datetime) -> Tuple[datetime, datetime]:
    """
    Get "next weekend" - the weekend FOLLOWING the upcoming one.
    Example: If today is Friday Jan 2, 2026:
    - Upcoming weekend = Jan 3-4
    - Next weekend = Jan 10-11
    """
    upcoming_saturday, _ = get_upcoming_weekend(current_date)
    next_saturday = upcoming_saturday + timedelta(days=7)
    next_sunday = next_saturday + timedelta(days=1)
    return next_saturday, next_sunday

def get_weekend_with_offset(current_date: datetime, base: str, weeks_offset: int) -> Tuple[datetime, datetime]:
    """
    Get a weekend with a weeks offset from a base weekend.
    
    Args:
        current_date: The reference date (usually today)
        base: "upcoming" or "next" - which weekend to start from
        weeks_offset: Number of weeks to add (can be 0)
    
    Returns:
        Tuple of (saturday, sunday) dates
    """
    if base == "next":
        base_saturday, _ = get_next_weekend(current_date)
    else:
        base_saturday, _ = get_upcoming_weekend(current_date)
    
    target_saturday = base_saturday + timedelta(weeks=weeks_offset)
    target_sunday = target_saturday + timedelta(days=1)
    return target_saturday, target_sunday

def parse_relative_weekend(text: str, current_date: Optional[datetime] = None) -> Optional[Tuple[str, str]]:
    """
    Parse relative weekend expressions and return date range.
    
    Supported patterns:
    - "this weekend" -> upcoming weekend
    - "next weekend" -> the weekend after the upcoming one
    - "1 week from next weekend" / "a week from next weekend" -> next weekend + 1 week
    - "2 weeks from next weekend" -> next weekend + 2 weeks
    - "1 week from this weekend" -> upcoming weekend + 1 week
    
    Args:
        text: The text containing the relative date expression
        current_date: Optional reference date (defaults to today)
    
    Returns:
        Tuple of (start_date, end_date) as YYYY-MM-DD strings, or None if no match
    """
    if current_date is None:
        current_date = datetime.now()
    
    text_lower = text.lower().strip()
    
    pattern_weeks_from = r'(\d+|a|one)\s*weeks?\s*from\s*(next|this)\s*weekend'
    match = re.search(pattern_weeks_from, text_lower)
    if match:
        weeks_str = match.group(1)
        if weeks_str in ('a', 'one'):
            weeks_offset = 1
        else:
            weeks_offset = int(weeks_str)
        
        base = match.group(2)
        saturday, sunday = get_weekend_with_offset(current_date, base, weeks_offset)
        return saturday.strftime("%Y-%m-%d"), sunday.strftime("%Y-%m-%d")
    
    if re.search(r'\bnext\s+weekend\b', text_lower):
        saturday, sunday = get_next_weekend(current_date)
        return saturday.strftime("%Y-%m-%d"), sunday.strftime("%Y-%m-%d")
    
    if re.search(r'\bthis\s+weekend\b', text_lower):
        saturday, sunday = get_upcoming_weekend(current_date)
        return saturday.strftime("%Y-%m-%d"), sunday.strftime("%Y-%m-%d")
    
    if re.search(r'\bupcoming\s+weekend\b', text_lower):
        saturday, sunday = get_upcoming_weekend(current_date)
        return saturday.strftime("%Y-%m-%d"), sunday.strftime("%Y-%m-%d")
    
    return None

def parse_relative_date(text: str, current_date: Optional[datetime] = None) -> Optional[str]:
    """
    Parse various relative date expressions.
    
    Supports:
    - Weekend expressions (delegated to parse_relative_weekend)
    - "tomorrow"
    - "next week"
    - "in X days"
    
    Returns:
        Date string or date range as "YYYY-MM-DD" or "YYYY-MM-DD to YYYY-MM-DD"
    """
    if current_date is None:
        current_date = datetime.now()
    
    text_lower = text.lower().strip()
    
    weekend_result = parse_relative_weekend(text, current_date)
    if weekend_result:
        start, end = weekend_result
        return f"{start} to {end}"
    
    if 'tomorrow' in text_lower:
        tomorrow = current_date + timedelta(days=1)
        return tomorrow.strftime("%Y-%m-%d")
    
    if re.search(r'\bnext\s+week\b', text_lower):
        days_until_monday = (7 - current_date.weekday()) % 7
        if days_until_monday == 0:
            days_until_monday = 7
        next_monday = current_date + timedelta(days=days_until_monday)
        next_sunday = next_monday + timedelta(days=6)
        return f"{next_monday.strftime('%Y-%m-%d')} to {next_sunday.strftime('%Y-%m-%d')}"
    
    days_match = re.search(r'in\s+(\d+)\s+days?', text_lower)
    if days_match:
        days = int(days_match.group(1))
        target = current_date + timedelta(days=days)
        return target.strftime("%Y-%m-%d")
    
    return None

def format_date_range(start_date: str, end_date: str) -> str:
    """Format a date range as 'YYYY-MM-DD to YYYY-MM-DD'."""
    return f"{start_date} to {end_date}"
