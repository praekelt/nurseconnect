from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from phonenumber_field.formfields import PhoneNumberField

from wagtail.contrib.settings.context_processors import SettingsProxy
from wagtail.wagtailcore.models import Site

ZATEL_REG = r"^((?:\+27|27)|0)[\s-]?(\d{2})[\s-]?(\d{3})[\s-]?(\d{4})[\s]*$"
INT_PREFIX = "+27"


class RegistrationForm(forms.Form):
    username = PhoneNumberField(
        required=False,
        widget=forms.TextInput(
            attrs={
                "placeholder": _("eg. 0821234567"),
                "class": "Form-input",
                "for": "mobilenum"
            }
        ),
        label=_("Mobile Number")
    )

    password = forms.RegexField(
        regex=r"^\w+$",
        widget=forms.PasswordInput(
            attrs={
                "required": True,
                "render_value": False,
                "type": "password",
                "placeholder": _("Enter Password"),
                "class": "Form-input",
                "for": "pword"
            }
        ),
        min_length=4,
        error_messages={
            "invalid": _(
                "Your password must contain any alphanumeric "
                "combination of 4 or more characters."
            ),
        },
        label=_("Password")
    )

    confirm_password = forms.RegexField(
        regex=r"^\w+$",
        widget=forms.PasswordInput(
            attrs={
                "required": True,
                "render_value": False,
                "type": "password",
                "placeholder": _("Re-enter password"),
                "class": "Form-input",
                "for": "pwordconf"
            }
        ),
        min_length=4,
        error_messages={
            "invalid": _(
                "Your password must contain any alphanumeric "
                "combination of 4 or more characters."
            ),
        },
        label=_("Confirm password")
    )

    terms_and_conditions = forms.BooleanField(
        required=True,
        error_messages={
            "invalid": _(
                "Please accept the T&amp;Cs "
                "in order to complete the registration"
            )
        },
        # widget=forms.RadioSelect(
        #     attrs={
        #         "class": "Form-choiceInput",
        #         "for": "checkbox1",
        #         "type": "checkbox",
        #         "name": "checkboxes",
        #         "id": "checkbox1"
        #     }
        # ),
        label=_("Accept the Terms of Use")
    )

    def __init__(self, *args, **kwargs):
        questions = kwargs.pop("questions")
        super(RegistrationForm, self).__init__(*args, **kwargs)
        site = Site.objects.get(is_default_site=True)
        settings = SettingsProxy(site)
        profile_settings = settings["profiles"]["UserProfilesSettings"]

        # Security questions fields are created dynamically.
        # This allows any number of security questions to be specified
        for index, question in enumerate(questions):
            self.fields["question_%s" % index] = forms.CharField(
                label=_(str(question)),
                widget=forms.TextInput(
                    attrs={
                        "max_length": 150,
                        "class": "Form-input",
                        "placeholder": "Enter " + str(question).lower(),
                        "for": "sq" + str(index)
                    }
                )
            )
            self.fields["question_%s" % index].required = (
                profile_settings.show_security_question_fields and
                profile_settings.security_questions_required
            )

    def security_questions(self):
        return [
            self[name] for name in filter(
                lambda x: x.startswith('question_'), self.fields.keys()
            )
            ]

    def clean_username(self):
        username = self.cleaned_data["username"]
        username = username.raw_input

        # if username and username[0] == "0":
        #     self.cleaned_data["username"] = \
        #         INT_PREFIX + username[1:len(username)]

        if User.objects.filter(
            username__iexact=self.cleaned_data["username"]
        ).exists():
            raise forms.ValidationError(_("Username already exists."))

        return self.cleaned_data["username"]

    def clean(self):
        password = self.cleaned_data.get("password", None)
        confirm_password = self.cleaned_data.get("confirm_password", None)
        if (password and confirm_password and
                (password == confirm_password)):
            return self.cleaned_data
        else:
            raise forms.ValidationError(_("Passwords do not match."))


class EditProfileForm(forms.Form):
    first_name = forms.CharField(
        required=False,
        label=_("First Name"),
        widget=forms.TextInput(
            attrs={
                "placeholder": _("Name"),
                "readonly": "true",
                "class": "Form-input"
            }
        ),
        max_length=30,
    )

    last_name = forms.CharField(
        required=False,
        label=_("Surname"),
        widget=forms.TextInput(
            attrs={
                "placeholder": _("Surname"),
                "readonly": "true",
                "class": "Form-input"
            }
        ),
        max_length=30
    )

    username = PhoneNumberField(
        required=False,
        widget=forms.TextInput(
            attrs={
                "placeholder": _("Username"),
                "readonly": "true",
                "class": "Form-input"
            }
        ),
    )

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request")
        super(EditProfileForm, self).__init__(*args, **kwargs)
        if self.request.user.first_name:
            self.fields["first_name"].initial = self.request.user.first_name
        else:
            self.fields["first_name"].initial = "Anonymous"

        if self.request.user.last_name:
            self.fields["last_name"].initial = self.request.user.last_name
        else:
            self.fields["last_name"].initial = "Anonymous"

        self.fields["username"].intial = self.request.user.username

    def clean_username(self):
        username = self.cleaned_data["username"]
        self.cleaned_data["username"] = username.raw_input

        if not self.request.user.username == self.cleaned_data["username"]:
            if User.objects.filter(
                username__iexact=self.cleaned_data["username"]
            ).exists():
                self.add_error(None, "Username already exists.")

        return self.cleaned_data["username"]

    def set_initial(self):
        if self.request.user.first_name:
            self.fields["first_name"].initial = self.request.user.first_name
        else:
            self.fields["first_name"].initial = "Anonymous"

        if self.request.user.last_name:
            self.fields["last_name"].initial = self.request.user.last_name
        else:
            self.fields["last_name"].initial = "Anonymous"

        self.fields["username"].intial = self.request.user.username

        return self

    def enable_fields(self):
        self.fields["first_name"].widget.attrs["readonly"] = False
        self.fields["last_name"].widget.attrs["readonly"] = False
        self.fields["username"].widget.attrs["readonly"] = False

        return self

    def disable_fields(self):
        self.fields["first_name"].widget.attrs["readonly"] = True
        self.fields["last_name"].widget.attrs["readonly"] = True
        self.fields["username"].widget.attrs["readonly"] = True

        return self


