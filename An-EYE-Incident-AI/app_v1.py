"""
An-EYE  v1.0  –  Violence Detection System
==========================================

LIVE MODE
---------
  * HP Victus webcam (1280x720, index 0)
  * 5-second rolling pre-event buffer always kept in memory
  * Violence confirmed (PERSIST_FRAMES) -> evidence clip saved to violent_clips/
  * Any new violence frame while recording  -> +EXTENSION_SECONDS added
  * Calm for CALM_SECONDS with no violence -> clip finalised + saved
  * Camera NEVER stops — live feed stays open throughout

  videolive recording (triggered only on violence):
    - OFF at session start; AI scans continuously
    - Violence clip saved -> videolive recording starts immediately
    - Records for exactly VIDEOLIVE_DURATION_SECONDS (default 120 s / 2 min)
    - After 2 min -> recording stops, AI resumes scanning for next violence
    - Next violence clip saved -> new videolive segment starts (seg002, seg003…)
    - Files: videolive/live_<YYYYMMDD_HHMMSS>_seg001.mp4, seg002.mp4, …
  * Press Q to quit

VIDEO MODE
----------
  * Give a video file path
  * Same AI pipeline as live (motion gate -> CNN -> pose -> fusion)
  * No annotated export — only evidence clips saved to violent_clips/
  * After first clip saved -> AI stops, rest of video plays raw on screen
  * Simultaneously written to videolive/video_<timestamp>.mp4 in real-time
  * Press Q to abort at any time
"""

import csv
import os
import platform
import time
import uuid
from collections import deque

import cv2
import numpy as np
import threading
import uvicorn
from streaming.stream_server import app

from detectors.violence_detector import ViolenceDetector
from detectors.pose_detector import PoseDetector
from ai_engine.services.cloud_uploader import upload_clip
from ai_engine.services.video_converter import convert_to_browser_format
from ai_engine.services.backend_client import send_incident
from ai_engine.services.incident_generator import generate_incident
from ai_engine.suspect_system.suspect_processor import process_suspect
from streaming import frame_buffer

# ======================== CONFIG ========================
MODEL_VIOLENCE       = "models/violence_model.h5"
MODEL_POSE           = "models/yolov8m-pose.pt"

OUTPUT_FOLDER        = "violent_clips"
LIVE_OUTPUT_FOLDER   = "videolive"

# ── Storage FPS ─────────────────────────────────────────
# The AI loop on this laptop runs at ~3-6 fps under load.
# STORAGE_FPS is what VideoWriter is told — it must match
# the actual frame-delivery rate or clips play fast/slow.
# We auto-calibrate this at startup (see _calibrate_fps).
# You can hard-code it here if calibration is wrong:
#   STORAGE_FPS = 6   (typical for CNN+pose on CPU)
STORAGE_FPS          = None   # None = auto-calibrate at startup
# ────────────────────────────────────────────────────────

VIDEOLIVE_DURATION_SECONDS = 120   # 2-minute post-violence window

THRESHOLD            = 0.55
SMOOTHING_WINDOW     = 15
MOTION_THRESHOLD     = 5.0
MODEL_ACTIVE_SECONDS = 150

PRE_BUFFER_SECONDS   = 5     # rolling look-back always in RAM
EXTENSION_SECONDS    = 5     # each new violence hit extends clip
CALM_SECONDS         = 3     # calm period before clip is finalised
PERSIST_FRAMES       = 8     # consecutive frames needed to confirm violence

CAM_INDEX   = 0
CAM_WIDTH   = 1280
CAM_HEIGHT  = 720
# ========================================================

os.makedirs(OUTPUT_FOLDER,      exist_ok=True)
os.makedirs(LIVE_OUTPUT_FOLDER, exist_ok=True)

violence_detector = ViolenceDetector(MODEL_VIOLENCE)
pose_detector     = PoseDetector(MODEL_POSE)


# ==================== MOTION GATE =======================

