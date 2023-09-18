from django.utils import translation
from django.conf import settings


class LangBasedOnUrlMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_request(self, request):
        if hasattr(request, 'session'):
            active_session_lang = request.session.get(translation.LANGUAGE_SESSION_KEY)
            if active_session_lang == request.LANGUAGE_CODE:
                return

            if any(request.LANGUAGE_CODE in language for language in settings.LANGUAGES):
                translation.activate(request.LANGUAGE_CODE)
                request.session[translation.LANGUAGE_SESSION_KEY] = request.LANGUAGE_CODE
