import boto3
import zipfile
import os
import tempfile

SOURCE_BUCKET = 'compression-file'
DEST_BUCKET = 'compression-file'
SOURCE_KEY = 'sample_50MB.txt'
DEST_KEY = 'sample_50MB.zip'

def lambda_handler(event, context):
    s3 = boto3.client('s3')
    
    with tempfile.TemporaryDirectory() as tmp:
        download_path = os.path.join(tmp, 'input_file')
        zip_path = os.path.join(tmp, 'output_file.zip')

        s3.download_file(SOURCE_BUCKET, SOURCE_KEY, download_path)

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.write(download_path, SOURCE_KEY)

        s3.upload_file(zip_path, DEST_BUCKET, DEST_KEY)

    return {
        'statusCode': 200,
        'body': 'File compressed and uploaded successfully!'
    }