from django.core.files.storage import FileSystemStorage


def save_avatar(request, avatar):
    fss = FileSystemStorage()
    file = fss.save(
        f'{request.user.username}_avatar.{avatar.name.split(".")[-1]}',
        avatar
        )
    request.user.profile.avatar = fss.url(file)
    request.user.profile.save()


def update_email(request, email: str) -> bool:
    if email == request.user.email:
        return False
    request.user.email = email
    request.user.save()
    return True


def update_alerts(request, alerts: bool) -> bool:
    print(f'Got to update alerts. Alerts: {alerts}')
    if request.user.profile.send_email == alerts:
        print('Alerts not updated')
        return False
    request.user.profile.send_email = alerts
    request.user.profile.save()
    print('Alerts updated')
    return True
