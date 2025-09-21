# Spam Detection Functions Server

A comprehensive system for spam call detection using multiple layers of validation, machine learning, and local RAG (Retrieval-Augmented Generation) functionality.

## Architecture Overview

**Single Flask Server** (`app.py`) - Complete functions API server with all endpoints integrated

## System Components

### Main Functions API (Port 5000)

#### Layer 1 Function (`/api/layer1/check_spam`)
- **Purpose**: Simple database lookup for known spam numbers
- **Method**: SQLite database with 64+ real spam/robocall numbers
- **Response**: Boolean (true/false) with confidence 1.0 or 0.0
- **Database**: Pre-populated with actual spam numbers

#### Layer 2 Function (`/api/layer2/ml_check_spam`)
- **Purpose**: ML-based spam detection with stochastic threshold
- **Method**: Custom trained scikit-learn model with realistic dataset
- **Features**: Time-based threshold adjustment, confidence noise, stochastic variance
- **Fallback**: Rule-based classifier for edge cases

#### RAG Functions (Local Implementation)
- **Storage**: Local in-memory storage with TF-IDF vectorization
- **Persistence**: JSON file storage (`data/rag_storage.json`)
- **Search**: Cosine similarity-based document retrieval
- **Categories**: `user_information`, `suspects`, `call_history`

**RAG Endpoints:**
- `get_user_information`: Query user information documents
- `get_call_history`: Retrieve relevant call history records  
- `post_suspect_information`: Add suspect data to local storage
- `add_user_documents`: Add user information documents
- `search_all`: Search across all categories
- `health`: Check RAG system status and document count

#### Training Functions
- **retrain_model**: Upload CSV to retrain the ML model
- **add_training_samples**: Add individual training samples via JSON
- **download_sample_csv**: Get sample training data format
- **training_history**: View training session history
- **health**: Check training system status

## Installation & Setup

### Prerequisites

```bash
# Install Python dependencies
pip install -r requirements.txt

# No external dependencies required - everything runs locally
````

### Environment Variables (Optional)

Create a `.env` file for customization:

```env
SECRET_KEY=your-secret-key-here
SPAM_DB_PATH=data/spam_numbers.db
```

### Running the Server

```bash
# Single command - starts everything
python app.py

# Server starts with external access enabled:
# - Local:    http://localhost:5000
# - Network:  http://[YOUR_LOCAL_IP]:5000  
# - External: http://[YOUR_PUBLIC_IP]:5000
#
# All components are initialized automatically:
# - Layer 1: Spam database with 64+ real numbers
# - Layer 2: Trained ML model ready
# - RAG: Local storage initialized
# - Training: Model retraining capabilities
# - CORS: Enabled for all origins
```

### External Access Configuration

The server is configured for **external access** by default:

- ✅ **Bind to all interfaces** (`0.0.0.0:5000`)
- ✅ **CORS enabled** for all origins (`*`)
- ✅ **All HTTP methods** supported (GET, POST, PUT, DELETE, OPTIONS)
- ✅ **Security headers** included

**Network Information Endpoint:**
```bash
curl http://[YOUR_IP]:5000/network-info
```

**Example External Usage:**
```bash
# From any external server/service:
curl -X POST http://[YOUR_SERVER_IP]:5000/api/layer1/check_spam \
  -H "Content-Type: application/json" \
  -d '{"From": "+15551234567"}'
```

### Quick Start Test

```bash
# Health check
curl http://localhost:5000/health

# Test Layer 1 (database lookup)
curl -X POST http://localhost:5000/api/layer1/check_spam \
  -H "Content-Type: application/json" \
  -d '{"From": "+18004419593"}'

# Test Layer 2 (ML detection)  
curl -X POST http://localhost:5000/api/layer2/ml_check_spam \
  -H "Content-Type: application/json" \
  -d '{"From": "+15551234567", "content": "FREE GIFT! Call now!"}'

# Test RAG (document storage)
curl -X POST http://localhost:5000/api/rag/post_suspect_information \
  -H "Content-Type: application/json" \
  -d '{"documents": ["Spam caller about fake lottery"], "metadata": {"phone": "+15551234567"}}'
