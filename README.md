
# Project DaStore

## Overview
This Django web application provides users with a convenient way to backup and restore their files by enabling file downloads. To support the development and maintenance of the application, a subscription feature has been implemented using dj_stripe and Stripe payment gateway. Users can select a plan, register for it, and proceed to the checkout session where they can securely enter their banking information for payment processing. Upon successful payment confirmation through the Stripe webhook, users gain access to the application's features and can log in.

### Subscription Plans
- **Basic Plan:** Offers essential backup and restore functionality with a moderate storage capacity.
 - **Premium Plan:** Provides enhanced backup and restore features along with increased storage capacity to accommodate more files.
- **Enterprise Plan:** Designed for small and large organizations, the Enterprise plan offers multiple users and a substantial storage capacity. This plan is ideal for teams working collaboratively on file management tasks.
#### Features and Functionality
- **User Registration:** Users can sign up for the application by selecting a subscription plan and completing the registration process.
- **File Backup and Restore:** Users can easily backup and restore their files through the application's intuitive interface.
- **Secure Payment Processing:** Integration with Stripe ensures the security and reliability of payment transactions during the checkout process.
- **Subscription Management:** Users have control over their subscription plans and can make changes or cancel their subscriptions as needed.
- **Enterprise Plan Team Management:** Users subscribed to the Enterprise plan can create, edit, and delete teams within their organization.
- **Team Invitations:** Enterprise plan users can invite others to join their team by sending email invitations containing a registration form.
- **Team Member Registration and Login**: Invited team members can register and subsequently log in to access shared files and collaborate with the team.
- **Limited Team Permissions:** Team members can only manage files and inherit the storage limit set by the team leader at the time of initial subscription. They cannot manage billing details, subscriptions, or overall storage capacity.

This application offers a comprehensive solution for users to securely backup and restore their files, manage subscriptions, and facilitate collaboration within organizations through the Enterprise plan.

## Installation

To set up and configure the Django web application, follow the steps below:

### Prerequisites:
- Python 3.x installed on your system.
- pip package manager.

### Step 1: Clone the Repository

1. Run the following command to clone the repository:
``` git clone https://github.com/lucrem78/dj_dastore.git ```

2. Create and Activate a Virtual Environment (Optional but Recommended)
``` python3 -m venv env ```

3. Activate the virtual environment:
- *For Windows:*
``` env\Scripts\activate ```
- *For macOS/Linux:*
``` source env/bin/activate ```

### Step 2: Install Dependencies
1. Install the required dependencies using pip:
```pip install -r requirements.txt```

### Step 3: Configure the Database
1. Create an environment file:

Create a new file in the project's root directory and name it .env.
Open the .env file in a text editor.
Configure the database settings:

2. Add the following configuration variables to the .env file:
~~~~
Copy code
SECRET_KEY=******
DEBUG=True
ALLOWED_HOSTS=*
RUN_ENVIRONMENT=local # prod or test
DB_HOST=127.0.0.1
DB_NAME=local
DB_USER=local
DB_PASSWORD=local
DB_CHARSET=utf8
~~~~

Make sure to replace ***** in the SECRET_KEY variable with a secure and unique secret key for your application. 

3.Use this command in order to **generate a secret key** :
~~~~
manage.py shell -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
~~~~

Update the values of the database variables **(DB_HOST, DB_NAME, DB_USER, DB_PASSWORD, DB_CHARSET)** according to your database configuration. For example, if you are using a local development database with default settings, you can set them as shown above.

4. Save the changes to the .env file.

The .env file will be used by the application to load the environment-specific configuration, including the database settings, secret key, and other sensitive information. It is important to keep this file secure and not share it publicly.

Note: Make sure you have the python-dotenv package installed `(pip install python-dotenv) ` to enable reading the environment variables from the .env file in your Django application.

5. Run migrations
This project uses Django migrations to set up the database. Please follow **in order** the steps below:

- Run the migrations for the `account` app first:
~~~~
python manage.py makemigrations account
python manage.py migrate account
~~~~
- Then run migrations for all other apps:
~~~~
python manage.py makemigrations
python manage.py migrate
~~~~

Please note that the `account` app must be migrated first due to its dependencies on other apps.


### Step 4: Generate a Symmetric Key for Cryptography
To generate a symmetric key for cryptography using Fernet from the cryptography library, follow these steps:

1. Open a Python interpreter.

Run the following command to generate the `key` :
~~~~
from cryptography.fernet import Fernet
from pathlib import Path

Fernet.generate_key()
~~~~

2. Save your key in the new file called `mykey.key` at the root directory:
- mykey.key file:

 `w-uNJmXQb3Qdzwn4svStvp8AePQj76PhCfZA05HWjvk=`

### Step 5: Set Up Stripe Account

Create an account on Stripe if you don't have one already.
Obtain your Stripe API keys (Publishable Key and Secret Key) from the Stripe Dashboard.

### Step 6: Configure Stripe Integration

1. Open the base.py file located in the project's directory dj_dastore/settings/.
2. In the STRIPE_API_KEY setting, replace the placeholder with your Stripe Secret Key.
3. (OPTIONAL) Set the `STRIPE_SUCCESS_URL` and `STRIPE_CANCEL_URL` settings to the appropriate URLs in your application where users will be redirected after successful payment or cancellation.
4. Save the changes.


### Step 7: Start the Development Server

Run the following command to start the development server:
Copy code
python manage.py runserver
The application will be accessible at http://localhost:8000/ in your web browser.

1. Synchronise your data from Stripe Dashboard to your database :
   - Enter:
     - `python manage.py djstripe_sync_models` (need to run in background)
     
Note : You need to add a API KEY in STRIPE API KEY in Admin Panel:
- Need the name : `STRIPE_TEST_SECRET_KEY`
- The API Key : `sk_test_51H*********` (you can find it in the settings file.)

2. Create an entry Point:

Note : In order the checkout the payement in TEST MODE, You will need to start an entry point with WEBHOOKS :
- Open a terminal in your root directory
- Enter `stripe login`
- Enter `stripe listen --forward-to localhost:8000/stripe/webhook/`
- Now your listening to the WEBHOOKS.

**You have successfully installed and configured the Django web application. Customize the application's templates, views, and models to suit your specific requirements.**

Enjoy :)

