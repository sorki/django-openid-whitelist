from django import forms
from django.utils.translation import ugettext as _
from django.conf import settings

from openid.yadis import xri

from models import Whitelisted

class OpenIDWhitelistForm(forms.ModelForm):
    class Meta:
            model = Whitelisted

    def clean_issuer(self):
        if 'issuer' in self.cleaned_data:
            openid_identifier = self.cleaned_data['issuer']
            if xri.identifierScheme(openid_identifier) == 'XRI' and getattr(
                settings, 'OPENID_DISALLOW_INAMES', False
                ):
                raise forms.ValidationError(_('i-names are not supported'))
            return self.cleaned_data['issuer']

    def clean_target(self):
        if 'target' in self.cleaned_data:
            openid_identifier = self.cleaned_data['target']
            if xri.identifierScheme(openid_identifier) == 'XRI' and getattr(
                settings, 'OPENID_DISALLOW_INAMES', False
                ):
                raise forms.ValidationError(_('i-names are not supported'))
            return self.cleaned_data['target']


