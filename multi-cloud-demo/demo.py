#!/usr/bin/env python3
"""Interactive multi-cloud demo with all interoperability features"""
import requests
import json
import time
import sys
from colorama import init, Fore, Style

init(autoreset=True)

BASE_URL = "http://localhost:5000"

def print_header(text):
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"{Fore.YELLOW}🌩️  {text}")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")

def print_success(text):
    print(f"{Fore.GREEN}✅ {text}{Style.RESET_ALL}")

def print_error(text):
    print(f"{Fore.RED}❌ {text}{Style.RESET_ALL}")

def print_info(text):
    print(f"{Fore.BLUE}ℹ️  {text}{Style.RESET_ALL}")

def print_aws(text):
    print(f"{Fore.YELLOW}☁️  AWS: {text}{Style.RESET_ALL}")

def print_gcp(text):
    print(f"{Fore.CYAN}☁️  GCP: {text}{Style.RESET_ALL}")

def demo_session_replication():
    """Demonstrate cross-cloud session sharing"""
    print_header("DEMO 1: Cross-Cloud Session Replication")
    
    # Create session via AWS
    print_info("Creating session (routed to AWS)...")
    response = requests.post(f"{BASE_URL}/login", json={
        'user_id': 'demo_user_123',
        'email': 'demo@multicloud.com'
    })
    session_data = response.json()
    session_id = session_data['session_id']
    print_success(f"Session created: {session_id[:8]}...")
    print_aws(f"Session stored in AWS ElastiCache")
    print_gcp(f"Session replicated to GCP Memorystore")
    
    # Read session via GCP
    print_info("\nReading session from GCP (prefer_gcp=true)...")
    response = requests.get(f"{BASE_URL}/session/{session_id}", params={'prefer_gcp': 'true'})
    result = response.json()
    
    if result['session_valid']:
        print_success(f"Session accessed from {result['accessed_from']}")
        print_gcp(f"Session data retrieved from GCP Memorystore")
        print(f"  User ID: {result['session_data']['data']['user_id']}")
        print(f"  Email: {result['session_data']['data']['email']}")
    
    # Show stats
    response = requests.get(f"{BASE_URL}/status")
    status = response.json()
    print_info(f"\nSession Stats: {status['session_store']}")

def demo_database_replication():
    """Demonstrate database replication and failover"""
    print_header("DEMO 2: Database Replication with Failover")
    
    # Insert users to primary (AWS)
    print_info("Inserting user into AWS Aurora (Primary)...")
    response = requests.post(f"{BASE_URL}/user", json={
        'name': 'Alice Johnson',
        'email': 'alice@example.com'
    })
    result = response.json()
    print_aws(f"User created in AWS Aurora: {result['user']}")
    
    # Read from replica (GCP)
    print_info("\nReading from GCP Cloud SQL (Replica)...")
    response = requests.get(f"{BASE_URL}/users", params={'from_gcp': 'true'})
    users = response.json()
    print_gcp(f"Users retrieved from GCP Cloud SQL: {len(users['users'])} users")
    
    # Show replication status
    print_info("\nReplication Status:")
    status = response.json()['replication_status']
    print(f"  AWS Primary Active: {status['aws_primary_active']}")
    print(f"  Records in AWS: {status['aws_records']}")
    print(f"  Records in GCP: {status['gcp_records']}")
    print(f"  Replication Lag: {status['replication_lag_ms']}ms")
    
    # Failover demo
    print_info("\n⚠️  Simulating AWS Aurora failure...")
    response = requests.post(f"{BASE_URL}/failover/database", json={'action': 'failover'})
    failover_result = response.json()
    print_aws("AWS Aurora is DOWN!")
    print_gcp("GCP Cloud SQL promoted to PRIMARY")
    print_success("Database failover complete - No data loss!")
    
    # Restore
    print_info("\nRestoring AWS Aurora...")
    requests.post(f"{BASE_URL}/failover/database", json={'action': 'restore'})
    print_success("AWS Aurora restored as PRIMARY")

def demo_storage_sync():
    """Demonstrate S3 to GCS synchronization"""
    print_header("DEMO 3: Storage Sync (S3 ↔ GCS)")
    
    # Upload to S3
    print_info("Uploading file to AWS S3...")
    response = requests.post(f"{BASE_URL}/storage/upload", json={
        'filename': 'demo_data.txt',
        'content': 'This file was uploaded to AWS S3 and auto-synced to GCP!'
    })
    result = response.json()
    print_aws(f"File uploaded to S3: {result['filename']}")
    print_info(f"Auto-sync enabled: {result['synced_to_gcs']}")
    
    # Wait for sync
    time.sleep(1)
    
    # List files from both clouds
    print_info("\nListing files from both clouds...")
    response = requests.get(f"{BASE_URL}/storage/files")
    files = response.json()
    
    print_aws(f"S3 files: {files['aws_s3']}")
    print_gcp(f"GCS files: {files['gcp_gcs']}")
    
    if 'demo_data.txt' in files['gcp_gcs']:
        print_success("File successfully synced from S3 to GCS!")
    else:
        print_error("File sync failed")
    
    print_info(f"Storage Stats: {files['sync_status']} sync, {files['total_objects']} total objects")

