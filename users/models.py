from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    send_email = models.BooleanField(default=False)

    @receiver(post_save, sender=User)
    def create_user_profile(sender, instance, created, **kwargs):
        if created:
            Profile.objects.create(user=instance)

    @receiver(post_save, sender=User)
    def save_user_profile(sender, instance, **kwargs):
        instance.profile.save()

    @classmethod
    def param_exists(cls, param: str, value) -> bool:
        """
        Check if there is a User in db who has
        a <param> set to <value>.
        Usage:
        * Profile.param_exists('email', 'alice@yaboo.net')
        """
        try:
            dct = {param: value}
            User.objects.get(**dct)
        except User.DoesNotExist:
            return False
        except Exception:
            raise
        else:
            return True
