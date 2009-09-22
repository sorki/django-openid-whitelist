import re
import urllib
from datetime import datetime

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _

from openid.consumer.consumer import (
    Consumer, SUCCESS, CANCEL, FAILURE)
from openid.consumer.discover import DiscoveryFailure
from openid.extensions import sreg

from forms import OpenIDWhitelistForm
from store import DjangoOpenIDStore
from models import Whitelisted


def make_consumer(request):
    """Create an OpenID Consumer object for the given Django request."""
    # Give the OpenID library its own space in the session object.
    session = request.session.setdefault('OPENID', {})
    store = DjangoOpenIDStore()
    return Consumer(session, store)


def render_openid_request(request, openid_request, return_to, trust_root=None):
    """Render an OpenID authentication request."""
    if trust_root is None:
        trust_root = getattr(settings, 'OPENID_TRUST_ROOT',
                             request.build_absolute_uri('/'))

    if openid_request.shouldSendRedirect():
        redirect_url = openid_request.redirectURL(
            trust_root, return_to)
        return HttpResponseRedirect(redirect_url)
    else:
        form_html = openid_request.htmlMarkup(
            trust_root, return_to, form_tag_attrs={'id': 'openid_message'})
        return HttpResponse(form_html, content_type='text/html;charset=UTF-8')


def render_failure(request, message, 
        status=403,
        template='whitelist/fail.html',
        extra_context=None):
    """Render failure template"""

    if extra_context is None: extra_context = {}
    c = RequestContext(request)
    for key, value in extra_context.items():
        if callable(value):
            c[key] = value()
        else:
            c[key] = value

    data = render_to_string(
        template, dict(message=message),
        context_instance=c)
    return HttpResponse(data, status=status)


def parse_openid_response(request):
    """Parse an OpenID response from a Django request."""

    current_url = request.build_absolute_uri()

    consumer = make_consumer(request)
    return consumer.complete(dict(request.REQUEST.items()), current_url)


def start(request, 
        form_class=OpenIDWhitelistForm,
        template_name='whitelist/start.html',
        failure_template_name='whitelist/fail.html',
        success_urlname='whitelist-finish',
        extra_context=None):
    """
    Render the form then render openid request.
    
    After successful OpenID authentication, redirect to ``success_url``.

    It is possible to pre-fill target OpenID using the ``oid`` GET variable.

    **Required arguments**

    None.

    **Optional arguments**

    ``extra_context``
        A dictionary of variables to add to the template context. Any
        callable object in this dictionary will be called to produce
        the end result which appears in the context.

    ``form_class``
        The form class to render.

    ``failure_template``
        A custom failure template, passed to ``render_failure``.

    ``success_url``
        The URL to redirect to after authentication.

    ``template_name``
        A custom template to use.

    **Context:**

    ``form``
        OpenID input form.
        Defaults to OpenIDWhitelistForm (modelform)

    **Template:**
    
        Standard:
        ``whitelist/start.html`` or ``template_name`` keyword argument.

        Failure:
        ``whitelist/fail.html`` or ``failure_template`` keyword argument.

    """


    if extra_context is None: extra_context = {}
    c = RequestContext(request)
    for key, value in extra_context.items():
        if callable(value):
            c[key] = value()
        else:
            c[key] = value


    openid_url = None

    if request.POST:
        frm = form_class(data=request.POST)
        if frm.is_valid():
            openid_url = frm.cleaned_data['issuer']
            request.session['OPENID_WHITELIST_DATA'] = frm.cleaned_data
    else:
        frm = form_class()
        if 'oid' in request.GET:
            data = { 'target' : request.GET['oid'] }
            frm = form_class(initial=data)

    # Invalid or no form data:
    if openid_url is None:
        return render_to_response(template_name, {
                'form': frm,
                }, context_instance=c)

    consumer = make_consumer(request)
    try:
        openid_request = consumer.begin(openid_url)
    except DiscoveryFailure, exc:
        return render_failure(
            request, _('OpenID discovery error: %s') % (str(exc),), status=500,
            template=failure_template_name,
            extra_context=extra_context)

    return_to = request.build_absolute_uri(reverse(success_urlname))
    return render_openid_request(request, openid_request, return_to)


