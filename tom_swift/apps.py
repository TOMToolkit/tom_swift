import logging

from django.apps import AppConfig
from django.urls import path, include


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class TomSwiftConfig(AppConfig):
    """The AppConfig for the TOMToolkit Swift Facility module.

    Integration points are implmented here.
    """
    name = 'tom_swift'

    # TOMToolkit Integration Points

    def include_url_paths(self):
        """
        Integration point for adding URL patterns to the Tom Common URL configuration.
        This method should return a list of URL patterns to be included in the main URL configuration.
        """
        urlpatterns = [
            path('swift/', include('tom_swift.urls')),
        ]
        return urlpatterns

    def profile_details(self):
        """
        Integration point for adding items to the user profile page.

        This method should return a list of dictionaries that include a `partial` key pointing to the path of the html
        profile partial. The `context` key should point to the dot separated string path to the templatetag that will
        return a dictionary containing new context for the accompanying partial.
        Typically, this partial will be a bootstrap card displaying some app specific user data.
        """
        profile_config = [
            {
                'partial': f'{self.name}/partials/swift_user_profile.html',
                'context': f'{self.name}.templatetags.swift_extras.swift_profile_data',
            }
        ]
        return profile_config
