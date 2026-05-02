"""Multi-cloud load balancer simulation"""
import random
import time
from typing import Dict, Any, Optional
from enum import Enum

class RoutingStrategy(Enum):
    LATENCY_BASED = "latency"
    ROUND_ROBIN = "round_robin"
    WEIGHTED = "weighted"
    FAILOVER = "failover"

class MultiCloudLoadBalancer:
    """Route traffic between AWS and GCP with health checks"""
    
    def __init__(self):
        self.aws_healthy = True
        self.gcp_healthy = True
        self.aws_latency_ms = 50  # 50ms to AWS
        self.gcp_latency_ms = 75  # 75ms to GCP
        self.strategy = RoutingStrategy.LATENCY_BASED
        self.aws_weight = 70  # 70% traffic to AWS
        self.gcp_weight = 30  # 30% to GCP
        self.round_robin_counter = 0
        
        self.stats = {
            'aws_requests': 0,
            'gcp_requests': 0,
            'failed_requests': 0
        }
    
    def route_request(self, request: Dict) -> str:
        """Determine which cloud should handle the request"""
        
        # Health check first
        if not self.aws_healthy and self.gcp_healthy:
            destination = 'GCP'
        elif not self.gcp_healthy and self.aws_healthy:
            destination = 'AWS'
        elif not self.aws_healthy and not self.gcp_healthy:
            destination = 'NONE'
        else:
            # Both healthy - apply routing strategy
            destination = self._apply_strategy()
        
        # Update stats
        if destination == 'AWS':
            self.stats['aws_requests'] += 1
        elif destination == 'GCP':
            self.stats['gcp_requests'] += 1
        else:
            self.stats['failed_requests'] += 1
        
        return destination
    
    def _apply_strategy(self) -> str:
        """Apply configured routing strategy"""
        
        if self.strategy == RoutingStrategy.LATENCY_BASED:
            # Route to lower latency cloud
            return 'AWS' if self.aws_latency_ms <= self.gcp_latency_ms else 'GCP'
        
        elif self.strategy == RoutingStrategy.ROUND_ROBIN:
            self.round_robin_counter += 1
            return 'AWS' if self.round_robin_counter % 2 == 0 else 'GCP'
        
        elif self.strategy == RoutingStrategy.WEIGHTED:
            # Weighted routing based on configured percentages
            r = random.randint(1, 100)
            return 'AWS' if r <= self.aws_weight else 'GCP'
        
        elif self.strategy == RoutingStrategy.FAILOVER:
            # Primary is AWS, failover to GCP only if AWS unhealthy
            return 'AWS' if self.aws_healthy else 'GCP'
        
        return 'AWS'  # Default
    
    def set_strategy(self, strategy: RoutingStrategy):
        self.strategy = strategy
    
    def set_weights(self, aws_weight: int, gcp_weight: int):
        self.aws_weight = aws_weight
        self.gcp_weight = gcp_weight
    
    def set_latency(self, aws_ms: int, gcp_ms: int):
        self.aws_latency_ms = aws_ms
        self.gcp_latency_ms = gcp_ms
    
    def health_check(self):
        """Perform health checks on both clouds"""
        # Simulate health check
        self.aws_healthy = random.random() > 0.1  # 90% healthy
        self.gcp_healthy = random.random() > 0.1
    
    def set_cloud_health(self, aws_healthy: bool, gcp_healthy: bool):
        self.aws_healthy = aws_healthy
        self.gcp_healthy = gcp_healthy
    
    def get_status(self) -> Dict:
        return {
            'aws': {'healthy': self.aws_healthy, 'latency_ms': self.aws_latency_ms},
            'gcp': {'healthy': self.gcp_healthy, 'latency_ms': self.gcp_latency_ms},
            'strategy': self.strategy.value,
            'stats': self.stats
        }