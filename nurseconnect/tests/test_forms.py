from django.contrib.auth.models import User
from django.test import TestCase

from molo.core.tests.base import MoloTestCaseMixin
from molo.profiles import models

from nurseconnect import forms


class RegisterFormTestCase(MoloTestCaseMixin, TestCase):
    def setUp(self):
        self.msisdn_form = forms.RegistrationMSISDNForm
        self.security_questions_form = forms.RegistrationSecurityQuestionsForm
        self.clinic_code_form = forms.RegistrationClinicCodeForm
        self.mk_main()
        self.user = User.objects.create_user(
            username="+27791234567",
            password="1234")
        self.question = models.SecurityQuestion(question="What is this?")
        self.clinic_code = "123456"

    def test_register_username_correct(self):
        form_data = {
            "username": "0820000000",
            "password": "1234",
            "confirm_password": "1234",
            "terms_and_conditions": True
        }
        form = self.msisdn_form(
            data=form_data,
        )
        self.assertEqual(form.is_valid(), True)

    def test_register_username_incorrect(self):
        form_data = {
            "username": "Jeyabal#",
            "password": "1234",
            "terms_and_conditions": True

        }
        form = self.msisdn_form(
            data=form_data
        )
        self.assertEqual(form.is_valid(), False)

    def test_register_security_questions_correct(self):
        form_data = {
            "question_0": "answer"

        }
        form = self.security_questions_form(
            data=form_data,
            questions=[self.question, ]
        )
        self.assertEqual(form.is_valid(), True)

    def test_register_clinic_code_correct(self):
        form_data = {
            "clinic_code": "123456"

        }
        form = self.clinic_code_form(
            data=form_data
        )
        self.assertEqual(form.is_valid(), True)

    def test_register_clinic_code_incorrect(self):
        form_data = {
            "clinic_code": "000000"

        }
        form = self.clinic_code_form(
            data=form_data
        )
        self.assertEqual(form.is_valid(), False)

    def test_register_password_incorrect(self):
        form_data = {
            "username": "Jeyabal#",
            "password": "12345",
            "terms_and_conditions": True

        }
        form = self.msisdn_form(
            data=form_data
        )
        self.assertEqual(form.is_valid(), False)

    def test_password_change_incorrect(self):
        form_data = {
            "old_password": "123",
            "new_password": "jey123",
            "confirm_password": "jey123",
        }
        form = forms.ProfilePasswordChangeForm(
            data=form_data,
        )
        self.assertEqual(form.is_valid(), False)

    def test_password_change_correct(self):
        form_data = {
            "old_password": "1234",
            "new_password": "3456",
            "confirm_password": "3456",
        }
        form = forms.ProfilePasswordChangeForm(
            data=form_data,
        )
        self.assertEqual(form.is_valid(), True)

    def test_terms_and_conditions_is_required(self):
        form_data = {
            "username": "test",
            "password": "12345",
        }
        form = self.msisdn_form(
            data=form_data
        )
        self.assertEqual(form.is_valid(), False)


class PasswordRecoveryTestCase(MoloTestCaseMixin, TestCase):
    def setUp(self):
        self.mk_main()
        self.user = User.objects.create_user(
            username="0831231234",
            email="tester@example.com",
            password="tester")

        self.question = models.SecurityQuestion(question="What is this?")
        self.question.save()

    def test_username_and_security_answer(self):
        form_data = {
            "username": "0831231234",
            "question_0": "20"
        }
        form = forms.ForgotPasswordForm(
            data=form_data,
            questions=[self.question, ]
        )
        self.assertEqual(form.is_valid(), True)
