from datetime import datetime, timezone


def get_time_diff(thetime):
    now = datetime.now(timezone.utc)
    delta = now - thetime

    if delta.total_seconds() > 60*60*24*365:  # year
        return f'{round(delta.days / 365)} year(s) ago'
    elif delta.total_seconds() > 60*60*24*30:  # month
        return f'{round(delta.days / 30)} month(s) ago'
    elif delta.total_seconds() > 60*60*24*7:  # week
        return f'{round(delta.days / 7)} week(s) ago'
    elif delta.total_seconds() > 60*60*24:  # day
        return f'{delta.days} day(s) ago'
    elif delta.total_seconds() > 60*60:  # hours
        return f'{round(delta.seconds/60/60)} hour(s) ago'
    elif delta.total_seconds() > 60:  # minutes
        return f'{round(delta.total_seconds() / 60)} minute(s) ago'
    else:
        return 'Just now'
