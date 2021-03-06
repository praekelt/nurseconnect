"""
Tests for the registration process.

The registration process is broken down into three steps:
1) MSISDN: for userame and password
2) Security questions: getting answers to be used for password recovery
3) Clinic code: For obtaining the user's clinic code
"""
import mock

from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.test import TestCase
from django.test.client import Client


from molo.core.models import SiteLanguageRelation, Languages, Main
from molo.core.tests.base import MoloTestCaseMixin
from molo.profiles.models import (
    SecurityQuestion, UserProfilesSettings, SecurityQuestionIndexPage)

from nurseconnect.models import UserProfile
from nurseconnect import forms


class PerfectRegistrationTestCase(TestCase, MoloTestCaseMixin):
    """
    Tests for the 3 step registration process.
    Successful flow through the steps is as follows
    MSISDN -> Security Questions -> Clinic code
    """
    def setUp(self):
        self.mk_main()
        self.client = Client()

        self.main = Main.objects.all().first()
        self.language_setting = Languages.objects.create(
            site_id=self.main.get_site().pk)
        self.english = SiteLanguageRelation.objects.create(
            language_setting=self.language_setting,
            locale='en',
            is_active=True)

        self.profile_settings = UserProfilesSettings.for_site(
            self.main.get_site())
        self.profile_settings.show_security_question_fields = True
        self.profile_settings.security_questions_required = True
        self.profile_settings.save()

        # security question
        self.security_index = SecurityQuestionIndexPage(
            title='Security Questions',
            slug='security_questions',
        )
        self.main.add_child(instance=self.security_index)
        self.security_index.save()
        # create a few security questions
        self.q1 = SecurityQuestion(
            title="How old are you?",
            slug="how-old-are-you",
        )
        self.security_index.add_child(instance=self.q1)
        self.q1.save()

    @mock.patch("nurseconnect.views.get_clinic_code")
    def test_it(self, clinic_code_mock):
        clinic_code_mock.return_value = "388624", "Test", "gp Test"
        data = {
            "username": "0820000000",
            "password": "1234",
            "confirm_password": "1234",
            "terms_and_conditions": True,
        }
        url = reverse("user_register_msisdn")

        # post msisdn step
        response = self.client.post(url, data, follow=True)

        # user object not created right away, confirm that is the case
        count = User.objects.filter().count()
        self.assertEqual(count, 0)

        url = reverse("user_register_security_questions")
        self.assertRedirects(response, url)

        # post security question step
        url = reverse("user_register_security_questions")
        self.client.get(reverse("user_register_security_questions"))

        question_data = {"question_0": "answer"}
        response = self.client.post(url, question_data, follow=True)

        url = reverse("user_register_clinic_code")
        self.assertRedirects(response, url)

        # post clinic code step
        clinic_data = {"clinic_code": "000000"}
        url = reverse("user_register_clinic_code")
        response = self.client.post(url, clinic_data, follow=True)
        self.assertContains(response, "Your clinic code is valid")

        count = User.objects.all().count()
        self.assertEqual(count, 1)


class MSISDNTestCase(MoloTestCaseMixin, TestCase):
    """
    Verify the correct error messages for the
    MSISDN step
    """

    def setUp(self):
        self.mk_main()
        self.client = Client()
        self.user = User.objects.create_user(
            username="+27821231234",
            password="0000")

    def test_existing_username_raises_error(self):
        response = self.client.post(reverse("user_register_msisdn"), {
            "username": "+27821231234",
            "password": "0000",
            "confirm_password": "0000",
            "terms_and_conditions": True,
        })
        self.assertContains(response, "Username already exists")

    def test_invalid_username_raises_error(self):
        # Username is expected to be a South African number,
        # normalised to +27 country code
        response = self.client.post(reverse("user_register_msisdn"), {
            "username": "wrong username",
            "confirm_password": "1234"
        })
        self.assertFormError(
            response, "form", "username",
            [u"Please enter a valid South African cellphone number."]
        )

    def test_password_with_non_alphanumneric_chars_raise_error(self):
        response = self.client.post(reverse("user_register_msisdn"), {
            "password": "wrong$$$"
        })
        self.assertFormError(
            response, "form", "password",
            [u"Your password must contain any alphanumeric "
             u"combination of 4 or more characters."]
        )


class ClinicCodeTestCase(MoloTestCaseMixin, TestCase):
    def setUp(self):
        self.mk_main()
        self.client = Client()

    @mock.patch("nurseconnect.views.get_clinic_code")
    def test_invalid_clinic_code_raises_error(self, clinic_code_mock):
        clinic_code_mock.return_value = None
        response = self.client.post(
            reverse("user_register_clinic_code"),
            {
                "clinic_code": "000000",
            },
            follow=True
        )
        self.assertContains(response, "Clinic code does not exist")


