import django_filters as dj_filter
from .models import Log
from django import forms


class LogFilter(dj_filter.FilterSet):
    user = dj_filter.CharFilter(
        label='User',
        lookup_expr='icontains',
        widget=forms.TextInput(
            attrs={'class': 'form-control form-form shadow-none '
                            'td-margin-bottom-5 textarea_custom',
                   'placeholder': 'Search by user'}))
    CHOICES_APPLI = (
        ('ACCOUNTS', 'ACCOUNTS'),
        ('BACKUP', 'BACKUP'),
        ('FOLDER', 'FOLDER'),
        ('TEAM', 'TEAM'),
    )
    CHOICES_ACTION = (
        ('CREATE', 'CREATE'),
        ('DELETE', 'DELETE'),
        ('UPDATE', 'UPDATE'),
        ('LOGIN', 'LOGIN'),
        ('LOGOUT', 'LOGOUT'),
    )
    appli = dj_filter.ChoiceFilter(
        empty_label='All Appli', choices=CHOICES_APPLI,
        widget=forms.Select(
            attrs={'class': 'form-control form-form shadow-none '
                            'td-margin-bottom-5 textarea_custom'}))
    action = dj_filter.ChoiceFilter(
        empty_label='All Action', choices=CHOICES_ACTION,
        widget=forms.Select(
            attrs={'class': 'form-control form-form shadow-none '
                            'td-margin-bottom-5 textarea_custom'}))
    description = dj_filter.CharFilter(
        label='Description',
        lookup_expr='icontains',
        widget=forms.TextInput(
            attrs={'class': 'form-control form-form shadow-none '
                            'td-margin-bottom-5 textarea_custom',
                   'placeholder': 'Search by text'}))
    date_open = dj_filter.DateRangeFilter(
        label='Open date',
        empty_label='Always',
        widget=forms.Select(
            attrs={'class': 'form-control form-form shadow-none '
                            'td-margin-bottom-5 textarea_custom'}))
    start_date = dj_filter.DateFilter(
        field_name="date_open",
        label='From',
        lookup_expr='date__gte',
        widget=forms.DateInput(
            attrs={'class': 'form-control form-form shadow-none '
                            'td-margin-bottom-5 textarea_custom',
                   'name': 'start_date', 'placeholder': 'Search by date (From)'}))
    end_date = dj_filter.DateFilter(
        field_name="date_open",
        label='To',
        lookup_expr='date__lte',
        widget=forms.DateInput(
            attrs={'class': 'form-control form-form shadow-none '
                            'td-margin-bottom-5 textarea_custom',
                   'name': 'end_date', 'placeholder': 'Search by date (To)'}))

    class Meta:
        model = Log
        fields = ['user', 'action', 'appli', 'description', 'date_open']
