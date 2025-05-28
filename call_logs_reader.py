import os
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv
import pytz
import logging

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger("teliphonic-rag-agent")

# Azure credentials
AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
AZURE_LOGS_CONTAINER_NAME = os.getenv("AZURE_LOGS_CONTAINER_NAME", "call-logs")

# Timezone for IST
IST_TIMEZONE = pytz.timezone('Asia/Kolkata')

# Initialize Azure client
logger.debug("Initializing Azure client...")
blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
container_client = blob_service_client.get_container_client(AZURE_LOGS_CONTAINER_NAME)

def fetch_call_logs(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> List[Dict[str, Any]]:
    """
    Fetch call logs from Azure Blob Storage.
    
    Args:
        start_date (Optional[datetime]): Start date for filtering logs (inclusive)
        end_date (Optional[datetime]): End date for filtering logs (inclusive)
        
    Returns:
        List[Dict[str, Any]]: List of call log data
    """
    try:
        # Ensure dates are timezone-aware
        if start_date and not start_date.tzinfo:
            start_date = start_date.replace(tzinfo=IST_TIMEZONE)
        if end_date and not end_date.tzinfo:
            end_date = end_date.replace(tzinfo=IST_TIMEZONE)
            
        # If end_date is provided, set it to end of day
        if end_date:
            end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
            
        logger.debug(f"Fetching call logs from {start_date} to {end_date}")
        
        # List all blobs in the container
        call_logs = []
        blob_list = container_client.list_blobs()
        
        for blob in blob_list:
            try:
                # Parse date from blob name (format: YYYY-MM-DD/HH_MM_SS_phone.json)
                path_parts = blob.name.split('/')
                if len(path_parts) != 2:
                    continue
                    
                date_str = path_parts[0]
                time_str = path_parts[1].split('_')[0:3]  # Get HH_MM_SS part
                time_str = '_'.join(time_str)
                
                # Create datetime object from blob name
                blob_datetime = datetime.strptime(
                    f"{date_str} {time_str}",
                    "%Y-%m-%d %H_%M_%S"
                ).replace(tzinfo=IST_TIMEZONE)
                
                # Filter by date range if specified
                if start_date and blob_datetime < start_date:
                    continue
                if end_date and blob_datetime > end_date:
                    continue
                
                # Download and parse the blob content
                blob_client = container_client.get_blob_client(blob.name)
                blob_data = blob_client.download_blob()
                log_data = json.loads(blob_data.readall())
                
                # Add blob name to the log data
                log_data['blob_name'] = blob.name
                
                call_logs.append(log_data)
                logger.debug(f"Successfully loaded call log: {blob.name}")
                
            except Exception as e:
                logger.error(f"Error processing blob {blob.name}: {e}")
                continue
        
        # Sort logs by timestamp
        call_logs.sort(
            key=lambda x: datetime.fromisoformat(x['call_timestamps']['start']),
            reverse=True  # Most recent first
        )
        
        logger.info(f"Successfully fetched {len(call_logs)} call logs")
        return call_logs
        
    except Exception as e:
        logger.error(f"Error fetching call logs: {e}")
        raise

# Example usage
if __name__ == "__main__":
    try:
        # Example: Fetch logs for the last 7 days
        from datetime import timedelta
        
        end_date = datetime.now(IST_TIMEZONE)
        start_date = end_date - timedelta(days=7)
        
        logs = fetch_call_logs(start_date, end_date)
        print(f"Found {len(logs)} call logs")
        
        # Print first log as example
        if logs:
            print("\nExample log:")
            print(json.dumps(logs, indent=2))
            
    except Exception as e:
        print(f"Error: {e}") 