class EditPersonalDetailsTestCase(MoloTestCaseMixin, TestCase):
    def setUp(self):
        self.client = Client()
        self.mk_main()
        self.user = User.objects.create_user("+27811231234", password="1234")
        self.client.login(username="+27811231234", password="1234")

    def test_personal_details_fields_are_editable(self):
        response = self.client.get(
            reverse("edit_my_profile", kwargs={"edit": "edit-settings"})
        )

        # EditProfileForm fields should be editable
        self.assertEqual(
            response.context["settings_form"].fields[
                "first_name"].widget.attrs["readonly"],
            False
        )

    @mock.patch("nurseconnect.views.get_clinic_code")
    def test_personal_details_can_be_changed_in(self, clinic_code_mock):
        clinic_code_mock.return_value = "388624", "Test", "gp Test"
        response = self.client.post(
            reverse("edit_my_profile", kwargs={"edit": "edit-settings"}),
            {
                "settings_form-first_name": "First",
                "settings_form-last_name": "Last",
                "settings_form-clinic_code": "388624",
                "settings_form-username": "+27811231234",
            },
            follow=True
        )
        self.assertContains(response, "Profile successfully updated")

    @mock.patch("nurseconnect.views.get_clinic_code")
    def test_username_can_be_changed(self, clinic_code_mock):
        clinic_code_mock.return_value = "388624", "Test", "gp Test"
        response = self.client.post(
            reverse("edit_my_profile", kwargs={"edit": "edit-settings"}),
            {
                "settings_form-clinic_code": "388624",
                "settings_form-username": "+27811231233",
            },
            follow=True
        )
        self.assertContains(response, "Username successfully updated")

    def test_invalid_username_raises_error(self):
        response = self.client.post(
            reverse("edit_my_profile", kwargs={"edit": "edit-settings"}),
            {
                "settings_form-username": "39311231233",
            },
            follow=True
        )
        self.assertContains(
            response,
            "Please enter a valid South African cellphone number"
        )

    @mock.patch("nurseconnect.views.get_clinic_code")
    def test_clinic_code_can_be_changed(self, clinic_code_mock):
        clinic_code_mock.return_value = "388624", "Test", "gp Test"
        self.client.post(
            reverse("edit_my_profile", kwargs={"edit": "edit-settings"}),
            {
                "settings_form-username": "+27811231233",
                "settings_form-clinic_code": "000111"
            },
            follow=True
        )
        # TODO: save the changed clinic code

    @mock.patch("nurseconnect.views.get_clinic_code")
    def test_invalid_clinic_code_raises_error(self, clinic_code_mock):
        clinic_code_mock.return_value = None
        response = self.client.post(
            reverse("edit_my_profile", kwargs={"edit": "edit-settings"}),
            {
                "settings_form-username": "+27811231233",
                "settings_form-clinic_code": "000111"
            },
            follow=True
        )
        self.assertContains(response, "Clinic code does not exist")


class EditPasswordTestCase(MoloTestCaseMixin, TestCase):
    def setUp(self):
        self.client = Client()
        self.mk_main()
        self.user = User.objects.create_user("+27811231234", password="1234")
        self.client.login(username="+27811231234", password="1234")
        self.profile = UserProfile.objects.filter(user=self.user).first()
        self.profile.site = self.site
        self.profile.migrated_username = "+27811231234"
        self.profile.save()

    def test_password_fields_are_editable(self):
        response = self.client.get(
            reverse("edit_my_profile", kwargs={"edit": "edit-password"})
        )

        # ProfilePasswordChangeForm fields should be editable
        self.assertEqual(
            response.context["profile_password_change_form"].fields[
                "old_password"].widget.attrs["readonly"],
            False
        )

    def test_passwords_can_be_changed(self):
        self.client.get(
            reverse("edit_my_profile", kwargs={"edit": "edit-password"})
        )
        response = self.client.post(
            reverse("edit_my_profile", kwargs={"edit": "edit-password"}),
            {
                "profile_password_change_form-old_password": "1234",
                "profile_password_change_form-new_password": "0000",
                "profile_password_change_form-confirm_password": "0000"
            },
            follow=True
        )
        self.assertEqual(response.request["PATH_INFO"], "/view/myprofile/")
        self.assertContains(response, "Password successfully changed!")

    def test_unmatching_passwords_raises_error(self):
        response = self.client.post(
            reverse("edit_my_profile", kwargs={"edit": "edit-password"}),
            {
                "profile_password_change_form-old_password": "1234",
                "profile_password_change_form-new_password": "0000",
                "profile_password_change_form-confirm_password": "0012"
            },
            follow=True
        )
        self.assertContains(response, "New passwords do not match.")

    def test_incoreect_old_password_raises_error(self):
        response = self.client.post(
            reverse("edit_my_profile", kwargs={"edit": "edit-password"}),
            {
                "profile_password_change_form-old_password": "0000",
                "profile_password_change_form-new_password": "0000",
                "profile_password_change_form-confirm_password": "0000"
            },
            follow=True
        )
        self.assertContains(response, "The old password is incorrect")

    def test_forgot_password_without_security_questions(self):
        self.client.logout()
        data = {'username': self.user.username}
        response = self.client.post(reverse('forgot_password'), data=data)
        self.assertFalse(self.user.profile.security_question_answers.exists())

        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            reverse("molo.profiles:reset_password") in response.url)


class ViewProfileTestCase(MoloTestCaseMixin, TestCase):
    def setUp(self):
        self.client = Client()
        self.mk_main()

    def test_redirect_to_log_in_if_user_not_logged_in(self):
        # Redirects to login page if user is not logged in
        response = self.client.get(reverse("view_my_profile"))
        redirect_url = reverse("auth_login") + "?next=/view/myprofile/"
        self.assertRedirects(response, redirect_url)

    def test_both_forms_are_displayed(self):
        # EditProfileForm and ProfilePasswordChangeForm should both be rendered
        self.user = User.objects.create_user(
            username="+27811231234",
            password="1234"
        )
        self.client.login(username="+27811231234", password="1234")

        response = self.client.get(
            reverse("view_my_profile"),
        )
        self.assertIsInstance(
            response.context["settings_form"],
            forms.EditProfileForm
        )
        self.assertIsInstance(
            response.context["profile_password_change_form"],
            forms.ProfilePasswordChangeForm
        )

        # Fields in both forms should be read-only
        self.assertEqual(
            response.context["settings_form"].fields[
                "first_name"].widget.attrs["readonly"],
            True
        )
        self.assertEqual(
            response.context["profile_password_change_form"].fields[
                "old_password"].widget.attrs["readonly"],
            True
        )
