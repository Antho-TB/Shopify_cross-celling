import json
import os
from azure.storage.blob import BlobServiceClient
from datetime import datetime

class ReportManager:
    def __init__(self, connection_string=None, container_name="reports"):
        self.connection_string = connection_string or os.environ.get("AzureWebJobsStorage")
        self.container_name = container_name
        self.blob_service_client = None
        
        if self.connection_string and self.connection_string != "UseDevelopmentStorage=true":
            self.blob_service_client = BlobServiceClient.from_connection_string(self.connection_string)
            self._ensure_container_exists()

    def _ensure_container_exists(self):
        try:
            container_client = self.blob_service_client.get_container_client(self.container_name)
            if not container_client.exists():
                container_client.create_container()
        except Exception:
            pass

    def save_report(self, report_data):
        """Saves a report to the storage account."""
        if not self.blob_service_client:
            return False
            
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        blob_name = f"report_{timestamp}.json"
        
        container_client = self.blob_service_client.get_container_client(self.container_name)
        blob_client = container_client.get_blob_client(blob_name)
        
        blob_client.upload_blob(json.dumps(report_data, indent=2), overwrite=True)
        return True

    def get_latest_reports(self, limit=5):
        """Retrieves the most recent reports."""
        if not self.blob_service_client:
            return []
            
        container_client = self.blob_service_client.get_container_client(self.container_name)
        blobs = list(container_client.list_blobs())
        # Sort by timestamp in name (descending)
        blobs.sort(key=lambda x: x.name, reverse=True)
        
        latest_reports = []
        for blob in blobs[:limit]:
            blob_client = container_client.get_blob_client(blob.name)
            content = blob_client.download_blob().readall()
            latest_reports.append(json.loads(content))
            
        return latest_reports
