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
    #  TODO: re-consider (or remove?) assumption that all Layout instances have a group property
    #        (see tom_observations.view,py::get_form::L#255 and other layout methods of other
    #         facility forms):
    #            if settings.TARGET_PERMISSIONS_ONLY:
    #                groups = Div()
    #            else:
    #                groups = Row('groups')
    #
    # TODO: see www.swift.psu.edu/toop/toorequest.php of the NASA/PSU Swift ToO Request Form
    # TODO: support "GI Program" requests
    #

    urgency = forms.ChoiceField(
        required=True,
        label='Urgency',
        choices=SWIFT_URGENCY_CHOICES,
        initial=SWIFT_URGENCY_CHOICES[2])

    target_classification = forms.CharField(
        required=True,
        label='Target Type or Classification',
        help_text=(
            'Target Type or Classification. '
            'Focus, clear, and click to select from choices or enter a custom value.'),
        # custom widget to allow user to enter a custom value or select from a choices
        # TODO: Create drop down with Other menu item which when selected shows a text box
        #       for the user to enter a custom value.
        widget=ListTextWidget(data_list=SWIFT_TARGET_CLASSIFICATION_CHOICES,
                              name='target-classification'))

    obs_type = forms.ChoiceField(
        required=True,
        label='Observation Type',
        choices=SWIFT_OBSERVATION_TYPE_CHOICES,
        help_text='What is driving the exposure time?',
        initial=SWIFT_OBSERVATION_TYPE_CHOICES[0])

    optical_magnitude = forms.FloatField(required=False, label='Optical Magnitude')
    optical_filter = forms.CharField(required=False, label='What filter was this measured in?',initial='u')
    exposure = forms.FloatField(required=False, label='Exposure time requested [s]',initial=500)
    exp_time_just = forms.CharField(
        required=False, label='Time Justification',
        initial="TOM Toolkit test by llindstrom@lco.global (please contact if this is a problem)")

    num_of_visits= forms.IntegerField(
        required=False,
        label='Number of visits [integer]',
        help_text=('If number of visits more than one change next exposure'
                   'time per visit and monitoring frequency, otherwise leave blank.'),
        initial=1)

    monitoring_freq = forms.CharField(required=False, label='Frequency of visits')
    exp_time_per_visit = forms.FloatField(required=False, label='Exposure time per visit(s) [s]')

    uvot_mode = forms.CharField(
        required=False,
        label='UVOT filter mode (can write instructions or specific mode)',
        initial='0x9999') # 0x9999 is the "Filter of the Day" and does not require justification

    # required unless uvot_mode is 0x9999 (Filter of the Day)
    uvot_just = forms.CharField(
        required=False, label='UVOT Mode Justification',
        initial="TOM Toolkit test by llindstrom@lco.global (please contact if this is a problem)")

    science_just = forms.CharField(
        required=False, label='Science Justification',
        initial="TOM Toolkit test by llindstrom@lco.global (please contact if this is a problem)")

    immediate_objective = forms.CharField(
        required=False, label='Immediate Objective',
        initial="TOM Toolkit test by llindstrom@lco.global (please contact if this is a problem)")


    def layout(self):
        layout = Layout(
            'urgency',
            'target_classification',
            'immediate_objective',
            'science_just',
            Accordion(
                AccordionGroup('Observation/Exposure Information',
                    Div(
                        'obs_type',
                        'optical_magnitude',
                        'optical_filter',
                        'exposure',
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


    def _configure_too(self, observation_payload):
        """In preparation for calls to self.swift_api.too.validate() and self.swift_api.too.submit(),
        both validate_observation() and submit_observation() call this method to
        configure the Swift_TOO object (self.too) from the observation_payload.

        For this Facility, the observation_payload is the serialized form.cleaned_data
        plus the target information (which doesn't come from the form).
        See SwiftObservationForm.observation_payload() for details.

        Reference Documentation:
         * https://www.swift.psu.edu/too_api/
         * https://www.swift.psu.edu/too_api/index.php?md=TOO parameters.md
        """
        #logger.debug(f'_configure_too - observation_payload: {observation_payload}')
        #for key, value in observation_payload.items():
        #    logger.debug(f'_configure_too -- observation_payload.{key}: {value}')


        # User information (this should already be configured in the SwiftAPI.__init__())
        logger.debug(f'_configure_too - self.swift_api.too.username: {self.swift_api.too.username}')
        logger.debug(f'_configure_too - self.swift_api.too.shared_secret: {self.swift_api.too.shared_secret}')

        # Object Information
        self.swift_api.too.source_name = observation_payload['source_name']
        self.swift_api.too.ra = observation_payload['ra']
        self.swift_api.too.dec = observation_payload['dec']

        # Type or Classification
        self.swift_api.too.source_type = observation_payload['target_classification']

        # What is driving the exposure time?
        self.swift_api.too.obs_type = observation_payload['obs_type']

        # TODO: Tiling Support
        # Tiling (yes/no)
        # if yes, then
        #   Number of Tiles; Exposure Time per Tile; Tiling Justification

        # Immediate Objective
        self.swift_api.too.immediate_objective = observation_payload['immediate_objective']

        # TODO: Guest InvestigatorI Program Support
        # Are you triggering a GI program? (yes/no)
        # if yes, then
        #   GI Program Details: Proposal ID; Proposal PI; Trigger Justification
        # Since "this will count against the number of awarded triggers", show
        # triggers used / total number triggers awarded. (and trigger remaining?)..

        # Instrument (XRT/UVOT/BAT)
        # TODO: plumb this through to the form
        self.swift_api.too.instrument = "XRT"

        # XRT Mode
        # TODO: Auto; Windowed Timing; Photon Counting;
        self.swift_api.too.xrt_mode = "WT" # observation_payload['xrt_mode']
        self.swift_api.too.xrt_countrate = 20.0 # observation_payload['xrt_countrate']  # counts/second

        # UVOT Mode
        self.swift_api.too.uvot_mode = observation_payload['uvot_mode']
        self.swift_api.too.uvot_just = observation_payload['uvot_just']

        # Ugency
        self.swift_api.too.urgency = observation_payload['urgency']

        # Object Brightness
        self.swift_api.too.optical_magnitude = observation_payload['optical_magnitude']
        self.swift_api.too.optical_filter = observation_payload['optical_filter']
        #self.swift_api.too.xrt_countrate = observation_payload['xrt_countrate']  # counts/second
        #self.swift_api.too.bat_countrate = observation_payload['bat_countrate']  # counts/second
        #self.swift_api.too.other_brightness = observation_payload['other_brightness']

        # Science Justification
        self.swift_api.too.science_just = observation_payload['science_just']

        # Observation Strategy
        # Single Observation / Multiple Observations
        self.swift_api.too.exposure = observation_payload['exposure']
        self.swift_api.too.exp_time_just = observation_payload['exp_time_just']
        # if Multiple Observations, then Monitoring Details
        #    Number of Visits; Exposure Time per Visit; Monitoring Cadence Number + Units
        multiple_observations = False  # TODO: plumb this through to the form
        if multiple_observations:
            self.swift_api.too.num_of_visits = observation_payload['num_of_visits']
            self.swift_api.too.exp_time_per_visit = observation_payload['exp_time_per_visit']
            self.swift_api.too.monitoring_freq = observation_payload['monitoring_freq']
        # TODO: Units for monitoring_freq (days, hours, minutes, seconds, orbits, others, etc.)

        # Debug
        self.swift_api.too.debug = True   # TODO: plumb this through to the form




    def validate_observation(self, observation_payload) -> [()]:
        """Perform a dry-run of submitting the observation.

        See submit_observation() for details.

        The super class method is absract. No need to call it.
        """
        self._configure_too(observation_payload)

        validation_errors = []
        # first, validate the too locally
        too_is_valid = self.swift_api.too.validate()
        logger.debug(f'validate_observation response: {too_is_valid}')

        if too_is_valid:
            # if the too was internally valid, now validate with the server
            logger.debug(f'validate_observation - calling too.server_validate()')
            too_is_server_valid = self.swift_api.too.server_validate()
        
        logger.debug(f'validate_observation - too.status: {self.swift_api.too.status}')
        #logger.debug(f'validate_observation - dir(too.status): {dir(self.swift_api.too.status)}')

        too_status_properties_removed = [
            'clear', 'submit', 'jwt', 'queue',
            'error', 'warning', 'validate',
        ]
        too_status_properties = ['api_data', 'api_name', 'api_version', 'began',
                                 'complete', 'completed', 'errors', 'fetchresult',
                                 'ignorekeys', 'jobnumber', 'result', 'shared_secret',
                                 'status', 'submit_url', 'timeout', 'timestamp',
                                 'too_api_dict', 'too_id', 'username', 'warnings']
        
        for property in too_status_properties:
            logger.debug(f'validate_observation - too.status.{property}: {getattr(self.swift_api.too.status, property)}')

        if not (too_is_valid and too_is_server_valid):
            # TODO: extract the error messages from the response
            # the too.status.errors is a list of strings. for example: ['Missing key: exp_time_just']
            logger.debug(f'validate_observation - too.status.status: {self.swift_api.too.status.status}')
            logger.debug(f'validate_observation - too.status.errors: {self.swift_api.too.status.errors}')
            logger.debug(f'validate_observation - type(too.status.errors): {type(self.swift_api.too.status.errors)}')
            
            # this assumes the format of the error message, which is not correct
            #for error_string in self.swift_api.too.status.errors:
            #    field = error_string.split(':')[1].strip()
            #    error = error_string.split(':')[0].strip()
            #    validation_errors.append((field, error))

            validation_errors = self.swift_api.too.status.errors

        return validation_errors

    def submit_observation(self, observation_payload) -> [()]:
        """Submit the observation to the Swift ToO API

        `observation_payload` is the serialized form.cleaned_data

        For the SwiftFacility, sumbitting (or validating) an observation request means
        instanciating a Swift_TOO object, setting it properties from the observation_payload,
        and calling its submit() (or validate()) method. self.too is the Swift_TOO object, whose
        proerties we need to set.

        returns a list of (field, error) tuples if the observation is invalid

        See https://www.swift.psu.edu/too_api/ for documentation. 

        The super class method is absract. No need to call it.
         """
        self._configure_too(observation_payload)
        self.swift_api.too.submit()

        logger.info(f'submit_observation - too.status.status: {self.swift_api.too.status.status}')
        logger.info(f'submit_observation - too.status.errors: {self.swift_api.too.status.errors}')

        logger.debug(f'submit_observation - too.status: {self.swift_api.too.status}')

        #too_status_properties_removed = [
        #    'clear', 'submit', 'jwt', 'queue',
        #    'error', 'warning', 'validate',
        #]
        #too_status_properties = ['api_data', 'api_name', 'api_version', 'began',
        #                         'complete', 'completed', 'errors', 'fetchresult',
        #                         'ignorekeys', 'jobnumber', 'result', 'shared_secret',
        #                         'status', 'submit_url', 'timeout', 'timestamp',
        #                         'too_api_dict', 'too_id', 'username', 'warnings']
        #
        #for property in too_status_properties:
        #    logger.debug(f'submit_observation - too.status.{property}: {getattr(self.swift_api.too.status, property)}')

        if self.swift_api.too.status.status == 'Accepted':
            # this was a successful submission
            logger.info(f'submit_observation - too.status.status: {self.swift_api.too.status.status}')
            logger.info(f'submit_observation - too.status.too_id: {self.swift_api.too.status.too_id}')

            # lets examine the TOO created
            # TODO: move this code into swift_api.py
            # see https://www.swift.psu.edu/too_api/index.php?md=Swift TOO Request Example Notebook.ipynb

            # configure the request object
            self.swift_api.too_request.username = self.swift_api.too.username
            self.swift_api.too_request.shared_secret = self.swift_api.too.shared_secret
            self.swift_api.too_request.detail = True
            self.swift_api.too_request.too_id = self.swift_api.too.status.too_id
            too_request_response = self.swift_api.too_request.submit()

            if too_request_response:
                logger.debug(f'submit_observation - too_request[0]: {self.swift_api.too_request[0]}')
            else:
                logger.error(f'submit_observation - too_request_response: {too_request_response}')
        else:
            logger.error(f'submit_observation - too.status.status: {self.swift_api.too.status.status}')

        return []


