import logging

from crispy_forms.layout import Layout, Div, Field, Row, HTML
from crispy_forms.bootstrap import Accordion, AccordionGroup
from django import forms
from django.conf import settings

from tom_observations.facility import BaseObservationForm, BaseObservationFacility, get_service_class
from tom_targets.models import Target

from tom_swift import __version__
from tom_swift.swift_api import (SwiftAPI,
                                 SWIFT_OBSERVATION_TYPE_CHOICES,
                                 SWIFT_TARGET_CLASSIFICATION_CHOICES,
                                 SWIFT_URGENCY_CHOICES)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class ListTextWidget(forms.TextInput):
    """A widget that supplies a list of options for a text input field, but
    also allows the user to enter a custom value.

    Used here for the target_classification field of the SwiftObservationForm.
    """
    def __init__(self, data_list, name, *args, **kwargs):
        super(ListTextWidget, self).__init__(*args, **kwargs)
        self._name = name
        self._list = data_list
        self.attrs.update({'list':'list__%s' % self._name})

    def render(self, name, value, attrs=None, renderer=None):
        text_html = super(ListTextWidget, self).render(name, value, attrs=attrs)
        data_list = '<datalist id="list__%s">' % self._name
        for item in self._list:
            data_list += '<option value="%s">' % item
        data_list += '</datalist>'

        return (text_html + data_list)




class SwiftObservationForm(BaseObservationForm):
    # TODO: cannot user BaseRoboticObservationForm b/c it assumes
    #   (in tom_observations/templatetags/observation_extras.py::L#110 get_sidereal_visibility)
    #   that the Facility has a fixed Lat/Lon, lol. 

#    # TODO: re-consider (or remove?) assumption that all Layout instances have a group property
#    #  (see tom_observations.view,py::get_form::L#255 and other layout methods of other facility forms)
#    if settings.TARGET_PERMISSIONS_ONLY:
#        groups = Div()
#    else:
#        groups = Row('groups')
#

    urgency = forms.ChoiceField(
        required=True,
        label='Urgency',
        choices=SWIFT_URGENCY_CHOICES,
        initial=SWIFT_URGENCY_CHOICES[2])

    target_classification = forms.CharField(
        required=True,
        label='Target Classification',
        help_text=(
            'Target type or classification. '
            'Focus, clear, and click to select from choices or enter a custom value.'),
        # custom widget to allow user to enter a custom value or select from a choices
        widget=ListTextWidget(data_list=SWIFT_TARGET_CLASSIFICATION_CHOICES,
                              name='target-classification'))

    swift_observation_type = forms.ChoiceField(
        required=True,
        label='Observation Type',
        choices=SWIFT_OBSERVATION_TYPE_CHOICES,
        help_text='What is driving the exposure time?',
        initial=SWIFT_OBSERVATION_TYPE_CHOICES[0])

    optical_magnitude = forms.FloatField(required=False, label='Optical Magnitude')
    optical_filter = forms.CharField(required=False, label='What filter was this measured in?',initial='u')
    exposure_time = forms.FloatField(required=False, label='Exposure time requested [s]',initial=500)
    exp_time_just = forms.CharField(required=False, label='Time Justification', initial="500s to determine if source has faded")

    num_of_visits= forms.IntegerField(
        required=False,
        label='Number of visits [integer]',
        help_text=('If number of visits more than one change next exposure'
                   'time per visit and monitoring frequency, otherwise leave blank.'),
        initial=1)

    monitoring_freq = forms.CharField(required=False, label='Frequency of visits')
    exp_time_per_visit = forms.FloatField(required=False, label='Exposure time per visit(s) [s]')

    uvot_mode = forms.CharField(required=False, label='UVOT filter mode (can write instructions or specific mode)', initial='0x01AB')
    uvot_just = forms.CharField(required=False, label='UVOT Mode Justification', initial="Needs to be revised, do we want default as u or all filters?")

    science_just = forms.CharField(required=False, label='Science Justification', initial="500s to determine if source has faded")
    immediate_objective = forms.CharField(required=False, label='Immediate Objective',initial="To determine if source has faded.")

    def layout(self):
        layout = Layout(
            'urgency',
            'target_classification',
            'immediate_objective',
            'science_just',
            Accordion(
                AccordionGroup('Observation/Exposure Information',
                    Div(
                        'swift_observation_type',
                        'optical_magnitude',
                        'optical_filter',
                        'exposure_time',
                        'exp_time_just',
                    ),
                    Div(
                        'num_of_visits',
                        'exp_time_per_visit',
                        'monitoring_freq',
                    )
                ),
                AccordionGroup('Instrument Information',
                    Div(
                        'uvot_mode',
                        'uvot_just',
                    ),
                ),
            ),
        ) # end layout

