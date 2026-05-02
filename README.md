# multi_cloud_architecture

COMPANY : CODTECH IT SOLUTION

NAME : LIKHITHA

INTERN ID : CTIS8012

DOMAIN : CLOUD COMPUTING

MENTOR : NEELA SANTHOSH KUMAR

Overview: A production-grade simulation platform demonstrating seamless integration between AWS and GCP, implementing four critical cross-cloud patterns without incurring real cloud costs.

Key Features Demonstrated:
Active-Active Session Replication – User sessions automatically sync between AWS ElastiCache and GCP Memorystore, allowing seamless failover between clouds

Database Replication with Auto-Failover – AWS Aurora MySQL (primary) replicates to GCP Cloud SQL (replica); simulated failure triggers automatic promotion with zero data loss

Bi-Directional Object Storage Sync – Files uploaded to S3 automatically sync to GCS via queue-based background workers, and vice versa

Intelligent Multi-Cloud Load Balancing – Supports 4 routing strategies: latency-based, weighted (70/30), round-robin, and failover patterns

Unified Observability Dashboard – Single API endpoint provides real-time status across both cloud providers including replication lag, session counts, and request distribution

Technical Implementation:
RESTful API built with Flask, mock cloud service implementations, and colored console output distinguishing AWS (yellow) from GCP (cyan)

Interactive demo runner that sequentially tests all interoperability features with automated validation

Cloud-agnostic design pattern that can be extended to support Azure, making it a reference architecture for vendor-agnostic deployments

Business Value:
Enables disaster recovery across cloud providers (RTO < 2 min, RPO < 10 sec simulated)

Prevents vendor lock-in through portable application logic and cloud abstraction layers

Provides cost-free learning environment for multi-cloud architecture patterns

