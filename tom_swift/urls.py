from django.urls import path

from tom_swift.views import ProfileUpdateView

app_name = 'tom_swift'

# by convention, URL patterns and names have dashes, while function names
# (as python identifiers) have underscores.
urlpatterns = [
    path('users/<int:pk>/update/', ProfileUpdateView.as_view(), name='swift-profile-update'),
]