```

## API Documentation

### Complete Endpoint List

**GET** `/` - List all available endpoints  
**GET** `/health` - System health check  

### Layer 1: Database Lookup

**POST** `/api/layer1/check_spam`

```json
{
  "From": "+18004419593"
}
```

**Response:**
```json
{
  "is_spam": true,
  "confidence": 1.0,
  "layer": 1,
  "method": "database_lookup",
  "phone_number": "+18004419593",
  "match_info": {
    "number": "+18004419593",
    "description": "IRS Tax Scam",
    "category": "government_impersonation"
  }
}
```

#### Layer 2: ML Detection

**POST** `/api/layer2/ml_check_spam`

```json
{
  "From": "+15551234567",
  "content": "FREE GIFT! Call now to claim your prize!",
  "Timestamp": "2024-01-01T12:00:00Z",
  "duration": 30
}
```

**Response:**
```json
{
  "is_spam": true,
  "confidence": 0.87,
  "layer": 2,
  "method": "ml_stochastic",
  "model_type": "custom",
  "phone_number": "+15551234567",
  "details": {
    "ml_prediction": {
      "is_spam": true,
      "confidence": 0.85,
      "threshold": 0.5
    },
    "stochastic_adjustment": {
      "time_adjustment": -0.1,
      "confidence_noise": 0.02,
      "final_threshold": 0.4
    }
  }
}
```

### RAG Functions (Local Storage)

**GET** `/api/rag/health` - Check RAG system status

**POST** `/api/rag/post_suspect_information`

```json
{
  "documents": [
    "Caller +15551234567 repeatedly calls about fake lottery winnings",
    "Reports indicate this number is associated with IRS scam calls"
  ],
  "metadata": {
    "phone_number": "+15551234567",
    "source": "user_reports"
  }
}
```

**POST** `/api/rag/add_user_documents`

```json
{
  "documents": [
    "User prefers to block unknown callers",
    "User reports receiving 3+ spam calls daily"
  ],
  "metadata": {
    "user_id": "user123",
    "source": "user_profile"
  }
}
```

**POST** `/api/rag/get_user_information`

```json
{
  "query": "elderly user vulnerable to scams",
  "top_k": 5
}
```

**POST** `/api/rag/search_all` - Search across all categories

```json
{
  "query": "IRS scam calls",
  "top_k": 5
}
```

### Training Functions

**POST** `/api/training/retrain_model` - Upload CSV file for retraining

**POST** `/api/training/add_training_samples`

```json
{
  "samples": [
    {
      "text": "URGENT: Your package delivery failed. Click link to reschedule.",
      "label": 1
    },
    {
      "text": "Hi, its your neighbor. Can we chat later?", 
      "label": 0
    }
  ]
}
```

**GET** `/api/training/download_sample_csv` - Get sample training data format

**GET** `/api/training/training_history` - View training session history

**GET** `/api/training/health` - Check training system status
```

## Data Storage

### Layer 1 Database
- **File**: `data/spam_numbers.db` (SQLite)
- **Content**: 64+ real spam/robocall numbers with descriptions
- **Categories**: Government impersonation, telemarketing, robocalls, etc.

### RAG Document Storage  
- **File**: `data/rag_storage.json`
- **Format**: JSON with document vectors
- **Categories**: `user_information`, `suspects`, `call_history`
- **Search**: TF-IDF vectorization with cosine similarity

### ML Model Storage
- **File**: `models/spam_detection_model.joblib`
- **Type**: Scikit-learn trained model
- **Training Data**: 149 realistic spam/legitimate call samples
- **Features**: Custom text vectorization and classification

## System Features

### Layer 1 Features
- ✅ Real spam number database (64+ entries)
- ✅ Instant lookup with O(1) complexity
- ✅ Detailed match information with categories
- ✅ 100% confidence for known spam numbers

### Layer 2 Features  
- ✅ Custom ML model with realistic training data
- ✅ Stochastic threshold adjustment (time-based)
- ✅ Confidence noise for variance
- ✅ Rule-based fallback classifier
- ✅ Detailed prediction breakdown

### RAG Features
- ✅ Local vector storage (no external dependencies)
- ✅ Category-based document organization
- ✅ Semantic search with similarity scoring
- ✅ Persistent storage across restarts
- ✅ Metadata support for context

### Training Features
- ✅ CSV upload for bulk training
- ✅ Individual sample addition via API
- ✅ Model retraining with new data
- ✅ Training history tracking
- ✅ Sample data download

## Usage Workflow

### For Main Product Integration

1. **Incoming Call** → Your main product calls the spam detection server
2. **Layer 1 Check** → Call `/api/layer1/check_spam`
   - If spam detected (confidence 1.0) → Reject call immediately
   - If not spam → Continue to Layer 2
3. **Layer 2 Check** → Call `/api/layer2/ml_check_spam`
   - If spam detected (confidence > threshold) → Reject call
   - If not spam → Connect to agent/user
4. **Agent Access** → Your system can use RAG functions:
   - `/api/rag/get_user_information` - Get user context
   - `/api/rag/get_call_history` - Check previous interactions
   - `/api/rag/post_suspect_information` - Report suspicious activity
   - `/api/rag/search_all` - Search all documents

### For Agent Dashboard Integration

Agents have access to these functions during calls:

