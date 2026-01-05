"""
Tests for Swift instrument/mode validation and configuration.

These tests verify that instrument-specific mode requirements are properly handled.
"""
from django.contrib.auth.models import User
from django.test import TestCase

from tom_observations.facility import CredentialStatus
from tom_swift.swift import SwiftFacility, SwiftObservationForm
from tom_swift.swift_api import SwiftAPI
from tom_swift.models import SwiftProfile


class InstrumentModeConfigurationTests(TestCase):
    """Test that _configure_too() properly handles instrument-specific modes."""

    def setUp(self):
        """Set up test fixtures."""
        self.facility = SwiftFacility()
        self.user = User.objects.create_user(username='testuser', password='testpass')

        # Create a Swift profile (don't worry about encrypted field in tests)
        self.profile = SwiftProfile.objects.create(
            user=self.user,
            swift_username='testuser'
        )

        # Mock the facility API setup since we don't have encrypted credentials in tests
        self.facility.user = self.user
        self.facility.swift_api = SwiftAPI()
        self.facility.swift_api.set_credentials('testuser', 'testsecret')
        self.facility.credential_status = CredentialStatus.USING_USER_CREDS

    def test_uvot_instrument_ignores_user_xrt_mode(self):
        """Test that UVOT instrument observations ignore user-selected xrt_mode.

        The swifttools TOO object always includes xrt_mode in api_data with a default value.
        This test verifies that we DON'T set the user's xrt_mode choice when UVOT is selected.
        The xrt_mode should remain at its default value (PC or Unset), not the user's choice (WT).
        """
        observation_payload = {
            'debug': True,
            'source_name': 'Test Source',
            'ra': 150.0,
            'dec': 10.0,
            'poserr': 0.0,
            'target_classification_choices': 'Supernova',
            'instrument': 'UVOT',  # UVOT selected
            'urgency': 3,
            'obs_type': 'Light Curve',
            'optical_magnitude': 15.0,
            'optical_filter': 'V',
            'xrt_countrate': None,
            'bat_countrate': None,
            'other_brightness': '',
            'grb_detector_choices': '',
            'grb_triggertime': None,
            'immediate_objective': 'Test objective',
            'science_just': 'Test justification',
            'exposure': 1000.0,
            'exp_time_just': 'Need 1000s',
            'exp_time_per_visit': None,
            'num_of_visits': 1,
            'monitoring_freq': 1,
            'monitoring_units': 'days',
            'proposal': False,
            'proposal_id': '',
            'proposal_pi': '',
            'proposal_trigger_just': '',
            'xrt_mode': 6,  # User selected Windowed Timing - should be IGNORED
            'uvot_mode_choices': '0x9999',
            'uvot_mode': '',
            'uvot_just': '',
            'slew_in_place': False,
            'tiling': False,
            'number_of_tiles': None,
            'exposure_time_per_tile': None,
            'tiling_justification': '',
        }

        self.facility._configure_too(observation_payload)

        # The swifttools library always includes xrt_mode with a default value
        self.assertIn('xrt_mode', self.facility.swift_api.too.api_data,
                     "xrt_mode will be in api_data (swifttools default behavior)")
        # Verify we didn't set it to the user's choice (WT = Windowed Timing)
        self.assertNotEqual(self.facility.swift_api.too.api_data['xrt_mode'], 'WT',
                           "xrt_mode should not be set to user's choice (WT) when instrument is UVOT")
        # It should be the default (PC or Unset)
        self.assertIn(self.facility.swift_api.too.api_data['xrt_mode'], ['PC', 'Unset'],
                     f"xrt_mode should be default value, got: {self.facility.swift_api.too.api_data['xrt_mode']}")

    def test_xrt_instrument_uses_default_uvot_mode(self):
        """Test that XRT instrument observations use default uvot_mode.

        The swifttools TOO object always includes uvot_mode in api_data.
        This test verifies we don't set a custom uvot_mode when XRT is selected.
        The uvot_mode should remain at the default value (0x9999 = Filter of the Day).
        """
        observation_payload = {
            'debug': True,
            'source_name': 'Test Source',
            'ra': 150.0,
            'dec': 10.0,
            'poserr': 0.0,
            'target_classification_choices': 'Supernova',
            'instrument': 'XRT',  # XRT selected
            'urgency': 3,
            'obs_type': 'Light Curve',
            'optical_magnitude': 15.0,
            'optical_filter': 'V',
            'xrt_countrate': None,
            'bat_countrate': None,
            'other_brightness': '',
            'grb_detector_choices': '',
            'grb_triggertime': None,
            'immediate_objective': 'Test objective',
            'science_just': 'Test justification',
            'exposure': 1000.0,
            'exp_time_just': 'Need 1000s',
            'exp_time_per_visit': None,
            'num_of_visits': 1,
            'monitoring_freq': 1,
            'monitoring_units': 'days',
            'proposal': False,
            'proposal_id': '',
            'proposal_pi': '',
            'proposal_trigger_just': '',
            'xrt_mode': 6,  # User's XRT mode choice - should be used
            'uvot_mode_choices': '0x9999',  # Default UVOT mode
            'uvot_mode': '',
            'uvot_just': '',
            'slew_in_place': False,
            'tiling': False,
            'number_of_tiles': None,
            'exposure_time_per_tile': None,
            'tiling_justification': '',
        }

        self.facility._configure_too(observation_payload)

        # uvot_mode will be in api_data with default value
        self.assertIn('uvot_mode', self.facility.swift_api.too.api_data,
                     "uvot_mode will be in api_data (swifttools default behavior)")
        # Should be the default Filter of the Day
        self.assertEqual(self.facility.swift_api.too.api_data['uvot_mode'], '0x9999',
                        f"uvot_mode should be default (0x9999), got: {self.facility.swift_api.too.api_data['uvot_mode']}")

    def test_bat_instrument_uses_default_modes(self):
        """Test that BAT instrument observations use default xrt_mode and uvot_mode.

        The swifttools TOO object always includes both modes in api_data with default values.
        This test verifies we don't set custom modes when BAT is selected.
        """
        observation_payload = {
            'debug': True,
            'source_name': 'Test Source',
            'ra': 150.0,
            'dec': 10.0,
            'poserr': 0.0,
            'target_classification_choices': 'Supernova',
            'instrument': 'BAT',  # BAT selected
            'urgency': 3,
            'obs_type': 'Light Curve',
            'optical_magnitude': 15.0,
            'optical_filter': 'V',
            'xrt_countrate': None,
            'bat_countrate': 50.0,
            'other_brightness': '',
            'grb_detector_choices': '',
            'grb_triggertime': None,
            'immediate_objective': 'Test objective',
            'science_just': 'Test justification',
            'exposure': 1000.0,
            'exp_time_just': 'Need 1000s',
            'exp_time_per_visit': None,
            'num_of_visits': 1,
            'monitoring_freq': 1,
            'monitoring_units': 'days',
            'proposal': False,
            'proposal_id': '',
            'proposal_pi': '',
            'proposal_trigger_just': '',
            'xrt_mode': 6,  # User selection - should be IGNORED
            'uvot_mode_choices': '0x9999',
            'uvot_mode': '',
            'uvot_just': '',
            'slew_in_place': False,
            'tiling': False,
            'number_of_tiles': None,
            'exposure_time_per_tile': None,
            'tiling_justification': '',
        }

        self.facility._configure_too(observation_payload)

        # Both modes will be in api_data with default values
        self.assertIn('xrt_mode', self.facility.swift_api.too.api_data,
                     "xrt_mode will be in api_data (swifttools default behavior)")
        self.assertIn('uvot_mode', self.facility.swift_api.too.api_data,
                     "uvot_mode will be in api_data (swifttools default behavior)")
        # Verify user's xrt_mode choice (WT) was not used
        self.assertNotEqual(self.facility.swift_api.too.api_data['xrt_mode'], 'WT',
                           "xrt_mode should not be set to user's choice when instrument is BAT")
        # Both should be default values
        self.assertIn(self.facility.swift_api.too.api_data['xrt_mode'], ['PC', 'Unset'],
                     f"xrt_mode should be default, got: {self.facility.swift_api.too.api_data['xrt_mode']}")
        self.assertEqual(self.facility.swift_api.too.api_data['uvot_mode'], '0x9999',
                        f"uvot_mode should be default (0x9999), got: {self.facility.swift_api.too.api_data['uvot_mode']}")

    def test_xrt_instrument_sets_xrt_mode_correctly(self):
        """Test that XRT instrument observations properly set xrt_mode."""
        observation_payload = {
            'debug': True,
            'source_name': 'Test Source',
            'ra': 150.0,
            'dec': 10.0,
            'poserr': 0.0,
            'target_classification_choices': 'Supernova',
            'instrument': 'XRT',
            'urgency': 3,
            'obs_type': 'Light Curve',
            'optical_magnitude': 15.0,
            'optical_filter': 'V',
            'xrt_countrate': None,
            'bat_countrate': None,
            'other_brightness': '',
            'grb_detector_choices': '',
            'grb_triggertime': None,
            'immediate_objective': 'Test objective',
            'science_just': 'Test justification',
            'exposure': 1000.0,
            'exp_time_just': 'Need 1000s',
            'exp_time_per_visit': None,
            'num_of_visits': 1,
            'monitoring_freq': 1,
            'monitoring_units': 'days',
            'proposal': False,
            'proposal_id': '',
            'proposal_pi': '',
            'proposal_trigger_just': '',
            'xrt_mode': 6,  # Windowed Timing
            'uvot_mode_choices': '0x9999',
            'uvot_mode': '',
            'uvot_just': '',
            'slew_in_place': False,
            'tiling': False,
            'number_of_tiles': None,
            'exposure_time_per_tile': None,
            'tiling_justification': '',
        }

        self.facility._configure_too(observation_payload)

        # xrt_mode SHOULD be set for XRT instrument
        self.assertIn('xrt_mode', self.facility.swift_api.too.api_data,
                     "xrt_mode should be present in api_data when instrument is XRT")
        # The value should be 'WT' (Windowed Timing) after conversion
        self.assertEqual(self.facility.swift_api.too.api_data['xrt_mode'], 'WT')

    def test_uvot_instrument_sets_uvot_mode_correctly(self):
        """Test that UVOT instrument observations properly set uvot_mode."""
        observation_payload = {
            'debug': True,
            'source_name': 'Test Source',
            'ra': 150.0,
            'dec': 10.0,
            'poserr': 0.0,
            'target_classification_choices': 'Supernova',
            'instrument': 'UVOT',
            'urgency': 3,
            'obs_type': 'Light Curve',
            'optical_magnitude': 15.0,
            'optical_filter': 'V',
            'xrt_countrate': None,
            'bat_countrate': None,
            'other_brightness': '',
            'grb_detector_choices': '',
            'grb_triggertime': None,
            'immediate_objective': 'Test objective',
            'science_just': 'Test justification',
            'exposure': 1000.0,
            'exp_time_just': 'Need 1000s',
            'exp_time_per_visit': None,
            'num_of_visits': 1,
            'monitoring_freq': 1,
            'monitoring_units': 'days',
            'proposal': False,
            'proposal_id': '',
            'proposal_pi': '',
            'proposal_trigger_just': '',
            'xrt_mode': 6,
            'uvot_mode_choices': '0x30d4',  # Custom UVOT mode
            'uvot_mode': '',
            'uvot_just': 'Need specific filter',
            'slew_in_place': False,
            'tiling': False,
            'number_of_tiles': None,
            'exposure_time_per_tile': None,
            'tiling_justification': '',
        }

        self.facility._configure_too(observation_payload)

        # uvot_mode SHOULD be set for UVOT instrument
        self.assertIn('uvot_mode', self.facility.swift_api.too.api_data,
                     "uvot_mode should be present in api_data when instrument is UVOT")
        self.assertEqual(self.facility.swift_api.too.api_data['uvot_mode'], '0x30d4')


