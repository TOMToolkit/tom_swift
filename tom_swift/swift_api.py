#
# This module is intended to hold the Swift ToO API specific information
# see https://www.swift.psu.edu/too_api/  for documentation
# see https://gitlab.com/DrPhilEvans/swifttools  for source code
#

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
# Observation Type
#
# Note that: 
# >>> TOO().obs_types
# ['Spectroscopy', 'Light Curve', 'Position', 'Timing']
