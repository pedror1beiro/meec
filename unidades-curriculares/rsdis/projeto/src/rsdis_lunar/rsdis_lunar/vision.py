"""Colour-sphere marker perception; target coordinates never enter this module."""

import math
import cv2
import numpy as np

RANGES = {
    "red": [((0, 120, 70), (8, 255, 255)), ((172, 120, 70), (179, 255, 255))],
    "green": [((40, 120, 70), (85, 255, 255))],
    "blue": [((100, 120, 70), (130, 255, 255))],
    "magenta": [((135, 120, 70), (169, 255, 255))],
    "orange": [((9, 120, 70), (25, 255, 255))],
}


def detect(bgr, camera_matrix, diameter=0.5):
    """Return (colour ID, forward distance, left distance, shape score).

    Pinhole/known diameter approximation, suitable for an initial flat test field.
    Cropped blobs and very small blobs are rejected to avoid biased range estimates.
    """
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    height, width = bgr.shape[:2]
    fx, cx = camera_matrix[0], camera_matrix[2]
    if fx <= 0:
        return []
    detections = []
    for target_id, ranges in RANGES.items():
        mask = np.zeros((height, width), dtype=np.uint8)
        for low, high in ranges:
            mask |= cv2.inRange(hsv, np.array(low), np.array(high))
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        candidates = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            area = cv2.contourArea(contour)
            perimeter = cv2.arcLength(contour, True)
            circularity = 4 * math.pi * area / max(perimeter**2, 1)
            if (
                w < 8
                or h < 8
                or x <= 1
                or y <= 1
                or x + w >= width - 1
                or y + h >= height - 1
                or not 0.65 < w / h < 1.5
                # A filled rectangle can reach pi/4 circularity. Keep the cutoff
                # above that to reject coloured panels on the detailed rovers.
                or circularity < 0.8
            ):
                continue
            forward = fx * diameter / w
            left = -(x + w / 2 - cx) * forward / fx
            if forward < 15:
                candidates.append((area, (target_id, forward, left, min(1.0, circularity))))
        if candidates:
            detections.append(max(candidates, key=lambda c: c[0])[1])
    return detections


def to_world(forward, left, pose, camera_offset):
    x, y, yaw = pose
    forward += camera_offset
    return (
        x + math.cos(yaw) * forward - math.sin(yaw) * left,
        y + math.sin(yaw) * forward + math.cos(yaw) * left,
    )
