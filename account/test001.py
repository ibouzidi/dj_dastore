from unittest import TestCase
from account.models import Account
from faker import Faker
from random import randrange
import random


class AccountFactory(TestCase):

    @staticmethod
    def make_random_password(allowed_chars='abcdefghijklmnopqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789'):
        # Generate a random password using the specified length and allowed characters
        random_password = ''.join(random.choice(allowed_chars) for _ in range(12))
        print(random_password)
        return random_password

        # Generate a random password of length 12 characters

    @classmethod
    def gen_user_test(cls):
        accountest = Account()
        fake = Faker()
        accountest.password = AccountFactory.make_random_password()
        accountest.email = fake.email()
        accountest.username = fake.user_name()
        accountest.date_joined = fake.date()
        accountest.first_name = fake.first_name()
        accountest.last_name = fake.last_name()
        accountest.phone = fake.phone_number()
        accountest.address = fake.street_address()
        accountest.number = randrange(1, 42)
        accountest.city = fake.city()
        accountest.zip = fake.postcode()
        accountest.last_login = fake.date()
        boolean_choice = [False, True]
        accountest.is_admin = random.choice(boolean_choice)
        accountest.is_active = random.choice(boolean_choice)
        accountest.is_staff = random.choice(boolean_choice)
        accountest.is_superuser = random.choice(boolean_choice)
        accountest.profile_image = "dastore/default_user_icon.png"
        accountest.storage_usage = randrange(0, 40)
        accountest.storage_limit = randrange(40, 50)
        plan_id_options = ['price_1NGGoCJWztZpQABxESSIiJeD', 'price_1NGGepJWztZpQABxWl2gvIDC', 'price_1NJ0fPJWztZpQABxqF2rr8f6']
        accountest.plan_id = random.choice(plan_id_options)
        accountest.request_counts = randrange(0, 10)
        accountest.last_request_timestamp = fake.date()

        print("username:", accountest.username)
        return accountest

    def test_account(self):
        for _ in range(5):
            account = AccountFactory.gen_user_test()
            account.save()

