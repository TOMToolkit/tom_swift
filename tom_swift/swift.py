import logging

from crispy_forms.layout import Layout, Div, Row, HTML

from django import forms
from django.conf import settings

from tom_observations.facility import BaseObservationForm, BaseObservationFacility

from tom_swift import __version__
from tom_swift.swift_api import SwiftAPI

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class SwiftObservationForm(BaseObservationForm):
    # TODO: cannot user BaseRoboticObservationForm b/c it assumes
    #   (in tom_observations/templatetags/observation_extras.py::L#110 get_sidereal_visibility)
    #   that the Facility has a fixed Lat/Lon, lol. 

#    exposure_time = forms.IntegerField()
#    exposure_count = forms.IntegerField()
#    groups = forms.IntegerField()
#
#    # TODO: re-consider (or remove?) assumption that all Layout instances have a group property
#    #  (see tom_observations.view,py::get_form::L#255 and other layout methods of other facility forms)
#    if settings.TARGET_PERMISSIONS_ONLY:
#        groups = Div()
#    else:
#        groups = Row('groups')
#
#    def layout(self):
#        return Layout(
#            'exposure_time',
#            'exposure_count',
#            'groups'
#        )
#

#
# This is Sam's UVOTObservationForm

# Fields for user to fill in in Swift ToO form.
# Some fields are filled automatically by default for rapid submission of EM-GW candidates

    urgency = forms.IntegerField(required=False, label='ToO Urgency',initial=2)
    obs_type = forms.CharField(required=False, label='Observation type (Spectroscopy; Light curve; Position, Timing',initial='Light Curve')
    opt_mag = forms.FloatField(required=False, label='Optical Magnitude')
    opt_filt = forms.CharField(required=False, label='What filter was this measured in',initial='u')
    exposure = forms.FloatField(required=False, label='Exposure time requested [s]',initial=500)
    exp_time_just = forms.CharField(required=False, label='Time Justification', initial="500s to determine if source has faded")
    num_of_visits= forms.IntegerField(required=False, label='Number of visits [integer]',initial=1)
    monitoring_freq = forms.CharField(required=False, label='Frequency of visits')
    exp_time_per_visit = forms.FloatField(required=False, label='Exposure time per visit(s) [s]')
    uvot_mode = forms.CharField(required=False, label='UVOT filter mode (can write instructions or specific mode)', initial='0x01AB')
    science_just = forms.CharField(required=False, label='Science Justification', initial="500s to determine if source has faded")
    immediate_objective = forms.CharField(required=False, label='Immediate Objective',initial="To determine if source has faded.")
    source_type=forms.CharField(required=False, label='Source Type',initial='Optical/UV transient in GW error region')
    uvot_just = forms.CharField(required=False, label='UVOT Mode Justification', initial="Needs to be revised, do we want default as u or all filters?")

    def layout(self):
        return Layout(
            'source_type',
            'urgency',
            'obs_type',
            'opt_mag',
            'opt_filt',
            'exposure',
            'num_of_visits',
            HTML('<p>If number of visits more than one change next exposure time per visit and monitoring frequency, otherwise leave blank.</p>'),
            'exp_time_per_visit',
            'monitoring_freq',
            'exp_time_just',
            'immediate_objective',
            'science_just',
        )

class SwiftUVOTObservationForm(SwiftObservationForm):
    """Extends the SwiftObservationForm with UVOT-specific fields
    """
    def layout(self):
        layout = super().layout()
        layout.append('uvot_mode')
        layout.append('uvot_just')
        return layout

class SwiftXRTObservationForm(SwiftObservationForm):
    pass

class SwiftBATObservationForm(SwiftObservationForm):
    pass


class SwiftFacility(BaseObservationFacility):
    def __init__(self):
        super().__init__()
        self.swift_api = SwiftAPI()

    name = 'Swift'
    observation_types = [
        ('OBSERVATION', 'Custom Observation')
    ]

    # observation_forms key-values become TABs in the observation_form template
    observation_forms = {
        # TODO: this should be driven by swift_api.SWIFT_INSTRUMENT_CHOICES
        'UVOT': SwiftUVOTObservationForm,
        'XRT': SwiftXRTObservationForm,
        'BAT': SwiftBATObservationForm,
    }
    template_name = 'tom_swift/observation_form.html'

    def get_facility_context_data(self, **kwargs):
        """Provide Facility-specific data to context for ObservationCreateView's template

        This method is called by ObservationCreateView.get_context_data() and returns a
        dictionary of context data to be added to the View's context
        """
        facility_context_data = super().get_facility_context_data(**kwargs)
        logger.debug(f'get_facility_context_data -- kwargs: {kwargs}')
        new_context_data = {
            'version': __version__,  # from tom_swift/__init__.py
            'username': self.swift_api.username,
        }
        target = kwargs['target']
        resolved_target = self.swift_api.resolve_target(target)
        new_context_data['resolver'] = resolved_target.resolver
        new_context_data['resolved_target_name'] = resolved_target.name
        new_context_data['resolved_target_ra'] = resolved_target.ra
        new_context_data['resolved_target_dec'] = resolved_target.dec

        facility_context_data.update(new_context_data)
        return facility_context_data

    def get_form(self, observation_type):
        return SwiftObservationForm

    def data_products(self): pass

    def get_observation_status(self): pass

    def get_observation_url(self): pass

    def get_observing_sites(self): pass

    def get_terminal_observing_states(self): pass

    def validate_observation(self): pass

    def submit_observation(self): pass