class ProfilePasswordChangeForm(forms.Form):
    old_password = forms.RegexField(
        regex=r"^\w+$",
        widget=forms.PasswordInput(
            attrs={
                "required": True,
                "render_value": False,
                "type": "password",
                "placeholder": _("Old Password"),
                "readonly": True,
                "class": "Form-input"
            }
        ),
        min_length=4,
        error_messages={
            "invalid": _(
                "Your password must contain any alphanumeric "
                "combination of 4 or more characters."
            ),
        },
        label=_("Old Password")
    )

    new_password = forms.RegexField(
        regex=r"^\w+$",
        widget=forms.PasswordInput(
            attrs={
                "required": True,
                "render_value": False,
                "type": "password",
                "placeholder": _("New Password"),
                "readonly": True,
                "class": "Form-input"
            }
        ),
        min_length=4,
        error_messages={
            "invalid": _(
                "Your password must contain any alphanumeric "
                "combination of 4 or more characters."
            ),
        },
        label=_("New Password")
    )

    confirm_password = forms.RegexField(
        regex=r"^\w+$",
        widget=forms.PasswordInput(
            attrs={
                "required": True,
                "render_value": False,
                "type": "password",
                "placeholder": _("Confirm Password"),
                "readonly": True,
                "class": "Form-input"
            }
        ),
        min_length=4,
        error_messages={
            "invalid": _(
                "Your password must contain any alphanumeric "
                "combination of 4 or more characters."
            ),
        },
        label=_("Confirm Password")
    )

    def clean(self):
        new_password = self.cleaned_data.get("new_password", None)
        confirm_password = self.cleaned_data.get("confirm_password", None)
        if (new_password and confirm_password and
                (new_password == confirm_password)):
            return self.cleaned_data
        else:
            raise forms.ValidationError(_("New passwords do not match."))

    def enable_fields(self):
        self.fields["old_password"].widget.attrs["readonly"] = False
        self.fields["new_password"].widget.attrs["readonly"] = False
        self.fields["confirm_password"].widget.attrs["readonly"] = False

        return self

    def disable_fields(self):
        self.fields["old_password"].widget.attrs["readonly"] = True
        self.fields["new_password"].widget.attrs["readonly"] = True
        self.fields["confirm_password"].widget.attrs["readonly"] = True


class ForgotPasswordForm(forms.Form):
    username = PhoneNumberField(required=False)

    def clean_username(self):
        username = self.cleaned_data["username"]
        username = username.raw_input

        if username and username[0] == "0":
            self.cleaned_data["username"] = \
                INT_PREFIX + username[1:len(username)]

        return self.cleaned_data["username"]

    def __init__(self, *args, **kwargs):
        questions = kwargs.pop("questions")
        super(ForgotPasswordForm, self).__init__(*args, **kwargs)

        for index, question in enumerate(questions):
            self.fields["question_%s" % index] = forms.CharField(
                label=_(str(question)),
                widget=forms.TextInput(
                    attrs=dict(
                        required=True,
                        max_length=150,
                    )
                )
            )


class ResetPasswordForm(forms.Form):
    username = forms.CharField(
        widget=forms.HiddenInput()
    )

    token = forms.CharField(
        widget=forms.HiddenInput()
    )

    password = forms.RegexField(
        regex=r"^\w+$",
        widget=forms.PasswordInput(
            attrs={
                "required": True,
                "render_value": False,
                "type": "password",
                "placeholder": _("Enter Password"),
                "class": "Form-input"
            }

        ),
        min_length=4,
        error_messages={
            "invalid": _(
                "Your password must contain any alphanumeric "
                "combination of 4 or more characters."
            ),
        },
        label=_("Password")
    )

    confirm_password = forms.RegexField(
        regex=r"^\w+$",
        widget=forms.PasswordInput(
            attrs={
                "required": True,
                "render_value": False,
                "type": "password",
                "placeholder": _("Confirm Password"),
                "class": "Form-input"
            }
        ),
        min_length=4,
        error_messages={
            "invalid": _(
                "Your password must contain any alphanumeric "
                "combination of 4 or more characters."
            ),
        },
        label=_("Confirm Password")
    )


class NurseconnectAuthenticationForm(AuthenticationForm):
    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username and username[0] == "0":
            username = INT_PREFIX + username[1:len(username)]

        if username and password:
            self.user_cache = authenticate(username=username,
                                           password=password)
            if self.user_cache is None:
                raise forms.ValidationError(
                    self.error_messages['invalid_login'],
                    code='invalid_login',
                    params={'username': self.username_field.verbose_name},
                )
            else:
                self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data
