from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import blueprints
from api.layer1 import layer1_bp
from api.layer2 import layer2_bp
from api.rag_functions import rag_bp
from api.training import training_bp

def create_app():
    app = Flask(__name__)
    
    # Enhanced CORS configuration for external access
    CORS(app, 
         origins='*',  # Allow all origins
         methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
         allow_headers=['Content-Type', 'Authorization', 'X-Requested-With'],
         expose_headers=['Content-Range', 'X-Content-Range'],
         supports_credentials=True
    )
    
    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
    app.config['QDRANT_HOST'] = os.getenv('QDRANT_HOST', 'localhost')
    app.config['QDRANT_PORT'] = os.getenv('QDRANT_PORT', 6333)
    
    # Register blueprints
    app.register_blueprint(layer1_bp, url_prefix='/api/layer1')
    app.register_blueprint(layer2_bp, url_prefix='/api/layer2')
    app.register_blueprint(rag_bp, url_prefix='/api/rag')
    app.register_blueprint(training_bp, url_prefix='/api/training')
    
    # Add headers for external access
    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-Requested-With')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        response.headers.add('X-Frame-Options', 'SAMEORIGIN')
        response.headers.add('X-Content-Type-Options', 'nosniff')
        return response
    
    @app.route('/health', methods=['GET'])
    def health_check():
        return jsonify({'status': 'healthy', 'service': 'spam-detection-api'})
    
    @app.route('/network-info', methods=['GET'])
    def network_info():
        """Get network information for external access"""
        import socket
        hostname = socket.gethostname()
        try:
            local_ip = socket.gethostbyname(hostname)
        except:
            local_ip = "Unable to determine"
        
        return jsonify({
            'service': 'Spam Detection Functions Server',
            'external_access': True,
            'hostname': hostname,
            'local_ip': local_ip,
            'port': 5000,
            'cors_enabled': True,
            'access_urls': {
                'local': 'http://localhost:5000',
                'network': f'http://{local_ip}:5000' if local_ip != "Unable to determine" else 'http://[YOUR_IP]:5000',
                'external': 'http://[YOUR_PUBLIC_IP]:5000'
            },
            'note': 'Server is configured to accept connections from any IP address'
        })
    
    @app.route('/', methods=['GET'])
    def index():
        return jsonify({
            'service': 'Spam Detection Functions Server',
            'version': '1.0.0',
            'endpoints': {
                'layer1': '/api/layer1/check_spam',
                'layer2': '/api/layer2/ml_check_spam',
                'rag': {
                    'health': '/api/rag/health',
                    'get_user_info': '/api/rag/get_user_information',
                    'get_call_history': '/api/rag/get_call_history',
                    'post_suspect_info': '/api/rag/post_suspect_information',
                    'add_user_docs': '/api/rag/add_user_documents',
                    'search_all': '/api/rag/search_all'
                },
                'training': {
                    'retrain_model': '/api/training/retrain_model',
                    'add_samples': '/api/training/add_training_samples',
                    'download_sample': '/api/training/download_sample_csv',
                    'history': '/api/training/training_history',
                    'health': '/api/training/health'
                }
            }
        })
    
    return app

if __name__ == '__main__':
    app = create_app()
    
    # Display network information
    import socket
    hostname = socket.gethostname()
    try:
        local_ip = socket.gethostbyname(hostname)
        print(f"\n🌐 EXTERNAL ACCESS ENABLED 🌐")
        print(f"Server is accessible from external networks!")
        print(f"")
        print(f"📍 Access URLs:")
        print(f"   Local:    http://localhost:5000")
        print(f"   Network:  http://{local_ip}:5000")
        print(f"   External: http://[YOUR_PUBLIC_IP]:5000")
        print(f"")
        print(f"🔓 CORS enabled for all origins")
        print(f"🔗 Ready for external API calls")
        print(f"=" * 50)
    except:
        print(f"\n🌐 EXTERNAL ACCESS ENABLED 🌐")
        print(f"Server configured for external access on port 5000")
        print(f"=" * 50)
    
    app.run(host='0.0.0.0', port=5000, debug=True)