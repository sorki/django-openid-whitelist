from django.db import models
from django.utils.translation import ugettext_lazy as _


#{{{ to support DjangoOpenIDStore
class Nonce(models.Model):
    server_url = models.CharField(max_length=2047)
    timestamp = models.IntegerField()
    salt = models.CharField(max_length=40)

    def __unicode__(self):
        return u"Nonce: %s, %s" % (self.server_url, self.salt)


class Association(models.Model):
    server_url = models.TextField(max_length=2047)
    handle = models.CharField(max_length=255)
    secret = models.TextField(max_length=255) # Stored base64 encoded
    issued = models.IntegerField()
    lifetime = models.IntegerField()
    assoc_type = models.TextField(max_length=64)

    def __unicode__(self):
        return u"Association: %s, %s" % (self.server_url, self.handle)
#}}}


# if there is TimeStampedModel available use it
# - useful to keep track of changes
try:
    from django_extensions.db.models import TimeStampedModel
    default_model = TimeStampedModel
except ImportError:
    default_model = models.Model


class Whitelisted(default_model):
    issuer = models.CharField(max_length=400,
            verbose_name=_('Issuers OpenID'),
            help_text=_('Your, already whitelisted OpenID'))
    target = models.CharField(max_length=400,
            verbose_name=_('Whitelisted OpenID'),
            help_text=_('OpenID to whitelist'))
    note = models.CharField(max_length=255, blank=True,
            verbose_name=_('Note about whitelisted OpenID'),
            help_text=_('Name, e-mail or any other identifier of the person '
                'whose OpenID is going to be whitelisted (for possible identification and removal)'))
    no_further = models.BooleanField(
            verbose_name=_('Disallow further whitelisting'),
            help_text=_('Whitelisted OpenID can\'t be used to whitelist another '
                'openid'))
    temporary = models.BooleanField(
            verbose_name=_('Whitelist temporary'), 
            help_text=_('Whitelisted OpenID will expire after specified time'))
    expire = models.DateTimeField(null=True, blank=True,
            verbose_name=_('Expiration time and date'),
            help_text=_('Effective only if whitelisted temporary'))

    class Meta:
        verbose_name = _('Whitelisted OpenID')
        verbose_name_plural = _('Whitelisted OpenID\'s')

    def __unicode__(self):
        return self.target
