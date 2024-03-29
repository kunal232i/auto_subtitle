import logging
from moviepy.editor import VideoFileClip
from faster_whisper import WhisperModel
import openai
from dotenv import load_dotenv
import json
import os
from subtitle_in_video import subtitle_in_video

load_dotenv()

logging.basicConfig(level=logging.INFO)


def video_to_audio(input_video, target_language):
    try:
        video_clip = VideoFileClip(input_video)
        audio_clip = video_clip.audio

        audio_folder = os.path.join("temp", "audio")
        os.makedirs(audio_folder, exist_ok=True)

        audio_filename = os.path.splitext(os.path.basename(input_video))[0] + ".mp3"
        output_audio = os.path.join(audio_folder, audio_filename)

        audio_clip.write_audiofile(output_audio)
        video_clip.close()
        audio_clip.close()
        logging.info(f"Conversion complete. Audio saved to {output_audio}")
        
        detect_language_and_transcribe(output_audio, target_language, input_video)
    except Exception as e:
        logging.error(f"Error in video_to_audio: {e}")


def detect_language_and_transcribe(audio_path, target_language, input_video_file):
    try:
        model_size = "base"
        model = WhisperModel(model_size, device="cpu", compute_type="int8")
        segments, info = model.transcribe(audio_path, word_timestamps=True)
        segments = list(segments)
        wordlevel_info = []

        for segment in segments:
            for word in segment.words:
                wordlevel_info.append({'word': word.word, 'start': word.start, 'end': word.end})

        logging.info("Transcription successfully done!")
        translate_text(info.language, target_language, wordlevel_info, input_video_file)
    except Exception as e:
        logging.error(f"Error in detect_language_and_transcribe: {e}")

def translate_text(source_language, target_language, wordlevel_info, input_video_file):
    try:
        openai.api_key = os.getenv("OPENAI_API_KEY")
        data = wordlevel_info

        word_timestamps = [(item['word'], item['start'], item['end']) for item in data]

        input_text = ' '.join([word for word, _, _ in word_timestamps])

        conversation = [{"role": "user", "content": f"Act as an expert translator for song lyrics. \
                        Translate the the following lyrics from {source_language} to {target_language}:\n\n{input_text}. \
                        Only respond with the translated lyrics at all cost. \
                        "}]

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=conversation
        )

        translated_text = response['choices'][0]['message']['content']

        translated_words = translated_text.split()

        translated_data = []
        for i in range(min(len(translated_words), len(word_timestamps))):
            data_point = {
                "word": translated_words[i],
                "start": word_timestamps[i][1],
                "end": word_timestamps[i][2]
            }
            translated_data.append(data_point)
        
        with open("translation.json", 'w') as output_file:
            json.dump(translated_data, output_file, indent=2, ensure_ascii=False)
        
        subtitle_in_video(translated_data, input_video_file, target_language)
    except Exception as e:
        logging.error(f"Error in translate_text: {e}")

def translate(input_video_file, target_language):
    try:
        video_to_audio(input_video_file, target_language)
    except Exception as e:
        logging.error(f"Error in translate: {e}")