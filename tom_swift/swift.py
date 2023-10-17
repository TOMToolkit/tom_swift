import logging

from crispy_forms.layout import Layout, Div, Field, Row, HTML
from crispy_forms.bootstrap import Accordion, AccordionGroup
from django import forms
from django.conf import settings
from django.contrib import messages # not sure if we can do this outside of a View
from django.utils.safestring import mark_safe

from tom_observations.facility import BaseObservationForm, BaseObservationFacility, get_service_class
from tom_targets.models import Target

from tom_swift import __version__
from tom_swift.swift_api import (SwiftAPI,
                                 SWIFT_INSTRUMENT_CHOICES,
                                 SWIFT_TARGET_CLASSIFICATION_CHOICES,
                                 SWIFT_URGENCY_CHOICES,
                                 SWIFT_XRT_MODE_CHOICES,
                                 get_observation_type_choices,
                                 get_monitoring_unit_choices,)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

#  TODO: re-consider (or remove?) assumption that all Layout instances have a group property
#        (see tom_observations.view,py::get_form::L#255 and other layout methods of other
#         facility forms):
#            if settings.TARGET_PERMISSIONS_ONLY:
#                groups = Div()
#            else:
#                groups = Row('groups')


class SwiftObservationForm(BaseObservationForm):
    """The fields in this form follow this documentation:
    https://www.swift.psu.edu/too_api/index.php?md=TOO%20parameters.md
    """
    # TODO: support "GI Program" requests

    #
    # User identification (not part of the form - see SwiftAPI.get_credentials())
    #

    #
    # Source name, type, location, position_error
    #
    # source_name, ra, dec are not part of the form

    # see tom_swift/templates/tom_swift/observation_form.html for javascript
    # that displays/hides the target_classification ChoiceField if "Other (please specify)""
    # is chosen in the target_classification_choices drop-down menu widget.
    target_classification_choices = forms.ChoiceField(
        required=True,
        label='Target Type or Classification',
        choices=SWIFT_TARGET_CLASSIFICATION_CHOICES,
        initial=SWIFT_TARGET_CLASSIFICATION_CHOICES[0]
    )
    target_classification = forms.CharField(
        required=False, label='Other Target Classification',
        # here's how to add placehoder text as an alternative to help_text
        widget=forms.TextInput(attrs={'placeholder': 'Please specify other target classification'})
    )

    poserr = forms.FloatField(
        required=False,
        initial=0.0,
        label='Position Error [arcminutes]',
        help_text='90% confidence arcminutes.'
    )

    #
    # TOO Request Details
    #
    instrument = forms.ChoiceField(
        required=True,
        choices=SWIFT_INSTRUMENT_CHOICES,
        initial=SWIFT_INSTRUMENT_CHOICES[1],  # XRT is default
    )

    urgency = forms.ChoiceField(
        required=True,
        label='Urgency',
        choices=SWIFT_URGENCY_CHOICES,
        initial=SWIFT_URGENCY_CHOICES[2])

    #
    # Observation Type ('Specroscopy', 'Light Curve', 'Position', 'Timing')
    #
    obs_type = forms.ChoiceField(
        required=True,
        label='Observation Type',
        choices=get_observation_type_choices(),
        help_text='What is driving the exposure time?')

    #
    # Description of the source brightness for various instruments
    #
    # TODO: validation - answer at least one of these questions
    optical_magnitude = forms.FloatField(required=False, label='Optical Magnitude')
    optical_filter = forms.CharField(required=False, help_text='What filter was the optical magnitude measured in?', initial='u')
    xrt_countrate = forms.FloatField(required=False, label='XRT Count Rate [counts/second]')
    bat_countrate = forms.FloatField(required=False, label='BAT Count Rate [counts/second]')
    other_brightness = forms.CharField(
        required=False, label='Other Brightness',
        widget=forms.TextInput(attrs={'placeholder': 'Any other brightness information.'})
    )

    #
    # GRB stuff
    #
    grb_detector = forms.CharField(
        required=False,
        label='GRB Detector',
        widget=forms.TextInput(attrs={'placeholder': 'Should be "Mission/Detection" (e.g. Swift/BAT, Fermi/LAT)'})
    )

    grb_triggertime = forms.DateTimeField(
        required=False,
        label='GRB Trigger Date/Time',
        widget=forms.DateTimeInput) # TODO: finish this
    # TODO: validate: required if target_classification is GRB
    # TODO: make the widget nice

    #
    # Science Justification
    #
    immediate_objective = forms.CharField(
        required=False, label='Immediate Objective',
        widget=forms.Textarea(attrs={
            'rows': 2,
            'placeholder' : 'One sentence explanation of this TOO request.'})
        )

    science_just = forms.CharField(
        required=False, label='Science Justification',
        widget=forms.Textarea(attrs={
            'rows': 8,
            'placeholder' : 'A pursuasive paragraph or two explaining why this object requires rapid observation.'})
        )

    #
    # Exposure requested time (total)
    #
    exposure = forms.FloatField(required=False, label='Exposure time requested [s]',initial=500)
    exp_time_just = forms.CharField(
        required=False, label='Exposure Time Justification',
        widget=forms.Textarea(attrs={
            'rows': 2,
            'placeholder': 'Briefly justify the exposure time requested.'}),
    )

    #
    # Monitoring requests
    #
    exp_time_per_visit = forms.FloatField(required=False, label='Exposure time per visit(s) [s]')
    num_of_visits= forms.IntegerField(
        required=False,
        label='Number of visits [integer]',
        help_text=('If number of visits is more than one, then complete exposure'
                   ' time per visit and monitoring frequency.'),
        initial=1)
    monitoring_freq = forms.IntegerField(required=False, label='Monitoring Frequency', initial=1)
    monitoring_units = forms.ChoiceField(
        required=False,
        choices=get_monitoring_unit_choices(),
    )

    #
    # Swift Guest Investigator program parameters
    #
    proposal = forms.BooleanField(required=False, label='Are you triggering a GI program?')
    proposal_id = forms.CharField(required=False, label='Proposal ID')
    proposal_trigger_just = forms.CharField(
        required=False, label='Trigger Justification',
        widget=forms.Textarea(attrs={'rows': 4}))
    proposal_pi = forms.CharField(required=False, label='Proposal PI name')

    #
    # Instrument mode
    #
    xrt_mode = forms.TypedChoiceField(
        required=False,
        label='XRT mode',
        choices=SWIFT_XRT_MODE_CHOICES,
        coerce=int, # convert the string '6' to int 6
        initial=6) # Windowed Timing (WT))

    uvot_mode = forms.CharField(
        required=False,
        label='UVOT filter mode',
        initial='0x9999',
        help_text=mark_safe(('Supply a specific UVOT Filter mode or written instructions.'
                             ' See <a target=_blank'
                             ' href=https://www.swift.psu.edu/operations/mode_lookup.php>'
                             'UVOT Mode Lookup Tool</a>'
                            )),
    ) # 0x9999 is the "Filter of the Day" and does not require justification

    # required unless uvot_mode is 0x9999 (Filter of the Day)
    uvot_just = forms.CharField(
        required=False,
        label='UVOT Mode Justification',
        widget=forms.Textarea(attrs={
            'rows': 3,
            'placeholder': ('Required unless uvot_mode is 0x9999 (Filter of the Day).'
                            ' If you are not sure what filter mode to use, explain what you want here in words.')}
        ),
    )

    slew_in_place = forms.BooleanField(
        required=False,
        initial=False,
        help_text='Typically for GRISM observations.',
        label='Slew in place')

    #
    # Tiling request
    #
    tiling = forms.BooleanField(
        required=False,
        initial=False,
        help_text='Is this a tiling request?')

    number_of_tiles = forms.IntegerField(
        required=False,
        help_text=(
            'Set this if you want a fixed number of tiles. Traditional tiling patterns'
            ' are 4, 7, 19, or 37 "circular" tilings. If not set, then it will be calculated'
            ' based on target error radius.'
        ),
        initial=None,
    )

    exposure_time_per_tile = forms.FloatField(
        required=False,
        label='Exposure time per tile [s]',
        help_text=(
            'Set this if you want to have a fixed exposure time per tile. Otherwise, it will'
            ' be exposure time / number_of_tiles'
        ),
        initial=None,
    )

    tiling_justification = forms.CharField(
        required=False,
        help_text='Text description of why tiling is justified.',
        widget=forms.Textarea(attrs={
            'rows': 4,
            'placeholder': 'Please describe why tiling is justified.'
        }),
    )


    #
    # Debug parameter
    #
    debug = forms.BooleanField(required=False, label='Debug', initial=True)



    def layout(self):
        layout = Layout(
            'urgency',
            Accordion(
                AccordionGroup('Target Information',
                'target_classification_choices',
                'target_classification',
                'grb_detector',
                'grb_triggertime',
                'poserr',
                ),
                AccordionGroup('Science Justification',
                    Div(
                        'immediate_objective',
                        'science_just',
                    )
                ),
                AccordionGroup('Instrument Information',
                    Div(
                        Div(# this div is to put instrument drop-down and slew_in_place checkbox
                            # side-by-side in the same row
                            Div(Field('instrument'), css_class='col-md-6',),
                            Div(Field('slew_in_place'), css_class='col-md-6',),
                            css_class='row',
                        ),
                        'xrt_mode',
                        'uvot_mode',
                        'uvot_just',
                    ),
                ),
                AccordionGroup('Source Brightness',
                    Div(
                        'obs_type',
                        'optical_magnitude',
                        'optical_filter',
                        'xrt_countrate',
                        'bat_countrate',
                        'other_brightness',
                    ),
                ),
                AccordionGroup('Exposure Information',
                    Div(
                        'exposure',
                        'exp_time_just',
                    ),
                    Div(
                        'num_of_visits',
                        'exp_time_per_visit',
                        Div(
                            Div(Field('monitoring_freq'), css_class='col-md-6',),
                            Div(Field('monitoring_units'), css_class='col-md-6',),
                            css_class='row',
                        ),
                    )
                ),
                AccordionGroup('Tiling',
                    Div(
                        'tiling',
                        'number_of_tiles',
                        'exposure_time_per_tile',
                        'tiling_justification',
                    )
                ),
                AccordionGroup('Swift Guest Investigator',
                    Div(
                        'proposal',
                        'proposal_id',
                        'proposal_pi',
                        'proposal_trigger_just',
                    )
                ),
            ),
            'debug'
        ) # end layout

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
        # the two). NB: field can be None.
        #
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
        plus the target information should be sufficient. See _configure_too() for how
        the observation_payload is used to configure the TOO attributes.
        """
        # At the moment it's unclear why the obeervation_payload needs to differ from
        # the form.cleaned_data...
        payload = self.cleaned_data.copy() # copy() just to be safe

        # ...but we need to add the target information because only the target_id is
        # in the form via get_initial().
        target = Target.objects.get(pk=self.cleaned_data['target_id'])
        payload['source_name'] = target.name
        payload['ra'] = target.ra
        payload['dec'] = target.dec

        return payload


class SwiftFacility(BaseObservationFacility):
    def __init__(self):
        super().__init__()
        self.swift_api = SwiftAPI()

    name = 'Swift'
    observation_types = [
        ('OBSERVATION', 'Custom Observation')
    ]

    observation_forms = {
        'Swift TOO Observation': SwiftObservationForm,
    }

    template_name = 'tom_swift/observation_form.html'

    def get_facility_context_data(self, **kwargs):
        """Provide Facility-specific data to context for ObservationCreateView's template

        This method is called by ObservationCreateView.get_context_data() and returns a
        dictionary of context data to be added to the View's context
        """
        facility_context_data = super().get_facility_context_data(**kwargs)
        logger.debug(f'get_facility_context_data -- kwargs: {kwargs}')

        # get the username from the SwiftAPI for the context
        username = self.swift_api.get_credentials()[0]  # returns (username, shared_secret)
        new_context_data = {
            'version': __version__,  # from tom_swift/__init__.py
            'username': username,
        }

        # get the resovled target info from the SwiftAPI
        target = kwargs['target']
        resolved_target = self.swift_api.resolve_target(target)
        if resolved_target:
            new_context_data['resolver'] = resolved_target.resolver
            new_context_data['resolved_target_name'] = resolved_target.name
            new_context_data['resolved_target_ra'] = resolved_target.ra
            new_context_data['resolved_target_dec'] = resolved_target.dec
        else:
            # TODO: display bootstrap warning alert
            new_context_data['resolved_target_name'] = 'Target not resolved'

        facility_context_data.update(new_context_data)
        return facility_context_data

    def get_form(self, observation_type):
        return SwiftObservationForm

    def all_data_products(self, observation_record):
        data_products = super().all_data_products(observation_record)
        logger.debug(f'all_data_products: {data_products}')
        # TODO: right now we just extend this to log a debug message. So remove this
        # and just let the super class method handle it, when we're finished developing.
        return data_products

    def data_products(self, observation_id, product_id=None):
        logger.debug('data_products')
        # TODO: how do we get data products from Swift?
        return []

    def get_observation_status(self):
        logger.debug('get_observation_status')
        raise NotImplementedError('SwiftFacility.get_observation_status not yet implemented')

    def get_observation_url(self, observation_id):
        """
        """
        logger.debug('get_observation_url')
        return 'SwiftFacility.get_observation_url()'

    def get_observing_sites(self):
        """Normally this would return an iterable dictionary of site LAT,LON,ELV values
        to be used for target visibiliy window calculations. See, for example,
        tom_base/tom_observations/facilities/ocs.py::OCSSettings.get_sites()

        Swift is entirely different. Just return and empty dict for now.
        """
        logger.debug('get_observing_sites')
        return {}

    def get_terminal_observing_states(self):
        """
        """
        # super().get_terminal_observing_states() returns None
        # TODO: this just a made-up list of states. Find out what the real states are.
        terminal_states = ['Completed', 'Failed', 'Canceled']

        logger.warning(f'get_terminal_observing_states - (FAKE!) terminal_states: {terminal_states}')

        return terminal_states



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
        self.swift_api.too.debug = observation_payload['debug']

        #
        # User identification
        #
        self.swift_api.too.username, self.swift_api.too.shared_secret = self.swift_api.get_credentials()

        #
        # Source name, type, location, position_error
        #
        self.swift_api.too.source_name = observation_payload['source_name']
        self.swift_api.too.ra = observation_payload['ra']
        self.swift_api.too.dec = observation_payload['dec']
        self.swift_api.too.poserr = observation_payload['poserr']

        # Get the source_type from target_classification_choices or target_classification
        # depending on if they selected "Other (please specify)" in the drop-down menu
        if observation_payload['target_classification_choices'] == 'Other (please specify)':
            # they specified a custom target classification. So, use that.
            self.swift_api.too.source_type = observation_payload['target_classification']
        else:
            # use the value from the drop-down menu
            self.swift_api.too.source_type = observation_payload['target_classification_choices']

        #
        # TOO Request details
        #
        self.swift_api.too.instrument = observation_payload['instrument']
        self.swift_api.too.urgency = observation_payload['urgency']

        #
        # Observation Type
        #     What is driving the exposure time? (Spectroscopy, Light Curve, Position, Timing)
        self.swift_api.too.obs_type = observation_payload['obs_type']

        #
        # Description of the source brightness for various instruments
        #
        # Object Brightness
        self.swift_api.too.opt_mag = observation_payload['optical_magnitude']
        self.swift_api.too.opt_filt = observation_payload['optical_filter']
        self.swift_api.too.xrt_countrate = observation_payload['xrt_countrate']  # counts/second
        self.swift_api.too.bat_countrate = observation_payload['bat_countrate']  # counts/second
        self.swift_api.too.other_brightness = observation_payload['other_brightness']
        # TODO: validation - answer at least one of these questions

        #
        # GRB stuff
        #
        # TODO: GRB stuff

        #
        # Science Justification
        #
        self.swift_api.too.immediate_objective = observation_payload['immediate_objective']
        self.swift_api.too.science_just = observation_payload['science_just']

        #
        # Exposure requested time (total)
        #
        self.swift_api.too.exposure = observation_payload['exposure']
        self.swift_api.too.exp_time_just = observation_payload['exp_time_just']

        #
        # Monitoring requests
        #
        self.swift_api.too.num_of_visits = observation_payload['num_of_visits'] # use assignment expression?
        if self.swift_api.too.num_of_visits > 1:
            self.swift_api.too.exp_time_per_visit = observation_payload['exp_time_per_visit']
            # construct monitoring_freq from monitoring_freq and monitoring_units e.g '1 hour'
            self.swift_api.too.monitoring_freq = f"{observation_payload['monitoring_freq']} {observation_payload['monitoring_units']}"
        else:
            self.swift_api.too.exp_time_per_visit = None
            self.swift_api.too.monitoring_freq = None

        #
        # Swift Guest Investigator program parameters
        #
        # TODO: Guest InvestigatorI Program Support
        # Are you triggering a GI program? (yes/no)
        # if yes, then
        #   GI Program Details: Proposal ID; Proposal PI; Trigger Justification
        # Since "this will count against the number of awarded triggers", show
        # triggers used / total number triggers awarded. (and trigger remaining?)..
        if observation_payload['proposal']:
            # this is a Swift Guest Investigator request, so set it's too attributes
            self.swift_api.too.proposal = observation_payload['proposal']
            self.swift_api.too.proposal_id = observation_payload['proposal_id']
            self.swift_api.too.proposal_pi = observation_payload['proposal_pi']
            self.swift_api.too.proposal_trigger_just = observation_payload['proposal_trigger_just']
        else:
            # just in case there are previously set attributes lingering in the too, reset them
            self.swift_api.too.proposal = False
            self.swift_api.too.proposal_id = None
            self.swift_api.too.proposal_pi = None
            self.swift_api.too.proposal_trigger_just = None

        #
        # Instrument mode
        #
        # self.swift_api.too.instrument is set above in the TOO Request details section
        # Set and unset too.attributes according to the instrument selected.
        if self.swift_api.too.instrument == 'BAT':
            # not sure what to do here!  TODO: find out
            self.swift_api.too.xrt_mode = None
            self.swift_api.too.uvot_mode = None
            self.swift_api.too.uvot_just = None
        elif self.swift_api.too.instrument == 'UVOT':
            self.swift_api.too.uvot_mode = observation_payload['uvot_mode']
            self.swift_api.too.uvot_just = observation_payload['uvot_just']
            self.swift_api.too.xrt_mode = None
        else:
            # XRT mode
            self.swift_api.too.xrt_mode = observation_payload['xrt_mode']
            self.swift_api.too.uvot_mode = None
            self.swift_api.too.uvot_just = None
        self.swift_api.too.slew_in_place = observation_payload['slew_in_place']

        #
        # Tiling request
        #
        if observation_payload['tiling']:
            # this is a tiling request to set tiling too attributes
            self.swift_api.too.tiling = observation_payload['tiling']
            self.swift_api.too.number_of_tiles = observation_payload['number_of_tiles']
            self.swift_api.too.exposure_time_per_tile = observation_payload['exposure_time_per_tile']
            # TODO: validation, if exposure_time_per_tile is unset, position_error should be set
            self.swift_api.too.tiling_justification = observation_payload['tiling_justification']
        else:
            # just in case there are previously set attributes lingering in the too, reset them
            self.swift_api.too.tiling = False
            self.swift_api.too.number_of_tiles = None
            self.swift_api.too.exposure_time_per_tile = None
            self.swift_api.too.tiling_justification = None

        #
        # Debug parameter
        #
        self.swift_api.too.debug = observation_payload['debug']

        logger.info(f'SwiftFacility._configure_too - configured too:\n{self.swift_api.too}')


    def validate_observation(self, observation_payload) -> []:
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

        #logger.debug(f'validate_observation - too.status: {self.swift_api.too.status}')
        ##logger.debug(f'validate_observation - dir(too.status): {dir(self.swift_api.too.status)}')
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
        #    logger.debug(f'validate_observation - too.status.{property}: {getattr(self.swift_api.too.status, property)}')

        if not (too_is_valid and too_is_server_valid):
            logger.debug(f'validate_observation - too.status.status: {self.swift_api.too.status.status}')
            logger.debug(f'validate_observation - too.status.errors: {self.swift_api.too.status.errors}')
            logger.debug(f'validate_observation - type(too.status.errors): {type(self.swift_api.too.status.errors)}')
            
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

        # TODO: remove this for production
        if not self.swift_api.too.debug:
            # while in development, exit early if we're not in debug mode. (i.e. don't submit).
            logger.warning(f'submit_observation - Skipping ACTUAL submission!!! too.debug: {self.swift_api.too.debug}'
                           f' Even though, in the form, Debug is {self.swift_api.too.debug}, it is being reset'
                           f' to True before we call too.submit()')
            self.swift_api.too.debug = True

        logger.debug(f'calling too.submit()')
        self.swift_api.too.submit()
        logger.debug(f'too.submit() returned')

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

        too_id = None
        if self.swift_api.too.status.status == 'Accepted':
            too_id = self.swift_api.too.status.too_id
            # this was a successful submission
            logger.info(f'submit_observation - too.status.status: {self.swift_api.too.status.status}')
            logger.info(f'submit_observation - too_id: {too_id}')

            # lets examine the TOO created
            # see https://www.swift.psu.edu/too_api/index.php?md=Swift TOO Request Example Notebook.ipynb

            if self.swift_api.too.debug:
                # this was a debug submission and thus, no TOO was made and
                # the too_id returned in the too.status is points to nothing.
                logger.warning((f'submit_observation - DEBUG submission - too_id: {too_id} is not real.'))
        else:
            logger.error(f'submit_observation - too.status.status: {self.swift_api.too.status.status}')

        # TODO: remove this -- it is only for debugging/development
        #self.swift_api.too.status.too_id = 19529 # an actual NCG1566 TOO

        return [too_id]


