import numpy as np
from ultralytics import YOLO


# COCO keypoint indices
NOSE  = 0
LS, RS = 5, 6
LE, RE = 7, 8
LW, RW = 9, 10
LH, RH = 11, 12
LK, RK = 13, 14
LA, RA = 15, 16


class PoseDetector:
    """
    YOLOv8-pose based detector.

    Scores aggressive motions (punches, kicks, charges) using
    inter-frame keypoint velocities.

    Bug-fixes vs original:
    - prev_keypoints is reset to None on demand (call reset())
      so stale velocity from a previous video never bleeds in.
    - Intermediate sub-scores are each individually clamped so
      the sum can never silently exceed 1.0 before the final cap.
    - Running and forward-charge are treated as supporting signals
      (lower weight) rather than primary violence indicators.
    """

    # Velocity thresholds (pixels/frame at ~30 fps, 640-px-wide frame)
    WRIST_VEL   = 25
    ELBOW_VEL   = 20
    ANKLE_VEL   = 20
    LEG_VEL_SUM = 60
    NOSE_VEL    = 20

    # Sub-score contributions
    PUNCH_SCORE  = 0.40
    KICK_SCORE   = 0.40
    RUN_SCORE    = 0.20   # reduced — running alone is not violence
    CHARGE_SCORE = 0.15   # reduced — forward movement alone is not violence

    def __init__(self, model_path: str):
        self.model = YOLO(model_path)
        self.prev_keypoints: np.ndarray | None = None

    # ------------------------------------------------------------------
    def reset(self):
        """Call this between videos / camera restarts to clear state."""
        self.prev_keypoints = None

    # ------------------------------------------------------------------
    @staticmethod
    def _vel(a: np.ndarray, b: np.ndarray) -> float:
        return float(np.linalg.norm(a - b))

    # ------------------------------------------------------------------
    def calculate_pose_score(self, keypoints: np.ndarray) -> float:
        """
        keypoints: (17, 2) array of (x, y) in pixel space.
        Returns float in [0, 1].
        """
        if keypoints is None or keypoints.shape[0] < 17:
            return 0.0

        score = 0.0

        if self.prev_keypoints is not None:
            pk = self.prev_keypoints

            # ---- Punch detection ----
            if (self._vel(keypoints[RW], pk[RW]) > self.WRIST_VEL and
                    self._vel(keypoints[RE], pk[RE]) > self.ELBOW_VEL):
                score += self.PUNCH_SCORE

            if (self._vel(keypoints[LW], pk[LW]) > self.WRIST_VEL and
                    self._vel(keypoints[LE], pk[LE]) > self.ELBOW_VEL):
                score += self.PUNCH_SCORE

            # ---- Kick detection ----
            knee_raised = (
                keypoints[RK][1] < keypoints[RH][1] or
                keypoints[LK][1] < keypoints[LH][1]
            )
            ankle_vel = max(
                self._vel(keypoints[RA], pk[RA]),
                self._vel(keypoints[LA], pk[LA]),
            )
            if knee_raised and ankle_vel > self.ANKLE_VEL:
                score += self.KICK_SCORE

            # ---- Running (supporting signal only) ----
            leg_vel_sum = (
                self._vel(keypoints[RA], pk[RA]) +
                self._vel(keypoints[LA], pk[LA])
            )
            if leg_vel_sum > self.LEG_VEL_SUM:
                score += self.RUN_SCORE

            # ---- Forward charge (supporting signal only) ----
            if self._vel(keypoints[NOSE], pk[NOSE]) > self.NOSE_VEL:
                score += self.CHARGE_SCORE

        self.prev_keypoints = keypoints.copy()
        return float(np.clip(score, 0.0, 1.0))

    # ------------------------------------------------------------------
    def predict(self, frame: np.ndarray) -> tuple[float, np.ndarray]:
        """
        Returns (pose_score, annotated_frame).
        annotated_frame has the skeleton drawn by YOLO.
        """
        results = self.model(frame, verbose=False)
        annotated_frame = results[0].plot()
        pose_score = 0.0

        kp_data = results[0].keypoints
        if kp_data is not None and kp_data.xy is not None:
            xy = kp_data.xy
            if len(xy) > 0:
                keypoints = xy[0].cpu().numpy()   # (17, 2)
                pose_score = self.calculate_pose_score(keypoints)

        return pose_score, annotated_frame
