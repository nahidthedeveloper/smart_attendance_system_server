from channels.generic.websocket import WebsocketConsumer
import numpy as np
import cv2
import os
import json
from asgiref.sync import async_to_sync
from django.conf import settings
from django.core.cache import cache
from authentication.models import Account
from face_detect.models import Dataset


class VideoConsumer(WebsocketConsumer):
    def connect(self):
        self.room_name = self.scope['url_route']['kwargs'].get('room_name')
        self.room_group_name = self.room_name
        user = self.scope['user']
        self.user = user

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
        try:
            user = Account.objects.get(academic_id=self.user)
            qs, created = Dataset.objects.get_or_create(user=user)
        except Account.DoesNotExist:
            self.send(text_data=json.dumps({
                'error': 'User account does not exist',
            }))
            return
        except Dataset.MultipleObjectsReturned:
            self.send(text_data=json.dumps({
                'error': 'Multiple datasets found for the same user',
            }))
            return
        except Exception as e:
            self.send(text_data=json.dumps({
                'error': f'Unexpected error: {str(e)}',
            }))
            return

        dataset_object = qs

        if dataset_object.is_sampleUploaded:
            self.send(text_data=json.dumps({
                'message': 'Sample photo already uploaded',
            }))
            return

        user_folder = f"faceRecognition_data/training_dataset/{user.academic_id}/"
        os.makedirs(user_folder, exist_ok=True)

        haar_cascade_path = os.path.join(settings.BASE_DIR, 'face_detect', 'haarcascades',
                                         'haarcascade_frontalface_default.xml')
        face_cascade = cv2.CascadeClassifier(haar_cascade_path)
        sample_number = 0

        while sample_number < 200:  # Limit to 200 frames
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.3, 5)
            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
                sample_number += 1
                # Save the sample image
                cv2.imwrite(
                    f"{user_folder}/{sample_number}.jpg",
                    gray[y:y + h, x:x + w])

            _, jpeg = cv2.imencode('.jpg', frame)
            processed_frame_bytes = jpeg.tobytes()

            # Save the processed frame to cache (optional)
            cache.set('processed_frame', processed_frame_bytes, timeout=5)

            # Send the processed frame back to the client as bytes
            self.send(bytes_data=processed_frame_bytes)

        # Update the Dataset object
        # dataset_object.is_sampleUploaded = True
        dataset_object.sample = str(sample_number)  # Adjust as needed
        dataset_object.save(update_fields=['is_sampleUploaded', 'sample'])

        # Send the final message to the client as JSON
        self.send(text_data=json.dumps({
            'message': 'Dataset Created',
            'trained': True
        }))
