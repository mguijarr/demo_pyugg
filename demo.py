import bottle
import os
import gevent
import cv2
import time
import base64
import cStringIO

WEBCAM_GREENLET = None
WEBCAM_IMAGE = None
WEBCAM_NEW_IMAGE = gevent.event.Event()

def _do_webcam_acq():
    webcam = cv2.VideoCapture(0)
    while True:
        _, frame = webcam.read()
        h,w,depth = frame.shape
        if depth == 3:
            mode="RGB"
        else:
            mode="L" 
        raw_data = frame.tostring()
        WEBCAM_IMAGE = Image.fromstring(mode,(w,h),raw_data) 
        WEBCAM_NEW_IMAGE.set()
        time.sleep(0.04)
        WEBCAM_NEW_IMAGE.clear()
                     
def start_webcam_acq():
    global WEBCAM_GREENLET
    if WEBCAM_GREENLET:
        WEBCAM_GREENLET = gevent.spawn(_do_webcam_acq)

@bottle.route("/")
def demo_app():
    start_webcam_acq()

    return bottle.static_file("demo.html", root=os.path.dirname(__file__))

@bottle.route("/stream")
def send_jpeg_stream():
    response.content_type = "text/event-stream"
    response.connection = "keep-alive"
    response.cache_control = "no-cache"
    while True:
        jpeg_file = cStringIO.StringIO()
        WEBCAM_NEW_IMAGE.wait()
        WEBCAM_IMAGE.write(jpeg_file, format="JPG")
        yield "data: %s\n\n" % base64.b64encode(jpeg_file.read())

