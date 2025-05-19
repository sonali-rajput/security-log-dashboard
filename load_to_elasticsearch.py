import boto3
import pandas as pd
from elasticsearch import Elasticsearch
from io import BytesIO

# Connect to Elasticsearch without authentication
es = Elasticsearch(["http://localhost:9200"])

# Verify connection
print("Elasticsearch info:", es.info())

# Create index with mappings
index_name = "security-logs"

# Define the index mapping
mapping = {
    "mappings": {
        "properties": {
            "ip": {"type": "ip"},
            "timestamp_parsed": {"type": "date"},
            "date": {"type": "date"},
            "hour_of_day": {"type": "integer"},
            "method": {"type": "keyword"},
            "endpoint": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
            "http_version": {"type": "keyword"},
            "status_code": {"type": "integer"},
            "bytes": {"type": "long"},
            "is_error": {"type": "integer"},
            "is_client_error": {"type": "integer"},
            "is_server_error": {"type": "integer"},
            "is_potential_attack": {"type": "integer"},
            "referrer": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
            "user_agent": {"type": "text"}
        }
    }
}

# Create the index
# Updated for Elasticsearch 9
try:
    es.indices.create(index=index_name, mappings=mapping["mappings"])
    print(f"Created index: {index_name}")
except Exception as e:
    if "resource_already_exists_exception" in str(e):
        print(f"Index {index_name} already exists, continuing...")
    else:
        print(f"Error creating index: {str(e)}")

# Access S3 and load the data
s3 = boto3.client('s3')

# List all parquet files in the transformed folder
# Using the correct path we discovered
bucket = "security-log-analysis-bucket"
prefix = "security-log-analysis-bucket-database/security-log-analysis-transformed/"

print(f"Looking for parquet files in s3://{bucket}/{prefix}")

response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)

# Check if any files are found
if 'Contents' not in response:
    print("No files found in the specified S3 location!")
    exit(1)

file_count = 0
indexed_count = 0

for obj in response.get('Contents', []):
    if obj['Key'].endswith('.parquet'):
        file_count += 1
        print(f"Processing file: {obj['Key']}, Size: {obj['Size']} bytes")
        
        try:
            # Get the parquet file
            obj_response = s3.get_object(Bucket=bucket, Key=obj['Key'])
            parquet_file = BytesIO(obj_response['Body'].read())
            
            # Read parquet with pandas
            df = pd.read_parquet(parquet_file)
            print(f"Read {len(df)} records from parquet file")
            
            # Handle column names - adjust as needed based on your transformed data
            # These should match the field names you used in your Glue job
            column_mapping = {
                # Add any column name mappings if needed
                # For example: 'ip': 'clientip',
            }
            
            for old_name, new_name in column_mapping.items():
                if old_name in df.columns:
                    df.rename(columns={old_name: new_name}, inplace=True)
            
            # Process timestamp columns if needed
            timestamp_cols = ['timestamp_parsed', 'date']
            for ts_col in timestamp_cols:
                if ts_col in df.columns:
                    df[ts_col] = df[ts_col].astype(str)
            
            # Print schema to verify column names
            print("DataFrame columns:", df.columns.tolist())
            
            # Bulk index into Elasticsearch
            actions = []
            for i, row in df.iterrows():
                # Convert row to dictionary and handle NaN values
                doc = row.to_dict()
                # Replace NaN with None for JSON compatibility
                doc = {k: (None if pd.isna(v) else v) for k, v in doc.items()}
                
                # Create action for bulk API
                action = {
                    "_index": index_name,
                    "_source": doc
                }
                actions.append(action)
            
            # Use the bulk API to index data
            from elasticsearch.helpers import bulk
            success, failed = bulk(es, actions)
            print(f"Indexed {success} documents, {failed} failed")
            indexed_count += success
        
        except Exception as e:
            print(f"Error processing file {obj['Key']}: {str(e)}")
            # Print detailed exception for debugging
            import traceback
            traceback.print_exc()

print(f"Processed {file_count} parquet files")
print(f"Total indexed documents: {indexed_count}")

# Verify data was indexed
count = es.count(index=index_name)
print(f"Total documents in Elasticsearch: {count['count']}")

print("Indexing complete")