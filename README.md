# Project

## Setup

### For Windows

```bash
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

### For Mac/Linux

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Environment Variable setup

Run the following command to set up the environment variables:

```bash
mv .env.example .env
```

Now, open the `.env` file and add the required key for the "openAI" configuration.

## Usage

```bash
python main.py --video path/to/your/video.mp4 --target_language desired_language
```

- `--video`: Path to the video file.
- `--target_language`: Target language for subtitles conversion. Default is "en".

Make sure to replace `path/to/your/video.mp4` with the actual path to your video file and specify the desired language for subtitles conversion.

Feel free to customize the command based on your requirements.

**Note**: Ensure that you have activated the virtual environment before running the commands.
