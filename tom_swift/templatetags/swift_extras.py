
from django import template

from tom_common.session_utils import get_encrypted_field

from tom_swift.models import SwiftProfile
from tom_swift.forms import SwiftProfileForm

register = template.Library()


@register.inclusion_tag('tom_swift/partials/swift_user_profile.html')
def swift_profile_data(user) -> dict:
    """
    Gathers the Swift profile data for display in the user profile partial.

    This tag prepares a structured list of data for the template, including
    field labels (verbose_name) and their corresponding values. This is more
    robust than using model_to_dict, as it gives full control over the
    presentation and handles non-model fields (like encrypted properties)
    gracefully.
    """
    try:
        profile: SwiftProfile = user.swiftprofile
    except SwiftProfile.DoesNotExist:
        profile = SwiftProfile.objects.create(user=user)

    profile_data_list = []

    # Define the standard model fields we want to display.
    model_fields_to_display = ['swift_username']

    for field_name in model_fields_to_display:
        field = profile._meta.get_field(field_name)
        # Use get_..._display() for choice fields to get the human-readable value.
        if hasattr(profile, f'get_{field_name}_display'):
            value = getattr(profile, f'get_{field_name}_display')()
        else:
            value = getattr(profile, field_name)

        profile_data_list.append({
            'label': field.verbose_name,
            'value': value,
        })

    # Handle the special case of the encrypted shared_secret field.
    decrypted_shared_secret = get_encrypted_field(user, profile, 'swift_shared_secret')
    shared_secret_label = SwiftProfileForm.base_fields['swift_shared_secret'].label or 'Shared Secret'

    shared_secret_display_value = decrypted_shared_secret
    if decrypted_shared_secret is None:
        shared_secret_display_value = "[Password not available]"

    profile_data_list.append({'label': shared_secret_label, 'value': shared_secret_display_value})

    return {'user': user, 'swift_profile': profile, 'profile_data_list': profile_data_list}