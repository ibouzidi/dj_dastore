import random
import time
from account.models import Account
from extbackup.models import File


def generate_files(num_files, username):
    # Get user object
    user = Account.objects.get(username=username)

    # Generate random filenames
    for i in range(num_files):
        # Get current time as timestamp
        timestamp = time.strftime("%Y%m%d_%H%M%S", time.gmtime())
        filename = f'save_{timestamp}_{username}.zip'
        # Store file in the model
        File.objects.create(file=filename, user=user)

# def generate_files(num_files):
#     # Get user objects
#     users = Account.objects.all()
#
#     # Generate random filenames
#     for i in range(num_files):
#         # Get current time as timestamp
#         timestamp = time.strftime("%Y%m%d_%H%M%S", time.gmtime())
#         username = random.choice(users)
#         filename = f'save_{timestamp}_{username}.zip'
#         # Store file in the model
#         File.objects.create(file=filename, user=username)
