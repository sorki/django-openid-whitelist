from django.contrib import admin
from models import Whitelisted

class WhitelistedItemsAdmin(admin.ModelAdmin):
    list_display = ('target', 'note', 'no_further', 'temporary')


admin.site.register(Whitelisted, WhitelistedItemsAdmin)
