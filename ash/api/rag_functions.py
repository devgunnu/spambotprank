from flask import Blueprint, request, jsonify
import json
import os
import time
from typing import List, Dict, Any
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

rag_bp = Blueprint('rag', __name__)

# Configuration
RAG_DATA_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'rag_storage.json')

# In-memory storage for RAG documents
class LocalRAGStorage:
    def __init__(self):
        self.documents = []
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        self.document_vectors = None
        self.load_data()
        
    def load_data(self):
        """Load existing data from file"""
        try:
            if os.path.exists(RAG_DATA_FILE):
                with open(RAG_DATA_FILE, 'r') as f:
                    data = json.load(f)
                    self.documents = data.get('documents', [])
                    if self.documents:
                        self._update_vectors()
        except Exception as e:
            print(f"Warning: Could not load RAG data: {e}")
            self.documents = []
    
    def save_data(self):
        """Save data to file"""
        try:
            os.makedirs(os.path.dirname(RAG_DATA_FILE), exist_ok=True)
            with open(RAG_DATA_FILE, 'w') as f:
                json.dump({'documents': self.documents}, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save RAG data: {e}")
    
    def _update_vectors(self):
        """Update document vectors for similarity search"""
        if self.documents:
            texts = [doc['content'] for doc in self.documents]
            self.document_vectors = self.vectorizer.fit_transform(texts)
    
    def add_document(self, title: str, content: str, category: str = 'general', metadata: Dict = None):
        """Add a document to the storage"""
        doc = {
            'id': len(self.documents),
            'title': title,
            'content': content,
            'category': category,
            'metadata': metadata or {},
            'timestamp': time.time()
        }
        self.documents.append(doc)
        self._update_vectors()
        self.save_data()
        return doc['id']
    
    def search(self, query: str, top_k: int = 5, category: str = None):
        """Search for similar documents"""
        if not self.documents:
            return []
        
        # Filter by category if specified
        filtered_docs = self.documents
        if category:
            filtered_docs = [doc for doc in self.documents if doc.get('category') == category]
        
        if not filtered_docs:
            return []
        
        # Vectorize query
        query_vector = self.vectorizer.transform([query])
        
        # Calculate similarities
        if len(filtered_docs) == len(self.documents):
            similarities = cosine_similarity(query_vector, self.document_vectors)[0]
        else:
            # Re-vectorize filtered docs
            filtered_texts = [doc['content'] for doc in filtered_docs]
            filtered_vectors = self.vectorizer.transform(filtered_texts)
            similarities = cosine_similarity(query_vector, filtered_vectors)[0]
        
        # Get top results
        top_indices = np.argsort(similarities)[::-1][:top_k]
        results = []
        
        for idx in top_indices:
            if similarities[idx] > 0:  # Only return if there's some similarity
                doc = filtered_docs[idx]
                results.append({
                    'id': doc['id'],
                    'title': doc['title'],
                    'content': doc['content'],
                    'category': doc['category'],
                    'metadata': doc['metadata'],
                    'similarity_score': float(similarities[idx])
                })
        
        return results

# Global storage instance
rag_storage = LocalRAGStorage()

def make_rag_request(endpoint: str, method: str = 'GET', data: Dict = None) -> Dict:
    """Local RAG operations - no external server needed"""
    try:
        # This is now handled locally, not via HTTP requests
        return {'status': 'local_rag_active'}
    except Exception as e:
        return {'error': f'Local RAG error: {str(e)}'}

@rag_bp.route('/get_user_information', methods=['POST'])
def get_user_information():
    """
    Get user information from RAG database
    
    Expected JSON payload:
    {
        "query": "search query about user",
        "top_k": 5
    }
    
    Returns:
    {
        "results": [...],
        "query": "search query",
        "count": 3
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        query = data.get('query', '')
        top_k = data.get('top_k', 5)
        
        if not query:
            return jsonify({'error': 'Query is required'}), 400
        
        # Search in local storage for user information
        results = rag_storage.search(query, top_k=top_k, category='user_information')
        
        return jsonify({
            'success': True,
            'results': results,
            'query': query,
            'count': len(results),
            'category': 'user_information'
        })
        
    except Exception as e:
        return jsonify({'error': f'Get user information failed: {str(e)}'}), 500

@rag_bp.route('/get_call_history', methods=['POST'])
def get_call_history():
    """
    Get call history from RAG database
    
    Expected JSON payload:
    {
        "query": "search query about calls",
        "top_k": 10
    }
    
    Returns:
    {
        "results": [...],
        "query": "search query",
        "count": 5
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        query = data.get('query', '')
        top_k = data.get('top_k', 10)
        
        if not query:
            return jsonify({'error': 'Query is required'}), 400
        
        # Search in local storage for call history
        results = rag_storage.search(query, top_k=top_k, category='call_history')
        
        return jsonify({
            'success': True,
            'results': results,
            'query': query,
            'count': len(results),
            'category': 'call_history'
        })
        
    except Exception as e:
        return jsonify({'error': f'Get call history failed: {str(e)}'}), 500

@rag_bp.route('/post_suspect_information', methods=['POST'])
def post_suspect_information():
    """
    Add suspect information to RAG database
    
    Expected JSON payload:
    {
        "documents": ["suspect info 1", "suspect info 2", ...],
        "metadata": {
            "phone_number": "+1234567890",
            "timestamp": "2024-01-01T12:00:00Z",
            "source": "agent_report"
        }
    }
    
    Returns:
    {
        "success": true,
        "message": "Added N documents"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        documents = data.get('documents', [])
        metadata = data.get('metadata', {})
        
        if not documents:
            return jsonify({'error': 'Documents are required'}), 400
        
        if not isinstance(documents, list):
            return jsonify({'error': 'Documents must be a list'}), 400
        
        # Add documents to local storage
        added_count = 0
        for i, doc in enumerate(documents):
            title = f"Suspect Info {i+1}"
            if metadata.get('phone_number'):
                title += f" - {metadata['phone_number']}"
            
            rag_storage.add_document(
                title=title,
                content=doc,
                category='suspects',
                metadata=metadata
            )
            added_count += 1
        
        return jsonify({
            'success': True,
            'message': f'Added {added_count} suspect documents',
            'category': 'suspects',
            'count': added_count
        })
        
    except Exception as e:
        return jsonify({'error': f'Post suspect information failed: {str(e)}'}), 500

@rag_bp.route('/add_user_documents', methods=['POST'])
def add_user_documents():
    """
    Add user information documents to RAG database
    
    Expected JSON payload:
    {
        "documents": ["user info 1", "user info 2", ...],
        "metadata": {
            "user_id": "user123",
            "source": "user_profile"
        }
    }
    
    Returns:
    {
        "success": true,
        "message": "Added N documents"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        documents = data.get('documents', [])
        metadata = data.get('metadata', {})
        
        if not documents:
            return jsonify({'error': 'Documents are required'}), 400
        
        if not isinstance(documents, list):
            return jsonify({'error': 'Documents must be a list'}), 400
        
        # Add documents to local storage
        added_count = 0
        for i, doc in enumerate(documents):
            title = f"User Info {i+1}"
            if metadata.get('user_id'):
                title += f" - {metadata['user_id']}"
            
            rag_storage.add_document(
                title=title,
                content=doc,
                category='user_information',
                metadata=metadata
            )
            added_count += 1
        
        return jsonify({
            'success': True,
            'message': f'Added {added_count} user documents',
            'category': 'user_information',
            'count': added_count
        })
        
    except Exception as e:
        return jsonify({'error': f'Add user documents failed: {str(e)}'}), 500

@rag_bp.route('/search_all', methods=['POST'])
def search_all_categories():
    """
    Search across all categories
    
    Expected JSON payload:
    {
        "query": "search query",
        "top_k": 5
    }
    
    Returns:
    {
        "results": [...],
        "query": "search query",
        "count": 5
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        query = data.get('query', '')
        top_k = data.get('top_k', 5)
        
        if not query:
            return jsonify({'error': 'Query is required'}), 400
        
        # Search across all categories (no category filter)
        results = rag_storage.search(query, top_k=top_k, category=None)
        
        return jsonify({
            'success': True,
            'results': results,
            'query': query,
            'count': len(results),
            'category': 'all'
        })
        
    except Exception as e:
        return jsonify({'error': f'Search all categories failed: {str(e)}'}), 500

@rag_bp.route('/health', methods=['GET'])
def health():
    """Health check for RAG functions"""
    try:
        # Check local RAG storage
        doc_count = len(rag_storage.documents)
        
        return jsonify({
            'status': 'healthy',
            'service': 'rag_functions',
            'storage_type': 'local_memory',
            'document_count': doc_count,
            'vectorizer_ready': rag_storage.document_vectors is not None
        })
        
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'service': 'rag_functions',
            'error': str(e)
        }), 500