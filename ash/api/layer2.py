from flask import Blueprint, request, jsonify
import os
import sys
import random
from typing import Dict, Any

# Add the models directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'models'))

try:
    from spam_detection import SpamDetectionModel
except ImportError:
    SpamDetectionModel = None
    print("Warning: Could not import SpamDetectionModel")

layer2_bp = Blueprint('layer2', __name__)

# Global model instance
spam_model = None

def initialize_model():
    """Initialize the spam detection model"""
    global spam_model
    
    if SpamDetectionModel is None:
        print("SpamDetectionModel not available")
        return False
    
    try:
        # Try to load existing custom model first
        spam_model = SpamDetectionModel("custom")
        
        if spam_model.model is None:
            print("No custom model found, trying Hugging Face model...")
            spam_model = SpamDetectionModel("huggingface")
            
            if spam_model.model is None:
                print("No Hugging Face model available, training custom model...")
                spam_model = SpamDetectionModel("custom")
                spam_model.train_custom_model()
        
        return spam_model.model is not None
        
    except Exception as e:
        print(f"Error initializing model: {e}")
        return False

def extract_call_content(call_data: Dict[str, Any]) -> str:
    """
    Extract relevant content from Twilio call object for spam analysis
    
    Args:
        call_data: Twilio call object data
    
    Returns:
        String content to analyze
    """
    # Extract various fields that might indicate spam
    content_parts = []
    
    # Phone number patterns
    from_number = call_data.get('From', '')
    if from_number:
        content_parts.append(f"Caller: {from_number}")
    
    # Call direction and status
    direction = call_data.get('Direction', '')
    status = call_data.get('Status', '')
    if direction:
        content_parts.append(f"Direction: {direction}")
    if status:
        content_parts.append(f"Status: {status}")
    
    # Geographic information
    from_city = call_data.get('FromCity', '')
    from_state = call_data.get('FromState', '')
    from_country = call_data.get('FromCountry', '')
    
    if from_city or from_state or from_country:
        location = f"{from_city} {from_state} {from_country}".strip()
        content_parts.append(f"Location: {location}")
    
    # Carrier information
    from_carrier = call_data.get('CallerName', '')
    if from_carrier:
        content_parts.append(f"Carrier: {from_carrier}")
    
    # Duration and time patterns
    duration = call_data.get('Duration', '')
    if duration:
        content_parts.append(f"Duration: {duration} seconds")
    
    # For analysis, we create a text description of the call characteristics
    # In a real scenario, you might have call transcripts or additional metadata
    content = " | ".join(content_parts)
    
    # If no meaningful content, create a basic description
    if not content:
        content = f"Incoming call from {from_number or 'unknown number'}"
    
    return content

def apply_stochastic_threshold(base_confidence: float, threshold: float = 0.5) -> Dict[str, Any]:
    """
    Apply stochastic threshold to add randomness to spam detection
    
    This simulates real-world uncertainty and prevents overly deterministic results
    
    Args:
        base_confidence: Base confidence from ML model
        threshold: Base threshold for spam classification
    
    Returns:
        Dict with adjusted results
    """
    # Add some randomness based on confidence level
    noise_factor = 0.1  # 10% noise
    confidence_noise = random.uniform(-noise_factor, noise_factor)
    adjusted_confidence = max(0.0, min(1.0, base_confidence + confidence_noise))
    
    # Dynamic threshold based on time of day (simulating call patterns)
    import datetime
    current_hour = datetime.datetime.now().hour
    
    # Adjust threshold based on time (spam calls more common during business hours)
    if 9 <= current_hour <= 17:  # Business hours
        time_adjustment = 0.05  # Slightly more sensitive
    elif 18 <= current_hour <= 21:  # Evening
        time_adjustment = 0.0  # Normal
    else:  # Night/early morning
        time_adjustment = -0.1  # Less sensitive (fewer legitimate calls)
    
    adjusted_threshold = max(0.1, min(0.9, threshold + time_adjustment))
    
    # Final decision with stochastic element
    is_spam = adjusted_confidence > adjusted_threshold
    
    # Add edge case handling - very high confidence (>0.9) has small chance of false negative
    if adjusted_confidence > 0.9:
        false_negative_chance = 0.02  # 2% chance
        if random.random() < false_negative_chance:
            is_spam = False
    
    # Very low confidence (<0.1) has small chance of false positive
    elif adjusted_confidence < 0.1:
        false_positive_chance = 0.01  # 1% chance
        if random.random() < false_positive_chance:
            is_spam = True
    
    return {
        "is_spam": is_spam,
        "confidence": adjusted_confidence,
        "base_confidence": base_confidence,
        "threshold": adjusted_threshold,
        "base_threshold": threshold,
        "time_adjustment": time_adjustment,
        "confidence_noise": confidence_noise
    }

