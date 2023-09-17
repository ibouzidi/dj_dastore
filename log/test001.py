from unittest import TestCase
from log.models import Log
from faker import Faker
import random


class LogFactory(TestCase):

    @classmethod
    def gen_user_logs(cls):
        logtest = Log()
        fake = Faker()
        logtest.user = fake.email()
        appli_id_options = ['ACCOUNTS', 'BACKUP', 'FOLDER', 'TEAM']
        logtest.appli = random.choice(appli_id_options)
        action_id_options = ['CREATE', 'DELETE', 'UPDATE', 'LOGIN', 'LOGOUT']
        logtest.action = random.choice(action_id_options)
        logtest.description = "username :"+fake.user_name()+", First name :"+fake.first_name()+"..."
        logtest.date_open = fake.date()
        print("appli:", logtest.appli)
        return logtest

    def test_log(self):
        for _ in range(5):
            log = LogFactory.gen_user_logs()
            log.save()

