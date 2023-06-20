import re

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from captcha.fields import ReCaptchaField
from account.models import Account, Team, Invitation


class RegistrationForm(UserCreationForm):
	# captcha = ReCaptchaField()
	email = forms.EmailField(max_length=254, help_text='Required. Add a valid email address.')

	class Meta:
		model = Account
		fields = ('email', 'username', 'password1', 'password2', )

	def clean_email(self):
		email = self.cleaned_data['email'].lower()
		try:
			account = Account.objects.exclude(pk=self.instance.pk).get(email=email)
		except Account.DoesNotExist:
			return email
		raise forms.ValidationError('Email "%s" is already in use.' % account)

	def clean_username(self):
		username = self.cleaned_data['username']
		try:
			account = Account.objects.exclude(pk=self.instance.pk).get(username=username)
		except Account.DoesNotExist:
			return username
		raise forms.ValidationError('Username "%s" is already in use.' % username)


class AccountAuthenticationForm(forms.ModelForm):
	password = forms.CharField(label='Password', widget=forms.PasswordInput)

	class Meta:
		model = Account
		fields = ('email', 'password')

	def clean(self):
		if self.is_valid():
			email = self.cleaned_data['email']
			password = self.cleaned_data['password']
			if not authenticate(email=email, password=password):
				raise forms.ValidationError("Invalid login")


class AccountUpdateForm(forms.ModelForm):
	class Meta:
		model = Account
		fields = (
			'first_name',
			'last_name',
			'city', 'phone',
			'number',
			'address',
			'zip',
			'profile_image',
			)

	def clean_email(self):
		email = self.cleaned_data['email'].lower()
		try:
			account = Account.objects.exclude(pk=self.instance.pk).get(email=email)
		except Account.DoesNotExist:
			return email
		raise forms.ValidationError('Email "%s" is already in use.' % account)

	def clean_phone(self):
		phone = self.cleaned_data['phone']
		if not re.match(r'^\+?1?\d{9,15}$',
						phone):  # Adjust the regex as needed
			raise ValidationError(
				"Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")
		return phone

	def clean_username(self):
		username = self.cleaned_data['username']
		if not re.match(r'^[\w.@+-]+$',
						username):  # Django's default validation
			raise ValidationError("Username contains invalid characters.")
		try:
			account = Account.objects.exclude(pk=self.instance.pk).get(
				username=username)
		except Account.DoesNotExist:
			return username
		raise forms.ValidationError(
			'Username "%s" is already in use.' % username)

	def clean_first_name(self):
		first_name = self.cleaned_data['first_name']
		if not re.match(r'^[a-zA-Z]+$',
						first_name):  # Only allows alphabetical characters
			raise ValidationError("First name must only contain letters.")
		return first_name

	def clean_last_name(self):
		last_name = self.cleaned_data['last_name']
		if not re.match(r'^[a-zA-Z]+$',
						last_name):  # Only allows alphabetical characters
			raise ValidationError("Last name must only contain letters.")
		return last_name

	def save(self, commit=True):
		account = super(AccountUpdateForm, self).save(commit=False)
		current_user = Account.objects.get(pk=self.instance.pk)

		account.username = current_user.username
		account.email = current_user.email

		account.first_name = self.cleaned_data['first_name']
		account.last_name = self.cleaned_data['last_name']
		account.address = self.cleaned_data['address']
		account.phone = self.cleaned_data['phone']
		account.city = self.cleaned_data['city']
		account.number = self.cleaned_data['number']
		account.zip = self.cleaned_data['zip']
		account.profile_image = self.cleaned_data['profile_image']

		if commit:
			account.save()
		return account


class AddMemberForm(forms.ModelForm):
	password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
	password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput)

	class Meta:
		model = Account
		fields = ['username', 'email']

	def clean_password2(self):
		password1 = self.cleaned_data.get('password1')
		password2 = self.cleaned_data.get('password2')

		if password1 and password2 and password1 != password2:
			raise ValidationError("Passwords don't match")

		return password2

	def save(self, commit=True):
		user = super().save(commit=False)
		user.set_password(self.cleaned_data['password1'])

		if commit:
			user.save()

		return user


class AddTeamForm(forms.ModelForm):
	class Meta:
		model = Team
		fields = ['team_name', 'team_id']

	def clean_team_id(self):
		team_id = self.cleaned_data.get('team_id').lower()
		if not re.match(r'^[a-z0-9_-]+$', team_id):
			raise forms.ValidationError(
				'Team ID should only contain lowercase letters, numbers, '
				'underscores, and hyphens.')
		if Team.objects.filter(team_id=team_id).exists():
			raise forms.ValidationError(
				'A team with this identifier already exists.')
		return team_id

	def clean_team_name(self):
		team_name = self.cleaned_data.get('team_name')
		if not re.match(r'^[a-zA-Z0-9\s]+$', team_name):
			raise forms.ValidationError(
				'Team name should only contain letters, numbers, and spaces.')
		return team_name


# class InvitationForm(forms.ModelForm):
# 	class Meta:
# 		model = Invitation
# 		fields = ['email']
#
# 	def clean_email(self):
# 		email = self.cleaned_data.get('email')
# 		return email.lower()
