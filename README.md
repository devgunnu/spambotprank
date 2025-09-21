Decoy - Fooling scammers, so you don't have to 

Decoy flips the script on scams: instead of just blocking calls, it wastes scammers’ time while protecting and educating users worldwide.

🚀 Features

AI-Powered Random Personalities: 4 different time-wasting personalities that are randomly selected per call

Natural Voice AI: Uses Vapi with 11labs voice for realistic conversations

Real-time Call Handling: Automatic call answering and conversation management via Twilio

Analytics Dashboard: Track calls, duration, and effectiveness of different personas

Database Storage: SQLite database for call logs and analytics

Random Personality Per Call: Each call gets a random personality that stays consistent throughout

📋 Prerequisites

Python 3.8+

Twilio Account with Voice capabilities

Vapi API key

ngrok (for local development webhooks)

🛠️ Installation

Clone the repository

git clone https://github.com/devgunnu/decoy.git
cd decoy


Install dependencies

pip install -r requirements.txt


Set up environment variables
Create a .env file in the root directory:

TWILIO_ACCOUNT_SID=your_twilio_account_sid_here
TWILIO_AUTH_TOKEN=your_twilio_auth_token_here
TWILIO_PHONE_NUMBER=your_twilio_phone_number
VAPI_API_KEY=your_vapi_api_key_here
NGROK_TUNNEL_URL=https://your-ngrok-url.ngrok.io
DATABASE_URL=sqlite+aiosqlite:///./database.db


Set up Vapi integration

Register your Twilio phone number with Vapi

Assign the "Random Personality Per Call" assistant

Configure Twilio webhook to point to Vapi: https://api.vapi.ai/twilio/inbound_call

🚀 Running the Application

Start the FastAPI server

python run.py


Access the dashboard
Open your browser and go to: http://localhost:8000

Test the system
Call your Twilio phone number to test Decoy in action!

📊 Dashboard Features

Real-time Analytics: View calls today, average duration, and time wasted

Call History: Browse recent calls with details

Persona Effectiveness: See which personas are most effective

System Status: Monitor application health

Call Details: View full conversation transcripts

🎭 Available Personalities (Random Per Call)

Chatty Neighbor: Very talkative, loves sharing stories about neighbors and local events

Confused Elderly: Slightly forgetful, needs things repeated, asks for clarification constantly

Overly Enthusiastic: Extremely excited about everything, asks lots of questions with high energy

Distracted Parent: Constantly multitasking, talks about children and family activities

🔧 API Endpoints

GET / - Dashboard interface

GET /health - Health check

POST /webhook/voice - Twilio voice webhook

POST /webhook/speech - Twilio speech recognition webhook

POST /webhook/status - Twilio call status webhook

GET /api/analytics/summary - Analytics summary

GET /api/calls - Recent calls list

GET /api/calls/{call_id} - Specific call details

🗄️ Database Schema

calls: Stores call information (duration, persona, status)

conversations: Stores individual conversation exchanges

analytics: Stores aggregated analytics data

🚨 Important Notes

Legal Compliance: Ensure you comply with local laws regarding call recording and automated systems

Rate Limiting: Be mindful of API rate limits for Twilio and Vapi

Cost Management: Monitor usage to avoid unexpected charges

Privacy: Consider data retention policies for call logs

🛡️ Security Considerations

Keep API keys secure and never commit them to version control

Use HTTPS in production

Implement proper authentication for the dashboard

Consider data encryption for sensitive information

🐛 Troubleshooting

Calls not being answered: Check Vapi phone number registration and Twilio webhook configuration

Voice not working: Verify Vapi assistant configuration and voice settings

AI responses not working: Check Vapi API key and assistant configuration

Database errors: Ensure SQLite file permissions are correct

📈 Future Enhancements

Add more sophisticated personalities

Implement call recording and playback

Add machine learning for personality selection

Create mobile app interface

Add real-time notifications

Implement call scheduling and automation

📄 License

This project is for educational and entertainment purposes. Please use responsibly and in compliance with applicable laws.

✨ Decoy – fooling scammers, so you don’t have to.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues and enhancement requests.

---

**Disclaimer**: This tool is designed to waste spam callers' time and should only be used for legitimate purposes. Always comply with local laws and regulations regarding automated phone systems.
