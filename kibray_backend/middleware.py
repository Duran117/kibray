from django.contrib.sessions.models import Session
from django.shortcuts import redirect
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
    SKIP_PATHS = ("/api/v1/health/", "/static/", "/favicon.ico", "/login/")

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
            stale = self._enforce_single_session(request)
            if stale:
                # Session was flushed — redirect to login immediately
                from django.conf import settings
                return redirect(getattr(settings, "LOGIN_URL", "/login/"))

        return self.get_response(request)

    def _enforce_single_session(self, request):
        """
        Ensure only one session per user. The LATEST login wins.
        
        Logic: on_login() stores the NEW session key in the profile.
        Here we check: does the stored key match THIS request's key?
        - If no stored key → store it (first visit after login).
        - If stored key matches → fine, continue.
        - If stored key differs → THIS session is stale, flush it.
        
        Returns True if the session was stale and flushed, False otherwise.
        """
        from core.models import Profile

        try:
            profile = Profile.objects.filter(user=request.user).first()
            if not profile:
                return False

            current_session_key = request.session.session_key
            stored_key = profile.active_session_key

            # Treat 'None' (string), empty string, and NULL the same
            if not stored_key or stored_key == 'None':
                # No active session recorded — register THIS session
                Profile.objects.filter(pk=profile.pk).update(
                    active_session_key=current_session_key
                )
                return False
            elif stored_key != current_session_key:
                # A DIFFERENT session is the active one.
                # Verify the active session actually exists before flushing this one.
                from django.contrib.sessions.models import Session
                active_session_exists = Session.objects.filter(
                    session_key=stored_key
                ).exists()
                
                if active_session_exists:
                    # The other session is truly active → flush THIS (old) session
                    request.session.flush()
                    return True
                else:
                    # The stored session expired/was deleted → THIS is now the active one
                    Profile.objects.filter(pk=profile.pk).update(
                        active_session_key=current_session_key
                    )
                    return False
        except Exception:
            # Never let session enforcement crash the app
            pass
        return False


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