class FormCrossFieldValidationTests(TestCase):
    """Test that form validates instrument/mode combinations."""

    def setUp(self):
        """Set up test fixtures."""
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.profile = SwiftProfile.objects.create(
            user=self.user,
            swift_username='testuser'
        )
        self.facility = SwiftFacility()
        self.facility.user = self.user
        self.facility.swift_api = SwiftAPI()
        self.facility.swift_api.set_credentials('testuser', 'testsecret')
        self.facility.credential_status = CredentialStatus.USING_USER_CREDS

    def test_form_rejects_uvot_with_xrt_mode(self):
        """Test that form validation rejects UVOT instrument with XRT mode set."""
        form_data = {
            'facility': 'Swift',
            'target_id': 1,
            'observation_type': 'OBSERVATION',
            'instrument': 'UVOT',
            'xrt_mode': 6,  # This should cause validation error
            'urgency': 3,
            'target_classification_choices': 'Supernova',
            'obs_type': 'Light Curve',
            'exposure': 1000,
            'exp_time_just': 'Test',
            'immediate_objective': 'Test',
            'science_just': 'Test',
        }

        form = SwiftObservationForm(data=form_data, facility=self.facility)

        self.assertFalse(form.is_valid(),
                         "Form should be invalid when UVOT is selected with xrt_mode")
        self.assertIn('xrt_mode', form.errors,
                     "xrt_mode should have a validation error")

    def test_form_accepts_xrt_with_xrt_mode(self):
        """Test that form validation accepts XRT instrument with XRT mode."""
        form_data = {
            'facility': 'Swift',
            'target_id': 1,
            'observation_type': 'OBSERVATION',
            'instrument': 'XRT',
            'xrt_mode': 6,  # This is valid for XRT
            'urgency': 3,
            'target_classification_choices': 'Supernova',
            'obs_type': 'Light Curve',
            'exposure': 1000,
            'exp_time_just': 'Test',
            'immediate_objective': 'Test',
            'science_just': 'Test',
        }

        form = SwiftObservationForm(data=form_data, facility=self.facility)

        # Should not have xrt_mode errors (may have other errors for missing fields)
        if not form.is_valid():
            self.assertNotIn('xrt_mode', form.errors,
                           "xrt_mode should not have validation errors when XRT is selected")
