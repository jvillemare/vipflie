import requests     # Downloading stream info and media
import time         # Sleeping in between failed HTTP requests
import os           # Checking if files exist
import glob         # For clearing segment directory
import re           # For extracting ID of clip
import datetime     # For creating new segment IDs

class DelDOT:
    """
	:author: James Villemarette (@jvillemare)

    Simple class for streaming a single DelDOT camera video.

    Here's how it works:
    1. First, this script load the playlist for a camera, which gives us the
       name of the chunklist.
    2. After loading the chunklist, we're given the names of the media clips.
    3. The media clips are downloaded and renamed appropriately.

    Here's the stuff you'll need:
        - get_missing_media():  Downloads all available clips, while also
                                renaming them into a usable, standard format.
                                Returns True if there's new clips, False if not.
        - get_next_segment():   Returns the file name of the next sequential
                                clip. Returns False if no clips have been
                                downloaded, or if you're on the latest clip.
                                Otherwise, returns the filename of the next
                                sequential clip.
    """

    class DelDOTException(Exception):
        """
        Custom exception for when too many failed HTTP requests are made.
        """
        pass

    def __init__(self, cameraID, segmentDir="buffer", retries=3, timeout=10, verbose=False):
        """
        Constructor.
        :param cameraID:        ID of the camera being streamed.
        :param segmentDir:      Directory where streaming segments are stored.
                                Does NOT need a trailing slash.
        :param retries:         Number of times to retry any HTTP request. If
                                -1, it will keep retrying requests.
        :param timeout:         Amount of time in seconds between retries.
        :param verbose:         True to print info and warning messages. False
                                to print no messages.
        """
        self.buffering = True           # Are we currently loading the video?
        self.cameraID = cameraID        # ID of the camera being streamed
        self.cameraURL = 'https://video.deldot.gov/live/' + self.cameraID + '.stream'
        self.segmentDir = segmentDir    # Where segments are held
        self.segments = []              # List of all the segment names that are downloaded
        self.renamedSegments = []       # Same as segments^, but prefixes the clips with YEARmonthDAY
        self.currentSegment = 0         # Index of the current segment^
        self.latest_chunklist = None    # Name of the latest chunklist
        self.retries = retries          # Number of times to retry an HTTP request
        self.timeout = timeout          # Cooldown time between retries (in seconds)
        self.verbose = verbose          # True to print info/warns, False if not

    def retrieve_playlist_manifest(self):
        """
        Retrieve the latest playlist that contains the latest chunklist.
        :returns: String of the name of the latest chunklist. False if the
            chunklist has not updated.
        """
        attempts = 0
        playlist = None
        while True:
            playlist = requests.get(self.cameraURL + '/playlist.m3u8')
            if playlist.status_code < 400:
                break
            else:
                attempts += 1
            if self.verbose:
                if self.retires != -1:
                    print('WARN: Failed to get playlist manifest. ' + str(attempts) + '/' + str(self.retries) + ' attempts remaining')
                else:
                    print('WARN: Failed to get playlist manifest. Currently at ' + str(attempts) + ' attempts')
            if attempts > self.retries:
                if self.retries == -1: # Continue indefinitely
                    continue
                else: # Stop on max retries
                    break
        playlist = playlist.text.split('\n')
        for line in playlist:
            if line.startswith('#') or len(line.strip()) == 0:
                continue # skip metadata or empty lines
            if self.latest_chunklist is not None and self.latest_chunklist == line:
                if self.verbose:
                    print('INFO: Playlist manifest has not updated; there is no new chunklist')
                return False
            self.latest_chunklist = line
            return self.latest_chunklist

    def extract_media_id(self, s):
        """
        Media file names look like "media_w158319480_25373.ts", I'm not sure
        what the first number is (seems to be random), but the second number
        counts up sequentially as a video ID.

        This method converts "media_w158319480_25373.ts" to -> 25373 (int).
        :returns: integer ID of media filename.
        """
        return int(re.findall(r"_(\d+).ts", s)[0])

    def rename_media(self, s):
        """
        "media_w158319480_25373.ts" seems to have the first name be random for
        some reason (maybe so you can't just easily download?)

        This method renames that complicated ID to be "media_YEARmonthDAY_ID",
        where "YEAR", "month", and "DAY" are system datetime, and "ID" is the
        original second integer in the media filename.
        :returns: New, usable media filename.
        """
        now = datetime.datetime.now()
        now = str(now.year) + '-' + str(now.month) + '-' + str(now.day)
        return "media_" + now + "_" + str(self.extract_media_id(s)) + ".ts"

    def retrieve_chunklist_manifest(self):
        """
        Retrieve the latest chunklist manifest that contains the latest segments.
        :returns: List of media segments.
        """
        chunklist_url = self.retrieve_playlist_manifest()
        if chunklist_url is False:
            return False

        chunklist = requests.get(self.cameraURL + '/' + chunklist_url)
        chunklist = chunklist.text.split('\n')
        media = []
        for line in chunklist:
            if line.startswith('#') or len(line.strip()) == 0:
                continue # skip meta data or empty lines
            media.append(line)
        if len(media) == 0:
            if self.verbose:
                print('INFO: Got new media list, but it does not contain any media')
        else:
            if self.verbose:
                print('INFO: Got new media list, containing \t' + ', '.join(media))
        return media

    def retrieve_media_segment(self, id, new_id):
        """
        Downloads a media segment to the self.segmentDir by its ID.
        :returns: True if successful, False if not.
        """
        if self.verbose:
            print('INFO: Downloading media segment \t' + id)
        media_file = requests.get(self.cameraURL + '/' + id)
        if media_file.status_code > 399:
            if self.verbose:
                print('WARN: Failed to download media segment \t' + id)
            return False
        with open(self.segmentDir + '/' + new_id, 'wb') as f:
            f.write(media_file.content)
        return True

    def make_segment_dir(self):
        """
        Create the segmentDir, if it does not exist.
        """
        if not os.path.exists(self.segmentDir):
            if self.verbose:
                print('INFO: Making segment directory at file location ' + self.segmentDir + '/')
            os.makedirs(self.segmentDir)

    def clear_segment_dir(self):
        """
        Delete all the media files downloaded in the segment directory.
        """
        files = glob.glob(self.segmentDir + '/*')
        for f in files:
            if self.verbose:
                print('INFO: Clearing segment directory at file location ' + self.segmentDir + '/')
            os.remove(f)

    def get_missing_media(self):
        """
        Checks for all media that is not downloaded, and downloads it.
        """
        self.make_segment_dir()
        media = self.retrieve_chunklist_manifest()
        for m in media:
            renamed = self.rename_media(m)
            if os.path.isfile(self.segmentDir + '/' + renamed) == False:
                print('INFO: ' + self.segmentDir + '/' + renamed + ' file does not exist')
                status = self.retrieve_media_segment(m, renamed)
                if status:
                    self.segments += m # Add to segment list
                    self.renamedSegments += renamed # Add to other segment list
                    if self.verbose:
                        print('INFO: Got new media segment \t\t' + m)
                else:
                    if self.verbose:
                        print('WARN: Failed to get media segment \t' + m)
            else:
                if self.verbose:
                    print('INFO: Segment file ' + m + ' already downloaded, skipping...')
        if self.verbose:
            sdSize = sum(d.stat().st_size for d in os.scandir(self.segmentDir + '/') if d.is_file())
            print('INFO: Segment directory is now at ' + str(sdSize) + ' bytes (' + str(round(sdSize/1000000, 2)) + ' megabytes)')

    def get_next_segment(self):
        """
        Helper function, returns the filename of the next available segment.
        :returns: False if no segment has been downloaded or if there's no new
            segment, otherwise, returns the relative file path of the next segment
        """
        if len(self.segments) == 0:
            return False
        if self.currentSegment >= len(self.segments):
            return False
        self.currentSegment += 1
        return self.segments[self.currentSegment - 1] # -1 to get the first segment

    def play_in_window(self):
        """
        Play the stream continuously in an OpenCV window.
        """
        return None

if __name__ == "__main__":
    while True:
        d = DelDOT('NCAM070', verbose=True)
        d.get_missing_media()
        time.sleep(7) # give the servers a break
