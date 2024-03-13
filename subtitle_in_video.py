from moviepy.editor import TextClip, CompositeVideoClip, concatenate_videoclips,VideoFileClip, ColorClip
import numpy as np
import os
import logging
import json
import boto3
import io
import shutil
from botocore.exceptions import ClientError

# Configure AWS S3 credentials
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY")
S3_OUTPUT_BUCKET_NAME = "clps-media"

logging.basicConfig(level=logging.INFO)

def split_text_into_lines(data):
    MaxChars = 30
    MaxDuration = 2.5
    MaxGap = 1.5 # Split if nothing is spoken (gap) for these many seconds

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

        temp = bytes(temp, 'utf-8').decode('unicode_escape')

        # Check if adding a new word exceeds the maximum character count or duration
        new_line_chars = len(temp)

        duration_exceeded = line_duration > MaxDuration
        chars_exceeded = new_line_chars > MaxChars
        if idx>0:
          gap = word_data['start'] - data[idx-1]['end']
          # print (word,start,end,gap)
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
    
    with open("subtitles.json", 'w') as output_file:
        json.dump(subtitles, output_file, indent=2, ensure_ascii=False)

    return subtitles
     
def create_caption(
        textJSON, 
        framesize, 
        fontsize=4, #4.0 is good for reels
        font="fonts/Poppins/Poppins-Bold.ttf", 
        color='white', 
        highlight_color='black', 
        stroke_color='black', 
        stroke_width=2.6,
        kerning=0,
        right_to_left=False,
        
):
    wordcount = len(textJSON['textcontents'])
    full_duration = textJSON['end'] - textJSON['start']

    word_clips = []
    xy_textclips_positions = []
    x_pos = 0
    y_pos = 0
    line_width = 0  # Total width of words in the current line
    frame_width = framesize[0]
    frame_height = framesize[1]

    x_buffer = frame_width * 1 / 10
    max_line_width = frame_width - 2 * x_buffer

    # Calculate fontsize based on the frame height and provided percentage
    fontsize = int(frame_height * fontsize / 100)
    space_width = 0
    space_height = 0

    # Use right-to-left text direction if the language is Arabic
    if right_to_left:
        enumerator = enumerate(reversed(textJSON["textcontents"]))
    else:
        enumerator = enumerate(textJSON["textcontents"])

    for index, wordJSON in enumerate(textJSON['textcontents']):
        duration = wordJSON['end'] - wordJSON['start']
        word_clip = TextClip(wordJSON['word'], font=font, fontsize=fontsize, color=color, stroke_color=stroke_color, stroke_width=stroke_width).set_start(textJSON['start']).set_duration(full_duration)
        word_clip_space = TextClip(" ", font=font, fontsize=fontsize, color=color).set_start(textJSON['start']).set_duration(full_duration)
        word_width, word_height = word_clip.size
        space_width, space_height = word_clip_space.size

        if line_width + word_width + space_width <= max_line_width:
            xy_textclips_positions.append({
                "x_pos": x_pos,
                "y_pos": y_pos,
                "width": word_width,
                "height": word_height,
                "word": wordJSON['word'],
                "start": wordJSON['start'],
                "end": wordJSON['end'],
                "duration": duration
            })

            word_clip = word_clip.set_position((x_pos, y_pos))
            word_clip_space = word_clip_space.set_position((x_pos + word_width, y_pos))
            x_pos = x_pos + word_width + space_width
            line_width = line_width + word_width + space_width
        else:
            x_pos = 0
            y_pos = y_pos + word_height + 10
            line_width = word_width + space_width
            xy_textclips_positions.append({
                "x_pos": x_pos,
                "y_pos": y_pos,
                "width": word_width,
                "height": word_height,
                "word": wordJSON['word'],
                "start": wordJSON['start'],
                "end": wordJSON['end'],
                "duration": duration
            })

            word_clip = word_clip.set_position((x_pos, y_pos))
            word_clip_space = word_clip_space.set_position((x_pos + word_width, y_pos))
            x_pos = word_width + space_width

        word_clips.append(word_clip)
        word_clips.append(word_clip_space)

    for highlight_word in xy_textclips_positions:
        word_clip_highlight = (
            TextClip(
            highlight_word['word'], 
            font=font, 
            fontsize=fontsize, 
            color=highlight_color, 
            stroke_color=stroke_color, 
            stroke_width=stroke_width,
            kerning=kerning
            )
            .set_start(highlight_word['start'])
            .set_duration(highlight_word['duration'])
        )

        word_clip_highlight = word_clip_highlight.set_position(
            (highlight_word['x_pos'], highlight_word['y_pos'])
            )
        word_clips.append(word_clip_highlight)

    return word_clips, xy_textclips_positions

def edit_video(
        input_video_filename, 
        linelevel_subtitles, 
        target_language, 
        subs_position='center'
):
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

            color_clip = ColorClip(size=(int(max_width * 1.1), int(max_height * 1.1)), color=(64, 64, 64))
            color_clip = color_clip.set_opacity(0)
            color_clip = color_clip.set_start(line['start']).set_duration(line['end'] - line['start'])
            clip_to_overlay = CompositeVideoClip([color_clip] + out_clips)

            if subs_position == "bottom75":
                clip_to_overlay = clip_to_overlay.set_position(
                    ("center", 0.75), relative=True
                )
            else:
                clip_to_overlay = clip_to_overlay.set_position(subs_position)

            all_linelevel_splits.append(clip_to_overlay)

        final_video = CompositeVideoClip([input_video] + all_linelevel_splits)
        final_video = final_video.set_audio(input_video.audio)


        video_folder = os.path.join("temp", "video")
        os.makedirs(video_folder, exist_ok=True)

        base_filename = os.path.splitext(os.path.basename(input_video_filename))[0]
        output_video_file = f"./temp/video/{base_filename}_{target_language}_subtitle.mp4"

        final_video.write_videofile(output_video_file, fps=30, codec="libx264", audio_codec="aac")

        s3_object_key = output_video_file.split("/")[-1]
        upload_file_to_s3(output_video_file, S3_OUTPUT_BUCKET_NAME, s3_object_key)
        logging.info(f"Subtitled video saved to {S3_OUTPUT_BUCKET_NAME}/{s3_object_key}")

    except Exception as e:
        logging.error(f"Error editing video: {str(e)}")

def upload_file_to_s3(file, bucket_name, s3_object_key):
    s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY)
    try:
        s3.upload_file(file, bucket_name, s3_object_key)
        logging.info(f"File uploaded to S3: {s3_object_key}")
        temp_folder_path = "temp"
        shutil.rmtree(temp_folder_path)
        logging.info(f"Temporary folder '{temp_folder_path}' has been removed.")
    except ClientError as e:
        logging.error(e)
        return False
    return True


def subtitle_in_video(wordlevel_info, input_video_filename, target_language):
    try:
        linelevel_subtitles = split_text_into_lines(wordlevel_info)
        logging.info("Subtitle is ready")
        edit_video(input_video_filename, linelevel_subtitles, target_language)
    except Exception as e:
        logging.error(f"Error creating subtitles: {str(e)}")