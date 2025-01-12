from django.utils.translation import ungettext, ugettext as _
from django.core.urlresolvers import reverse
from django.db.models import F
from django.contrib import messages
from forum.models.action import ActionProxy
from forum.models import Award, Badge, ValidationHash, User
from forum import settings, REQUEST_HOLDER
from forum.settings import APP_SHORT_NAME
from forum.utils.mail import send_template_email

class UserJoinsAction(ActionProxy):
    verb = _("joined")

    def repute_users(self):
        self.repute(self.user, int(settings.INITIAL_REP))

    def process_action(self):
        hash = ValidationHash.objects.create_new(self.user, 'email', [self.user.email])
        send_template_email([self.user], "auth/welcome_email.html", {'validation_code': hash})

    def describe(self, viewer=None):
        return _("%(user)s %(have_has)s joined the %(app_name)s Q&A community") % {
        'user': self.hyperlink(self.user.get_absolute_url(), self.friendly_username(viewer, self.user)),
        'have_has': self.viewer_or_user_verb(viewer, self.user, _('have'), _('has')),
        'app_name': APP_SHORT_NAME,
        }

class UserLoginAction(ActionProxy):
    verb = _("logged in")

    def describe(self, viewer=None):
        return _("%(user)s %(have_has)s logged in") % {
            'user' : self.hyperlink(self.user.get_absolute_url(), self.friendly_username(viewer, self.user)),
            'have_has': self.viewer_or_user_verb(viewer, self.user, _('have'), _('has')),
        }

class EmailValidationAction(ActionProxy):
    verb = _("validated e-mail")

    def repute_users(self):
        self.repute(self.user, int(settings.REP_GAIN_BY_EMAIL_VALIDATION))

    def process_action(self):
        self.user.email_isvalid = True
        self.user.save()

    def describe(self, viewer=None):
        return _("%(user)s %(have_has)s validated the e-mail %(email)s") % {
        'user': self.hyperlink(self.user.get_absolute_url(), self.friendly_username(viewer, self.user)),
        'have_has': self.viewer_or_user_verb(viewer, self.user, _('have'), _('has')),
        'email' : self.user.email if viewer.is_superuser or viewer.is_staff or viewer == self.user else ""
        }

class EditProfileAction(ActionProxy):
    verb = _("edited profile")

    def describe(self, viewer=None):
        return _("%(user)s edited %(hes_or_your)s %(profile_link)s") % {
        'user': self.hyperlink(self.user.get_absolute_url(), self.friendly_username(viewer, self.user)),
        'hes_or_your': self.viewer_or_user_verb(viewer, self.user, _('your'), _('his')),
        'profile_link': self.hyperlink(self.user.get_absolute_url(), _('profile')),
        }

class BonusRepAction(ActionProxy):
    verb = _("gave bonus")

    def process_data(self, value, affected):
        self._value = value
        self._affected = affected


    def repute_users(self):
        self.repute(self._affected, self._value)

        if self._value < 0:
            messages.info(REQUEST_HOLDER.request, _("You have penalized %s in %s reputation points.") % (self._affected, self._value) +
                    '<br />%s' % self.extra.get('message', ''))

    def describe(self, viewer=None):
        value = self.extra.get('value', _('unknown'))
        message = self.extra.get('message', '')

        try:
            if int(value) > 0:
                return _("%(user)s awarded an extra %(value)s reputation points to %(users)s: %(message)s") % {
                'user': self.hyperlink(self.user.get_absolute_url(), self.friendly_username(viewer, self.user)),
                'value': value, 'users':self.affected_links(viewer), 'message': message
                }
            else:
                return _("%(user)s penalised %(users)s in %(value)s reputation points: %(message)s") % {
                'user': self.hyperlink(self.user.get_absolute_url(), self.friendly_username(viewer, self.user)),
                'value': value, 'users':self.affected_links(viewer), 'message': message
                }
        except Exception, e:
            return ''

