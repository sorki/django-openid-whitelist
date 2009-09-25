OpenID whitelist 
=================

django-white-openid offers an easy way to keep your projects private.

After the installation add your OpenID to the whitelist. With this
OpenID it is possible to add another OpenID. If not disabled,
each whitelisted OpenID can be used to whitelist more IDs.

For example - if there is OpenID A, with A it is possible to add
OpenID B. Then with B it is possible to add another OpenID and so on.

It is pretty intuitive to use this application.

Requirements
-------------

- django >= 1.0
- python-openid

Installation
-------------

- install (for example easy_install django-white-openid)
- install python-openid
- add 'whitelist' to your INSTALLED_APPS
- run syncdb
- include whitelist.urls
(for example -  url(r'^whitelist/', include('whitelist.urls'))
- form then accessible at whitelist/start

Simple form style `whitelist_style.css` included in whitelist/media installation directory.


Usage
------

To verify OpenID use `whitelist-check` and `whitelist-check-json` views.
To add OpenID use `whitelist-start`.
(names in `quotes` are named urls - simply use {% url whitelist-start %} in
your template)

Also check view documentation in django admin.



Optional settings
-------------------

OPENID_TRUST_ROOT
  Trust root for the OpenID Request. 
  Defaults to the base URL of your page.

OPENID_DISALLOW_INAMES
  Disallow personal i-names. Defaults to false


Compatible with
-----------------

TracAuthOpenid
  Add `check_list` and `check_list_key` to your `[openid]` section in
  trac.ini. `check_list` has to point to `whitelist-check-json` view.
  Set `check_list_key` to whatever you like (`openid` for example).