#            Layout(
#            'target_classification',
#            'urgency',
#            'observation_type',
#            'optical_magnitude',
#            'optical_filter',
#            'exposure_time',
#            'num_of_visits',
#            HTML('<p>If number of visits more than one change next exposure time per visit and monitoring frequency, otherwise leave blank.</p>'),
#            'exp_time_per_visit',
#            'monitoring_freq',
#            'exp_time_just',
#            'immediate_objective',
#            'science_just',
#        )
        return layout

    def is_valid(self):
        """Validate the form

        This method is called by the view's form_valid() method.
        """
        # TODO: check validity of doc-string
        super().is_valid() # this adds cleaned_data to the form instance
        logger.debug(f'SwiftObservationForm.is_valid -- cleaned_data: {self.cleaned_data}')

        observation_payload = self.observation_payload()
        logger.debug(f'SwiftObservationForm.is_valid -- observation_payload: {observation_payload}')

        # BaseObservationForm.is_valid() says to make this call the Facility.validate_observation() method
        observation_module = get_service_class(self.cleaned_data['facility'])

        # validate_observation needs to return a list of (field, error) tuples
        # if the list is empty, then the observation is valid
        #
        # in order to call self.add_error(field, error), the field given must match the
        # a field declared on the Form, Thus, the form field names must match the properties
        # of the swifttoolkit.Swift_TOO object (unless we want to maintain a a mapping between
        # the two).
        #
        logger.debug(f'SwiftObservationForm.is_valid -- fields: {self.fields.keys()}')
        errors: [] = observation_module().validate_observation(observation_payload)

        if errors:
            self.add_error(None, errors)
            logger.debug(f'SwiftObservationForm.is_valid -- errors: {errors}')

        if self._errors:
            logger.warn(f'Facility submission has errors {self._errors.as_data()}')

        # if add_error has not been called, then a success message will be displayed in the template
        return not self._errors

    def observation_payload(self):
        """Transform the form.cleaned_data into a payload dictionary that can be:
           A. validated (see) SwiftFacility.validate_observation(); and
           B. submitted (see) SwiftFacility.submit_observation()

        For other facilities, observation_payload() transforms the form.cleaned_data
        into something that can be more directly submitted to the facility's API
        (via the Facility's validate_observation() and submit_observation() methods).

        For Swift, since we're configuring a Swift_TOO object, the form.cleaned_data
        plus the target information should be sufficient.
        """
        # At the moment it's unclear why the obeervation_payload needs to differ from
        # the form.cleaned_data...
        payload = self.cleaned_data.copy() # copy() just to be safe

        # ...but we need to add the target information (which doesn't come from the form).
        target = Target.objects.get(pk=self.cleaned_data['target_id'])
        payload['source_name'] = target.name
        payload['ra'] = target.ra
        payload['dec'] = target.dec

        return payload

class SwiftUVOTObservationForm(SwiftObservationForm):
    """Extends the SwiftObservationForm with UVOT-specific fields
    """
    def layout(self):
        layout = super().layout()
        #layout.append('uvot_mode')
        #layout.append('uvot_just')
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
            'username': self.swift_api.too.username,
        }
        target = kwargs['target']
        resolved_target = self.swift_api.resolve_target(target)
        if resolved_target:
            new_context_data['resolver'] = resolved_target.resolver
            new_context_data['resolved_target_name'] = resolved_target.name
            new_context_data['resolved_target_ra'] = resolved_target.ra
            new_context_data['resolved_target_dec'] = resolved_target.dec
        else:
            # TODO: display bootstrap warning alert
            new_context_data['resolved_target_name'] = 'Not found'

        facility_context_data.update(new_context_data)
        return facility_context_data

    def get_form(self, observation_type):
        return SwiftObservationForm

    def all_data_products(self, observation_record):
        data_products = super().all_data_products(observation_record)
        logger.debug('all_data_products: {data_products}}')
        raise NotImplementedError('SwiftFacility.all_data_products not yet implemented')
        return data_products

    def data_products(self, observation_id, product_id):
        # TODO: this is from the BaseRoboticObservationFacility class 
        #       not sure if it's needed here
        logger.debug('data_products')
        raise NotImplementedError('SwiftFacility.data_products not yet implemented')

    def get_observation_status(self):
        logger.debug('get_observation_status')
        raise NotImplementedError('SwiftFacility.get_observation_status not yet implemented')

    def get_observation_url(self):
        logger.debug('get_observation_url')
        raise NotImplementedError('SwiftFacility.get_observation_url not yet implemented')

    def get_observing_sites(self):
        logger.debug('get_observing_sites')
        raise NotImplementedError('SwiftFacility.get_observing_sites not yet implemented')
        return super().get_observing_sites()

    def get_terminal_observing_states(self):
        logger.debug('get_terminal_observing_states')
        raise NotImplementedError('SwiftFacility.get_terminal_observing_states not yet implemented')


    def validate_observation(self, observation_payload):
        """Perform a dry-run of submitting the observation.

        see submit_observation()

        The super class method is absract. No need to call it.
        """
        logger.debug(f'validate_observation - observation_payload: {observation_payload}')

    def submit_observation(self, observation_payload):
        """Submit the observation to the Swift ToO API

        `observation_payload` is the serialized form data.

        The super class method is absract. No need to call it.
         """
        logger.debug(f'submit_observation - observation_payload: {observation_payload}')


