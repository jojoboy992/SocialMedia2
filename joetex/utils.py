from datetime import timedelta
from django.utils import timezone

def time_since_creation(created_at):
    now = timezone.now()
    diff = now - created_at

    if diff < timedelta(seconds=1):
        return "just now"
    elif diff < timedelta(minutes=1):
        seconds = diff.seconds
        return f"{seconds}s ago" if seconds > 1 else "1s ago"
    elif diff < timedelta(hours=1):
        minutes = diff.seconds // 60
        return f"{minutes}m ago" if minutes > 1 else "1m ago"
    elif diff < timedelta(days=1):
        hours = diff.seconds // 3600
        return f"{hours}h ago" if hours > 1 else "1h ago"
    elif diff < timedelta(weeks=1):
        days = diff.days
        return f"{days}d ago" if days > 1 else "1d ago"
    elif diff < timedelta(weeks=52):
        weeks = diff.days // 7
        return f"{weeks}w ago" if weeks > 1 else "1w ago"
    else:
        years = diff.days // 365
        return f"{years}y ago" if years > 1 else "1y ago"
    
