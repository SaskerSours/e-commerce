from wagtail.contrib.modeladmin.options import ModelAdmin, ModelAdminGroup, modeladmin_register
from allauth.socialaccount.models import SocialApp


class SocialAppAdmin(ModelAdmin):
    model = SocialApp
    menu_icon = 'placeholder'
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_display = ('name', 'provider')


class SocialAuthGroup(ModelAdminGroup):
    menu_label = 'Social Accounts'
    menu_icon = 'users'
    menu_order = 1200
    items = (SocialAppAdmin,)


modeladmin_register(SocialAuthGroup)
