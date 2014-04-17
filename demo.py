import bottle
import os
import gevent
import gevent.event
import cv2
import time
import base64
import cStringIO
import Image
import numpy
import subprocess

WEBCAM_GREENLET = None
WEBCAM_ENCODED_JPEG = None
WEBCAM_NEW_IMAGE = gevent.event.Event()

def _do_webcam_acq():
    global WEBCAM_ENCODED_JPEG
    webcam = cv2.VideoCapture(0)

    while True:
        _, frame = webcam.read()
        h,w,depth = frame.shape
        im = Image.fromarray(frame) 
        # too bad it has to be converted from BGR to RGB :(
        b,g,r = im.split()
        rgb_im = Image.merge("RGB", (r,g,b))
        jpeg_file = cStringIO.StringIO()
        rgb_im.save(jpeg_file, format="JPEG")
        WEBCAM_ENCODED_JPEG = base64.b64encode(jpeg_file.getvalue())
        WEBCAM_NEW_IMAGE.set()
        WEBCAM_NEW_IMAGE.clear()
        time.sleep(0.04)
                     
def start_webcam_acq():
    global WEBCAM_GREENLET
    if WEBCAM_GREENLET is None:
        WEBCAM_GREENLET = gevent.spawn(_do_webcam_acq)

@bottle.route("/")
def demo_app():
    start_webcam_acq()
    return bottle.static_file("demo.html", root=os.path.dirname(__file__))

@bottle.route("/stream")
def send_jpeg_stream():
    bottle.response.content_type = "text/event-stream"
    bottle.response.connection = "keep-alive"
    bottle.response.cache_control = "no-cache"
    while True:
        WEBCAM_NEW_IMAGE.wait()
        yield "data: %s\n\n" % WEBCAM_ENCODED_JPEG

@bottle.route("/dummy_request")
def reply_dummy_request():
    print "Received request", bottle.request
    print "  - processing..."
    time.sleep(5)
    p=subprocess.Popen("fortune", stdout=subprocess.PIPE)
    p.wait()
    print "  - done."
    return p.stdout.read()

