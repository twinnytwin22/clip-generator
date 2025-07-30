import ffmpeg

from scenedetect import VideoManager, SceneManager
from scenedetect.detectors import AdaptiveDetector, ContentDetector, HashDetector
import math

def detect_scenes(input_path):
    out, _ = (
        ffmpeg
        .input(input_path)
        .filter('select', 'gt(scene\,0.4)')
        .output('pipe:', format='null')
        .run(capture_stdout=True, capture_stderr=True)
    )
    return out



def detect_scenes_pyscenedetect(input_path, threshold=30.0):
    video_manager = VideoManager([input_path])
    scene_manager = SceneManager()
    scene_manager.add_detector(ContentDetector(threshold=threshold))
    video_manager.start()
    scene_manager.detect_scenes(frame_source=video_manager)
    scene_list = scene_manager.get_scene_list()
    # Return list of (start_time, end_time) tuples in seconds
    return [(start.get_seconds(), end.get_seconds()) for start, end in scene_list]




def detect_scenes_local(
    input_path,
    content_thresh=27.0,
    adaptive_sensitivity=8.0,
    # frame-based detection only needs a small debounce; we'll enforce seconds later
    min_scene_len=15,
    min_duration=30.0,
    max_duration=60.0
):
    # --- 1) Run the regular PySceneDetect pipeline ---
    video_manager = VideoManager([input_path])
    scene_manager = SceneManager()

    scene_manager.add_detector(AdaptiveDetector(adaptive_sensitivity))
    scene_manager.add_detector(HashDetector())
    scene_manager.add_detector(ContentDetector(threshold=content_thresh,
                                              min_scene_len=min_scene_len))

    video_manager.start()
    scene_manager.detect_scenes(frame_source=video_manager)
    raw_scenes = scene_manager.get_scene_list()

    # --- 2) Post-process durations into just-right chunks ---
    filtered = []
    for start, end in raw_scenes:
        t0 = start.get_seconds()
        t1 = end.get_seconds()
        dur = t1 - t0

        # drop too-short scenes
        if dur < min_duration:
            continue

        # split too-long scenes into <= max_duration pieces
        if dur > max_duration:
            # how many splits we'll need
            parts = math.ceil(dur / max_duration)
            # actual chunk length (so we don't overshoot last frame)
            chunk = dur / parts
            for i in range(parts):
                cs = t0 + i * chunk
                ce = min(t0 + (i + 1) * chunk, t1)
                # drop any tiny last leftover
                if ce - cs >= min_duration:
                    filtered.append((cs, ce))
        else:
            # just-right scene
            filtered.append((t0, t1))

    return filtered
