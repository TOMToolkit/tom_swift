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

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from astropy.coordinates import SkyCoord
from requests.exceptions import ConnectionError

from swifttools.swift_too import TOO, TOORequests, Resolve
from swifttools.swift_too.api_resolve import Swift_Resolve

from tom_targets.models import Target

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class SwiftAPI:
    """This is the interface between the SwiftFacility and the swifttools.swift_too classes.

    This keeps the SwiftFacility class focued on implementing it's super class methods and separates
    the SwiftFacility from the swifttools.swift_too classes.
    """
    def __init__(self, debug=True):
        self.too = TOO()
        self.too_request = TOORequests()

        # gather username
        try:
            self.too.username = settings.FACILITIES['SWIFT'].get('SWIFT_USERNAME', 'SWIFT_USERNAME not configured')
            self.too.shared_secret = settings.FACILITIES['SWIFT'].get('SWIFT_PASSWORD', 'SWIFT_PASSWORD not configured')

            logger.info(f'swift username: {self.too.username}')
        except KeyError as ex:
            logger.error(f"'SWIFT' configuration dictionary not defined in settings.FACILITIES")
            raise ImproperlyConfigured


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


SWIFT_TARGET_CLASSIFICATION_CHOICES = [
    ('AGN', 'AGN'),
    ('Be Binary System', 'Be Binary System'),
    ('Comet or Asteroid','Comet or Asteroid'),
    ('Dwarf Nova', 'Dwarf Nova'),
    ('GRB', 'GRB'),
    ('Nova', 'Nova'),
    ('Pulsar', 'Pulsar'),
    ('Supernova', 'Supernova'),
    ('Tidal Disruption Event', 'Tidal Disruption Event'),
    ('X-Ray Transient', 'X-Ray Transient'),
    ('Other (please specify)', 'Other (please specify)'),
]


#
# Urgency
#
SWIFT_URGENCY_CHOICES = [
    (1, 'Within 4 hours (Wakes up the Swift Observatory Duty Scientist).'),
    (2, 'Within 24 hours'),
    (3, 'Days to a week'), # default
    (4, 'Week to a month'),
]

#
# Instruments
#
SWIFT_INSTRUMENT_CHOICES = {
    'UVOT' : 'UV/Optical Telescope',
    'XRT' : 'X-ray Telescope',
    'BAT' : 'Burst Alert Telescope',
}

#
# UVOT Modes
#

# >>> too.uvot_mode = 0x01AB  # Assign too.uvot_mode as a Hexidecimal number:
# >>> too.uvot_mode  # It's reported as a Hex string:
# '0x01ab'
# >>> type(too.uvot_mode)
# <class 'str'>
# Any string will validate:
# >>> too.uvot_mode = "I think I want all UV filters for this, whatever the UVOT team recommends."


#
# XRT Modes
#
# XRT modes are converted to numbers. So,
#    too.xrt_mode = 6
# and 
#    too.xrt_mode = 'WT'
# are equivalent.
#
SWIFT_XRT_MODE_CHOICES = {
    0 : "Auto", # picks a mode based on brightness, but if brightness is known, best to pick yourself
    1 : "Null",
    2 : "ShortIM",
    3 : "LongIM",
    4 : "PUPD",
    5 : "LRPD",
    6 : "WT", # Windowed Timing
    7 : "PC", # Photon Counting
    8 : "Raw",
    9 : "Bias",
}


#
# Observation Types
#
# Note that: 
# >>> TOO().obs_types
# ['Spectroscopy', 'Light Curve', 'Position', 'Timing']
SWIFT_OBSERVATION_TYPE_CHOICES = [
    ('Spectroscopy', 'Spectroscopy'),
    ('Light Curve', 'Light Curve'),
    ('Position', 'Position'),
    ('Timing', 'Timing'),
]

