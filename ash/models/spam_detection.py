import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import joblib
import os
import requests
from typing import Tuple, Dict, Any
import warnings
warnings.filterwarnings('ignore')

class SpamDetectionModel:
    def __init__(self, model_type: str = "custom"):
        """
        Initialize spam detection model
        
        Args:
            model_type: "custom" for training custom model, "huggingface" for pre-trained
        """
        self.model_type = model_type
        self.model = None
        self.vectorizer = None
        self.model_path = "models/spam_model.joblib"
        self.vectorizer_path = "models/vectorizer.joblib"
        
        if model_type == "huggingface":
            self._load_huggingface_model()
        elif os.path.exists(self.model_path):
            self.load_model()
    
    def _load_huggingface_model(self):
        """Load pre-trained model from Hugging Face"""
        try:
            # Try to import transformers
            from transformers import pipeline
            
            # Try multiple spam detection models
            models_to_try = [
                "martin-ha/toxic-comment-model",
                "unitary/toxic-bert"
            ]
            
            for model_name in models_to_try:
                try:
                    print(f"Trying to load model: {model_name}")
                    self.model = pipeline(
                        "text-classification",
                        model=model_name,
                        device=-1,  # Use CPU
                        return_all_scores=True
                    )
                    print(f"Successfully loaded Hugging Face model: {model_name}")
                    self.model_name = model_name
                    return
                except Exception as model_error:
                    print(f"Failed to load {model_name}: {model_error}")
                    continue
            
            # If all models fail, fall back to rule-based
            print("All Hugging Face models failed, using rule-based classifier")
            self.model = self._create_rule_based_classifier()
            self.model_name = "rule-based"
            
        except ImportError:
            print("Transformers library not available, using rule-based classifier")
            self.model = self._create_rule_based_classifier()
            self.model_name = "rule-based"
        except Exception as e:
            print(f"Failed to load any Hugging Face model: {e}")
            print("Falling back to rule-based classifier")
            self.model = self._create_rule_based_classifier()
            self.model_name = "rule-based"
    
    def _create_rule_based_classifier(self):
        """Create a simple rule-based spam classifier as fallback"""
        class RuleBasedClassifier:
            def __init__(self):
                self.spam_keywords = [
                    'free', 'win', 'winner', 'congratulations', 'prize', 'money',
                    'urgent', 'limited time', 'act now', 'call now', 'click here',
                    'guarantee', 'no risk', 'credit', 'loan', 'debt', 'cash',
                    'inheritance', 'lottery', 'sweepstakes', 'claim', 'reward',
                    'offer expires', 'final notice', 'suspended', 'verify',
                    'irs', 'tax', 'refund', 'social security', 'medicare',
                    'warranty', 'auto', 'car', 'insurance', 'pharmacy',
                    'medication', 'pills', 'viagra', 'diet', 'weight loss'
                ]
            
            def __call__(self, text):
                if isinstance(text, list):
                    text = text[0] if text else ""
                
                text_lower = text.lower()
                spam_score = 0
                total_keywords = len(self.spam_keywords)
                
                for keyword in self.spam_keywords:
                    if keyword in text_lower:
                        spam_score += 1
                
                # Calculate probability
                spam_probability = min(spam_score / 5.0, 1.0)  # Normalize to 0-1
                
                return [{
                    'label': 'SPAM' if spam_probability > 0.5 else 'HAM',
                    'score': spam_probability if spam_probability > 0.5 else 1 - spam_probability
                }]
        
        return RuleBasedClassifier()
    
    def create_sample_dataset(self) -> pd.DataFrame:
        """Create a comprehensive dataset with real spam patterns"""
        
        # Real spam call transcripts and patterns
        spam_texts = [
            # IRS/Tax scams
            "This is the IRS calling about your unpaid taxes. You must call back immediately or face arrest.",
            "Internal Revenue Service final notice. Your account will be closed if you don't respond.",
            "IRS legal department. There's a warrant for your arrest due to tax fraud.",
            "This is your final warning from the tax resolution center.",
            
            # Social Security scams
            "Your Social Security number has been suspended due to suspicious activity.",
            "Social Security Administration calling about fraudulent activity on your account.",
            "Your SSN will be blocked permanently if you don't verify immediately.",
            "Legal action will be taken against your Social Security number.",
            
            # Car warranty scams
            "Your car's extended warranty is about to expire. Press 1 to renew.",
            "Final notice about your vehicle's warranty expiration.",
            "Auto warranty department calling about your coverage ending today.",
            "Your car manufacturer warranty needs immediate renewal.",
            
            # Health insurance scams
            "You qualify for special health insurance with no pre-existing conditions.",
            "Medicare benefits department with important updates about your coverage.",
            "Health insurance marketplace calling about available plans.",
            "Your Medicare card needs to be replaced immediately.",
            
            # Tech support scams
            "Microsoft Windows support detected viruses on your computer.",
            "Apple security department about suspicious activity on your account.",
            "Your computer has been compromised. Call for immediate assistance.",
            "Windows defender has detected malware. Don't use your computer.",
            
            # Credit/Debt scams
            "Credit card services can lower your interest rate to zero percent.",
            "Debt consolidation program can eliminate your credit card debt.",
            "You've been approved for a loan of up to fifty thousand dollars.",
            "Credit monitoring service detected problems with your credit report.",
            
            # Prize/Lottery scams
            "Congratulations! You've won the Publishers Clearing House sweepstakes.",
            "You're the grand prize winner of our cash giveaway contest.",
            "Final notice: Claim your lottery winnings before they expire.",
            "You've won a free vacation to the Bahamas. Call to claim.",
            
            # Utility scams
            "Your electricity will be disconnected in 30 minutes for non-payment.",
            "Gas company calling about immediate disconnection of service.",
            "Your power bill is overdue. Service will be terminated today.",
            "Utility payment processing center with urgent notice.",
            
            # Charity scams
            "Veterans charity asking for donations to help wounded soldiers.",
            "Police benevolent association requesting contribution for fallen officers.",
            "Fire department fund drive for new equipment and training.",
            "Children's cancer research foundation seeking urgent donations.",
            
            # Romance/Lonely heart scams
            "I saw your profile online and would like to get to know you better.",
            "Lonely military soldier overseas looking for companionship.",
            "Attractive single person interested in meeting you for romance.",
            "Dating service with perfect matches in your area.",
            
            # Business opportunity scams
            "Make five thousand dollars a week working from home.",
            "Business opportunity requires no experience or investment.",
            "Guaranteed income of one hundred dollars per hour.",
            "Work from home envelope stuffing job opportunity.",
            
            # Robocall identifiers
            "Press 1 to speak with a representative about this urgent matter.",
            "Press 9 to be removed from our calling list.",
            "Stay on the line for an important message about your account.",
            "This call is being recorded for quality assurance purposes.",
            "Please hold while we connect you to the next available agent.",
            
            # Fake legal threats
            "Law enforcement will arrest you if you don't pay immediately.",
            "Legal action has been filed against you in federal court.",
            "Sheriff's department will serve papers at your residence.",
            "Avoid legal consequences by calling our settlement department.",
            
            # Immigration scams
            "Immigration services calling about your visa status.",
            "Deportation proceedings have been initiated against you.",
            "Green card lottery winner notification service.",
            "Citizenship and immigration services urgent notice.",
            
            # Investment scams
            "Stock market opportunity with guaranteed returns.",
            "Cryptocurrency investment with no risk and high profits.",
            "Real estate investment opportunity in prime locations.",
            "Gold and precious metals dealer with limited time offer.",
            
            # Energy/Solar scams
            "Government solar panel program for qualified homeowners.",
            "Free home energy audit and efficiency improvements.",
            "Utility company rebate program for new equipment installation.",
            "Energy savings program can cut your bills in half.",
        ]
        
        # Legitimate call patterns
        legitimate_texts = [
            # Doctor/Medical
            "This is Dr. Smith's office calling to confirm your appointment tomorrow at 2 PM.",
            "Medical center calling to remind you about your scheduled procedure.",
            "Pharmacy notification that your prescription is ready for pickup.",
            "Dental office calling to confirm your cleaning appointment next week.",
            "Hospital discharge coordinator with follow-up instructions.",
            
            # Family/Personal
            "Hi mom, just calling to check in and see how you're doing today.",
            "Hey, it's your neighbor. Your package was delivered to my house.",
            "This is your daughter calling from college. How are you?",
            "Hi dad, wanted to let you know I arrived safely at my destination.",
            "Your friend Sarah calling to catch up and make dinner plans.",
            
            # Business legitimate
            "This is John from ABC Company regarding your recent inquiry about our services.",
            "Human resources calling about your job application and interview.",
            "Insurance agent calling to discuss your policy renewal options.",
            "Bank calling to verify a recent transaction on your account.",
            "Real estate agent following up on the property you viewed.",
            
            # Service providers
            "Repair technician calling to schedule your appliance service appointment.",
            "Delivery driver calling because I can't find your address.",
            "Cable company technician confirming tomorrow's installation appointment.",
            "Plumber calling to let you know I'm running 15 minutes late.",
            "Auto mechanic calling to discuss repairs needed on your vehicle.",
            
            # Schools/Education
            "School nurse calling because your child has a fever.",
            "Principal's office calling about your child's academic achievement.",
            "Teacher calling to discuss your student's progress in class.",
            "College admissions office with information about your application.",
            "School transportation department about bus route changes.",
            
            # Government legitimate
            "County clerk's office calling about your jury duty service.",
            "DMV calling to schedule your driving test appointment.",
            "City hall calling about your permit application status.",
            "Library calling to notify you about overdue books.",
            "Voting registrar calling to confirm your polling location.",
            
            # Retail/Services
            "Store manager calling to let you know your order has arrived.",
            "Restaurant calling to confirm your reservation for tonight.",
            "Hotel calling to confirm your check-in details for next week.",
            "Dry cleaner calling to notify you about pickup ready.",
            "Auto dealer calling about your vehicle's scheduled maintenance.",
            
            # Financial legitimate
            "Credit union calling about your loan application approval.",
            "Financial advisor calling to discuss your investment portfolio.",
            "Accountant calling about your tax return preparation.",
            "Legitimate debt collector calling about a valid outstanding debt.",
            "Mortgage company calling about your refinancing application.",
            
            # Emergency/Urgent legitimate
            "Emergency contact calling because of a family situation.",
            "Work supervisor calling about an urgent project deadline.",
            "Veterinarian calling about your pet's test results.",
            "Home security company calling about alarm activation.",
            "Utility company calling about planned maintenance in your area.",
            
            # Appointment confirmations
            "Spa calling to confirm your massage appointment this Friday.",
            "Lawyer's office calling to reschedule your consultation.",
            "Contractor calling about starting your home renovation project.",
            "Personal trainer calling to confirm your workout session.",
            "Hair salon calling to confirm your styling appointment.",
        ]
        
        # Create balanced dataset
        data = []
        
        # Add spam examples
        for text in spam_texts:
            data.append({"text": text, "label": 1, "category": "spam"})
        
        # Add legitimate examples  
        for text in legitimate_texts:
            data.append({"text": text, "label": 0, "category": "legitimate"})
        
        # Add more variety by generating variations
        import random
        
        # Generate more spam variations
        spam_patterns = [
            "URGENT: {reason}. Call {phone} immediately!",
            "FINAL NOTICE: {threat}. Act now to avoid {consequence}.",
            "Congratulations! You've won {prize}. Call {phone} to claim.",
            "WARNING: {service} will be {action} unless you call {phone}.",
            "BREAKING: {opportunity} available. Limited time offer!",
        ]
        
        reasons = ["Your account is suspended", "Legal action pending", "Service termination", "Security breach"]
        threats = ["Your credit is at risk", "Immediate collection action", "Service disconnection", "Legal proceedings"]
        prizes = ["$10,000 cash", "a new car", "free vacation", "lottery jackpot"]
        services = ["electricity", "internet", "phone service", "credit card"]
        actions = ["disconnected", "terminated", "suspended", "cancelled"]
        consequences = ["arrest", "legal action", "service termination", "credit damage"]
        opportunities = ["Work from home job", "Investment opportunity", "Business partnership", "Easy money"]
        phones = ["+1-800-555-0123", "+1-888-555-9876", "+1-877-555-4567"]
        
        for _ in range(50):  # Generate 50 more spam examples
            pattern = random.choice(spam_patterns)
            text = pattern.format(
                reason=random.choice(reasons),
                threat=random.choice(threats),
                prize=random.choice(prizes),
                service=random.choice(services),
                action=random.choice(actions),
                consequence=random.choice(consequences),
                opportunity=random.choice(opportunities),
                phone=random.choice(phones)
            )
            data.append({"text": text, "label": 1, "category": "spam"})
        
        # Generate more legitimate variations
        legit_patterns = [
            "Hi {name}, this is {caller} from {company}. {purpose}",
            "Hello, {relation} calling about {topic}. Please call back.",
            "{service} calling to {action} for {date}.",
            "This is {title} {name} from {organization}. {message}",
        ]
        
        names = ["John", "Sarah", "Michael", "Lisa", "David", "Emily"]
        callers = ["Dr. Smith", "Manager Johnson", "Representative Wilson", "Agent Brown"]
        companies = ["ABC Company", "Medical Center", "First Bank", "Insurance Group"]
        purposes = ["regarding your appointment", "about your inquiry", "to discuss your account", "with important information"]
        relations = ["your neighbor", "your friend", "your colleague", "your family member"]
        topics = ["your package delivery", "dinner plans", "the meeting", "weekend plans"]
        services = ["Doctor's office", "Dentist office", "Repair service", "Delivery company"]
        actions = ["confirm your appointment", "schedule a visit", "update your information", "verify details"]
        dates = ["tomorrow", "next week", "this Friday", "Monday morning"]
        titles = ["Dr.", "Mr.", "Ms.", "Professor"]
        organizations = ["City Hospital", "State University", "Local Bank", "Community Center"]
        messages = ["regarding your recent visit", "about your application", "with test results", "to schedule follow-up"]
        
        for _ in range(50):  # Generate 50 more legitimate examples
            pattern = random.choice(legit_patterns)
            text = pattern.format(
                name=random.choice(names),
                caller=random.choice(callers),
                company=random.choice(companies),
                purpose=random.choice(purposes),
                relation=random.choice(relations),
                topic=random.choice(topics),
                service=random.choice(services),
                action=random.choice(actions),
                date=random.choice(dates),
                title=random.choice(titles),
                organization=random.choice(organizations),
                message=random.choice(messages)
            )
            data.append({"text": text, "label": 0, "category": "legitimate"})
        
        print(f"Created comprehensive dataset with {len(data)} samples")
        return pd.DataFrame(data)
    
    def load_or_create_dataset(self, csv_path: str = None) -> pd.DataFrame:
        """Load dataset from CSV or create sample data"""
        if csv_path and os.path.exists(csv_path):
            try:
                df = pd.read_csv(csv_path)
                print(f"Loaded dataset from {csv_path} with {len(df)} samples")
                return df
            except Exception as e:
                print(f"Error loading CSV: {e}")
        
        print("Creating sample dataset for training")
        return self.create_sample_dataset()
    
    def train_custom_model(self, csv_path: str = None) -> Dict[str, float]:
        """Train custom spam detection model"""
        print("Training custom spam detection model...")
        
        # Load dataset
        df = self.load_or_create_dataset(csv_path)
        
        # Prepare data
        X = df['text'].values
        y = df['label'].values
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Vectorize text
        self.vectorizer = TfidfVectorizer(
            max_features=5000,
            stop_words='english',
            ngram_range=(1, 2),
            lowercase=True
        )
        
        X_train_vectorized = self.vectorizer.fit_transform(X_train)
        X_test_vectorized = self.vectorizer.transform(X_test)
        
        # Train model
        self.model = LogisticRegression(random_state=42, max_iter=1000)
        self.model.fit(X_train_vectorized, y_train)
        
        # Evaluate
        y_pred = self.model.predict(X_test_vectorized)
        accuracy = accuracy_score(y_test, y_pred)
        
        print(f"Model trained with accuracy: {accuracy:.3f}")
        print("\nClassification Report:")
        print(classification_report(y_test, y_pred))
        
        # Save model
        self.save_model()
        
        return {
            "accuracy": accuracy,
            "train_samples": len(X_train),
            "test_samples": len(X_test)
        }
    
    def predict(self, text: str, threshold: float = 0.5) -> Dict[str, Any]:
        """
        Predict if text is spam
        
        Args:
            text: Input text to classify
            threshold: Confidence threshold for spam classification
        
        Returns:
            Dictionary with prediction results
        """
        if self.model_type == "huggingface" and self.model:
            try:
                result = self.model(text)
                
                # Handle different model output formats
                if isinstance(result, list) and len(result) > 0:
                    if isinstance(result[0], list):
                        # Model returns list of lists (multiple scores)
                        result = result[0]
                    
                    # Find spam/toxic prediction
                    spam_score = 0.0
                    for pred in result:
                        label = pred.get('label', '').upper()
                        score = pred.get('score', 0.0)
                        
                        if any(keyword in label for keyword in ['TOXIC', 'SPAM', 'NEGATIVE', '1']):
                            spam_score = max(spam_score, score)
                
                is_spam = spam_score > threshold
                
                return {
                    "is_spam": is_spam,
                    "confidence": spam_score,
                    "threshold": threshold,
                    "model_type": "huggingface",
                    "model_name": getattr(self, 'model_name', 'unknown')
                }
                
            except Exception as e:
                print(f"Hugging Face prediction error: {e}")
                # Fallback to rule-based
                return self._rule_based_prediction(text, threshold)
        
        elif self.model_type == "custom" and self.model and self.vectorizer:
            try:
                # Vectorize input
                text_vectorized = self.vectorizer.transform([text])
                
                # Get prediction probability
                prob = self.model.predict_proba(text_vectorized)[0]
                spam_probability = prob[1] if len(prob) > 1 else prob[0]  # Probability of spam class
                
                return {
                    "is_spam": spam_probability > threshold,
                    "confidence": spam_probability,
                    "threshold": threshold,
                    "model_type": "custom"
                }
            except Exception as e:
                print(f"Custom model prediction error: {e}")
                return self._rule_based_prediction(text, threshold)
        
        else:
            # Fallback to rule-based prediction
            return self._rule_based_prediction(text, threshold)
    
    def _rule_based_prediction(self, text: str, threshold: float = 0.5) -> Dict[str, Any]:
        """Fallback rule-based prediction"""
        try:
            # Create temporary rule-based classifier if needed
            if not hasattr(self, '_rule_classifier'):
                self._rule_classifier = self._create_rule_based_classifier()
            
            result = self._rule_classifier(text)
            spam_score = result[0]['score'] if result[0]['label'] == 'SPAM' else 1 - result[0]['score']
            
            return {
                "is_spam": spam_score > threshold,
                "confidence": spam_score,
                "threshold": threshold,
                "model_type": "rule-based"
            }
        except Exception as e:
            print(f"Rule-based prediction error: {e}")
            return {
                "is_spam": False, 
                "confidence": 0.0, 
                "threshold": threshold,
                "model_type": "fallback",
                "error": str(e)
            }
    
    def save_model(self):
        """Save trained model and vectorizer"""
        try:
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            
            if self.model_type == "custom":
                joblib.dump(self.model, self.model_path)
                joblib.dump(self.vectorizer, self.vectorizer_path)
                print(f"Model saved to {self.model_path}")
                print(f"Vectorizer saved to {self.vectorizer_path}")
        except Exception as e:
            print(f"Error saving model: {e}")
    
    def load_model(self):
        """Load saved model and vectorizer"""
        try:
            if os.path.exists(self.model_path) and os.path.exists(self.vectorizer_path):
                self.model = joblib.load(self.model_path)
                self.vectorizer = joblib.load(self.vectorizer_path)
                self.model_type = "custom"
                print("Loaded custom trained model")
                return True
        except Exception as e:
            print(f"Error loading model: {e}")
        return False
    
    def retrain_with_new_data(self, csv_path: str) -> Dict[str, Any]:
        """Retrain model with new CSV data"""
        try:
            if not os.path.exists(csv_path):
                return {"error": f"CSV file not found: {csv_path}"}
            
            # Load new data
            new_df = pd.read_csv(csv_path)
            
            # Validate required columns
            required_columns = ['text', 'label']
            if not all(col in new_df.columns for col in required_columns):
                return {"error": f"CSV must contain columns: {required_columns}"}
            
            # Load existing data if available
            existing_df = self.load_or_create_dataset()
            
            # Combine datasets
            combined_df = pd.concat([existing_df, new_df], ignore_index=True)
            combined_df = combined_df.drop_duplicates(subset=['text'])
            
            print(f"Retraining with {len(combined_df)} total samples")
            
            # Retrain model
            results = self.train_custom_model()
            results['new_samples'] = len(new_df)
            results['total_samples'] = len(combined_df)
            
            return results
            
        except Exception as e:
            return {"error": f"Retraining failed: {str(e)}"}