class MotionGate:
    def __init__(self):
        self.prev_gray        = None
        self.models_active    = False
        self.last_motion_time = 0.0

    def check(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        if self.prev_gray is None:
            self.prev_gray = gray
            return False

        score = cv2.absdiff(self.prev_gray, gray).mean()
        self.prev_gray = gray
        now = time.time()

        if score > MOTION_THRESHOLD:
            self.models_active    = True
            self.last_motion_time = now

        if self.models_active and (now - self.last_motion_time > MODEL_ACTIVE_SECONDS):
            self.models_active = False

        return self.models_active


# ==================== SMART RECORDER ====================

class SmartRecorder:
    """
    State machine: IDLE -> RECORDING -> CALM -> IDLE

    Stores raw frames; writes them at `storage_fps` which is calibrated
    to the actual loop speed so saved clips play back at real-world speed.
    """

    IDLE      = "IDLE"
    RECORDING = "RECORDING"
    CALM      = "CALM"

    def __init__(self, storage_fps, w, h):
        self.fps = storage_fps   # actual loop fps — used for VideoWriter & counters
        self.w   = w
        self.h   = h

        self.pre_buffer      = deque(maxlen=max(1, int(storage_fps * PRE_BUFFER_SECONDS)))
        self.state           = self.IDLE
        self.persist_count   = 0
        self.calm_count      = 0
        self.ext_deadline    = 0.0
        self.event_frames    = []
        self.clip_path       = ""

    def feed(self, frame, is_violent, fusion_score=0.0):
        """Call once per frame. Returns (path, peak_score) when clip finalised, else (None, 0.0)."""
        self.pre_buffer.append(frame.copy())
        if is_violent and fusion_score > getattr(self, "peak_score", 0.0):
            self.peak_score = fusion_score

        if self.state == self.IDLE:
            return self._idle(frame, is_violent)
        if self.state == self.RECORDING:
            return self._recording(frame, is_violent)
        if self.state == self.CALM:
            return self._calm(frame, is_violent)
        return None, 0.0

    def status(self):
        return self.state

    def _idle(self, frame, is_violent):
        if is_violent:
            self.persist_count += 1
            if self.persist_count >= PERSIST_FRAMES:
                self._begin()
        else:
            self.persist_count = 0
        return None, 0.0

    def _recording(self, frame, is_violent):
        self.event_frames.append(frame.copy())
        now = time.time()
        if is_violent:
            self.ext_deadline = now + EXTENSION_SECONDS
            self.calm_count   = 0
        elif now >= self.ext_deadline:
            self.state      = self.CALM
            self.calm_count = 0
        return None, 0.0

    def _calm(self, frame, is_violent):
        self.event_frames.append(frame.copy())
        if is_violent:
            self.ext_deadline = time.time() + EXTENSION_SECONDS
            self.calm_count   = 0
            self.state        = self.RECORDING
            return None, 0.0
        self.calm_count += 1
        if self.calm_count >= int(self.fps * CALM_SECONDS):
            return self._finalise()
        return None, 0.0

    def _begin(self):
        self.state         = self.RECORDING
        self.calm_count    = 0
        self.persist_count = 0
        self.peak_score    = 0.0
        self.ext_deadline  = time.time() + EXTENSION_SECONDS
        self.event_frames  = list(self.pre_buffer)
        clip_id            = str(uuid.uuid4())[:8]
        self.clip_path     = os.path.join(OUTPUT_FOLDER, f"event_{clip_id}.mp4")
        print(f"\n[Rec] STARTED -> {self.clip_path}  (storage fps={self.fps:.1f})")

    def _finalise(self):
        n = len(self.event_frames)
        print(f"[Rec] FINALISING  {n} frames  @ {self.fps:.1f} fps  "
              f"= {n/self.fps:.1f}s clip  peak={self.peak_score:.3f}")
        writer = cv2.VideoWriter(
            self.clip_path,
            cv2.VideoWriter_fourcc(*"mp4v"),
            self.fps, (self.w, self.h),
        )
        for frm in self.event_frames:
            writer.write(frm)
        writer.release()

        path               = self.clip_path
        peak               = self.peak_score
        self.state         = self.IDLE
        self.event_frames  = []
        self.calm_count    = 0
        self.peak_score    = 0.0
        self.clip_path     = ""
        print(f"[Rec] SAVED -> {path}")
        return path, peak

    def force_finalise(self):
        if self.state != self.IDLE and self.event_frames:
            return self._finalise()
        return None, 0.0


# ==================== LOGGING ===========================

def log_event(cam_id, location, peak_score, clip_name):
    """
    Append one row to event_log.csv.
    timestamp  — Windows local time (same as the system clock)
    peak_score — highest fusion score recorded during the violence clip
    """
    log_path    = "event_log.csv"
    first_write = not os.path.isfile(log_path)
    # time.strftime reads the local system clock on Windows automatically
    timestamp   = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(log_path, mode="a", newline="") as fh:
        writer = csv.writer(fh)
        if first_write:
            writer.writerow(["timestamp", "cam_id", "location",
                             "peak_score", "clip"])
        writer.writerow([timestamp, cam_id, location,
                         round(peak_score, 3), clip_name])
    print(f"[Log] {timestamp}  {cam_id}  {location}  "
          f"peak={round(peak_score,3)}  {os.path.basename(clip_name)}")


# ==================== OPEN WEBCAM =======================

def open_webcam(index=CAM_INDEX):
    backend = cv2.CAP_DSHOW if platform.system() == "Windows" else cv2.CAP_V4L2
    cap = cv2.VideoCapture(index, backend)
    if not cap.isOpened():
        cap = cv2.VideoCapture(index)

    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  CAM_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAM_HEIGHT)
    cap.set(cv2.CAP_PROP_BUFFERSIZE,   1)

    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"[Webcam] index={index}  {w}x{h}")
    return cap


