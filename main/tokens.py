from django.conf import settings
from django.utils.http import base36_to_int, int_to_base36
from django.utils.crypto import constant_time_compare, salted_hmac
from datetime import datetime, time
from django.contrib.auth.tokens import PasswordResetTokenGenerator
import six
class TokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return (
            six.text_type(user.pk) + six.text_type(timestamp) +
            six.text_type(user.is_email_verified)
        )

    def check_token(self, user, token):
        """
        Check that a password reset token is correct for a given user.
        """
        timedout = False
        if not (user and token):
            return False, timedout
        # Parse the token
        try:
            ts_b36, _ = token.split("-")
            legacy_token = len(ts_b36) < 4
        except ValueError:
            return False, timedout

        try:
            ts = base36_to_int(ts_b36)
        except ValueError:
            return False, timedout


        if not constant_time_compare(self._make_token_with_timestamp(user, ts), token):
            if not constant_time_compare(
                self._make_token_with_timestamp(user, ts, legacy=True),
                token,
            ):
                return False, timedout

        now = self._now()
        if legacy_token:
            ts *= 24 * 60 * 60
            ts += int((now - datetime.combine(now.date(), time.min)).total_seconds())

        # Check the timestamp is within limit.
        if (self._num_seconds(now) - ts) > settings.PASSWORD_RESET_TIMEOUT:
            timedout = True
            return False, timedout

        return True, timedout

generate_token = TokenGenerator()
