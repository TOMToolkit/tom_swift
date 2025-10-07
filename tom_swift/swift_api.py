"""This module is intended to hold the Swift ToO API specific information
- see https://www.swift.psu.edu/too_api/  for documentation
- see https://gitlab.com/DrPhilEvans/swifttools  for source code

Notes:
  - swifttools.swift_too.TOO and swifttools.swift_too.Swift_TOO are both
    <class 'swifttools.swift_too.swift_toorequest.Swift_TOORequest'>
  - more
  - more notes
"""
import logging
from typing import Tuple

from django.core.exceptions import ImproperlyConfigured
from django.contrib.auth.models import User

from requests.exceptions import ConnectionError

from swifttools.swift_too import TOO, TOORequests, Resolve
from swifttools.swift_too.api_resolve import Swift_Resolve

from tom_targets.models import Target

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class SwiftAPI:
    """This is the interface between the SwiftFacility and the swifttools.swift_too classes.

    This keeps the SwiftFacility class focused on implementing its superclass methods and separates
    the SwiftFacility from the swifttools.swift_too classes.
    """
    def __init__(self, debug=True):
        self.too = TOO()
        self.too_request = TOORequests()
        self.credentials_set = False

    def set_credentials(self, username: str, shared_secret: str):
        """
        Set Swift credentials for API access.

        This replaces the settings-based credential approach with user-specific credentials.

        :param username: Swift username
        :param shared_secret: Swift shared secret (not password)
        """
        self.too.username = username
        self.too.shared_secret = shared_secret
        self.credentials_set = True
        logger.info(f'Swift API credentials set for username: {username}')

    def get_credentials(self, user: User) -> Tuple[str, str]:
        """Returns the currently set credentials.

        Credentials must have been previously set via set_credentials().
        This method no longer attempts to retrieve credentials from settings.
        """
        if not self.credentials_set:
            raise ImproperlyConfigured(
                'Swift API credentials have not been set. '
                'Call set_credentials() before accessing credentials.'
            )
        return self.too.username, self.too.shared_secret

    def resolve_target(self, target: Target):
        """
        """
        logger.info(f'resolve_target: {target.name}')

        try:
            resolved_target: Swift_Resolve = Resolve(target.name)  # this calls the API
            # <class 'swifttools.swift_too.api_resolve.Swift_Resolve'>
        except ConnectionError as err:
            logger.error(f'ConnectionError: {err}')
            resolved_target = None

        logger.info(f'resolved_target: {resolved_target}')
        logger.debug(f'type(resolved_target): {type(resolved_target)}')
        logger.debug(f'dir(resolved_target): {dir(resolved_target)}')
        if resolved_target is not None:
            for key, value in resolved_target.__dict__.items():
                logger.debug(f'resolved_target.{key}): {value}')

        return resolved_target


# define OTHER_CHOICE so it can be used consistently and tested against
SWIFT_OTHER_CHOICE = 'Other (please specify)'

#
# Urgency
#
SWIFT_URGENCY_CHOICES = [
    (0, 'Immediately (Urgency 0)'),
    (1, 'Within 4 hours (Wakes up the Swift Observatory Duty Scientist).'),
    (2, 'Within 24 hours'),
    (3, 'Days to a week'),  # default
    (4, 'Week to a month'),
]

SWIFT_TARGET_CLASSIFICATION_CHOICES = [
    ('AGN', 'AGN'),
    ('Be Binary System', 'Be Binary System'),
    ('Comet or Asteroid', 'Comet or Asteroid'),
    ('Dwarf Nova', 'Dwarf Nova'),
    ('GRB', 'GRB'),
    ('Nova', 'Nova'),
    ('Pulsar', 'Pulsar'),
    ('Supernova', 'Supernova'),
    ('Tidal Disruption Event', 'Tidal Disruption Event'),
    ('X-Ray Transient', 'X-Ray Transient'),
    (SWIFT_OTHER_CHOICE, SWIFT_OTHER_CHOICE),
]


