import cv2
from threading import Thread
from deepface import DeepFace
import numpy as np
from PIL import Image
import csv
import random
import os
import re
import spotipy
# from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyClientCredentials

global cam
facecascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
global last_frame
last_frame = np.zeros((480, 640, 3), dtype=np.uint8)


class LiveVedioFeed:

    def __init__(self, src=0):
        self.stream = cv2.VideoCapture(src, cv2.CAP_DSHOW)
        (self.grabbed, self.frame) = self.stream.read()
        self.stopped = False

    def start(self):
        # start the thread to read frames from the video stream
        Thread(target=self.update, args=()).start()
        return self

    def update(self):
        # keep looping infinitely until the thread is stopped
        while True:
            # if the thread indicator variable is set, stop the thread
            if self.stopped:
                return
            # otherwise, read the next frame from the stream
            (self.grabbed, self.frame) = self.stream.read()

    def read(self):
        # return the frame most recently read
        return self.frame

    def stop(self):
        # indicate that the thread should be stopped
        self.stopped = True


class VideoCamera(object):

    def get_frame(self):
        global cam
        global emotion
        cam = LiveVedioFeed(src=0).start()
        frame = cam.read()

        result = DeepFace.analyze(
            frame, actions=['emotion'], enforce_detection=False)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        faces = facecascade.detectMultiScale(gray, 1.1, 4)

        # Draw a rectangle around the faces
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            cv2.putText(frame, result[0]['dominant_emotion'],
                        (x+int(w/3), y), cv2.FONT_ITALIC, 1, (246, 6, 13), 2)

        global last_frame
        last_frame = frame.copy()
        img = Image.fromarray(last_frame)
        img = np.array(img)
        ret, buffer = cv2.imencode('.jpg', img)
        emotion = result[0]['dominant_emotion']
        return buffer.tobytes(), emotion


class SpotipyAPI(object):

    def getSongOnMood(self, mood):

        CLIENT_ID = os.getenv("CLIENT_ID", "011e37396bd5450ab6273510416b5e1f")
        CLIENT_SECRET = os.getenv(
            "CLIENT_SECRET", "62aafcf856bb4914907d3d6f1db46ae9")
        PLAYLIST_LINK = "https://open.spotify.com/playlist/0z5GPu1ZL2ryEmPbTyH0tB?si=d42be5c6ec194bb9&nd=1"

        emotions = {
            'sad': '0z5GPu1ZL2ryEmPbTyH0tB',
            'angry': '0a4Hr64HWlxekayZ8wnWqx',
            'happy': '1ZKdvf5yXvwVyzgznVz2Nl',
            'surprise': '3FDsPHUToNnMClpbcQ1fyj'
        }

        f_emotion = mood

        # map facial expression emotion with song genre
        if f_emotion in emotions:
            code = emotions[f_emotion]

            PLAYLIST_LINK = f"https://open.spotify.com/playlist/{code}?si=d42be5c6ec194bb9&nd=1"
        else:
            print(f"Error: '{f_emotion}' is not a valid emotion.")

        client_credentials_manager = SpotifyClientCredentials(
            client_id=CLIENT_ID, client_secret=CLIENT_SECRET
        )

        # create spotify session object
        session = spotipy.Spotify(
            client_credentials_manager=client_credentials_manager)

        # get uri from https link
        if match := re.match(r"https://open.spotify.com/playlist/(.*)\?", PLAYLIST_LINK):
            playlist_uri = match.groups()[0]

        else:
            raise ValueError(
                "Expected format: https://open.spotify.com/playlist/...")

        # get list of tracks in a given playlist (note: max playlist length 100)
        tracks = session.playlist_tracks(playlist_uri)["items"]

        # extract name and artist
        playlist = []
        for track in tracks:
            name = track["track"]["name"]
            uri = track["track"]["preview_url"]

            artists = ", ".join([artist["name"]
                                for artist in track["track"]["artists"]])
            if uri and artists:
                playlist.append((uri, name, artists))

        random_playlists = random.sample(playlist, 8)

        recommendedPlaylist = {
            'currentMood': mood,
            'playlists': random_playlists
        }

        return recommendedPlaylist
