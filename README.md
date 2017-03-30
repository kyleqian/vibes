# Vibes
YouTube Playlist Downloader &amp; Organizer

1) Install requirements (ffmpeg could take a while to fully install, and is necessary for iTunes):
```
$ pip install -r requirements.txt
$ brew install youtube-dl
$ brew install ffmpeg
```

2) Copy the sample settings file:
```
$ cp sample_vibes_settings.py vibes_settings.py
```

3) Fill out credentials as needed in vibes_settings.py:
```
  #!/usr/bin/python
  import os

  vibes_settings = {

    # FILL THESE OUT
    "YT_CHANNEL_ID": "",
    "YT_API_KEY": "",

    # By default saves everything in a main directory on the desktop called VibesMusic
    "MAIN_DIR_PATH": os.path.expanduser("~/Desktop/VibesMusic")
  }
```

4) Start downloading to directory designated in vibes_settings.py:
```
$ python vibes.py
```
