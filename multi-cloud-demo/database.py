"""Cross-cloud database replication simulation"""
from cloud_providers import MockAurora, MockCloudSQL
import time

class CrossCloudDatabase:
    """Manages AWS Aurora (primary) and GCP Cloud SQL (replica)"""
    
    def __init__(self):
        self.aws_aurora = MockAurora()
        self.gcp_cloudsql = MockCloudSQL()
        
        # Setup replication (AWS -> GCP)
        self.aws_aurora.add_replica(self.gcp_cloudsql)
        
        self.failover_active = False
        self.replication_lag_ms = 100  # 100ms typical lag
    
    def insert_user(self, name: str, email: str) -> dict:
        """Insert user into primary database (AWS)"""
        user = {
            'name': name,
            'email': email,
            'created_at': time.time()
        }
        result = self.aws_aurora.execute("INSERT INTO users", user)
        return result
    
    def get_users(self, from_replica: bool = False) -> list:
        """Read users from either database"""
        if from_replica or self.failover_active:
            # Read from GCP (replica or after failover)
            return self.gcp_cloudsql.execute("SELECT * FROM users")
        else:
            # Read from AWS (primary)
            return self.aws_aurora.execute("SELECT * FROM users")
    
    def failover_to_gcp(self):
        """Simulate failover from AWS Aurora to GCP Cloud SQL"""
        print("⚠️  FAILOVER: AWS Aurora primary is DOWN")
        print("🔄 Promoting GCP Cloud SQL to primary...")
        time.sleep(1)
        
        # Promote replica
        self.gcp_cloudsql.is_primary = True
        self.failover_active = True
        
        # Transfer any pending writes
        pending_writes = self._get_pending_writes()
        for write in pending_writes:
            self.gcp_cloudsql.execute(write['query'], write['params'])
        
        print("✅ GCP Cloud SQL is now PRIMARY")
        return True
    
    def restore_aws(self):
        """Restore AWS as primary after failover"""
        print("🔄 Restoring AWS Aurora as primary...")
        self.aws_aurora.is_primary = True
        self.failover_active = False
        self.aws_aurora.add_replica(self.gcp_cloudsql)
        print("✅ AWS Aurora restored as PRIMARY")
        return True
    
    def _get_pending_writes(self) -> list:
        """Get writes that haven't been replicated"""
        return self.aws_aurora.transactions[-5:] if self.aws_aurora.transactions else []
    
    def get_replication_status(self) -> dict:
        """Get database replication status"""
        return {
            'aws_primary_active': self.aws_aurora.is_primary and not self.failover_active,
            'gcp_replica_active': not self.failover_active,
            'gcp_is_primary': self.gcp_cloudsql.is_primary,
            'replication_lag_ms': self.replication_lag_ms,
            'aws_records': sum(len(table) for table in self.aws_aurora.data.values()),
            'gcp_records': sum(len(table) for table in self.gcp_cloudsql.data.values()),
            'failover_mode': self.failover_active
        }