# ==================== HUD HELPERS =======================

def start_stream_server():

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        reload=False
    )

def _put(frame, text, pos, scale=0.75, color=(255, 255, 255), thick=2):
    cv2.putText(frame, text, pos,
                cv2.FONT_HERSHEY_SIMPLEX, scale, color, thick, cv2.LINE_AA)


def draw_hud_live(frame, cnn, pose, avg, rec_state, models_active):
    if not models_active:
        cv2.rectangle(frame, (15, 10), (270, 48), (0, 0, 0), -1)
        _put(frame, "IDLE  (no motion)", (22, 36), 0.65, (150, 150, 150), 1)
        return

    alarm   = avg > THRESHOLD
    s_color = (0, 50, 255) if alarm else (30, 210, 30)

    cv2.rectangle(frame, (15, 10), (375, 185), (10, 10, 10), -1)
    cv2.rectangle(frame, (15, 10), (375, 185), s_color, 2)

    _put(frame, "VIOLENT" if alarm else "NORMAL", (25, 44), 0.9, s_color, 3)
    _put(frame, f"CNN  : {cnn:.2f}",  (25,  80), 0.7, (220, 220, 220))
    _put(frame, f"POSE : {pose:.2f}", (25, 107), 0.7, (220, 220, 220))
    _put(frame, f"SCORE: {avg:.2f}",  (25, 134), 0.85, s_color, 2)

    rec_color = {
        SmartRecorder.IDLE:      (70, 70, 70),
        SmartRecorder.RECORDING: (0, 0, 200),
        SmartRecorder.CALM:      (0, 140, 220),
    }.get(rec_state, (70, 70, 70))

    cv2.rectangle(frame, (25, 150), (235, 176), rec_color, -1)
    _put(frame, f"REC: {rec_state}", (30, 169), 0.55, (255, 255, 255), 1)