#
# Observation Types
#
# Note that:
# >>> TOO().obs_types
# ['Spectroscopy', 'Light Curve', 'Position', 'Timing']
#
def get_observation_type_choices():
    """Returns a list of tuples for the observation type choices.

    Since the TOO() object has property describing the valid observation types,
    use that to create the choices list of tuples (e.g. [('Spectroscopy', 'Spectroscopy'), ('Light Curve',
    'Light Curve'), ...]).
    """
    observation_type_choices = []
    for obs_type in TOO().obs_types:
        observation_type_choices.append((obs_type, obs_type))
    return observation_type_choices


#
# Instruments
#
# could also use TOO().instruments, which is [ 'XRT', 'BAT', 'UVOT']
# but that doesn't include the full names
SWIFT_INSTRUMENT_CHOICES = [
    ('UVOT', 'UV/Optical Telescope (UVOT)'),
    ('XRT', 'X-ray Telescope (XRT)'),
    ('BAT', 'Burst Alert Telescope (BAT)'),
]

#
# GRB Detectors
#


def get_grb_detector_choices():
    """Returns a list of tuples for the GRB detector choices.

    Since the TOO() object has property describing the valid GRB detectors,
    use that to create the choices list of tuples (e.g. [('Swift/BAT', 'Swift/BAT'), ('Fermi/LAT',
    'Fermi/LAT'), ...]).
    """
    grb_detector_choices = []
    for mission in TOO().mission_names:
        if mission != 'ANTARES':
            grb_detector_choices.append((mission, mission))

    # add the SWIFT_OTHER_CHOICE
    grb_detector_choices.append((SWIFT_OTHER_CHOICE, SWIFT_OTHER_CHOICE))
    return grb_detector_choices


#
# XRT Modes
#
# XRT modes are converted to numbers. So,
#    too.xrt_mode = 6
# and
#    too.xrt_mode = 'WT'
# are equivalent.
#
SWIFT_XRT_MODE_CHOICES = [
    (0, "Auto"),  # picks a mode based on brightness, but if brightness is known, best to pick yourself
    # (1, "Null"),
    # (2, "ShortIM"),
    # (3, "LongIM"),
    # (4, "PUPD"),
    # (5, "LRPD"),
    (6, "Windowed Timing (WT)"),
    (7, "Photon Counting (PC)"),
    # (8, "Raw"),
    # (9, "Bias"),
]

#
# UVOT Modes
#

# >>> too.uvot_mode = 0x01AB  # Assign too.uvot_mode as a Hexadecimal number:
# >>> too.uvot_mode  # It's reported as a Hex string:
# '0x01ab'
# >>> type(too.uvot_mode)
# <class 'str'>
# Any string will validate:
# >>> too.uvot_mode = "I think I want all UV filters for this, whatever the UVOT team recommends."

SWIFT_UVOT_FILTER_MODE_CHOICES = [
    (0x015a, 'uvm2 (0x015a)'),
    (0x011e, 'uvw2 (0x011e)'),
    (0x01aa, 'u (0x01aa)'),
    (0x018c, 'uvw1 (0x018c)'),
    (0x2016, 'B (0x2016)'),
    (0x2005, 'V (0x2005)'),
    (0x2019, 'white (0x2019)'),
    (0x209a, 'three optical filters (0x209a)'),
    (0x308f, 'three NUV filters (0x308f)'),
    (0x30d5, 'four UV/NUV filters (0x30d5)'),
    (0x30ed, 'standard six-filter blue-weighted mode (0x30ed)'),
    (0x223f, 'heavily weighted six-filter mode; for supernovae and very red objects (0x223f)'),
    (0x2241, 'all seven optical/UV filters (0x2241)'),
    (0x0270, ('unscaled six-filter mode to get 6 broadband filters in AT observations with'
              ' snapshot lengths > 1000s (0x0270)')),
    (0x9999, 'Filter of the Day (0x9999)'),
    (SWIFT_OTHER_CHOICE, SWIFT_OTHER_CHOICE),
]


#
# Monitoring
#
def get_monitoring_unit_choices():
    """Returns a list of tuples for the monitoring frequency unit choices.

    Since the TOO() object has property describing the valid monitoring frequency units,
    use that to create the choices list of tuples (e.g. [('day', 'day'), ('week', 'week'), ...]).
    """
    monitoring_unit_choices = []
    for unit in TOO().monitoring_units:
        monitoring_unit_choices.append((unit, f'{unit}(s)'))
    return monitoring_unit_choices
