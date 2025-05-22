import ffmpeg

from scenedetect import VideoManager, SceneManager
from scenedetect.detectors import ContentDetector

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