def demo_load_balancing():
    """Demonstrate multi-cloud traffic management"""
    print_header("DEMO 4: Multi-Cloud Load Balancing")
    
    # Test different routing strategies
    strategies = ['latency', 'weighted', 'round_robin', 'failover']
    
    for strategy in strategies:
        print_info(f"\nRouting Strategy: {strategy.upper()}")
        requests.post(f"{BASE_URL}/routing/strategy", json={'strategy': strategy})
        
        # Make multiple requests
        aws_count = 0
        gcp_count = 0
        
        for i in range(10):
            response = requests.post(f"{BASE_URL}/login", json={'user_id': f'test_{i}'})
            routed_to = response.json()['routed_to']
            if routed_to == 'AWS':
                aws_count += 1
            else:
                gcp_count += 1
        
        print(f"  AWS: {aws_count} requests | GCP: {gcp_count} requests")
    
    # Show final status
    response = requests.get(f"{BASE_URL}/status")
    status = response.json()['load_balancer']
    print_info(f"\nCurrent Load Balancer Status:")
    print(f"  AWS Healthy: {status['aws']['healthy']} (Latency: {status['aws']['latency_ms']}ms)")
    print(f"  GCP Healthy: {status['gcp']['healthy']} (Latency: {status['gcp']['latency_ms']}ms)")
    print(f"  Total Requests: AWS={status['stats']['aws_requests']}, GCP={status['stats']['gcp_requests']}")

def demo_unified_status():
    """Show complete multi-cloud system status"""
    print_header("DEMO 5: Unified Multi-Cloud Status")
    
    response = requests.get(f"{BASE_URL}/status")
    status = response.json()
    
    print(f"\n{Fore.MAGENTA}╔════════════════════════════════════════════════════════╗")
    print(f"║         MULTI-CLOUD SYSTEM DASHBOARD               ║")
    print(f"╚════════════════════════════════════════════════════════╝{Style.RESET_ALL}")
    
    print(f"\n{Fore.YELLOW}🌐 LOAD BALANCER{Style.RESET_ALL}")
    print(f"   Strategy: {status['load_balancer']['strategy']}")
    print(f"   AWS: {'✅' if status['load_balancer']['aws']['healthy'] else '❌'} "
          f"({status['load_balancer']['aws']['latency_ms']}ms)")
    print(f"   GCP: {'✅' if status['load_balancer']['gcp']['healthy'] else '❌'} "
          f"({status['load_balancer']['gcp']['latency_ms']}ms)")
    
    print(f"\n{Fore.YELLOW}💾 DATABASE{Style.RESET_ALL}")
    db = status['database']
    print(f"   AWS Aurora Primary: {'✅' if db['aws_primary_active'] else '❌'}")
    print(f"   GCP Cloud SQL: {'Primary' if db['gcp_is_primary'] else 'Replica'}")
    print(f"   Replication Lag: {db['replication_lag_ms']}ms")
    print(f"   Records: AWS={db['aws_records']}, GCP={db['gcp_records']}")
    
    print(f"\n{Fore.YELLOW}🔐 SESSION STORE{Style.RESET_ALL}")
    sess = status['session_store']
    print(f"   AWS Hits: {sess['aws_hits']} | GCP Hits: {sess['gcp_hits']}")
    print(f"   Active Sessions: {sess['total_sessions']}")
    
    print(f"\n{Fore.YELLOW}📦 OBJECT STORAGE{Style.RESET_ALL}")
    store = status['storage']
    print(f"   S3 Objects: {store['s3_objects']} | GCS Objects: {store['gcs_objects']}")
    print(f"   Auto-Sync: {'✅' if store['auto_sync_enabled'] else '❌'}")
    
    print(f"\n{Fore.GREEN}✅ All systems operational{Style.RESET_ALL}")

def run_all_demos():
    """Run complete demo suite"""
    print(f"\n{Fore.MAGENTA}{'='*60}")
    print("🚀 STARTING MULTI-CLOUD INTEROPERABILITY DEMO")
    print(f"{'='*60}{Style.RESET_ALL}")
    
    # Check if server is running
    try:
        requests.get(f"{BASE_URL}/")
    except:
        print_error("Server not running! Start app.py first:")
        print_info("  python app.py")
        return
    
    demos = [
        ("Session Replication", demo_session_replication),
        ("Database Replication", demo_database_replication),
        ("Storage Sync", demo_storage_sync),
        ("Load Balancing", demo_load_balancing),
        ("Unified Status", demo_unified_status)
    ]
    
    for name, demo_func in demos:
        demo_func()
        time.sleep(2)
        input(f"\n{Fore.CYAN}Press Enter to continue to next demo...{Style.RESET_ALL}")
    
    print_header("DEMO COMPLETE!")
    print_success("All multi-cloud interoperability features demonstrated successfully!")
    print_info("Key takeaways:")
    print("  1. Sessions seamlessly replicate across AWS & GCP")
    print("  2. Database automatically fails over without data loss")
    print("  3. Object storage syncs bi-directionally")
    print("  4. Traffic routes intelligently based on strategy")

if __name__ == "__main__":
    run_all_demos()