from unittest import TestCase
from log.models import Log
from faker import Faker
import time
import random
from datetime import datetime, timedelta
from django.utils import timezone


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

        # Générez une date aléatoire dans les 7 derniers jours
        days_in_past = random.randint(1, 7)
        random_date = timezone.now() - timedelta(days=days_in_past)
        print(random_date)
        logtest.date_open = random_date
        return logtest

    def test_log(self):
        ifin = int(input("Enter number of entries to generate: "))
        self.temps_debut = time.time()
        for i in range(ifin):
            log = LogFactory.gen_user_logs()
            log.save()
        temps_ecoule = time.time() - self.temps_debut
        print(f"Temps écoulé pour le test : {temps_ecoule} secondes")

