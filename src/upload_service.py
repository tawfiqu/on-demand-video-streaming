from io import BytesIO
import os
import boto3
from filechunkio import FileChunkIO
from tqdm import tqdm

# Chunk size for uploading in parts
chunk_size_bytes = 1024 * 1024 * 10 

# AWS S3 configuration
session = boto3.Session(
    aws_access_key_id='your_access_key',
    aws_secret_access_key='your_secret_key'
)
objects = session.client(service_name="s3", endpoint_url="https://your-s3-endpoint.com/", use_ssl=True)

def upload_video(source_path):

    key_file = os.path.basename(source_path)  # Extracted filename
    target_bucket = "videos"  # Name of the Amazon S3 bucket
    content_type  = "video/mp4"  # MIME type or content type of the file

    # Create a multipart upload
    response = objects.create_multipart_upload(
        ACL="public-read",
        Bucket=target_bucket,
        ContentType=content_type,
        Key=key_file
    )
    UploadId = response['UploadId']

    # Initialize part number and parts list
    part_number = 1
    parts = []

    try:
        # Get the total file size for tqdm
        total_size = os.path.getsize(source_path)
        # Open the local file using FileChunkIO for efficient handling of large files
        with FileChunkIO(source_path, 'rb', offset=0, closefd=True) as fd:
            for data in tqdm(iter(lambda: fd.read(chunk_size_bytes), b""), total=total_size/chunk_size_bytes, unit="MB", unit_scale=True, leave=False, dynamic_ncols=True):
                # Upload each part
                part = objects.upload_part(
                    Bucket=target_bucket,
                    Key=key_file,
                    Body=BytesIO(data),
                    PartNumber=part_number,
                    UploadId=UploadId
                )
                parts.append({"PartNumber": part_number, "ETag": part["ETag"]})
                part_number += 1

        # Complete the multipart upload
        objects.complete_multipart_upload(
            Bucket=target_bucket,
            Key=key_file,
            UploadId=UploadId,
            MultipartUpload={"Parts": parts}
        )

    except Exception as e:
        # Handle any exceptions, such as cleanup or logging
        print(f"Error: {e}")
        # Optionally abort the multipart upload if an error occurs
        objects.abort_multipart_upload(Bucket=target_bucket, Key=key_file, UploadId=UploadId)
        raise  # Re-raise the exception after cleanup