from crispy_forms.layout import Layout, Div, Row

from django import forms
from django.conf import settings

from tom_observations.facility import BaseRoboticObservationForm, BaseRoboticObservationFacility



class SwiftObservationForm(forms.Form):
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
    pass

class SwiftFacility:
    name = 'Swift'
    observation_types = [
        ('OBSERVATION', 'Custom Observation')
    ]

    observation_forms = {
        'OBSERVATION': SwiftObservationForm
    }

    def get_form(self, observation_type):
        return SwiftObservationForm

    def data_products(self): pass

    def get_observation_status(self): pass

    def get_observation_url(self): pass

    def get_observing_sites(self): pass

    def get_terminal_observing_states(self): pass

    def validate_observation(self): pass

    def submit_observation(self): pass

