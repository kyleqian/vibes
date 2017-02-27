#!/usr/bin/python
import requests
import os
import errno
import json
import pafy
import pdb
import shutil
from time import sleep
from vibes_settings import vibes_settings

# TODO: Try-catch blocks
# TODO: Cut down on API response size via fields/part params
# TODO: %s -> string.format?
# TODO: Limited to 50 playlists for now
# TODO: What if video not available
# TODO: Create temporary staging directory where new audio files are downloaded along with artwork, combine them there, then
# TODO: http://stackoverflow.com/questions/23301256/python-mutagen-add-cover-photo-album-art-by-url
# TODO: After that, move to main directory and clean up staging, remove staging directory at the very end
# TODO: https://img.youtube.com/vi/<insert-youtube-video-id-here>/maxresdefault.jpg
# TODO: Hacky .replace?
class Vibes(object):
  def __init__(self):
    self.YT_API_KEY = vibes_settings["YT_API_KEY"]
    self.YT_CHANNEL_ID = vibes_settings["YT_CHANNEL_ID"]
    self.PLAYLISTS_URL = "https://www.googleapis.com/youtube/v3/playlists?key=%s&part=snippet&maxResults=50&channelId=%s" % (self.YT_API_KEY, self.YT_CHANNEL_ID)
    self.PLAYLISTITEMS_URL = "https://www.googleapis.com/youtube/v3/playlistItems?key=%s&part=snippet&maxResults=50&playlistId=" % self.YT_API_KEY
    self.MAIN_DIR_PATH = vibes_settings["MAIN_DIR_PATH"]
    self.LIBRARY_PATH = self.MAIN_DIR_PATH + "/lib.json"
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

          # Create Pafy object and grab audio
          pafy_object = pafy.new(video_id, basic=False)

          # Assemble and download file and metadata
          self.__process_pafy(pafy_object)

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

  def __process_pafy(self, pafy_object):
    # Get audio stream from Pafy
    audio = pafy_object.getbestaudio(preftype="m4a")

    # Download audio file to assembler directory
    # remux_audio necessary to play on iTunes
    # >>> Requires ffmpeg installed <<<
    file_path = audio.download(quiet=True, filepath=curr_assembler_path, remux_audio=True)

    # Assemble audio file with metadata
    pass

    # Move assembled file into parent directory and clear assembler
    shutil.move(file_path, file_path.replace("/assembler"))
    self.__clear_dir(curr_assembler_path)

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

if __name__ == '__main__':
  V = Vibes()
  V.pull()
