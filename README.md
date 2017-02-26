# Vibes
YouTube Playlist Downloader &amp; Organizer

1) Copy the sample settings file:
```
$ cp sample_vibes_settings.py vibes_settings.py
```
2) Fill out credentials as needed in vibes_settings.py:
```
  #!/usr/bin/python
  import os

  vibes_settings = {

    # FILL THESE OUT
    "YT_CHANNEL_ID": "",
    "YT_API_KEY": "",

    # By default saves everything in a main folder on the desktop called Vibes
    "MAIN_FOLDER_PATH": os.path.expanduser("~/Desktop/Vibes")
  }
```
