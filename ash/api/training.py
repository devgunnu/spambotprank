from flask import Blueprint, request, jsonify, send_file
import os
import sys
import pandas as pd
from werkzeug.utils import secure_filename
import tempfile
from typing import Dict, Any

# Add the models directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'models'))

try:
    from spam_detection import SpamDetectionModel
except ImportError:
    SpamDetectionModel = None
    print("Warning: Could not import SpamDetectionModel")

training_bp = Blueprint('training', __name__)

# Configuration
UPLOAD_FOLDER = 'data/uploads'
ALLOWED_EXTENSIONS = {'csv'}

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_csv_format(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Validate CSV format for training data
    
    Expected columns: text, label (and optionally category, source, etc.)
    
    Args:
        df: DataFrame to validate
    
    Returns:
        Dict with validation results
    """
    required_columns = ['text', 'label']
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        return {
            'valid': False,
            'error': f'Missing required columns: {missing_columns}',
            'required_columns': required_columns,
            'found_columns': list(df.columns)
        }
    
    # Check data types and values
    issues = []
    
    # Check text column
    if df['text'].isna().any():
        issues.append('Text column contains missing values')
    
    # Check label column
    if df['label'].isna().any():
        issues.append('Label column contains missing values')
    
    unique_labels = df['label'].unique()
    valid_labels = {0, 1, '0', '1', 'spam', 'legitimate', 'ham', True, False}
    
    if not all(label in valid_labels for label in unique_labels):
        issues.append(f'Invalid label values. Found: {unique_labels}. Expected: 0/1, spam/legitimate, ham/spam, or True/False')
    
    # Convert labels to binary format
    try:
        df_copy = df.copy()
        df_copy['label'] = df_copy['label'].map({
            'spam': 1, 'legitimate': 0, 'ham': 0,
            '1': 1, '0': 0, 1: 1, 0: 0,
            True: 1, False: 0
        })
        
        if df_copy['label'].isna().any():
            issues.append('Could not convert all labels to binary format')
    except Exception as e:
        issues.append(f'Error processing labels: {str(e)}')
    
    return {
        'valid': len(issues) == 0,
        'issues': issues,
        'sample_count': len(df),
        'spam_count': sum(df_copy['label'] == 1) if 'df_copy' in locals() else 0,
        'legitimate_count': sum(df_copy['label'] == 0) if 'df_copy' in locals() else 0,
        'columns': list(df.columns)
    }

@training_bp.route('/retrain_model', methods=['POST'])
def retrain_model():
    """
    Retrain the spam detection model with new CSV data
    
    Expects multipart/form-data with a CSV file
    
    CSV format expected:
    text,label
    "Spam message text",1
    "Legitimate message text",0
    
    Labels can be: 0/1, spam/legitimate, ham/spam, True/False
    
    Returns:
    {
        "success": true,
        "message": "Model retrained successfully",
        "training_results": {...}
    }
    """
    try:
        if SpamDetectionModel is None:
            return jsonify({
                'success': False,
                'error': 'SpamDetectionModel not available'
            }), 500
        
        # Check if file is in request
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file provided. Please upload a CSV file.'
            }), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400
        
        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'error': 'Invalid file type. Please upload a CSV file.'
            }), 400
        
        # Create upload directory
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)
        
        try:
            # Load and validate CSV
            df = pd.read_csv(file_path)
            validation_result = validate_csv_format(df)
            
            if not validation_result['valid']:
                return jsonify({
                    'success': False,
                    'error': 'Invalid CSV format',
                    'validation_details': validation_result
                }), 400
            
            # Convert labels to binary format
            label_mapping = {
                'spam': 1, 'legitimate': 0, 'ham': 0,
                '1': 1, '0': 0, 1: 1, 0: 0,
                True: 1, False: 0
            }
            
            df['label'] = df['label'].map(label_mapping)
            df = df.dropna()  # Remove any rows that couldn't be mapped
            
            # Save processed CSV
            processed_file_path = file_path.replace('.csv', '_processed.csv')
            df.to_csv(processed_file_path, index=False)
            
            # Initialize model and retrain
            model = SpamDetectionModel("custom")
            training_results = model.retrain_with_new_data(processed_file_path)
            
            if 'error' in training_results:
                return jsonify({
                    'success': False,
                    'error': training_results['error'],
                    'validation_details': validation_result
                }), 500
            
            # Clean up uploaded files
            try:
                os.remove(file_path)
                os.remove(processed_file_path)
            except:
                pass  # Don't fail if cleanup fails
            
            return jsonify({
                'success': True,
                'message': 'Model retrained successfully',
                'training_results': training_results,
                'validation_details': validation_result,
                'filename': filename
            })
            
        except pd.errors.EmptyDataError:
            return jsonify({
                'success': False,
                'error': 'CSV file is empty'
            }), 400
            
        except pd.errors.ParserError as e:
            return jsonify({
                'success': False,
                'error': f'Error parsing CSV file: {str(e)}'
            }), 400
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Error processing CSV: {str(e)}'
            }), 500
        
        finally:
            # Clean up uploaded file if it still exists
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except:
                pass
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Training failed: {str(e)}'
        }), 500

@training_bp.route('/add_training_samples', methods=['POST'])
def add_training_samples():
    """
    Add individual training samples via JSON
    
    Expected JSON payload:
    {
        "samples": [
            {"text": "spam message", "label": 1},
            {"text": "legitimate message", "label": 0}
        ]
    }
    
    Returns:
    {
        "success": true,
        "message": "Added N training samples"
    }
    """
    try:
        if SpamDetectionModel is None:
            return jsonify({
                'success': False,
                'error': 'SpamDetectionModel not available'
            }), 500
        
        data = request.get_json()
        
        if not data or 'samples' not in data:
            return jsonify({
                'success': False,
                'error': 'No samples provided. Expected JSON with "samples" array.'
            }), 400
        
        samples = data['samples']
        
        if not isinstance(samples, list) or len(samples) == 0:
            return jsonify({
                'success': False,
                'error': 'Samples must be a non-empty array'
            }), 400
        
        # Validate sample format
        for i, sample in enumerate(samples):
            if not isinstance(sample, dict) or 'text' not in sample or 'label' not in sample:
                return jsonify({
                    'success': False,
                    'error': f'Sample {i} is invalid. Each sample must have "text" and "label" fields.'
                }), 400
        
        # Create temporary CSV file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as temp_file:
            temp_csv_path = temp_file.name
            
            # Write samples to CSV
            df = pd.DataFrame(samples)
            df.to_csv(temp_csv_path, index=False)
        
        try:
            # Validate CSV format
            validation_result = validate_csv_format(df)
            
            if not validation_result['valid']:
                return jsonify({
                    'success': False,
                    'error': 'Invalid sample format',
                    'validation_details': validation_result
                }), 400
            
            # Retrain model
            model = SpamDetectionModel("custom")
            training_results = model.retrain_with_new_data(temp_csv_path)
            
            if 'error' in training_results:
                return jsonify({
                    'success': False,
                    'error': training_results['error']
                }), 500
            
            return jsonify({
                'success': True,
                'message': f'Added {len(samples)} training samples',
                'training_results': training_results,
                'validation_details': validation_result
            })
            
        finally:
            # Clean up temporary file
            try:
                os.remove(temp_csv_path)
            except:
                pass
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Adding training samples failed: {str(e)}'
        }), 500

@training_bp.route('/download_sample_csv', methods=['GET'])
def download_sample_csv():
    """
    Download a sample CSV file with the correct format for training
    
    Returns:
    CSV file with sample training data
    """
    try:
        # Create sample data
        sample_data = [
            {"text": "Congratulations! You've won $1000! Call now to claim!", "label": 1},
            {"text": "FREE MONEY! Click here to get rich quick!", "label": 1},
            {"text": "Your account has been suspended. Verify immediately.", "label": 1},
            {"text": "Hi mom, just calling to check in on you.", "label": 0},
            {"text": "Your doctor appointment is tomorrow at 2 PM.", "label": 0},
            {"text": "Hello, this is John from work. How are you?", "label": 0}
        ]
        
        # Create temporary CSV file
        with tempfile.NamedTemporaryFile(mode='w', suffix='_training_sample.csv', delete=False) as temp_file:
            temp_csv_path = temp_file.name
            
            df = pd.DataFrame(sample_data)
            df.to_csv(temp_csv_path, index=False)
        
        return send_file(
            temp_csv_path,
            as_attachment=True,
            download_name='spam_training_sample.csv',
            mimetype='text/csv'
        )
        
    except Exception as e:
        return jsonify({
            'error': f'Could not generate sample CSV: {str(e)}'
        }), 500

@training_bp.route('/training_history', methods=['GET'])
def training_history():
    """
    Get training history and model information
    
    Returns:
    {
        "model_info": {...},
        "training_files": [...],
        "last_training": "..."
    }
    """
    try:
        # Get model information
        model_info = {}
        
        if SpamDetectionModel:
            try:
                model = SpamDetectionModel("custom")
                if model.model:
                    model_info = {
                        'model_type': model.model_type,
                        'model_loaded': True,
                        'model_file_exists': os.path.exists(model.model_path),
                        'vectorizer_file_exists': os.path.exists(model.vectorizer_path)
                    }
                else:
                    model_info = {'model_loaded': False}
            except Exception as e:
                model_info = {'error': str(e)}
        
        # Get training files
        training_files = []
        if os.path.exists(UPLOAD_FOLDER):
            for filename in os.listdir(UPLOAD_FOLDER):
                if filename.endswith('.csv'):
                    file_path = os.path.join(UPLOAD_FOLDER, filename)
                    stat = os.stat(file_path)
                    training_files.append({
                        'filename': filename,
                        'size': stat.st_size,
                        'modified': stat.st_mtime
                    })
        
        return jsonify({
            'model_info': model_info,
            'training_files': training_files,
            'upload_folder': UPLOAD_FOLDER,
            'allowed_extensions': list(ALLOWED_EXTENSIONS)
        })
        
    except Exception as e:
        return jsonify({
            'error': f'Could not get training history: {str(e)}'
        }), 500

@training_bp.route('/health', methods=['GET'])
def training_health():
    """Health check for training service"""
    try:
        model_available = SpamDetectionModel is not None
        upload_folder_exists = os.path.exists(UPLOAD_FOLDER)
        
        return jsonify({
            'status': 'healthy',
            'service': 'training',
            'model_available': model_available,
            'upload_folder_exists': upload_folder_exists,
            'upload_folder': UPLOAD_FOLDER
        })
        
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'service': 'training',
            'error': str(e)
        }), 500