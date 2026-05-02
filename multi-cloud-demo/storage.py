"""S3 to GCS synchronization simulation"""
from cloud_providers import MockS3, MockGCS
import time
from threading import Thread
from queue import Queue
from typing import Dict, Optional, Any

class CrossCloudStorage:
    """Manages S3 (AWS) and GCS (GCP) with bi-directional sync"""
    
    def __init__(self):
        self.s3 = MockS3()
        self.gcs = MockGCS()
        self.sync_queue = Queue()
        self.sync_enabled = True
        self.auto_sync = True
        
        # Start background sync worker if auto-sync enabled
        if self.auto_sync:
            self._start_sync_worker()
    
    def upload_to_s3(self, bucket: str, key: str, data: bytes, metadata: Dict = None):
        """Upload to S3 (AWS) with automatic sync to GCS"""
        etag = self.s3.put_object(bucket, key, data, metadata)
        
        if self.auto_sync:
            # Queue for async sync to GCS
            self.sync_queue.put({
                'type': 's3_to_gcs',
                'bucket': bucket,
                'key': key,
                'data': data,
                'metadata': metadata
            })
        
        return etag
    
    def upload_to_gcs(self, bucket: str, blob_name: str, data: bytes, metadata: Dict = None):
        """Upload to GCS (GCP) with automatic sync to S3"""
        self.gcs.upload_blob(bucket, blob_name, data, metadata)
        
        if self.auto_sync:
            # Queue for async sync to S3
            self.sync_queue.put({
                'type': 'gcs_to_s3',
                'bucket': bucket,
                'blob': blob_name,
                'data': data,
                'metadata': metadata
            })
        
        return True
    
    def get_from_s3(self, bucket: str, key: str) -> Optional[Dict]:
        """Get object from S3"""
        return self.s3.get_object(bucket, key)
    
    def get_from_gcs(self, bucket: str, blob_name: str) -> Optional[Dict]:
        """Get object from GCS"""
        return self.gcs.download_blob(bucket, blob_name)
    
    def sync_objects(self, from_s3: bool = True) -> bool:
        """Manually sync objects between clouds"""
        if from_s3:
            # Sync all S3 objects to GCS
            for bucket, objects in self.s3.buckets.items():
                for key, obj in objects.items():
                    self.gcs.upload_blob(bucket, key, obj['data'], obj['metadata'])
        else:
            # Sync all GCS objects to S3
            for bucket, blobs in self.gcs.buckets.items():
                for blob_name, blob in blobs.items():
                    self.s3.put_object(bucket, blob_name, blob['data'], blob['metadata'])
        
        return True
    
    def _start_sync_worker(self):
        """Background worker for automatic sync"""
        def worker():
            while self.sync_enabled:
                try:
                    task = self.sync_queue.get(timeout=1)
                    if task['type'] == 's3_to_gcs':
                        self.gcs.upload_blob(
                            task['bucket'], 
                            task['key'], 
                            task['data'], 
                            task['metadata']
                        )
                    elif task['type'] == 'gcs_to_s3':
                        self.s3.put_object(
                            task['bucket'],
                            task['blob'], 
                            task['data'], 
                            task['metadata']
                        )
                except:
                    pass
        
        Thread(target=worker, daemon=True).start()
    
    def get_stats(self) -> Dict:
        """Get storage statistics"""
        s3_count = sum(len(bucket) for bucket in self.s3.buckets.values())
        gcs_count = sum(len(bucket) for bucket in self.gcs.buckets.values())
        
        return {
            's3_objects': s3_count,
            'gcs_objects': gcs_count,
            'sync_queue_size': self.sync_queue.qsize(),
            'auto_sync_enabled': self.auto_sync,
            's3_buckets': list(self.s3.buckets.keys()),
            'gcs_buckets': list(self.gcs.buckets.keys())
        }