@layer2_bp.route('/ml_check_spam', methods=['POST'])
def layer2_ml_check_spam():
    """
    Layer 2 function: ML-based spam detection with stochastic threshold
    
    Expected JSON payload:
    {
        "From": "+1234567890",
        "To": "+0987654321",
        "CallSid": "CA1234567890abcdef",
        "Direction": "inbound",
        "Status": "ringing",
        "FromCity": "New York",
        "FromState": "NY",
        "FromCountry": "US",
        ...other Twilio call object fields
    }
    
    Returns:
    {
        "is_spam": true/false,
        "confidence": 0.85,
        "layer": 2,
        "method": "ml_stochastic",
        "model_type": "custom",
        "details": {...}
    }
    """
    global spam_model
    
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'No JSON data provided',
                'is_spam': False
            }), 400
        
        # Initialize model if not already done
        if spam_model is None:
            if not initialize_model():
                return jsonify({
                    'error': 'ML model not available',
                    'is_spam': False,
                    'layer': 2,
                    'method': 'fallback'
                }), 500
        
        # Extract call content for analysis
        call_content = extract_call_content(data)
        
        # Get base threshold from request or use default
        base_threshold = data.get('threshold', 0.5)
        
        # Get ML prediction
        ml_result = spam_model.predict(call_content, base_threshold)
        
        if 'error' in ml_result:
            return jsonify({
                'error': f'ML prediction failed: {ml_result["error"]}',
                'is_spam': False,
                'layer': 2
            }), 500
        
        # Apply stochastic threshold
        stochastic_result = apply_stochastic_threshold(
            ml_result['confidence'], 
            base_threshold
        )
        
        # Combine results
        response = {
            'is_spam': bool(stochastic_result['is_spam']),
            'confidence': float(stochastic_result['confidence']),
            'layer': 2,
            'method': 'ml_stochastic',
            'model_type': ml_result.get('model_type', 'unknown'),
            'phone_number': data.get('From', ''),
            'timestamp': data.get('Timestamp', ''),
            'call_content': call_content,
            'details': {
                'ml_prediction': {
                    'is_spam': bool(ml_result.get('is_spam', False)),
                    'confidence': float(ml_result.get('confidence', 0.0)),
                    'threshold': float(ml_result.get('threshold', 0.5)),
                    'model_type': ml_result.get('model_type', 'unknown')
                },
                'stochastic_adjustment': {
                    'is_spam': bool(stochastic_result['is_spam']),
                    'confidence': float(stochastic_result['confidence']),
                    'base_confidence': float(stochastic_result['base_confidence']),
                    'threshold': float(stochastic_result['threshold']),
                    'base_threshold': float(stochastic_result['base_threshold']),
                    'time_adjustment': float(stochastic_result['time_adjustment']),
                    'confidence_noise': float(stochastic_result['confidence_noise'])
                },
                'call_data_keys': list(data.keys())
            }
        }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({
            'error': f'Layer 2 ML check failed: {str(e)}',
            'is_spam': False,
            'layer': 2
        }), 500

@layer2_bp.route('/predict_text', methods=['POST'])
def predict_text():
    """
    Direct text prediction endpoint for testing
    
    Expected JSON payload:
    {
        "text": "Text to analyze",
        "threshold": 0.5
    }
    
    Returns:
    {
        "is_spam": true/false,
        "confidence": 0.85,
        "method": "ml_direct"
    }
    """
    global spam_model
    
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        text = data.get('text', '')
        threshold = data.get('threshold', 0.5)
        
        if not text:
            return jsonify({'error': 'Text is required'}), 400
        
        # Initialize model if not already done
        if spam_model is None:
            if not initialize_model():
                return jsonify({
                    'error': 'ML model not available',
                    'is_spam': False
                }), 500
        
        # Get prediction
        result = spam_model.predict(text, threshold)
        
        if 'error' in result:
            return jsonify({
                'error': f'Prediction failed: {result["error"]}',
                'is_spam': False
            }), 500
        
        result['method'] = 'ml_direct'
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'error': f'Text prediction failed: {str(e)}',
            'is_spam': False
        }), 500

@layer2_bp.route('/model_info', methods=['GET'])
def model_info():
    """Get information about the loaded model"""
    global spam_model
    
    try:
        if spam_model is None:
            initialize_model()
        
        if spam_model is None:
            return jsonify({
                'model_loaded': False,
                'error': 'No model available'
            })
        
        info = {
            'model_loaded': True,
            'model_type': spam_model.model_type,
            'model_available': spam_model.model is not None,
            'vectorizer_available': spam_model.vectorizer is not None if hasattr(spam_model, 'vectorizer') else None
        }
        
        return jsonify(info)
        
    except Exception as e:
        return jsonify({
            'model_loaded': False,
            'error': str(e)
        }), 500

@layer2_bp.route('/health', methods=['GET'])
def layer2_health():
    """Health check for Layer 2 service"""
    global spam_model
    
    try:
        model_status = "not_initialized"
        model_type = "unknown"
        
        if spam_model is not None:
            model_status = "loaded" if spam_model.model else "failed"
            model_type = spam_model.model_type
        
        return jsonify({
            'status': 'healthy',
            'service': 'layer2',
            'model_status': model_status,
            'model_type': model_type
        })
        
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'service': 'layer2',
            'error': str(e)
        }), 500

# Initialize model when module is imported
initialize_model()