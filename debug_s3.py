import boto3
import pandas as pd
from elasticsearch import Elasticsearch
from io import BytesIO

# Connect to Elasticsearch without authentication
es = Elasticsearch(["http://localhost:9200"])

# Verify connection
print("Elasticsearch info:", es.info())

# First, let's check what buckets we can access
s3 = boto3.client('s3')
print("Listing all S3 buckets:")
response = s3.list_buckets()
for bucket in response['Buckets']:
    print(f"- {bucket['Name']}")

# Now, let's try to list the contents of the bucket
bucket_name = "security-log-analysis-bucket"
print(f"\nListing root contents of bucket: {bucket_name}")
try:
    response = s3.list_objects_v2(Bucket=bucket_name, Delimiter='/')
    if 'CommonPrefixes' in response:
        print("Directories:")
        for prefix in response['CommonPrefixes']:
            print(f"- {prefix['Prefix']}")
    
    if 'Contents' in response:
        print("Files:")
        for item in response['Contents']:
            print(f"- {item['Key']}, Size: {item['Size']} bytes")
    else:
        print("No files found at the root level.")
        
    print("\nChecking specific paths where your files might be located:")
    possible_paths = [
        "security-log-analysis-transformed/",
        "security-log-analysis-bucket-database/security-log-analysis-transformed/",
        ""  # Root of bucket
    ]
    
    for path in possible_paths:
        print(f"\nListing contents for path: {path}")
        response = s3.list_objects_v2(Bucket=bucket_name, Prefix=path)
        if 'Contents' in response:
            print(f"Found {len(response['Contents'])} items:")
            for item in response['Contents']:
                if item['Key'].endswith('.parquet'):
                    print(f"- {item['Key']}, Size: {item['Size']} bytes (PARQUET FILE)")
                else:
                    print(f"- {item['Key']}, Size: {item['Size']} bytes")
        else:
            print("No files found.")
except Exception as e:
    print(f"Error accessing S3: {str(e)}")
    print("\nThis could be due to:")
    print("1. Incorrect bucket name")
    print("2. Insufficient permissions")
    print("3. AWS credentials not set up correctly")
    print("\nTry setting explicit AWS credentials:")
    print("s3 = boto3.client('s3', aws_access_key_id='YOUR_KEY', aws_secret_access_key='YOUR_SECRET', region_name='YOUR_REGION')")