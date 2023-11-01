# tom_swift
[Neil Gehrels Swift Observatory](https://swift.gsfc.nasa.gov/index.html) facility module for TOM Toolkit. This module uses the
[Swift TOO API](https://www.swift.psu.edu/too_api/) for all its interactions with the _Swift_ Observatory. When installed and
configured, your TOM can query target visibility, submit TOO observation requests to Swift, and check TOO observation status.

## Swift TOO Prerequisites
In order to submit TOO requests to Swift, you must [register with the Swift TOO system](https://www.swift.psu.edu/toop/too_newuser.php).
Once you are registered and have logged in, you can [get your shared secret](https://www.swift.psu.edu/toop/change_secret.php), which you
will use, along with your username, to make TOO requests. See the Configuration section below.

## Installation

Install the module into your TOM environment:

```shell
pip install tom-swift
```

1. In your project `settings.py`, add `tom_swift` to your `INSTALLED_APPS` setting:

    ```python
    INSTALLED_APPS = [
        ...
        'tom_swift',
    ]
    ```

2. Add `tom_swift.swift.SwiftFacility` to the `TOM_FACILITY_CLASSES` in your TOM's
`settings.py`:
   ```python
    TOM_FACILITY_CLASSES = [
        'tom_observations.facilities.lco.LCOFacility',
        ...
        'tom_swift.swift.SwiftFacility',
    ]
   ```   

## Configuration

Include the following settings inside the `FACILITIES` dictionary inside `settings.py`:

```python
    FACILITIES = {
        ...
        'SWIFT': {
            'SWIFT_USERNAME': os.getenv('SWIFT_USERNAME', 'anonymous'),
            'SWIFT_SHARED_SECRET': os.getenv('SWIFT_SHARED_SECRET', 'anonymous'),
        },
    }
```

If you followed the Prerequsites section above, then you have a Swift TOO username and shared secret.
(Your shared secret is _not_ your Swift TOO account password). Set environment variables `SWIFT_USERNAME`
and `SWIFT_SHARED_SECRET` to your Swift TOO username and shared secret, respectively. (Do not check them
into any software repository).

```shell
export SWIFT_USERNAME='<your Swift TOO usename>'
export SWIFT_SHARED_SECRET='<your Swift TOO shared secret>'
```

The `settings.FACILITIES['Swift']` configuration dictionary
above will get the values from the environment variables that you set. Your TOM will then use them to interact
with the Swift TOO API.
