from django.contrib.sessions.models import Session
from django.utils import timezone, translation


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


class SingleSessionMiddleware:
    """
    Enforce one active session per user at a time.

    When a user logs in on a new device/browser, all their previous sessions
    are invalidated (logged out). This prevents concurrent logins from
    multiple devices.

    How it works:
    1. On each request, if the user is authenticated, we store the current
       session key in the user's profile (or a dedicated field).
    2. If the stored session key doesn't match the current request's session,
       it means the user logged in elsewhere — we invalidate THIS session.
    3. On login, we delete all OTHER sessions for this user.

    Skips: anonymous users, API requests with JWT (no session), admin static files.
    """

    # Paths to skip (health checks, static files, API with JWT)
    SKIP_PATHS = ("/api/v1/health/", "/static/", "/favicon.ico")

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip for non-authenticated users or paths we don't care about
        if not hasattr(request, "user") or not hasattr(request, "session"):
            return self.get_response(request)

        if any(request.path.startswith(p) for p in self.SKIP_PATHS):
            return self.get_response(request)

        # Only enforce for authenticated users with session-based auth
        if request.user.is_authenticated and request.session.session_key:
            self._enforce_single_session(request)

        return self.get_response(request)

    def _enforce_single_session(self, request):
        """
        Ensure only one session per user. The LATEST login wins.
        """
        from core.models import Profile

        try:
            profile = Profile.objects.filter(user=request.user).first()
            if not profile:
                return

            current_session_key = request.session.session_key

            if not profile.active_session_key:
                # First login — just store the session key
                Profile.objects.filter(pk=profile.pk).update(
                    active_session_key=current_session_key
                )
            elif profile.active_session_key != current_session_key:
                # Different session detected — this means user logged in from another device.
                # The OTHER device has the "active" session. THIS session is the old one.
                # Flush THIS session (force logout on this device).
                request.session.flush()
        except Exception:
            # Never let session enforcement crash the app
            pass


class SingleSessionLoginSignal:
    """
    Call this after a successful login to register the new session
    and invalidate all previous sessions for the user.

    Usage in login view or signal:
        SingleSessionLoginSignal.on_login(request, user)
    """

    @staticmethod
    def on_login(request, user):
        """
        Called after successful login. Deletes all other sessions for this user
        and stores the new session key in the user's profile.
        """
        from core.models import Profile

        try:
            # Ensure session is created
            if not request.session.session_key:
                request.session.save()

            new_session_key = request.session.session_key

            profile = Profile.objects.filter(user=user).first()
            if not profile:
                return

            old_session_key = profile.active_session_key

            # Delete the old session from the DB (force logout on other device)
            if old_session_key and old_session_key != new_session_key:
                Session.objects.filter(session_key=old_session_key).delete()

            # Store the new active session
            Profile.objects.filter(pk=profile.pk).update(
                active_session_key=new_session_key
            )
        except Exception:
            # Never let this crash the login flow
            pass
