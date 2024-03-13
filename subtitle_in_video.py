from moviepy.editor import TextClip, CompositeVideoClip, concatenate_videoclips,VideoFileClip, ColorClip
import numpy as np
import os
import logging

logging.basicConfig(level=logging.INFO)

def split_text_into_lines(data):
    MaxChars = 30
    MaxDuration = 2.5
    MaxGap = 1.5

    subtitles = []
    line = []
    line_duration = 0
    line_chars = 0

    for idx,word_data in enumerate(data):
        word = word_data["word"]
        start = word_data["start"]
        end = word_data["end"]

        line.append(word_data)
        line_duration += end - start

        temp = " ".join(item["word"] for item in line)
        new_line_chars = len(temp)

        duration_exceeded = line_duration > MaxDuration
        chars_exceeded = new_line_chars > MaxChars
        if idx>0:
          gap = word_data['start'] - data[idx-1]['end']
          maxgap_exceeded = gap > MaxGap
        else:
          maxgap_exceeded = False


        if duration_exceeded or chars_exceeded or maxgap_exceeded:
            if line:
                subtitle_line = {
                    "word": " ".join(item["word"] for item in line),
                    "start": line[0]["start"],
                    "end": line[-1]["end"],
                    "textcontents": line
                }
                subtitles.append(subtitle_line)
                line = []
                line_duration = 0
                line_chars = 0
    if line:
        subtitle_line = {
            "word": " ".join(item["word"] for item in line),
            "start": line[0]["start"],
            "end": line[-1]["end"],
            "textcontents": line
        }
        subtitles.append(subtitle_line)

    return subtitles
     
def create_caption(textJSON, framesize,font = "Roboto", color='white', highlight_color='white',stroke_color='black',stroke_width=1.5):
    wordcount = len(textJSON['textcontents'])
    full_duration = textJSON['end']-textJSON['start']

    word_clips = []
    xy_textclips_positions =[]

    x_pos = 0
    y_pos = 0
    line_width = 0
    frame_width = framesize[0]
    frame_height = framesize[1]

    x_buffer = frame_width*1/10

    max_line_width = frame_width - 2 * (x_buffer)

    fontsize = int(frame_height * 0.06)

    space_width = ""
    space_height = ""

    for index,wordJSON in enumerate(textJSON['textcontents']):
      duration = wordJSON['end']-wordJSON['start']
      word_clip = TextClip(wordJSON['word'], font = font,fontsize=fontsize, color=color,stroke_color=stroke_color,stroke_width=stroke_width).set_start(textJSON['start']).set_duration(full_duration)
      word_clip_space = TextClip(" ", font = font,fontsize=fontsize, color=color).set_start(textJSON['start']).set_duration(full_duration)
      word_width, word_height = word_clip.size
      space_width,space_height = word_clip_space.size
      if line_width + word_width+ space_width <= max_line_width:
            xy_textclips_positions.append({
                "x_pos":x_pos,
                "y_pos": y_pos,
                "width" : word_width,
                "height" : word_height,
                "word": wordJSON['word'],
                "start": wordJSON['start'],
                "end": wordJSON['end'],
                "duration": duration
            })

            word_clip = word_clip.set_position((x_pos, y_pos))
            word_clip_space = word_clip_space.set_position((x_pos+ word_width, y_pos))

            x_pos = x_pos + word_width+ space_width
            line_width = line_width+ word_width + space_width
      else:
            x_pos = 0
            y_pos = y_pos+ word_height+10
            line_width = word_width + space_width
            xy_textclips_positions.append({
                "x_pos":x_pos,
                "y_pos": y_pos,
                "width" : word_width,
                "height" : word_height,
                "word": wordJSON['word'],
                "start": wordJSON['start'],
                "end": wordJSON['end'],
                "duration": duration
            })

            word_clip = word_clip.set_position((x_pos, y_pos))
            word_clip_space = word_clip_space.set_position((x_pos+ word_width , y_pos))
            x_pos = word_width + space_width


      word_clips.append(word_clip)
      word_clips.append(word_clip_space)


    for highlight_word in xy_textclips_positions:

      word_clip_highlight = TextClip(highlight_word['word'], font = font,fontsize=fontsize, color=highlight_color,stroke_color=stroke_color,stroke_width=stroke_width).set_start(highlight_word['start']).set_duration(highlight_word['duration'])
      word_clip_highlight = word_clip_highlight.set_position((highlight_word['x_pos'], highlight_word['y_pos']))
      word_clips.append(word_clip_highlight)

    return word_clips,xy_textclips_positions


def edit_video(input_video_filename, linelevel_subtitles, target_language):
    try:
        input_video = VideoFileClip(input_video_filename)
        frame_size = input_video.size

        all_linelevel_splits = []

        for line in linelevel_subtitles:
            out_clips, positions = create_caption(line, frame_size)

            max_width = 0
            max_height = 0

            for position in positions:
                x_pos, y_pos = position['x_pos'], position['y_pos']
                width, height = position['width'], position['height']

                max_width = max(max_width, x_pos + width)
                max_height = max(max_height, y_pos + height)

            color_clip = ColorClip(size=(int(max_width * 1.1), int(max_height * 1.1)),
                                   color=(64, 64, 64))
            color_clip = color_clip.set_opacity(.6)
            color_clip = color_clip.set_start(line['start']).set_duration(line['end'] - line['start'])
            clip_to_overlay = CompositeVideoClip([color_clip] + out_clips)
            clip_to_overlay = clip_to_overlay.set_position("bottom")

            all_linelevel_splits.append(clip_to_overlay)

        input_video_duration = input_video.duration

        final_video = CompositeVideoClip([input_video] + all_linelevel_splits)

        final_video = final_video.set_audio(input_video.audio)

        output_folder = "output_video"
        os.makedirs(output_folder, exist_ok=True)
        base_filename = os.path.splitext(os.path.basename(input_video_filename))[0]
        output_audio_file = f"./output_video/{base_filename}_{target_language}_subtitle.mp4"

        final_video.write_videofile(output_audio_file, fps=24, codec="libx264", audio_codec="aac")

    except Exception as e:
        logging.error(f"Error editing video: {str(e)}")

def subtitle_in_video(wordlevel_info, input_video_filename, target_language):
    try:
        linelevel_subtitles = split_text_into_lines(wordlevel_info)
        logging.info("Subtitle is ready")
        edit_video(input_video_filename, linelevel_subtitles, target_language)
    except Exception as e:
        logging.error(f"Error creating subtitles: {str(e)}")