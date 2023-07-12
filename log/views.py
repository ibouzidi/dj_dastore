import json

from django.contrib.auth.decorators import user_passes_test
from django.db.models import Count
from django.db.models.functions import TruncDate
from django.shortcuts import render, redirect
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from dj_dastore.decorator import dev
from log.filters import LogFilter
from log.models import Log
from datetime import timedelta
import datetime
from django.http import HttpResponse
import time
import csv


@user_passes_test(dev)
def dashboard(request):
    """
    A function used  to generate data information needed to create a
     dashboard.
    :param request:Contains information about current user.
    :return:Returns a render function with 3 arguments:
        1.A str 'requests' contains information about current user.
        2.An url that will be used to generate the access page.
        3.A dictionary that contains 5 keys:
            3.1.'list_items' contains all the items from a queryset.
            3.2.'count' contains the number of items.
            3.3.'chart_label' contains a list of the last 7 days
             (ex:['Nov/01', 'Nov/02', ...]).
            3.4.'chart_data' contains a list of the number items by day.
            3.5.'offdatelog' contains all the items from a queryset
             filtered 'date_close' is earlier than today and state
              open.
    """
    list_items = Log.objects.all().order_by('-id')[:10]
    count = {'log_number': ['log Number', Log.objects.count()]}
    label, chart_data = list(), list()

    last_seven_days_logs = (
        Log.objects.filter(
            date_open__date__gte=timezone.now() - timedelta(days=7))
            .annotate(date=TruncDate('date_open'))
            .values('date')
            .annotate(count=Count('id'))
            .order_by('date')
    )

    for item in last_seven_days_logs:
        label.append(item['date'].strftime("%b/%d"))
        chart_data.append(item['count'])

    chart_datasets = [{
        'data': chart_data,
        'label': 'Nb log',
        'borderColor': 'purple',  # replace this with your desired color
        'fill': 'false'
    }]

    context = {
        'list_items': list_items,
        'count': count,
        'label': label,
        'chart_datasets_json': json.dumps(chart_datasets),
    }

    return render(request, 'log/log_dashboard.html', context)


@user_passes_test(dev)
def log_list(request):
    """
    A function used to return all items with pagination.
    :param request:Contains information about current user.
    :return:Returns a render function with 3 arguments:
        1.A str 'requests' contains information about current user.
        2.An url that will be used to generate the access page.
        3.A dictionary that contains 1 key:
            3.1.'list_items' contains all the items from a queryset.
    """

    page = request.GET.get('page', 1)
    eventlog = Log.objects.all().order_by('-date_open')
    filtered_qs = LogFilter(request.GET, queryset=eventlog)

    # Check if 'all' is in the request
    if 'all' in request.GET:
        # Show all items in one page
        paginator = Paginator(filtered_qs.qs,
                              filtered_qs.qs.count())
    else:
        paginator = Paginator(filtered_qs.qs, 15)  # Show 15 items per page

    try:
        list_items = paginator.page(page)
    except PageNotAnInteger:
        list_items = paginator.page(1)
    except EmptyPage:
        list_items = paginator.page(paginator.num_pages)

    return render(request,
                  'log/log_list.html',
                  {"list_items": list_items, 'filtered_qs': filtered_qs})


@user_passes_test(dev)
def log_select(request, pk=None):
    """
    A function used to return information about a specified item in URL
     argument.
    :param request:Contains information about current user.
    :param pk:Primary key of item used in queryset.
    :return:Returns a render function with 3 arguments:
        1.A str 'requests' contains information about current user.
        2.An url that will be used to generate the access page.
        3.A dictionary that contains 1 key:
            3.1.'item' contains information of the specified item.
    """
    try:
        item = Log.objects.get(pk=pk)
        description_parts = item.description.split(
            ', ') if item.description else []
        return render(request,
                      'log/log_select.html',
                      {'item': item, 'description_parts': description_parts})
    except ObjectDoesNotExist:
        messages.error(request, f'log {pk} does not exist')
        return redirect('log:log_dashboard')


@user_passes_test(dev)
def log_export(request):
    """
    A function used to generate csv file containing the information
    of the requested response.
    :param request:Contains information about current user.
    :return:Returns a response containing a csv file.
    """
    logs = Log.objects.all()
    rslt_filter = LogFilter(request.GET, queryset=logs).qs
    if rslt_filter.exists():
        response = HttpResponse(content_type='text/csv')
        timestr = time.strftime("%d_%m_%Y-%H%M%S")
        response['Content-Disposition'] = 'attachement; ' \
                                          'filename=dastore_log_export_' \
                                          + timestr + '.csv'
        writer = csv.writer(response)
        writer.writerow(['User',
                         'Action',
                         'Appli',
                         'Description',
                         'date_open'])
        for log in rslt_filter.values('user',
                                      'action',
                                      'appli',
                                      'description',
                                      'date_open'):
            writer.writerow([log["user"],
                             log["action"],
                             log["appli"],
                             log["description"],
                             log["date_open"]])
        return response
    else:
        messages.info(request, "Cannot export empty data")
        return redirect('log:log_list')


@user_passes_test(dev)
def log_delete(request):
    """
    A function used to delete all the logs older than 3 month.
    Is executed on server's crontab:
    0 0 * * * curl http://127.0.0.1:80/log/delete/
    """
    # TODO : create cron user and cron job
    Log.objects.filter(
        date_open__lte=datetime.datetime.now() - timedelta(days=90)).delete()
    return HttpResponse("logs older than 90 days has been deleted")
