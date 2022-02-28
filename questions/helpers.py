from datetime import datetime, timezone
from django.core.exceptions import ObjectDoesNotExist


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


def save_tags(tags, question, tag_model):
    if not tags:
        return
    for tag in tags:
        tag = tag.strip()
        try:
            old_tag = tag_model.objects.get(title=tag)
        except ObjectDoesNotExist:
            pass
        else:
            old_tag.questions.add(question)
            continue
        t = tag_model.objects.create(title=tag)
        t.questions.add(question)
