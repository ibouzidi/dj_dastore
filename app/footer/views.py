from django.shortcuts import render, redirect


def about_us(request):
    context = {}
    return render(request, 'app/footer/about_us.html', context)


def terms_of_service(request):
    context = {}
    return render(request, 'app/footer/terms_of_service.html', context)
