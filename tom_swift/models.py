import logging

from django.db import models

from tom_common.models import EncryptableModelMixin, EncryptedProperty

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class SwiftProfile(EncryptableModelMixin, models.Model):
    """User Profile for the TOMToolkit Swift Facility

    The swifttools.swift_too.TOO object requires a username and "shared secret".
    These  are available from the PSU Swift Missions Operation Ceenter target of
    opportunity web page. (https://www.swift.psu.edu/toop/too.php).

    NOTE: Your "shared secret" is distinct from your password. When you create
    an account, you'll provide a username and password. After you create your
    account, you can get your "shared secret".

    We only need the User's Swift username and shared_secret. So, those are
    the fields of the SwiftProfile model.
    """
    swift_username = models.CharField(
        max_length=255,
        null=True, blank=True,
        verbose_name='Swift Username')

    _swift_shared_secret = models.BinaryField(null=True, blank=True)
    swift_shared_secret = EncryptedProperty('_swift_shared_secret')
