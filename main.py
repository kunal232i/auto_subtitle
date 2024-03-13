import argparse
import logging
from audio_translation import translate

def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    parser = argparse.ArgumentParser(description='Convert subtitles for a video to a specified language.')

    parser.add_argument('--video', type=str, help='Path to the video file.')
    parser.add_argument('--target_language', type=str, default='en', help='Target language for subtitles conversion. Default is "en".')

    args = parser.parse_args()

    video_file = args.video
    target_language = args.target_language
    
    logging.info(f"Converting subtitles for video file: {video_file} to language: {target_language}")
    
    translate(video_file, target_language)

if __name__ == '__main__':
    main()
