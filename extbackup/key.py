from cryptography.fernet import Fernet
from pathlib import Path
from django.conf import settings

# key = Fernet.generate_key()

# with open('mykey.key','wb') as mykey:
#  mykey.write(key)
BASE_DIR = Path(__file__).resolve().parent.parent
mykey = BASE_DIR / 'mykey.key'
with open(str(mykey), 'rb') as mykey:
    key = mykey.read()


