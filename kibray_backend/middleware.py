from django.utils import translation


class LanguageQueryMiddleware:
    """
    Allow overriding language via ?lang=xx for API and WebSocket handshake.
    Should be placed before LocaleMiddleware.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        lang = request.GET.get("lang") or request.headers.get("X-Language")
        if lang:
            translation.activate(lang)
            request.LANGUAGE_CODE = translation.get_language()
        response = self.get_response(request)
        return response
