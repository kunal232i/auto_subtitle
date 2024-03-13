# Demo

-

## Prerequisites

Make sure you have the following installed:

- Python 3.7 or later
- [pip](https://pip.pypa.io/en/stable/installation/)

## Setup

1. Create a virtual environment:

   ```bash
   python3 -m venv venv
   ```

2. Activate the virtual environment:

   - On Linux/macOS:

     ```bash
     source venv/bin/activate
     ```

   - On Windows (Command Prompt):

     ```bash
     .\venv\Scripts\activate
     ```

     On Windows (PowerShell):

     ```bash
     .\venv\Scripts\Activate.ps1
     ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

## Run the Application

1. Start the FastAPI application:

   ```bash
   uvicorn main:app --reload
   ```

   This will launch the FastAPI development server. The `--reload` option enables automatic reloading of the server upon code changes during development.

2. Open your web browser and go to [http://localhost:8000](http://localhost:8000) to access the FastAPI Swagger documentation.

## API Endpoints

## 1. Home Page

- **Endpoint**: `/`
- **Method**: GET
- **Response Type**: HTML
- **Description**: Renders the home page using the Jinja2 template `index.html`.

## 2. Video Translation

- **Endpoint**: `/translate`
- **Method**: POST
- **Parameters**:
  - `video`: File (required) - The video file to be translated.
  - `target_language`: Form field (optional, default: 'en') - The target language for translation.
- **Response Type**: JSON
- **Description**: Uploads a video file, translates its subtitles to the specified target language, and returns a success message.

## 3. List Videos

- **Endpoint**: `/videos`
- **Method**: GET
- **Response Type**: JSON
- **Description**: Retrieves a list of video keys from the specified AWS S3 bucket (`clps-media`).

## 4. Get Video Stream

- **Endpoint**: `/videos/{video_key}`
- **Method**: GET
- **Parameters**:
  - `video_key`: Path parameter (required) - The key of the video in the AWS S3 bucket.
- **Response Type**: Video Streaming (video/mp4)
- **Description**: Streams the specified video from the AWS S3 bucket.

## Notes

- The application assumes the existence of a `temp` folder to store temporary video files during translation.
- Logging is configured to display INFO-level messages.
