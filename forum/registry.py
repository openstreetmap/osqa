from forum.modules import ui, get_modules_script
from django.utils.translation import ugettext as _
from django.utils.encoding import smart_unicode
from django.core.urlresolvers import reverse
from django.template.defaultfilters import slugify

from forum.models import User
from forum.templatetags.extra_tags import get_score_badge
from forum.utils.html import cleanup_urls
from forum import settings


try:
    from django.template import get_templatetags_modules
    modules_template_tags = get_modules_script('templatetags')
    django_template_tags = get_templatetags_modules()

    for m in modules_template_tags:
        django_template_tags.append(m.__name__)
except:
    pass

ui.register(ui.HEADER_LINKS,
            ui.Link(_('faq'), ui.Url('faq'), weight=400, name='FAQ'),
            ui.Link(_('about'), ui.Url('about'), weight=300, name='ABOUT'),

#            ui.Link(
#                    visibility=ui.Visibility.ANONYMOUS,
#                    text=_('login'),
#                    url=lambda u, c: reverse('auth_signin'),
#                    weight=200, name='LOGIN'),
            ui.Link(
                    visibility=ui.Visibility.AUTHENTICATED,
                    text=_('logout'),
                    url=lambda u, c: reverse('logout'),
                    weight=200, name='LOGOUT'),
            ui.Link(
                    visibility=ui.Visibility.AUTHENTICATED,
                    text=lambda u, c: smart_unicode(u.username),
                    url=lambda u, c: u.get_profile_url(),
                    post_code=lambda u, c: get_score_badge(u),
                    weight=100, name='ACCOUNT'),

            ui.Link(
                    visibility=ui.Visibility.SUPERUSER,
                    text=_('administration'),
                    url=lambda u, c: reverse('admin_index'),
                    weight=0, name='ADMINISTRATION')

)

class SupportLink(ui.Link):
    def can_render(self, context):
        return bool(settings.SUPPORT_URL)


ui.register(ui.FOOTER_LINKS,
            ui.Link(
                    text=_('contact'),
                    url=lambda u, c: settings.CONTACT_URL and settings.CONTACT_URL or "%s?next=%s" % (reverse('feedback'), cleanup_urls( c['request'].path)),
                    weight=400),
            SupportLink(_('support'), settings.SUPPORT_URL, attrs={'target': '_blank'}, weight=300),
            ui.Link(_('privacy'), ui.Url('privacy'), weight=200),
            ui.Link(_('faq'), ui.Url('faq'), weight=100),
            ui.Link(_('about'), ui.Url('about'), weight=0),
)

class ModerationMenuGroup(ui.AjaxMenuGroup):
    def can_render(self, context):
        return context['user'] != context['viewer'] and super(ModerationMenuGroup, self).can_render(context)

class SuperUserSwitchMenuItem(ui.UserMenuItem):
    def can_render(self, context):
        return context['viewer'].is_siteowner or not context['user'].is_superuser

ui.register(ui.USER_MENU,
            ui.UserMenuItem(
                label=_("edit profile"),
                url=lambda u, c: reverse('edit_user', kwargs={
                    'id': c['user'].id,
                    'slug' : slugify(c['user'].username)
                }),
                span_attrs={'class': 'user-edit'},
                weight=0,
                name='EDIT_PROFILE'
            ),
            ui.UserMenuItem(
                label=_("authentication settings"),
                url=lambda u, c: reverse('user_authsettings', kwargs={'id': c['user'].id}),
                span_attrs={'class': 'user-auth'},
                weight=100,
                name='AUTH_SETTINGS'
            ),
            ui.UserMenuItem(
                label=_("email notification settings"),
                url=lambda u, c: User.objects.get(id=int(c['user'].id)).get_user_subscriptions_url(),
                span_attrs={'class': 'user-subscriptions'},
                weight=200,
                name='EMAIL_SETTINGS'
            ),
            ui.UserMenuItem(
                label=_("other preferences"),
                url=lambda u, c: reverse('user_preferences', kwargs={'id': c['user'].id, 'slug': slugify(c['user'].username)}),
                weight=200,
                name='OTHER_PREFS'
            ),
            ModerationMenuGroup(_("Moderation tools"), items=(
                ui.UserMenuItem(
                    label=lambda u, c: c['user'].is_suspended() and _("withdraw suspension") or _("suspend this user"),
                    url=lambda u, c: reverse('user_suspend', kwargs={'id': c['user'].id}),
                    a_attrs=lambda u, c: {'class': c['user'].is_suspended() and 'ajax-command confirm' or 'ajax-command withprompt'},
                    render_to=lambda u: not u.is_superuser,
                    name='SUSPENSION'
                ),
                ui.UserMenuItem(
                    label=lambda u, c: _("give/take karma"),
                    url=lambda u, c: reverse('user_award_points', kwargs={'id': c['user'].id}),
                    a_attrs=lambda u, c: {'id': 'award-rep-points', 'class': 'ajax-command withprompt'},
                    span_attrs={'class': 'user-award_rep'},
                    render_to=lambda u: not u.is_suspended(),
                    name='KARMA'
                ),
                ui.UserMenuItem(
                    label=lambda u, c: c['user'].is_staff and _("remove moderator status") or _("grant moderator status"),
                    url=lambda u, c: reverse('user_powers', kwargs={'id': c['user'].id, 'action':c['user'].is_staff and 'remove' or 'grant', 'status': 'staff'}),
                    a_attrs=lambda u, c: {'class': 'ajax-command confirm'},
                    span_attrs={'class': 'user-moderator'},
                    name='MODERATOR'
                ),
                SuperUserSwitchMenuItem(
                    label=lambda u, c: c['user'].is_superuser and _("remove super user status") or _("grant super user status"),
                    url=lambda u, c: reverse('user_powers', kwargs={'id': c['user'].id, 'action':c['user'].is_superuser and 'remove' or 'grant', 'status': 'super'}),
                    a_attrs=lambda u, c: {'class': 'ajax-command confirm'},
                    span_attrs={'class': 'user-superuser'},
                    name='SUPERUSER'
                ),
            ), visibility=ui.Visibility.SUPERUSER, weight=500, name='MOD_TOOLS')
)
