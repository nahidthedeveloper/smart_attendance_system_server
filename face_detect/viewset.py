import shutil

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from .models import Dataset
from .serializers import DatasetSerializer
from django.conf import settings
import cv2
import os
import numpy as np


class DatasetViewSet(viewsets.ModelViewSet):
    queryset = Dataset.objects.all()
    serializer_class = DatasetSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated], url_path='add-photo')
    def add_photo(self, request):
        user = request.user
        dataset = Dataset.objects.get(user=user)

        if dataset.is_sampleUploaded:
            return Response({'messages_': 'Sample photo already uploaded', 'trained': dataset.is_trained},
                            status=status.HTTP_200_OK)

        user_folder = os.path.join('faceRecognition_data', 'training_dataset', str(user.academic_id))
        os.makedirs(user_folder, exist_ok=True)

        cam = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        haar_cascade_path = os.path.join(settings.BASE_DIR, 'face_detect', 'haarcascades',
                                         'haarcascade_frontalface_default.xml')
        face_cascade = cv2.CascadeClassifier(haar_cascade_path)

        sample_number = 0
        while sample_number < 200:
            ret, img = cam.read()
            if not ret:
                break

            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.3, 5)

            for (x, y, w, h) in faces:
                sample_number += 1
                face_img = gray[y:y + h, x:x + w]
                cv2.imwrite(os.path.join(user_folder, f"{sample_number}.jpg"), face_img)
                cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)

                cv2.imshow("Collecting Sample", img)
                cv2.setWindowProperty("Collecting Sample", cv2.WND_PROP_TOPMOST, 1)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cam.release()
        cv2.destroyAllWindows()

        dataset.is_sampleUploaded = True
        dataset.sample = str(user.academic_id)
        dataset.save(update_fields=['is_sampleUploaded', 'sample'])

        return Response({'messages': 'Dataset Created'}, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated], url_path='train-data')
    def train_data(self, request):
        user = request.user
        dataset = Dataset.objects.get(user=user)

        if not dataset.is_sampleUploaded:
            return Response({'messages': 'Upload Sample'}, status=status.HTTP_400_BAD_REQUEST)

        if dataset.is_trained:
            return Response({'messages': 'Already Trained'}, status=status.HTTP_400_BAD_REQUEST)

        recognizer = cv2.face.LBPHFaceRecognizer_create()
        global detector
        detector = cv2.CascadeClassifier(
            os.path.join(settings.BASE_DIR, 'face_detect', 'haarcascades', 'haarcascade_frontalface_default.xml'))
        faces, ids = self.getImagesAndLabels(
            os.path.join('faceRecognition_data', 'training_dataset', str(user.academic_id)))

        recognizer.train(faces, np.array(ids))
        try:
            os.makedirs("model", exist_ok=True)
            recognizer.save(os.path.join('model', 'trained_model2.yml'))
        except Exception as e:
            return Response({'messages_': 'Please make "model" folder'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        dataset.is_trained = True
        dataset.save(update_fields=['is_trained'])

        return Response({'messages': 'Model Trained'}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated], url_path='delete-photo')
    def delete_photo(self, request):
        user = request.user
        dataset = Dataset.objects.get(user=user)
        user_folder = os.path.join('faceRecognition_data', 'training_dataset', str(user.academic_id))

        if dataset.is_sampleUploaded:
            if os.path.exists(user_folder):
                shutil.rmtree(user_folder)
                dataset.is_sampleUploaded = False
                dataset.is_trained = False
                dataset.sample = "0"
                dataset.save(update_fields=['is_sampleUploaded', 'sample', 'is_trained'])
                return Response({'messages_': 'Sample has been deleted'}, status=status.HTTP_200_OK)
            else:
                dataset.is_sampleUploaded = False
                dataset.is_trained = False
                dataset.sample = "0"
                dataset.save(update_fields=['is_sampleUploaded', 'sample', 'is_trained'])
                return Response({'messages_': 'Sample has already been deleted'}, status=status.HTTP_200_OK)
        else:
            return Response({'messages_': 'Sample photo not uploaded yet'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated], url_path='take_attendance')
    def attendance_in(self, request):
        haar_cascade_path = os.path.join(settings.BASE_DIR, 'face_detect', 'haarcascades',
                                         'haarcascade_frontalface_default.xml')
        face_cascade = cv2.CascadeClassifier(haar_cascade_path)
        font = cv2.FONT_HERSHEY_SIMPLEX
        recognizer = cv2.face.LBPHFaceRecognizer_create()
        recognizer.read('model/trained_model2.yml')

        cam = cv2.VideoCapture(0)
        results = []

        while True:
            ret, img = cam.read()
            if not ret:
                break

            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=10)

            for (x, y, w, h) in faces:
                cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
                id, pred = recognizer.predict(gray[y:y + h, x:x + w])
                confidence = int(100 * (1 - pred / 300))

                name = None
                if confidence > 77:
                    qs = Dataset.objects.get(sample=request.user.academic_id)
                    id_ = qs.user.academic_id
                    name = qs.user.name
                    confidence = "  {0}%".format(round(100 - confidence))
                else:
                    id_ = "unknown"
                    confidence = "  {0}%".format(round(100 - confidence))

                results.append({'username': id_, 'confidence': confidence})

                cv2.putText(img, f'{id_}', (x + 5, y - 20), font, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
                cv2.putText(img, f'{name}', (x + 5, y - 5), font, 0.5, (255, 255, 255), 1, cv2.LINE_AA)

            winName = "Taking Attendance"
            cv2.namedWindow(winName)
            cv2.moveWindow(winName, 40, 30)
            cv2.imshow(winName, img)
            cv2.setWindowProperty(winName, cv2.WND_PROP_TOPMOST, 1)

            k = cv2.waitKey(10) & 0xff  # Press 'ESC' for exiting video
            if k == 27:
                break

        cam.release()
        cv2.destroyAllWindows()
        return Response({'results': results})

    def getImagesAndLabels(self, path):
        imagePaths = [os.path.join(path, f) for f in os.listdir(path)]
        faceSamples = []
        ids = []
        for imagePath in imagePaths:
            PIL_img = cv2.imread(imagePath, 0)
            img_numpy = np.array(PIL_img, 'uint8')
            id = int(os.path.split(imagePath)[-1].split(".")[0])
            faces = detector.detectMultiScale(img_numpy)
            for (x, y, w, h) in faces:
                faceSamples.append(img_numpy[y:y + h, x:x + w])
                ids.append(id)
        return faceSamples, ids
