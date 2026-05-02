"""Cross-cloud session store with active-active replication"""
import uuid
import time
from typing import Dict, Optional
from cloud_providers import MockElastiCache, MockMemorystore

class CrossCloudSessionStore:
    """Manages sessions across AWS ElastiCache and GCP Memorystore"""
    
    def __init__(self):
        # Initialize primary (AWS) and replica (GCP)
        self.aws_redis = MockElastiCache(region='us-east-1')
        self.gcp_redis = MockMemorystore(region='us-central1')
        
        # Configure replication (active-active)
        self.aws_redis.add_replica(self.gcp_redis)
        
        self.stats = {
            'aws_hits': 0,
            'gcp_hits': 0,
            'replications': 0
        }
    
    def create_session(self, user_data: Dict) -> str:
        """Create new session (always write to primary)"""
        session_id = str(uuid.uuid4())
        session_data = {
            'user_id': user_data.get('user_id'),
            'email': user_data.get('email'),
            'created_at': time.time(),
            'last_accessed': time.time(),
            'data': user_data
        }
        self.aws_redis.set(f"session:{session_id}", session_data, ttl=3600)
        return session_id
    
    def get_session(self, session_id: str, prefer_gcp: bool = False) -> Optional[Dict]:
        """Get session from either cloud (active-active)"""
        key = f"session:{session_id}"
        
        if prefer_gcp:
            # Try GCP first
            data = self.gcp_redis.get(key)
            if data:
                self.stats['gcp_hits'] += 1
                return data
            # Fallback to AWS
            data = self.aws_redis.get(key)
            if data:
                self.stats['aws_hits'] += 1
            return data
        else:
            # Try AWS first (primary)
            data = self.aws_redis.get(key)
            if data:
                self.stats['aws_hits'] += 1
                return data
            # Fallback to GCP
            data = self.gcp_redis.get(key)
            if data:
                self.stats['gcp_hits'] += 1
            return data
    
    def update_session(self, session_id: str, updates: Dict) -> bool:
        """Update session (write to both clouds)"""
        key = f"session:{session_id}"
        
        # Read from primary
        session_data = self.aws_redis.get(key)
        if not session_data:
            return False
        
        # Update
        session_data['data'].update(updates)
        session_data['last_accessed'] = time.time()
        
        # Write to both (active-active)
        self.aws_redis.set(key, session_data)
        self.gcp_redis.set(key, session_data)
        self.stats['replications'] += 1
        
        return True
    
    def delete_session(self, session_id: str) -> bool:
        """Delete session from both clouds"""
        key = f"session:{session_id}"
        
        if key in self.aws_redis.data:
            del self.aws_redis.data[key]
        if key in self.gcp_redis.data:
            del self.gcp_redis.data[key]
        
        return True
    
    def get_stats(self) -> Dict:
        """Get session store statistics"""
        return {
            **self.stats,
            'aws_session_count': len([k for k in self.aws_redis.data.keys() if k.startswith('session:')]),
            'gcp_session_count': len([k for k in self.gcp_redis.data.keys() if k.startswith('session:')]),
            'total_sessions': len(set(list(self.aws_redis.data.keys()) + list(self.gcp_redis.data.keys())))
        }