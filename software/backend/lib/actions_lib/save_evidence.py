import boto3


def save_evidence(mp4_file, bucket_name, clip, aws_access_key_id, aws_secret_access_key, region_name, endpoint_url):
    s3 = boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region_name=region_name
    )
    
    s3.upload_file(mp4_file, bucket_name, f"{clip.filename.split('.')[0]}.mp4", ExtraArgs={'ContentType': 'video/mp4'})
