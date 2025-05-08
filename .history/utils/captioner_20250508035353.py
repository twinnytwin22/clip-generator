from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip

def add_captions_to_clip(clip_path, caption_text, output_path):
    video = VideoFileClip(clip_path)
    txt_clip = TextClip(caption_text, fontsize=48, color='white', font='Arial', method='caption', size=video.size)
    txt_clip = txt_clip.set_position(('center', 'bottom')).set_duration(video.duration)
    final = CompositeVideoClip([video, txt_clip])
    final.write_videofile(output_path, codec="libx264")
