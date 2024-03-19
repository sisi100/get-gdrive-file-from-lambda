import io
import json
import os

import boto3
from google.auth import aws
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload

FOLDER_ID = os.getenv("FOLDER_ID")
BUCKET_NAME = os.getenv("BUCKET_NAME")

bucket = boto3.resource("s3").Bucket(BUCKET_NAME)


def get_drive():
    with open("./google_config.json") as f:
        json_config_info = json.loads(f.read())
    credentials = aws.Credentials.from_info(json_config_info)
    return build("drive", "v3", credentials=credentials)


def download_file(drive, file_id):
    try:
        request = drive.files().get_media(fileId=file_id)
        file = io.BytesIO()
        downloader = MediaIoBaseDownload(file, request)
        done = False
        while done is False:
            _, done = downloader.next_chunk()

    except HttpError as error:
        print(f"An error occurred: {error}")
        file = None

    return file.getvalue()


def upload_file_to_s3(file_name, file):
    bucket.put_object(Key=file_name, Body=file)


def process_files(drive):
    #  https://developers.google.com/drive/api/guides/search-files?hl=ja
    query = " and ".join(
        [
            f"'{FOLDER_ID}' in parents",
            "mimeType='text/plain'",
        ]
    )

    results = drive.files().list(q=query).execute()
    items = results.get("files", [])
    for item in items:
        file_name = item["name"]
        file_id = item["id"]

        file = download_file(drive, file_id)

        upload_file_to_s3(file_name, file)


def handler(event, context):
    drive = get_drive()
    process_files(drive)
