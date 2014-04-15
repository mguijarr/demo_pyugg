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

WEBCAM_GREENLET = None
WEBCAM_IMAGE = None
WEBCAM_NEW_IMAGE = gevent.event.Event()

def _do_webcam_acq():
    global WEBCAM_IMAGE
    webcam = cv2.VideoCapture(0)
    while True:
        _, frame = webcam.read()
        h,w,depth = frame.shape
        # too bad it has to be converted from BGR to RGB :(
        WEBCAM_IMAGE = Image.fromarray(numpy.roll(frame, 1, axis=-1)) 
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
    frame_no = 0
    while True:
        jpeg_file = cStringIO.StringIO()
        WEBCAM_NEW_IMAGE.wait()
        frame_no += 1
        WEBCAM_IMAGE.save(jpeg_file, format="JPEG")
        encoded_data = base64.b64encode(jpeg_file.getvalue())
        yield "data: %s\n\n" % encoded_data

