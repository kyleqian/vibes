#!/usr/bin/python
import requests
import os
import errno
import json
import pafy
import pdb
import shutil
from time import sleep
from mutagen.mp4 import MP4, MP4Cover
from vibes_settings import vibes_settings

# TODO: Try-catch blocks
# TODO: Cut down on API response size via fields/part params
# TODO: %s -> string.format?
# TODO: Limited to 50 playlists for now
# TODO: What if video not available
# TODO: Hacky .replace?
class Vibes(object):
  def __init__(self):
    self.YT_API_KEY = vibes_settings["YT_API_KEY"]
    self.YT_CHANNEL_ID = vibes_settings["YT_CHANNEL_ID"]
    self.PLAYLISTS_URL = "https://www.googleapis.com/youtube/v3/playlists?key=%s&part=snippet&maxResults=50&channelId=%s" % (self.YT_API_KEY, self.YT_CHANNEL_ID)
    self.PLAYLISTITEMS_URL = "https://www.googleapis.com/youtube/v3/playlistItems?key=%s&part=snippet&maxResults=50&playlistId=" % self.YT_API_KEY
    self.MAIN_DIR_PATH = vibes_settings["MAIN_DIR_PATH"]
    self.LIBRARY_PATH = self.MAIN_DIR_PATH + "/lib.json"
    self.COVER_ART_URL = "https://img.youtube.com/vi/%s/maxresdefault.jpg"
    pafy.set_api_key(self.YT_API_KEY)

  def pull(self):
    # Create main directory
    self.__create_dir(self.MAIN_DIR_PATH, dirtype="main")

    # Load library
    library = json.load(open(self.LIBRARY_PATH, "r"))
    assert isinstance(library, dict)

    # Get all playlists
    playlists = requests.get(self.PLAYLISTS_URL).json()["items"]

    for p in playlists:
      playlist_id = p["id"]
      playlist_title = p["snippet"]["title"]

      # Create directory for playlist, plus the containing assembler directory
      curr_playlist_path = self.MAIN_DIR_PATH + "/" + playlist_title
      curr_assembler_path = curr_playlist_path + "/assembler"
      self.__create_dir(curr_playlist_path)
      self.__create_dir(curr_assembler_path, dirtype="assembler")
      # log = open(curr_playlist_path + "/log.txt", "a")

      # Add playlist to library
      if playlist_id not in library:
        library[playlist_id] = {
          "title": playlist_title,
          "items": {}
        }

      counter = 0
      page_token = ""
      while True:
        # Get page of videos in playlist
        videos_json = requests.get(self.PLAYLISTITEMS_URL + playlist_id + "&pageToken=" + page_token).json()
        page_token = videos_json["nextPageToken"] if "nextPageToken" in videos_json else ""

        videos = videos_json["items"]
        for v in videos:
          video_id = v["snippet"]["resourceId"]["videoId"]
          video_title = v["snippet"]["title"]

          # Skip if already in library
          if video_id in library[playlist_id]["items"]: continue

          # Create Pafy object and download audio
          pafy_object = pafy.new(video_id, basic=False)
          audio_stream = pafy_object.getbestaudio(preftype="m4a")

          # Download audio file to assembler directory
          # remux_audio necessary to play on iTunes
          # >>> Requires ffmpeg installed <<<
          file_path = audio_stream.download(quiet=True, filepath=curr_assembler_path, remux_audio=True)

          # Assemble metadata
          self.__assemble(pafy_object, file_path)

          # Move assembled file into parent directory and clear assembler
          shutil.move(file_path, file_path.replace("/assembler", ""))
          self.__clear_dir(curr_assembler_path)

          # Update library file
          library[playlist_id]["items"][video_id] = video_title
          with open(self.LIBRARY_PATH, "w") as lib:
            lib.write(json.dumps(library, indent=2, sort_keys=True))

          # Console log
          counter += 1
          data = "%s || %s || %d" % (video_id, video_title, counter)
          print data
          # log.write(data + os.linesep)

          # Sleep in case of rate limiting
          # sleep(5)

        # No more videos
        if page_token == "": break

      # Delete assembler directory
      shutil.rmtree(curr_assembler_path)

      # log.close()

  def __assemble(self, pafy_object, file_path):
    # Open audio file with Mutagen and assemble metadata
    audio_file = MP4(file_path)
    audio_file["\xa9cmt"] = pafy_object.videoid

    # Cover art
    cover_art = requests.get(self.COVER_ART_URL % pafy_object.videoid)
    audio_file["covr"] = [MP4Cover(cover_art.content, MP4Cover.FORMAT_JPEG)]

    # Save metadata
    audio_file.save()

  # Creates directory; defaults to playlist
  def __create_dir(self, path, dirtype="playlist"):
    try:
      os.makedirs(path)
    except OSError as exception:
      if exception.errno != errno.EEXIST:
        raise

    # Default playlist dir
    if dirtype == "playlist":
      pass

    # Main dir including library file
    elif dirtype == "main":
      if os.path.isfile(self.LIBRARY_PATH) == False:
        with open(self.LIBRARY_PATH, "w") as lib:
          lib.write("{}")

    # Assembler dir, makes sure it's empty
    elif dirtype == "assembler":
      self.__clear_dir(path)

    # Unknown type
    else:
      raise

  # Clears directory
  def __clear_dir(self, path):
    try:
      shutil.rmtree(path)
      os.makedirs(path)
    except OSError as exception:
      if exception.errno != errno.EEXIST:
        raise

if __name__ == "__main__":
  V = Vibes()
  V.pull()