def finish(request,
        template_name='whitelist/finish.html', 
        failure_template_name='whitelist/fail.html',
        extra_context=None):
    """
    Parse OpenID response, check if issuer is valid then add 
    target OpenID to whitelist and render template.

    Also delete expired entries.

    **Required arguments**

    None.

    **Optional arguments**

    ``extra_context``
        A dictionary of variables to add to the template context. Any
        callable object in this dictionary will be called to produce
        the end result which appears in the context.

    ``failure_template``
        A custom failure template, passed to ``render_failure``.

    ``template_name``
        A custom template to use.

    **Context:**

    ``data``
        Dictionary with data used to create and save ``Whitelisted`` object.  
        
    **Template:**
    
        Standard:
        ``whitelist/finish.html`` or ``template_name`` keyword argument.

        Failure:
        ``whitelist/fail.html`` or ``failure_template`` keyword argument.

    """

    # delete temporary & expired items
    # - expired Whitelisted items
    for i in Whitelisted.objects.filter(
            temporary=True,
            expire__lte=datetime.now()):
        i.delete()
    # - expired Nonces & Associations
    DjangoOpenIDStore().cleanup()

    if extra_context is None: extra_context = {}
    openid_response = parse_openid_response(request)
    if not openid_response:
        return render_failure(
            request, _('This is an OpenID relying party endpoint.'),
            template=failure_template_name, 
            extra_context=extra_context)

    if openid_response.status == SUCCESS:
        ''' - important part following
            1. resolve full identifier
            2. check issuers presence in whitelist
            3. add new entry
        '''
        issuer = openid_response.identity_url
        if openid_response.endpoint.canonicalID:
            issuer = openid_response.endpoint.canonicalID
        data = request.session.get('OPENID_WHITELIST_DATA', False)
        data['issuer'] = issuer
        passed = False
        if data:
            if len(Whitelisted.objects.all()) == 0:
                passed = True
                data['target'] = data['issuer']
            else:
                try:
                    Whitelisted.objects.filter(
                            target=issuer,
                            no_further=False).exclude(
                                    temporary=True,
                                    expire__lte=datetime.now())[0]
                    
                    passed = True
                except IndexError:
                    passed = False


        if passed:
            new = Whitelisted(**data)
            new.save()
            c = RequestContext(request)
            for key, value in extra_context.items():
                if callable(value):
                    c[key] = value()
                else:
                    c[key] = value

            return render_to_response(template_name, dict(data=data),
                context_instance=c)
        else:
            return render_failure(
                    request, _('You are not allowed to whitelist'),
                    template=failure_template_name,
                    extra_context=extra_context)

    elif openid_response.status == FAILURE:
        return render_failure(
            request, 'OpenID authentication failed: %s' %
            openid_response.message, template=failure_template_name,
            extra_context=extra_context)
    elif openid_response.status == CANCEL:
        return render_failure(request, 'Authentication cancelled',
                template=failure_template_name,
                extra_context=extra_context)
    else:
        assert False, (
            'Unknown OpenID response type: %r' % openid_response.status)

def check(request, json=False):
    '''
    Check if supplied OpenID is whitelisted.
    First GET variable is used as input.
    If ``json`` is set GET variable name is used in response.
    
        For example:

        ../check?getvar_oid=openid_to_check

        Output:

        ``true`` or ``false``

        Output (json):

        ``{"getvar_oid" : true}``

    **Required arguments**

    None.

    **Optional arguments**

    ``json`` set to True to return JSON response
    '''

 
    result = 'false'

    try:
        get_var, openid = request.GET.items()[0]
    except:
        # nothing to check
        get_var = 'fail'

    try: 
        Whitelisted.objects.filter(
                            target=openid,
                            ).exclude(
                                    temporary=True,
                                    expire__lte=datetime.now())[0]

        result = 'true'
    except:
        # not whitelisted
        pass
    

    if json:
        return HttpResponse('{"%s": %s}' % (get_var, result))
    else:
        return HttpResponse(result)