def main():
    """Main function for training and testing the model"""
    print("Spam Detection Model Training")
    print("=" * 40)
    
    # Try to use Hugging Face model first
    print("Attempting to load Hugging Face model...")
    hf_model = SpamDetectionModel("huggingface")
    
    if hf_model.model:
        print("Testing Hugging Face model:")
        test_texts = [
            "Congratulations! You've won $1000!",
            "Hi, this is John from work. How are you?"
        ]
        
        for text in test_texts:
            result = hf_model.predict(text)
            print(f"Text: {text}")
            print(f"Spam: {result['is_spam']}, Confidence: {result['confidence']:.3f}")
            print()
    
    # Train custom model
    print("Training custom model...")
    custom_model = SpamDetectionModel("custom")
    training_results = custom_model.train_custom_model()
    
    print("Training Results:", training_results)
    
    # Test custom model
    print("\nTesting custom model:")
    test_texts = [
        "Congratulations! You've won $1000! Call now!",
        "Hi mom, just calling to check in on you.",
        "FREE MONEY! Click here now!",
        "Your doctor appointment is tomorrow at 2 PM."
    ]
    
    for text in test_texts:
        result = custom_model.predict(text)
        print(f"Text: {text}")
        print(f"Spam: {result['is_spam']}, Confidence: {result['confidence']:.3f}")
        print()

if __name__ == "__main__":
    main()