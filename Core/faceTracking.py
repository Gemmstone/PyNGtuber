import mediapipe as mp
import cv2
import numpy as np
import pandas as pd
import pickle
import warnings
from PyQt6.QtGui import QImage
from collections import deque


"""
This script is based on the work by Mostafa Nafie.
Original repository: https://github.com/Mostafa-Nafie/Head-Pose-Estimation

Modifications and additional functionalities have been added to suit the specific needs of this project.
"""

warnings.filterwarnings("ignore", category=UserWarning)

# Load the model
model = pickle.load(open('Core/model.pkl', 'rb'))

# Define columns for DataFrame
cols = []
for pos in ['nose_', 'forehead_', 'left_eye_', 'mouth_left_', 'chin_', 'right_eye_', 'mouth_right_']:
    for dim in ('x', 'y'):
        cols.append(pos + dim)

face_mesh = mp.solutions.face_mesh.FaceMesh(min_detection_confidence=0.5, min_tracking_confidence=0.5)

# Initialize buffers for smoothing
buffer_size = 3  # Adjust the buffer size as needed
pitch_buffer = deque(maxlen=buffer_size)
yaw_buffer = deque(maxlen=buffer_size)
roll_buffer = deque(maxlen=buffer_size)


def extract_features(img, face_mesh):
    NOSE = 1
    FOREHEAD = 10
    LEFT_EYE = 33
    MOUTH_LEFT = 61
    CHIN = 199
    RIGHT_EYE = 263
    MOUTH_RIGHT = 291

    result = face_mesh.process(img)
    face_features = []

    if result.multi_face_landmarks is not None:
        for face_landmarks in result.multi_face_landmarks:
            for idx, lm in enumerate(face_landmarks.landmark):
                if idx in [FOREHEAD, NOSE, MOUTH_LEFT, MOUTH_RIGHT, CHIN, LEFT_EYE, RIGHT_EYE]:
                    face_features.append(lm.x)
                    face_features.append(lm.y)

    return face_features


def normalize(poses_df):
    normalized_df = poses_df.copy()

    for dim in ['x', 'y']:
        for feature in ['forehead_' + dim, 'nose_' + dim, 'mouth_left_' + dim, 'mouth_right_' + dim, 'left_eye_' + dim,
                        'chin_' + dim, 'right_eye_' + dim]:
            normalized_df[feature] = poses_df[feature] - poses_df['nose_' + dim]

        diff = normalized_df['mouth_right_' + dim] - normalized_df['left_eye_' + dim]
        for feature in ['forehead_' + dim, 'nose_' + dim, 'mouth_left_' + dim, 'mouth_right_' + dim, 'left_eye_' + dim,
                        'chin_' + dim, 'right_eye_' + dim]:
            normalized_df[feature] = normalized_df[feature] / diff

    return normalized_df


def draw_axes(img, pitch, yaw, roll, tx, ty, size=50):
    yaw = -yaw
    rotation_matrix = cv2.Rodrigues(np.array([pitch, yaw, roll]))[0].astype(np.float64)
    axes_points = np.array([
        [1, 0, 0, 0],
        [0, 1, 0, 0],
        [0, 0, 1, 0]
    ], dtype=np.float64)
    axes_points = rotation_matrix @ axes_points
    axes_points = (axes_points[:2, :] * size).astype(int)
    axes_points[0, :] = axes_points[0, :] + tx
    axes_points[1, :] = axes_points[1, :] + ty

    new_img = img.copy()

    default_size = 50
    default_thickness = 3
    thickness_scale = size / default_size
    adjusted_thickness = int(default_thickness * thickness_scale)

    cv2.line(
        new_img,
        tuple(axes_points[:, 3].ravel()),
        tuple(axes_points[:, 0].ravel()),
        (255, 0, 0),
        adjusted_thickness
    )
    cv2.line(
        new_img,
        tuple(axes_points[:, 3].ravel()),
        tuple(axes_points[:, 1].ravel()),
        (0, 255, 0),
        adjusted_thickness
    )
    cv2.line(
        new_img,
        tuple(axes_points[:, 3].ravel()),
        tuple(axes_points[:, 2].ravel()),
        (0, 0, 255),
        adjusted_thickness
    )
    return new_img


def process_frame(img, privacy_mode=True):
    img_h, img_w, img_c = img.shape
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    face_features = extract_features(img_rgb, face_mesh)
    if len(face_features):
        face_features_df = pd.DataFrame([face_features], columns=cols)
        face_features_normalized = normalize(face_features_df)
        pitch_pred, yaw_pred, roll_pred = model.predict(face_features_normalized).ravel()
        nose_x = face_features_df['nose_x'].values[0] * img_w
        nose_y = face_features_df['nose_y'].values[0] * img_h

        # Update buffers with new predictions
        pitch_buffer.append(pitch_pred)
        yaw_buffer.append(yaw_pred)
        roll_buffer.append(roll_pred)

        # Compute the average of the buffers
        smoothed_pitch = np.mean(pitch_buffer)
        smoothed_yaw = np.mean(yaw_buffer)
        smoothed_roll = np.mean(roll_buffer)

        if privacy_mode:
            blank_image = np.full((img_h, img_w, img_c), 255, dtype=np.uint8)
            img = draw_axes(blank_image, smoothed_pitch, smoothed_yaw, smoothed_roll, img_w/2, img_h/2, size=200)
        else:
            img = draw_axes(img, smoothed_pitch, smoothed_yaw, smoothed_roll, nose_x, nose_y)

        adjusted_position = {
            "x": int(smoothed_yaw * 100),
            "y": int(smoothed_pitch * 100) * -1,
            "z": int(smoothed_roll * 100)
        }
    else:
        adjusted_position = {"x": 0, "y": 0, "z": 0}
        if privacy_mode:
            img = np.full((img_h, img_w, img_c), 255, dtype=np.uint8)

    qt_image = None
    if img is not None:
        rgb_image = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)

    return qt_image, adjusted_position