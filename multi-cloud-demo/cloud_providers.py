"""Simulates AWS and GCP services for multi-cloud demo"""
import json
import threading
import time
from datetime import datetime
from typing import Dict, Any, Optional
from collections import defaultdict
import hashlib

class MockS3:
    """Simulates AWS S3 storage"""
    def __init__(self):
        self.buckets = defaultdict(dict)
        self.events = []
    
    def put_object(self, bucket: str, key: str, data: bytes, metadata: Dict = None):
        self.buckets[bucket][key] = {
            'data': data,
            'metadata': metadata or {},
            'last_modified': datetime.now().isoformat(),
            'etag': hashlib.md5(data).hexdigest()
        }
        self.events.append({
            'type': 'S3:PUT',
            'bucket': bucket,
            'key': key,
            'timestamp': datetime.now().isoformat(),
            'size': len(data)
        })
        return self.buckets[bucket][key]['etag']
    
    def get_object(self, bucket: str, key: str) -> Optional[Dict]:
        return self.buckets.get(bucket, {}).get(key)
    
    def list_objects(self, bucket: str) -> list:
        return list(self.buckets.get(bucket, {}).keys())

class MockGCS:
    """Simulates Google Cloud Storage"""
    def __init__(self):
        self.buckets = defaultdict(dict)
        self.events = []
    
    def upload_blob(self, bucket: str, blob_name: str, data: bytes, metadata: Dict = None):
        self.buckets[bucket][blob_name] = {
            'data': data,
            'metadata': metadata or {},
            'uploaded': datetime.now().isoformat(),
            'size': len(data)
        }
        self.events.append({
            'type': 'GCS:UPLOAD',
            'bucket': bucket,
            'blob': blob_name,
            'timestamp': datetime.now().isoformat()
        })
    
    def download_blob(self, bucket: str, blob_name: str) -> Optional[Dict]:
        return self.buckets.get(bucket, {}).get(blob_name)

class MockElastiCache:
    """Simulates AWS ElastiCache (Redis)"""
    def __init__(self, region: str = 'us-east-1'):
        self.region = region
        self.data = {}
        self.replication_role = 'primary'
        self.replicas = []
    
    def set(self, key: str, value: Any, ttl: int = None):
        self.data[key] = {
            'value': value,
            'timestamp': time.time(),
            'ttl': ttl
        }
        # Simulate replication to GCP
        if self.replicas:
            for replica in self.replicas:
                replica.replicate(key, value)
        return True
    
    def get(self, key: str) -> Optional[Any]:
        item = self.data.get(key)
        if item:
            if item.get('ttl') and time.time() - item['timestamp'] > item['ttl']:
                del self.data[key]
                return None
            return item['value']
        return None
    
    def add_replica(self, replica):
        self.replicas.append(replica)
    
    def replicate(self, key: str, value: Any):
        self.data[key] = {
            'value': value,
            'timestamp': time.time(),
            'replicated_from': self.region
        }

class MockMemorystore:
    """Simulates GCP Memorystore (Redis)"""
    def __init__(self, region: str = 'us-central1'):
        self.region = region
        self.data = {}
        self.replication_role = 'replica'
        self.master = None
    
    def set(self, key: str, value: Any):
        self.data[key] = {
            'value': value,
            'timestamp': time.time(),
            'region': self.region
        }
        return True
    
    def get(self, key: str) -> Optional[Any]:
        item = self.data.get(key)
        return item['value'] if item else None
    
    def replicate(self, key: str, value: Any):
        self.data[key] = {
            'value': value,
            'timestamp': time.time(),
            'replicated_from': 'aws-primary',
            'region': self.region
        }

class MockAurora:
    """Simulates AWS Aurora MySQL"""
    def __init__(self):
        self.data = {}
        self.transactions = []
        self.binlog = []
        self.is_primary = True
        self.replicas = []
    
    def execute(self, query: str, params: Dict = None):
        if query.upper().startswith('INSERT'):
            table = query.split()[2]
            if table not in self.data:
                self.data[table] = []
            record = {'id': len(self.data[table]) + 1, **(params or {})}
            self.data[table].append(record)
            self.transactions.append({'query': query, 'result': record, 'time': time.time()})
            # Replicate to GCP
            for replica in self.replicas:
                replica.replicate(table, record)
            return record
        elif query.upper().startswith('SELECT'):
            table = query.split()[3].split('=')[0] if '=' in query else query.split()[3]
            return self.data.get(table, [])
        return None
    
    def add_replica(self, replica):
        self.replicas.append(replica)

class MockCloudSQL:
    """Simulates GCP Cloud SQL (MySQL replica)"""
    def __init__(self):
        self.data = {}
        self.replication_lag = 0
        self.is_primary = False
    
    def execute(self, query: str, params: Dict = None):
        if query.upper().startswith('SELECT'):
            table = query.split()[3].split('=')[0] if '=' in query else query.split()[3]
            return self.data.get(table, [])
        return None
    
    def replicate(self, table: str, record: Dict):
        # Simulate replication lag
        time.sleep(0.1)
        if table not in self.data:
            self.data[table] = []
        self.data[table].append(record)