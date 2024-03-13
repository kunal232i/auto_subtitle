from fastapi import FastAPI, File, UploadFile, Form, Request, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from starlette.responses import StreamingResponse
import asyncio
from audio_translation import translate
import logging
import boto3
from botocore.exceptions import ClientError
import os

app = FastAPI()
templates = Jinja2Templates(directory="templates")
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@app.get("/", response_class=HTMLResponse)
async def read_item(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/translate")
async def translate_video(video: UploadFile = File(...), target_language: str = Form('en')):
    temp_folder = "temp"
    if not os.path.exists(temp_folder):
        os.makedirs(temp_folder)

    video_path = os.path.join(temp_folder, video.filename)
    with open(video_path, "wb") as video_file:
        content = await video.read()
        video_file.write(content)

    logging.info(f"Converting subtitles for video file: {video_path} to language: {target_language}")
    translate(video_path, target_language)
    return {"message": "Translation successful"}

AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY")
bucket_name = "clps-media"

s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY)

@app.get("/videos")
def get_videos():
    videos = []
    try:
        response = s3.list_objects(Bucket=bucket_name)
        for obj in response.get('Contents', []):
            videos.append(obj['Key'])
    except Exception as e:
        return {"error": str(e)}
    
    return {"videos": videos}

@app.get("/videos/{video_key}")
async def get_video(video_key: str):
    try:
        s3_response = s3.get_object(Bucket=bucket_name, Key=video_key)
        video_streaming = s3_response['Body']
    except Exception as e:
        raise HTTPException(status_code=404, detail="Video not found")

    return StreamingResponse(video_streaming, media_type="video/mp4")