class AwardPointsAction(ActionProxy):
    verb = _("gave reputation points")

    def process_data(self, value, affected):
        self._value = value
        self._affected = affected


    def repute_users(self):
        self.repute(self._affected, self._value)
        self.repute(self.user, -self._value)

    def describe(self, viewer=None):
        value = self.extra.get('value', _('unknown'))

        try:
            if int(value) > 0:
                return _("%(user)s awarded an extra %(value)s reputation points to %(users)s") % {
                'user': self.hyperlink(self.user.get_absolute_url(), self.friendly_username(viewer, self.user)),
                'value': value, 'users':self.affected_links(viewer),
                }
            else:
                return _("%(user)s penalised %(users)s in %(value)s reputation points") % {
                'user': self.hyperlink(self.user.get_absolute_url(), self.friendly_username(viewer, self.user)),
                'value': value, 'users':self.affected_links(viewer),
                }
        except Exception, e:
            return ''

class AwardAction(ActionProxy):
    verb = _("was awarded")

    def process_data(self, badge, trigger):
        self.__dict__['_badge'] = badge
        self.__dict__['_trigger'] = trigger

    def process_action(self):
        badge = self.__dict__['_badge']
        trigger = self.__dict__['_trigger']

        award = Award(user=self.user, badge=badge, trigger=trigger, action=self)
        if self.node:
            award.node = self.node

        award.save()
        award.badge.awarded_count = F('awarded_count') + 1
        award.badge.save()

        if award.badge.type == Badge.GOLD:
            self.user.gold += 1
        if award.badge.type == Badge.SILVER:
            self.user.silver += 1
        if award.badge.type == Badge.BRONZE:
            self.user.bronze += 1

        self.user.save()

    def cancel_action(self):
        award = self.award
        badge = award.badge
        badge.awarded_count = F('awarded_count') - 1
        badge.save()
        award.delete()

    @classmethod
    def get_for(cls, user, badge, node=False):
        try:
            if node is False:
                return Award.objects.get(user=user, badge=badge).action
            else:
                return Award.objects.get(user=user, node=node, badge=badge).action
        except:
            return None

    def describe(self, viewer=None):
        return _("%(user)s %(were_was)s awarded the %(badge_name)s badge") % {
        'user': self.hyperlink(self.user.get_absolute_url(), self.friendly_username(viewer, self.user)),
        'were_was': self.viewer_or_user_verb(viewer, self.user, _('were'), _('was')),
        'badge_name': self.award.badge.name,
        }


class ReportAction(ActionProxy):
    verb = _("suspended")

    def process_data(self, **kwargs):
        self.extra = kwargs
        # message here?


    def process_action(self):

        all_superusers = User.objects.filter(is_superuser=True)


        send_template_email(all_superusers, "notifications/user_reported.html", {
            'reported': self.extra['reported'],
            'user':self.user,
            'message': self.extra['publicmsg']
            }
            )

    def describe(self, viewer=None):

        return _("%(user)s reported %(reported) : %(msg)s") % {
            'user': self.hyperlink(self.user.get_absolute_url(), self.friendly_username(viewer, self.user)),
            'reporter': self.extra.get('reported').username,
            'msg': self.extra.get('publicmsg', _('N/A'))
        }

class SuspendAction(ActionProxy):
    verb = _("suspended")

    def process_data(self, **kwargs):
        self._suspended = kwargs.pop('suspended')
        self.extra = kwargs

    def repute_users(self):
        self.repute(self._suspended, 0)

    def process_action(self):
        self._suspended.is_active = False
        self._suspended.save()

    def cancel_action(self):
        for u in User.objects.filter(reputes__action=self).distinct():
            u.is_active = True
            u._pop_suspension_cache()
            u.save()

    def describe(self, viewer=None):
        if self.extra.get('bantype', 'indefinitely') == 'forxdays' and self.extra.get('forxdays', None):
            suspension = _("for %s days") % self.extra['forxdays']
        else:
            suspension = _("indefinetely")

        return _("%(user)s suspended %(users)s %(suspension)s: %(msg)s") % {
        'user': self.hyperlink(self.user.get_absolute_url(), self.friendly_username(viewer, self.user)),
        'users': self.affected_links(viewer), 'suspension': suspension, 'msg': self.extra.get('publicmsg', _('Bad behaviour'))
        }
