from django import forms
from tom_swift.models import SwiftProfile
from tom_common.session_utils import set_encrypted_field, get_encrypted_field


class SwiftProfileForm(forms.ModelForm):

    # even though this is a ModelForm (and we automatically have forms.Fields for
    # each SwiftProfile model field), we have to add CharFields for any encrypted
    # fields because they exist in the model as a combination property descriptor
    # and BinaryField. )
    swift_shared_secret = forms.CharField(
        required=False,
        label="Shared Secret",
        help_text="Enter your Swift TOO shared secret. Leave blank to keep unchanged."
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        # set the initial value of the swift_shared_secret CharField
        if self.instance and self.instance.pk:
            self.fields['swift_shared_secret'].initial = get_encrypted_field(self.user, self.instance, 'swift_shared_secret')

    class Meta:
        model = SwiftProfile
        fields = ['swift_username', 'swift_shared_secret']

    def save(self, commit=True):
        """Override save to handle the custom encrypted property."""
        # The form's 'swift_shared_password' is not a model field, so super().save() will ignore it,
        # because super() is forms.ModelForm.
        instance = super().save(commit=False)

        cleaned_swift_shared_secret = self.cleaned_data.get('swift_shared_secret')
        # only update the swift_shared_secret if a new one is provided (cleaned_swift_shared_secret of '' is False)
        if cleaned_swift_shared_secret:
            # The user object is available from the instance
            user = instance.user
            # Use the helper to set the encrypted field
            success = set_encrypted_field(user, instance, 'swift_shared_secret', cleaned_swift_shared_secret)

            if not success:
                # The helper function returns False on failure. We can add an error to the form.
                self.add_error(None, "Could not save encrypted password due to a server error. "
                                     "Please ensure you are logged in correctly.")

        if commit and not self.errors:
            instance.save()
        return instance
