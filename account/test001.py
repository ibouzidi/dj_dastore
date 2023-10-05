import os
from unittest import TestCase
from account.models import Account
from faker import Faker
from random import randrange
import random
import time


class AccountFactory(TestCase):

    @staticmethod
    def make_random_password(allowed_chars='abcdefghijklmnopqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789'):
        # Generate a random password using the specified length and allowed characters
        random_password = ''.join(random.choice(allowed_chars) for _ in range(12))
        print(random_password)
        return random_password

        # Generate a random password of length 12 characters

    @classmethod
    def gen_user_test(cls, val):
        accountest = Account()
        fake = Faker()
        accountest.password = AccountFactory.make_random_password()

        accountest.email = str(val)+fake.email()
        accountest.username = str(val)+fake.user_name()
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
        # my_timezone = 'Europe/Paris'
        # my_tz = pytz.timezone(my_timezone)
        # start_date = datetime(2023, 1, 1, tzinfo=my_tz)
        # end_date = datetime(2023, 12, 31, tzinfo=my_tz)
        # accountest.last_request_timestamp = fake.date_time_between(start_date=start_date, end_date=end_date)
        # accountest.last_request_timestamp =  #non géré par appli
        print("username:", accountest.username)
        return accountest

    def test_account(self):
        ifin = int(input("Enter number of entries to generate: "))
        self.temps_debut = time.time()
        for i in range(ifin):
            account = AccountFactory.gen_user_test(i)
            account.save()
        temps_ecoule = time.time() - self.temps_debut
        print(f"Temps écoulé pour le test : {temps_ecoule} secondes")