- **get_user_information**: Query user details and preferences
- **get_call_history**: Check previous call interactions  
- **post_suspect_information**: Report suspicious callers
- **search_all**: Search across all stored documents

### For Training and Improvement

- **Continuous Learning**: Use `/api/training/add_training_samples` to improve the model
- **Bulk Training**: Upload CSV files via `/api/training/retrain_model`
- **Monitor Performance**: Check `/api/training/training_history`

## Training the Model

### Option 1: Use Pre-trained Model (Default)
The system comes with a pre-trained model on 149 realistic samples.

### Option 2: Custom Training
The system automatically attempts to load a Hugging Face model for spam detection.

### Option 2: Train Custom Model
1. Prepare CSV with `text` and `label` columns
2. Upload via `/api/training/retrain_model`
3. Model automatically trains and saves

### Option 3: Continuous Learning
- Add new samples via `/api/training/add_training_samples`
- Upload new CSV files to retrain with additional data

## Database Structure

1. Download sample CSV format:
```bash
curl -X GET http://localhost:5000/api/training/download_sample_csv > training_data.csv
```

2. Edit the CSV with your spam/legitimate call examples:
```csv
text,label
"Congratulations! You've won $1000! Call now!",1
"Hi mom, just calling to check in on you.",0
"Your account has been suspended. Verify immediately.",1
"Your doctor appointment is tomorrow at 2 PM.",0
```

3. Upload for training:
```bash
curl -X POST http://localhost:5000/api/training/retrain_model \
  -F "file=@training_data.csv" \
  -F "epochs=10" \
  -F "learning_rate=0.001"
```

### Option 3: Add Individual Samples
```bash
curl -X POST http://localhost:5000/api/training/add_training_samples \
  -H "Content-Type: application/json" \
  -d '{"samples": [{"text": "New spam example", "label": 1}]}'
```

## File Structure

```
ash/
├── app.py                          # Main Flask application
├── requirements.txt                # Python dependencies  
├── .env                           # Environment variables (optional)
├── api/
│   ├── __init__.py
│   ├── layer1.py                  # Database lookup functions
│   ├── layer2.py                  # ML spam detection
│   ├── rag_functions.py           # Local RAG implementation
│   └── training.py                # Model training endpoints
├── models/
│   ├── spam_detection.py          # ML model implementation
│   └── spam_detection_model.joblib # Trained model file
├── data/
│   ├── spam_numbers.db            # SQLite spam database (auto-created)
│   ├── rag_storage.json           # RAG documents storage (auto-created)
│   └── uploads/                   # Training file uploads
├── utilities/
│   └── client.py                  # Python client SDK
├── Dockerfile                     # Docker container setup
├── docker-compose.yml             # Docker compose config  
└── README.md                      # This documentation
```

## Health Checks

- **Main Server**: `GET http://localhost:5000/health`
- **Layer 1**: `GET http://localhost:5000/api/layer1/health` 
- **Layer 2**: `GET http://localhost:5000/api/layer2/health`
- **RAG Functions**: `GET http://localhost:5000/api/rag/health`
- **Training**: `GET http://localhost:5000/api/training/health`
- **Individual Services**:
  - `GET /api/layer1/health`
  - `GET /api/layer2/health`
  - `GET /api/rag/health`
  - `GET /api/training/health`

## Error Handling

All endpoints return appropriate HTTP status codes:
- **200**: Success
- **400**: Bad request (invalid input)
- **500**: Server error

Error responses include detailed error messages:
```json
{
  "error": "Detailed error message",
  "is_spam": false
}
```

## Security Considerations

1. **Input Validation**: All inputs are validated before processing
2. **File Upload Security**: Only CSV files allowed, filenames sanitized
3. **SQL Injection Prevention**: Parameterized queries used
4. **CORS Configuration**: Configure appropriately for production
5. **Environment Variables**: Sensitive data stored in environment variables

## Performance Notes

- **Layer 1**: Very fast database lookup (~1ms)
- **Layer 2**: ML prediction (~50-200ms depending on model)
- **RAG Search**: Vector similarity search (~10-50ms)
- **Model Training**: Minutes to hours depending on dataset size

## Troubleshooting

### Common Issues

1. **Qdrant Connection Error**: Ensure Qdrant is running on port 6333
2. **Model Not Loading**: Check if model files exist in `models/` directory
3. **CSV Upload Error**: Verify CSV has `text` and `label` columns
4. **Port Conflicts**: Ensure ports 5000 and 6334 are available

### Logs

Check console output for detailed error messages and debugging information.

## Contributing

1. Follow the existing code structure
2. Add appropriate error handling
3. Update this README for new features
4. Test all endpoints before committing

## License

[Add your license information here]