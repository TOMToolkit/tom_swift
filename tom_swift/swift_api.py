# This module is intended to hold the Swift ToO API specific information
# see https://www.swift.psu.edu/too_api/  for documentation
# see https://gitlab.com/DrPhilEvans/swifttools  for source code
#
import logging

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from astropy.coordinates import SkyCoord
from swifttools.swift_too import TOO, Resolve
from swifttools.swift_too.api_resolve import Swift_Resolve
from tom_targets.models import Target

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class SwiftAPI(TOO):
    """Extend the swifttools.swift_too.TOO class with some properties and
    API client-type methods.
    """
    def __init__(self, debug=True):
        self.debug = debug
        # gather username
        try:
            self.username = settings.FACILITIES['SWIFT'].get('SWIFT_USERNAME', 'SWIFT_USERNAME not configured')
            self.shared_secret = settings.FACILITIES['SWIFT'].get('SWIFT_PASSWORD', 'SWIFT_PASSWORD not configured')
            logger.debug(f'swift username: {self.username}')
        except KeyError as ex:
            logger.error(f"'SWIFT' configuration dictionary not defined in settings.FACILITIES")
            raise ImproperlyConfigured


    def resolve_target(self, target: Target):
        """
        """
        logger.debug(f'resolve_target: {target.name}')

        resolved_target: Swift_Resolve = Resolve(target.name)  # this calls the API
        # <class 'swifttools.swift_too.api_resolve.Swift_Resolve'>

        logger.debug(f'resolved_target: {resolved_target}')
        logger.debug(f'type(resolved_target): {type(resolved_target)}')
        logger.debug(f'dir(resolved_target): {dir(resolved_target)}')
        for key, value in resolved_target.__dict__.items():
            logger.debug(f'resolved_target.{key}): {value}')

        return resolved_target


    def get_observation_type_choices(self):
        """
        """
        logger.debug(f'get_observation_type_choices')
        pass

#
# Urgency
#
SWIFT_URGENCY_CHOICES = {
    1 : 'Within 4 hours',
    2 : 'Within 24 hours',
    3 : 'Days to a week', # default
    4 : 'Week to a month',
}

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
