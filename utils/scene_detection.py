import ffmpeg

def detect_scenes(input_path):
    out, _ = (
        ffmpeg
        .input(input_path)
        .filter('select', 'gt(scene\,0.4)')
        .output('pipe:', format='null')
        .run(capture_stdout=True, capture_stderr=True)
    )
    return out