def draw_hud_video(frame, cnn, pose, avg, rec_state, ts, live_ready):
    """Returns button rect (x1,y1,x2,y2) when live_ready, else None."""
    alarm   = avg > THRESHOLD
    s_color = (0, 50, 255) if alarm else (30, 210, 30)

    cv2.rectangle(frame, (15, 10), (375, 190), (10, 10, 10), -1)
    cv2.rectangle(frame, (15, 10), (375, 190), s_color, 2)

    _put(frame, "VIOLENT" if alarm else "NORMAL", (25, 44), 0.9, s_color, 3)
    _put(frame, f"CNN  : {cnn:.2f}",  (25,  80), 0.7, (220, 220, 220))
    _put(frame, f"POSE : {pose:.2f}", (25, 107), 0.7, (220, 220, 220))
    _put(frame, f"SCORE: {avg:.2f}",  (25, 134), 0.85, s_color, 2)
    _put(frame, f"t = {ts:.1f}s",     (25, 158), 0.6, (150, 150, 150), 1)

    rec_color = {
        SmartRecorder.IDLE:      (70, 70, 70),
        SmartRecorder.RECORDING: (0, 0, 200),
        SmartRecorder.CALM:      (0, 140, 220),
    }.get(rec_state, (70, 70, 70))
    cv2.rectangle(frame, (25, 166), (235, 183), rec_color, -1)
    _put(frame, f"REC: {rec_state}", (30, 180), 0.5, (255, 255, 255), 1)

    if live_ready:
        h_f, w_f = frame.shape[:2]
        bx1, by1 = w_f - 165, 15
        bx2, by2 = w_f - 10,  62
        cv2.rectangle(frame, (bx1, by1), (bx2, by2), (0, 130, 255), -1)
        cv2.rectangle(frame, (bx1, by1), (bx2, by2), (255, 255, 255), 2)
        _put(frame, "LIVE", (bx1 + 22, by2 - 13), 0.85, (255, 255, 255), 2)
        return (bx1, by1, bx2, by2)

    return None


# ==================== FPS CALIBRATION ===================

def _calibrate_storage_fps(cap, w, h, sample_frames=30):
    """
    Run the FULL AI pipeline (motion gate + CNN + pose) on `sample_frames`
    real webcam frames and measure the actual throughput.  This is the
    fps value we pass to VideoWriter — if it matches the loop speed, saved
    clips play back at real-world speed with no fast-forward or slow-motion.
    """
    print(f"\n[Cal] Calibrating storage FPS — running full AI pipeline "
          f"on {sample_frames} frames…")

    mg = MotionGate()
    t0 = time.perf_counter()
    frames_done = 0

    for _ in range(sample_frames):
        ret, frame = cap.read()
        if not ret:
            break
        if mg.check(frame):
            violence_detector.predict(frame)
            pose_detector.predict(frame)
        frames_done += 1

    elapsed = time.perf_counter() - t0
    measured = frames_done / elapsed if elapsed > 0 else 6.0
    # Clamp to something sane
    measured = max(1.0, min(measured, 30.0))

    print(f"[Cal] Full-pipeline throughput: {measured:.2f} fps  "
          f"({frames_done} frames in {elapsed:.1f}s)")
    print(f"[Cal] VideoWriter will use {measured:.1f} fps — "
          f"clips will play at real-world speed.")
    return measured


# ==================== LIVE MODE =========================

