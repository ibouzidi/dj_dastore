# from django.utils import translation
# from django.conf import settings
#
#
# class LangBasedOnUrlMiddleware:
#     def __init__(self, get_response):
#         self.get_response = get_response
#
#     def __call__(self, request):
#         # Get the language from the request
#         lang = request.GET.get('lang')
#
#         # Set the language
#         if lang:
#             translation.activate(lang)
#             request.LANGUAGE_CODE = lang
#
#         # Process the request
#         response = self.get_response(request)
#
#         return response
