from channels.generic.websocket import WebsocketConsumer
import numpy as np
import cv2
import os
import json
from asgiref.sync import async_to_sync
from django.conf import settings
from django.core.cache import cache


class VideoConsumer(WebsocketConsumer):
    def connect(self):
        self.room_name = self.scope['url_route']['kwargs'].get('room_name')
        self.room_group_name = self.room_name
        user = self.scope['user']

        if user and user.is_authenticated:
            async_to_sync(self.channel_layer.group_add)(
                self.room_group_name,
                self.channel_name
            )
            self.accept()
            self.send(text_data=json.dumps({
                'connect_message': 'Socket connected',
            }))
        else:
            self.close(code=4401)

    def disconnect(self, close_code):
        # Leave room group
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )

    def receive(self, text_data=None, bytes_data=None):
        if bytes_data:
            np_arr = np.frombuffer(bytes_data, np.uint8)
            frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

            if frame is not None:
                self.process_frame(frame)
        else:
            pass

    def process_frame(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        haar_cascade_path = os.path.join(settings.BASE_DIR, 'face_detect', 'haarcascades',
                                         'haarcascade_frontalface_default.xml')
        face_cascade = cv2.CascadeClassifier(haar_cascade_path)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30),
                                              flags=cv2.CASCADE_SCALE_IMAGE)
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)

        _, jpeg = cv2.imencode('.jpg', frame)
        processed_frame_bytes = jpeg.tobytes()

        # Save the processed frame to cache
        cache.set('processed_frame', processed_frame_bytes, timeout=5)

        # Send the processed frame back to the client
        self.send(bytes_data=processed_frame_bytes)
