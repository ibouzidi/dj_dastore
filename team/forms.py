import re
from django import forms
from django.core.exceptions import ValidationError
from setuptools._entry_points import _

from team.models import Team
from account.models import Account


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

        if self.instance.team_id != team_id and Team.objects.filter(
                team_id=team_id).exists():
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