def start_live(cam_id="CAM1", location="Ashok Rajpath Crossing"):
    cap = open_webcam()
    w   = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h   = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # ── Calibrate storage FPS under real AI load ───────────────────────────
    # We measure how many frames/sec the FULL pipeline (CNN + pose) can
    # process on this machine.  That number becomes the VideoWriter fps so
    # every saved file plays back at real-world speed.
    global STORAGE_FPS
    if STORAGE_FPS is None:
        STORAGE_FPS = _calibrate_storage_fps(cap, w, h)
    storage_fps = STORAGE_FPS
    # ────────────────────────────────────────────────────────────────────────

    # Flush stale frames left in the OS webcam buffer by calibration.
    # Without this, the main loop immediately processes ~30 old frames,
    # filling the pre-buffer and triggering a ghost clip with peak=0.
    print("[Live] Flushing webcam buffer after calibration…")
    for _ in range(5):
        cap.read()

    # videolive: write one frame every this many wall-clock seconds
    vl_frame_interval = 1.0 / storage_fps

    # Fresh objects — created AFTER flushing so no calibration frames leak in
    motion_gate = MotionGate()
    recorder    = SmartRecorder(storage_fps, w, h)
    prob_buffer = deque(maxlen=SMOOTHING_WINDOW)

    cnn = pose = avg = 0.0
    total_clips  = 0
    total_segs   = 0
    WIN = "A-EYE | Live (Q=quit)"

    cv2.namedWindow(WIN, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(WIN, min(w, 960), min(h, 540))

    # --- videolive state (OFF until first violence clip) ---
    session_ts    = time.strftime("%Y%m%d_%H%M%S")
    segment_idx   = 0
    live_writer   = None      # None = not recording
    live_file     = ""
    live_end_time = 0.0       # wall-clock time to stop current segment
    vl_next_write = 0.0       # next allowed write time (pacing)
    # -------------------------------------------------------

    # AI pause: set to future wall-clock time when AI must stay OFF.
    # 0.0 means AI is running normally.
    ai_paused_until = 0.0

    def _start_videolive_segment():
        nonlocal segment_idx, live_writer, live_file, live_end_time, vl_next_write
        segment_idx += 1
        live_file = os.path.join(
            LIVE_OUTPUT_FOLDER,
            f"live_{session_ts}_seg{segment_idx:03d}.mp4",
        )
        live_writer = cv2.VideoWriter(
            live_file,
            cv2.VideoWriter_fourcc(*"mp4v"),
            storage_fps, (w, h),
        )
        live_end_time = time.time() + VIDEOLIVE_DURATION_SECONDS
        vl_next_write = time.time()   # accept first frame immediately
        remaining     = VIDEOLIVE_DURATION_SECONDS
        print(f"[Live] videolive seg {segment_idx} STARTED  "
              f"@ {storage_fps:.1f} fps  ->  {live_file}")
        print(f"[Live] Will record for {remaining}s  "
              f"(~{int(remaining * storage_fps)} frames expected)")

    def _stop_videolive_segment():
        nonlocal live_writer, total_segs
        if live_writer is not None:
            live_writer.release()
            live_writer = None
            total_segs += 1
            print(f"[Live] videolive seg SAVED  ->  {live_file}")

    while True:
        ret, frame = cap.read()
        if not ret:
            time.sleep(0.01)
            continue

        now = time.time()
        ai_paused = now < ai_paused_until

        # ── Close videolive segment when 2-min window elapses ──
        if live_writer is not None and now >= live_end_time:
            _stop_videolive_segment()
            ai_paused_until = 0.0          # allow AI to run again
            print("[Live] 2-min window done. AI resumed.")

        # ── Write one frame to videolive at the calibrated pace ──
        if live_writer is not None:
            if now >= vl_next_write:
                live_writer.write(frame)
                vl_next_write += vl_frame_interval

        annotated = frame.copy()

        if ai_paused:
            # ── AI is OFF — show a simple countdown overlay ──
            remaining = ai_paused_until - now
            cv2.rectangle(annotated, (10, 8), (420, 50), (0, 0, 0), -1)
            _put(annotated,
                 f"AI PAUSED  —  recording aftermath  ({remaining:.0f}s remaining)",
                 (16, 36), 0.62, (0, 210, 255), 2)
        else:
            # ── AI is ON ──
            models_active = motion_gate.check(frame)
            is_violent    = False

            if models_active:
                cnn             = violence_detector.predict(frame)
                pose, annotated = pose_detector.predict(frame)
                fusion          = 0.7 * cnn + 0.3 * pose
                prob_buffer.append(fusion)
                avg        = sum(prob_buffer) / len(prob_buffer)
                is_violent = avg > THRESHOLD
            else:
                prob_buffer.clear()
                cnn = pose = avg = 0.0

            saved, peak = recorder.feed(frame, is_violent, avg)
            if saved:
                total_clips += 1
                log_event(cam_id, location, peak, saved)
                print(f"[Live] Violence clip #{total_clips} -> {saved}  peak={peak:.3f}")
                try:
                    converted_clip = convert_to_browser_format(saved)

                    clip_url = upload_clip(converted_clip)

                    threading.Thread(
                        target=process_suspect,
                        args=(saved,),
                        daemon=True
                    ).start()

                    print("Uploaded:", clip_url)
                    incident = generate_incident(
                        camera_data={
                            "camera_id": cam_id,
                            "city": "Patna",
                            "precinct": "South Belt",
                            "location": "Ashok Rajpath Crossing",
                            "latitude": 25.6175,
                            "longitude": 85.1710
                        },
                        confidence=peak,
                        violence_type="Physical Assault",
                        clip_path=clip_url,
                        thumbnail_path=None,
                    )
                    send_incident(incident)
                except Exception as upload_err:
                    print(f"[Live] Upload/send failed (network?): {upload_err}")
                    print("[Live] Clip saved locally. Continuing…")
                # Pause AI and start videolive recording regardless of upload result
                ai_paused_until = now + VIDEOLIVE_DURATION_SECONDS
                _stop_videolive_segment()
                _start_videolive_segment()
                print(f"[Live] AI paused for {VIDEOLIVE_DURATION_SECONDS}s.")

            draw_hud_live(annotated, cnn, pose, avg,
                          recorder.status(), models_active)

        frame_buffer.latest_frame = annotated.copy()
        cv2.imshow(WIN, annotated)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    _stop_videolive_segment()
    cap.release()
    cv2.destroyAllWindows()
    print(f"\n[Live] Done.  Violence clips: {total_clips}  |  "
          f"videolive segments: {total_segs}  ->  {LIVE_OUTPUT_FOLDER}/")


# ==================== VIDEO RAW PLAYBACK ================

def _raw_playback_and_record(cap, fps, w, h, from_frame):
    """
    Plays the rest of `cap` starting at `from_frame`.

    Simultaneously:
      1. Shows every frame in a live window on the laptop screen.
      2. Writes every frame in real-time to  videolive.mp4
         (file grows frame-by-frame as playback progresses).

    No AI runs here at all.
    Stops when the video ends or the user presses Q.
    """
    WIN       = "A-EYE | LIVE Footage (Q=quit)"
    live_ts   = time.strftime("%Y%m%d_%H%M%S")
    LIVE_FILE = os.path.join(LIVE_OUTPUT_FOLDER, f"video_{live_ts}.mp4")
    delay     = max(1, int(1000 / fps))   # pace to real video speed

    cap.set(cv2.CAP_PROP_POS_FRAMES, from_frame)

    # Resizable playback window
    cv2.namedWindow(WIN, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(WIN, min(w, 960), min(h, 540))

    live_writer = cv2.VideoWriter(
        LIVE_FILE,
        cv2.VideoWriter_fourcc(*"mp4v"),
        fps, (w, h),
    )

    print(f"\n[LivePlay] Auto-started from frame {from_frame}")
    print(f"[LivePlay] Writing to  {LIVE_FILE}  in real-time...")

    frames_written = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            print("[LivePlay] End of video reached.")
            break

        ts = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0

        # Overlay — minimal, clean
        display = frame.copy()
        cv2.rectangle(display, (10, 8), (280, 48), (0, 0, 0), -1)
        _put(display, f"LIVE  |  {ts:.1f}s", (16, 36), 0.78, (0, 210, 255), 2)

        frame_buffer.latest_frame = display.copy()
        # 1. Show on screen
        cv2.imshow(WIN, display)

        # 2. Write raw (no overlay) to videolive.mp4 in real-time
        live_writer.write(frame)
        frames_written += 1

        if cv2.waitKey(delay) & 0xFF == ord("q"):
            print("[LivePlay] User quit.")
            break

    live_writer.release()
    cv2.destroyWindow(WIN)

    duration = frames_written / fps
    print(f"[LivePlay] Done.  {frames_written} frames written  "
          f"({duration:.1f}s)  ->  {LIVE_FILE}")


# ==================== VIDEO MODE ========================

def analyze_video(video_path, cam_id="CAM2", location="Gandhi Maidan Gate 2"):
    """
    Phase 1 — AI analysis
    ---------------------
    Runs motion gate + CNN + pose + fusion on every frame.
    SmartRecorder: 5s pre-buffer, dynamic extension, calm-state stop.
    Saves evidence clip(s) to violent_clips/.

    Phase 2 — Auto live playback  (triggered automatically after first save)
    -------------------------------------------------------------------------
    The moment the first violence clip is finalised and saved:
      * AI analysis stops immediately.
      * Raw playback starts from the current frame position.
      * Every remaining frame is shown on screen AND written to videolive.mp4
        in real-time, simultaneously.
      * No AI runs during this phase.
      * Stops when the video file ends (or user presses Q).
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"[Video] Cannot open: {video_path}")
        return

    fps          = int(cap.get(cv2.CAP_PROP_FPS)) or 30
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    w            = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h            = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    print(f"\n[Video] {video_path}")
    print(f"[Video] {w}x{h}  @{fps}fps  ({total_frames} frames)")
    print("[Video] Phase 1: AI analysis running...\n")

    pose_detector.reset()

    motion_gate = MotionGate()
    recorder    = SmartRecorder(fps, w, h)
    prob_buffer = deque(maxlen=SMOOTHING_WINDOW)

    WIN   = "A-EYE | Video Analysis (Q=quit)"
    delay = max(1, int(1000 / fps))

    # Resizable window — opens at a comfortable size, drag to enlarge freely
    cv2.namedWindow(WIN, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(WIN, min(w, 960), min(h, 540))

    cnn = pose = avg = 0.0
    total_clips = 0
    frame_index = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        ts            = frame_index / fps
        models_active = motion_gate.check(frame)
        annotated     = frame.copy()
        is_violent    = False

        if models_active:
            cnn             = violence_detector.predict(frame)
            pose, annotated = pose_detector.predict(frame)
            fusion          = 0.8 * cnn + 0.2 * pose
            prob_buffer.append(fusion)
            avg        = sum(prob_buffer) / len(prob_buffer)
            is_violent = avg > THRESHOLD
        else:
            prob_buffer.clear()
            cnn = pose = avg = 0.0

        saved, peak = recorder.feed(frame, is_violent, avg)
        if saved:
            total_clips += 1
            log_event(cam_id, location, peak, saved)
            print(f"\n[Video] Violence clip saved -> {saved}  peak={peak:.3f}")
            try:
                converted_clip = convert_to_browser_format(saved)

                clip_url = upload_clip(converted_clip)

                threading.Thread(
                    target=process_suspect,
                    args=(saved,),
                    daemon=True
                ).start()

                print("Uploaded:", clip_url)
                incident = generate_incident(
                    camera_data={
                        "camera_id": cam_id,
                        "city": "Patna",
                        "precinct": "River Zone",
                        "location": location,
                        "latitude": 25.6208,
                        "longitude": 85.1450
                    },
                    confidence=peak,
                    violence_type="Physical Assault",
                    clip_path=clip_url,
                    thumbnail_path=None,
                )
                send_incident(incident)
            except Exception as upload_err:
                print(f"[Video] Upload/send failed (network?): {upload_err}")
                print("[Video] Clip saved locally. Continuing…")
            print("[Video] Phase 1 complete.")
            print("[Video] Phase 2: switching to LIVE playback automatically...")

            # -------------------------------------------------
            # PHASE 2: AI stops here.
            # Hand off current cap position to raw playback.
            # frame_index+1 because we already consumed this frame.
            # -------------------------------------------------
            cv2.destroyWindow(WIN)
            _raw_playback_and_record(cap, fps, w, h, frame_index + 1)

            # After playback ends, break out of analysis loop entirely
            cap.release()
            cv2.destroyAllWindows()

            print("\n+------------------------------------------+")
            print("|        VIDEO ANALYSIS COMPLETE           |")
            print(f"|   Violence clips : {total_clips:<22} |")
            print(f"|   Live footage   : videolive/ folder     |")
            print("+------------------------------------------+")
            return   # <-- exit function; no further processing

        # Draw HUD on analysis window (phase 1 only)
        draw_hud_video(annotated, cnn, pose, avg,
                       recorder.status(), ts, live_ready=False)
        cv2.imshow(WIN, annotated)
        if cv2.waitKey(delay) & 0xFF == ord("q"):
            break

        frame_index += 1
        if frame_index % 150 == 0:
            pct = frame_index / max(total_frames, 1) * 100
            print(f"  ... {frame_index}/{total_frames}  ({pct:.0f}%)")

    # --- Reached EOF without any violence detected ---
    saved, peak = recorder.force_finalise()
    if saved:
        log_event(cam_id, location, peak, saved)
        print(f"[Video] EOF flush -> {saved}  peak={peak:.3f}")
        try:
         converted_clip = convert_to_browser_format(saved)

         clip_url = upload_clip(converted_clip)

         print("Uploaded:", clip_url)

         incident = generate_incident(
            camera_data={
                "camera_id": cam_id,
                "city": "Patna",
                "precinct": "River Zone",
                "location": location,
                "latitude": 25.6208,
                "longitude": 85.1450 
            },
            confidence=peak,
            violence_type="Physical Assault",

            # IMPORTANT
            clip_path=clip_url,

            thumbnail_path=None,
         )
        

         send_incident(incident)
        except Exception as upload_err:
            print(f"[Video] EOF upload/send failed (network?): {upload_err}")
            print("[Video] Clip saved locally.")

    cap.release()
    cv2.destroyAllWindows()

    print("\n+------------------------------+")
    print("|   VIDEO ANALYSIS COMPLETE    |")
    print(f"|   Violence clips : {total_clips:<10} |")
    if total_clips == 0:
        print("|   No violence detected.      |")
    print("+------------------------------+")


# ==================== ENTRY POINT =======================

if __name__ == "__main__":
    
    print("+================================+")
    print("|       An-EYE  v1.0              |")
    print("|  Violence Detection System     |")
    print("+================================+\n")
    print("  1.  Live mode  (HP Victus webcam)")
    print("  2.  Analyse video file\n")

    choice = input("Enter choice [1/2]: ").strip()

    if choice == "1":

        stream_thread = threading.Thread(
            target=start_stream_server,
            daemon=True
        )

        stream_thread.start()

        print("\n[Stream] Live stream server started:")
        print("http://localhost:8001\n")

        start_live(cam_id="CAM1", location="Ashok Rajpath Crossing")
    
    elif choice == "2":
        path = input("Enter video path: ").strip()
        if os.path.isfile(path):
            stream_thread = threading.Thread(
                target=start_stream_server,
                daemon=True
            )

            stream_thread.start()

            print("\n[Stream] Live stream server started:")
            print("http://localhost:8001\n")
            analyze_video(path, cam_id="CAM2", location="gandhi Maidan Gate 2")
        else:
            print(f"[Error] File not found: {path}")
    else:
        print("Invalid choice.")
