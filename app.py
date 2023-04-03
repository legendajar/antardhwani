from flask import Flask, render_template, Response
from util import *

app = Flask(__name__)
 
def generate_frames(camera):
    while True:
        global emotion
        frame, emotion = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/video')
def video():
    return Response(generate_frames(VideoCamera()), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/get-songs')
def getSongs():
    recommendedPlaylist = SpotipyAPI().getSongOnMood(emotion)

    return render_template('index.html', recommendedPlaylist=recommendedPlaylist)


if __name__ == "__main__":
    app.run(debug=True)
