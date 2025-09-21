from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from qdrant_client.models import Filter, FieldCondition, Range, MatchValue
from sentence_transformers import SentenceTransformer
import uuid
import os
from typing import List, Dict, Any
import json

class QdrantRAGServer:
    def __init__(self, host: str = "localhost", port: int = 6333):
        self.client = QdrantClient(host=host, port=port)
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
        self.collection_name = "spam_detection_rag"
        self.vector_size = 384  # all-MiniLM-L6-v2 embedding size
        
        # Initialize collection
        self._setup_collection()
    
    def _setup_collection(self):
        """Setup Qdrant collection if it doesn't exist"""
        try:
            # Check if collection exists
            collections = self.client.get_collections()
            collection_exists = any(col.name == self.collection_name for col in collections.collections)
            
            if not collection_exists:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.vector_size,
                        distance=Distance.COSINE
                    )
                )
                print(f"Created collection: {self.collection_name}")
            else:
                print(f"Collection {self.collection_name} already exists")
                
        except Exception as e:
            print(f"Error setting up collection: {e}")
    
    def add_documents(self, documents: List[str], category: str, metadata: Dict[str, Any] = None) -> bool:
        """
        Add documents to the RAG database
        
        Args:
            documents: List of text documents to add
            category: Category for the documents ('user_information', 'suspects', 'call_history')
            metadata: Additional metadata for the documents
        
        Returns:
            bool: Success status
        """
        try:
            points = []
            
            for i, doc in enumerate(documents):
                # Generate embedding
                embedding = self.encoder.encode(doc).tolist()
                
                # Create point
                point_id = str(uuid.uuid4())
                payload = {
                    "text": doc,
                    "category": category,
                    "doc_index": i,
                    **(metadata or {})
                }
                
                point = PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload=payload
                )
                points.append(point)
            
            # Upload points
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            
            print(f"Added {len(documents)} documents with category '{category}'")
            return True
            
        except Exception as e:
            print(f"Error adding documents: {e}")
            return False
    
    def search_documents(self, query: str, category: str = None, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for relevant documents
        
        Args:
            query: Search query
            category: Filter by category (optional)
            top_k: Number of results to return
        
        Returns:
            List of relevant documents with scores
        """
        try:
            # Generate query embedding
            query_embedding = self.encoder.encode(query).tolist()
            
            # Prepare filter
            query_filter = None
            if category:
                query_filter = Filter(
                    must=[
                        FieldCondition(
                            key="category",
                            match=MatchValue(value=category)
                        )
                    ]
                )
            
            # Search
            search_results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                query_filter=query_filter,
                limit=top_k
            )
            
            # Format results
            results = []
            for result in search_results:
                results.append({
                    "text": result.payload.get("text", ""),
                    "category": result.payload.get("category", ""),
                    "score": result.score,
                    "metadata": {k: v for k, v in result.payload.items() 
                               if k not in ["text", "category"]}
                })
            
            return results
            
        except Exception as e:
            print(f"Error searching documents: {e}")
            return []
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the collection"""
        try:
            info = self.client.get_collection(self.collection_name)
            return {
                "name": info.config.name,
                "vector_size": info.config.params.vectors.size,
                "distance": info.config.params.vectors.distance,
                "points_count": info.points_count,
                "status": info.status
            }
        except Exception as e:
            print(f"Error getting collection info: {e}")
            return {}
    
    def delete_documents_by_category(self, category: str) -> bool:
        """Delete all documents of a specific category"""
        try:
            filter_condition = Filter(
                must=[
                    FieldCondition(
                        key="category",
                        match=MatchValue(value=category)
                    )
                ]
            )
            
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=filter_condition
            )
            
            print(f"Deleted documents with category '{category}'")
            return True
            
        except Exception as e:
            print(f"Error deleting documents: {e}")
            return False

# Standalone Qdrant RAG server
if __name__ == "__main__":
    from flask import Flask, request, jsonify
    from flask_cors import CORS
    
    app = Flask(__name__)
    CORS(app)
    
    # Initialize RAG server
    rag_server = QdrantRAGServer(
        host=os.getenv('QDRANT_HOST', 'localhost'),
        port=int(os.getenv('QDRANT_PORT', 6333))
    )
    
    @app.route('/health', methods=['GET'])
    def health():
        return jsonify({
            'status': 'healthy',
            'service': 'qdrant-rag-server',
            'collection_info': rag_server.get_collection_info()
        })
    
    @app.route('/add_documents', methods=['POST'])
    def add_documents():
        """
        Add documents to the RAG database
        
        Expected JSON:
        {
            "documents": ["text1", "text2", ...],
            "category": "user_information|suspects|call_history",
            "metadata": {"key": "value"}
        }
        """
        try:
            data = request.get_json()
            documents = data.get('documents', [])
            category = data.get('category', '')
            metadata = data.get('metadata', {})
            
            if not documents or not category:
                return jsonify({'error': 'Documents and category are required'}), 400
            
            success = rag_server.add_documents(documents, category, metadata)
            
            if success:
                return jsonify({'success': True, 'message': f'Added {len(documents)} documents'})
            else:
                return jsonify({'error': 'Failed to add documents'}), 500
                
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/search', methods=['POST'])
    def search():
        """
        Search documents
        
        Expected JSON:
        {
            "query": "search text",
            "category": "user_information", (optional)
            "top_k": 5
        }
        """
        try:
            data = request.get_json()
            query = data.get('query', '')
            category = data.get('category')
            top_k = data.get('top_k', 5)
            
            if not query:
                return jsonify({'error': 'Query is required'}), 400
            
            results = rag_server.search_documents(query, category, top_k)
            
            return jsonify({
                'results': results,
                'query': query,
                'category': category,
                'count': len(results)
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/collection/info', methods=['GET'])
    def collection_info():
        """Get collection information"""
        return jsonify(rag_server.get_collection_info())
    
    @app.route('/collection/delete_category', methods=['DELETE'])
    def delete_category():
        """
        Delete documents by category
        
        Expected JSON:
        {
            "category": "category_name"
        }
        """
        try:
            data = request.get_json()
            category = data.get('category', '')
            
            if not category:
                return jsonify({'error': 'Category is required'}), 400
            
            success = rag_server.delete_documents_by_category(category)
            
            if success:
                return jsonify({'success': True, 'message': f'Deleted documents in category: {category}'})
            else:
                return jsonify({'error': 'Failed to delete documents'}), 500
                
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    if __name__ == '__main__':
        app.run(host='0.0.0.0', port=6334, debug=True)