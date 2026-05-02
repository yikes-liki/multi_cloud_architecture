"""Multi-cloud demo application with Flask"""
from flask import Flask, request, jsonify
from session_store import CrossCloudSessionStore
from database import CrossCloudDatabase
from storage import CrossCloudStorage
from load_balancer import MultiCloudLoadBalancer, RoutingStrategy
import time

app = Flask(__name__)
app.secret_key = 'multi-cloud-demo-secret-key'

# Initialize multi-cloud components
session_store = CrossCloudSessionStore()
database = CrossCloudDatabase()
storage = CrossCloudStorage()
load_balancer = MultiCloudLoadBalancer()

@app.route('/')
def index():
    return jsonify({
        'service': 'Multi-Cloud Application',
        'status': 'running',
        'clouds': ['AWS (us-east-1)', 'GCP (us-central1)'],
        'features': [
            'Cross-cloud session sharing',
            'Database replication',
            'Object storage sync',
            'Traffic management'
        ]
    })

@app.route('/login', methods=['POST'])
def login():
    """Create session across both clouds"""
    data = request.get_json()
    
    # Route request based on load balancer
    destination = load_balancer.route_request({'action': 'login'})
    
    # Create session (replicates to both clouds)
    session_id = session_store.create_session({
        'user_id': data.get('user_id', 'anonymous'),
        'email': data.get('email', ''),
        'routed_to': destination
    })
    
    return jsonify({
        'session_id': session_id,
        'routed_to': destination,
        'message': f'Session created and replicated across AWS & GCP'
    })

@app.route('/session/<session_id>')
def get_session(session_id):
    """Get session from either cloud"""
    prefer_gcp = request.args.get('prefer_gcp', 'false').lower() == 'true'
    
    # Try different clouds based on preference
    session_data = session_store.get_session(session_id, prefer_gcp=prefer_gcp)
    
    if session_data:
        # Route the read request
        destination = load_balancer.route_request({'action': 'read_session'})
        
        return jsonify({
            'session_valid': True,
            'session_data': session_data,
            'accessed_from': destination,
            'cloud_stats': session_store.get_stats()
        })
    
    return jsonify({'session_valid': False, 'error': 'Session not found'}), 404

@app.route('/user', methods=['POST'])
def create_user():
    """Create user in cross-cloud database"""
    data = request.get_json()
    
    # Always write to primary (AWS)
    result = database.insert_user(
        name=data.get('name'),
        email=data.get('email')
    )
    
    # Route the request for response
    destination = load_balancer.route_request({'action': 'create_user'})
    
    return jsonify({
        'user': result,
        'written_to': 'AWS Aurora (Primary)',
        'replicating_to': 'GCP Cloud SQL',
        'routed_via': destination
    })

@app.route('/users')
def get_users():
    """Get users from either database"""
    from_replica = request.args.get('from_gcp', 'false').lower() == 'true'
    
    # Read from GCP replica if requested
    users = database.get_users(from_replica=from_replica)
    destination = load_balancer.route_request({'action': 'read_users'})
    
    return jsonify({
        'users': users,
        'source': 'GCP Cloud SQL' if from_replica else 'AWS Aurora',
        'routed_via': destination,
        'replication_status': database.get_replication_status()
    })

@app.route('/storage/upload', methods=['POST'])
def upload_file():
    """Upload file to cross-cloud storage"""
    data = request.get_json()
    content = data.get('content', '').encode()
    filename = data.get('filename', f"file_{int(time.time())}.txt")
    
    # Upload to S3 (auto-syncs to GCS)
    etag = storage.upload_to_s3('multi-cloud-demo', filename, content, {
        'uploaded_by': request.remote_addr,
        'timestamp': time.time()
    })
    
    destination = load_balancer.route_request({'action': 'upload'})
    
    return jsonify({
        'filename': filename,
        's3_etag': etag,
        'synced_to_gcs': storage.auto_sync,
        'routed_via': destination,
        'storage_stats': storage.get_stats()
    })

@app.route('/storage/files')
def list_files():
    """List files from both clouds"""
    # Get actual file lists
    s3_keys = list(storage.s3.buckets.get('multi-cloud-demo', {}).keys())
    gcs_blobs = list(storage.gcs.buckets.get('multi-cloud-demo', {}).keys())
    
    return jsonify({
        'aws_s3': s3_keys,
        'gcp_gcs': gcs_blobs,
        'sync_status': 'active' if storage.auto_sync else 'disabled',
        'total_objects': len(s3_keys) + len(gcs_blobs)
    })

@app.route('/failover/database', methods=['POST'])
def failover_database():
    """Trigger database failover from AWS to GCP"""
    action = request.json.get('action', 'failover')
    
    if action == 'failover':
        result = database.failover_to_gcp()
    elif action == 'restore':
        result = database.restore_aws()
    else:
        result = False
    
    return jsonify({
        'failover_executed': result,
        'status': database.get_replication_status()
    })

@app.route('/routing/strategy', methods=['POST'])
def set_routing_strategy():
    """Change load balancer routing strategy"""
    strategy_name = request.json.get('strategy', 'latency')
    
    strategy_map = {
        'latency': RoutingStrategy.LATENCY_BASED,
        'round_robin': RoutingStrategy.ROUND_ROBIN,
        'weighted': RoutingStrategy.WEIGHTED,
        'failover': RoutingStrategy.FAILOVER
    }
    
    if strategy_name in strategy_map:
        load_balancer.set_strategy(strategy_map[strategy_name])
        return jsonify({
            'strategy': strategy_name,
            'status': load_balancer.get_status()
        })
    
    return jsonify({'error': 'Invalid strategy'}), 400

@app.route('/status')
def status():
    """Get complete multi-cloud system status"""
    return jsonify({
        'load_balancer': load_balancer.get_status(),
        'session_store': session_store.get_stats(),
        'database': database.get_replication_status(),
        'storage': storage.get_stats(),
        'timestamp': time.time()
    })

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🌩️  MULTI-CLOUD DEMO APPLICATION")
    print("="*60)
    print("AWS (us-east-1) <---> GCP (us-central1)")
    print("-"*60)
    print("Features Enabled:")
    print("  ✅ Cross-cloud session replication (Active-Active)")
    print("  ✅ Database replication AWS Aurora → GCP Cloud SQL")
    print("  ✅ Object storage sync S3 ↔ GCS")
    print("  ✅ Intelligent multi-cloud load balancing")
    print("="*60)
    print("\n🚀 Starting server on http://localhost:5000\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)