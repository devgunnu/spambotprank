Decoy – Fooling scammers, so you don’t have to

Decoy flips the script on scams. Instead of just blocking calls, it wastes scammers’ time while protecting and educating users worldwide.

🚀 Features

AI-Powered Random Personalities: 4 time-wasting personas randomly assigned per call

Natural Voice AI: Realistic conversations using Vapi with 11labs voices

Real-time Call Handling: Automatic answering and conversation management via Twilio

Analytics Dashboard: Track calls, durations, and persona effectiveness

Database Storage: SQLite for call logs and analytics

Random Personality Per Call: Each call keeps a consistent personality throughout

📋 Prerequisites

Python 3.8+

Twilio account with Voice capabilities

Vapi API key

ngrok
 (for local development webhooks)

🛠️ Installation

Clone the repository

git clone https://github.com/devgunnu/decoy.git
cd decoy


Install dependencies

pip install -r requirements.txt


Set up environment variables
Create a .env file in the project root:

TWILIO_ACCOUNT_SID=your_twilio_account_sid_here
TWILIO_AUTH_TOKEN=your_twilio_auth_token_here
TWILIO_PHONE_NUMBER=your_twilio_phone_number
VAPI_API_KEY=your_vapi_api_key_here
NGROK_TUNNEL_URL=https://your-ngrok-url.ngrok.io
DATABASE_URL=sqlite+aiosqlite:///./database.db


Set up Vapi integration

Register your Twilio phone number with Vapi

Assign the "Random Personality Per Call" assistant

Configure Twilio webhook to point to Vapi:

https://api.vapi.ai/twilio/inbound_call

▶️ Running the Application

Start the FastAPI server

python run.py


Access the dashboard
Open your browser: http://localhost:8000

Test the system
Call your Twilio number to see Decoy in action!

📊 Dashboard Features

Real-time Analytics: Calls today, average duration, total time wasted

Call History: Browse recent calls with details

Persona Effectiveness: See which personas waste the most scammer time

System Status: Monitor health of the app

Call Details: View full conversation transcripts

🎭 Available Personalities

Chatty Neighbor – Talkative, loves sharing stories about local events

Confused Elderly – Forgetful, repeats questions, asks for clarification

Overly Enthusiastic – Excited about everything, asks endless questions

Distracted Parent – Always multitasking, mentions children and chores

🔧 API Endpoints

GET / – Dashboard interface

GET /health – Health check

POST /webhook/voice – Twilio voice webhook

POST /webhook/speech – Twilio speech recognition webhook

POST /webhook/status – Twilio call status webhook

GET /api/analytics/summary – Analytics summary

GET /api/calls – Recent calls list

GET /api/calls/{call_id} – Specific call details

🗄️ Database Schema

calls: Call information (duration, persona, status)

conversations: Individual conversation exchanges

analytics: Aggregated analytics data

🚨 Important Notes

Ensure compliance with local laws for call recording and automation

Be mindful of Twilio and Vapi rate limits

Monitor usage to control costs

Apply proper data retention policies for logs

🛡️ Security Considerations

Keep API keys out of version control

Use HTTPS in production

Add authentication to the dashboard

Encrypt sensitive data when needed

🐛 Troubleshooting

Calls not being answered → Check Twilio webhook setup and Vapi registration

No voice output → Verify Vapi assistant configuration and voice settings

AI responses missing → Confirm Vapi API key and assistant mapping

Database errors → Check SQLite file permissions

📈 Future Enhancements

More advanced personalities

Call recording and playback

Smarter persona selection via ML

Mobile app interface

Real-time notifications

Scheduled or automated calls

📄 License

This project is for educational and entertainment purposes. Use responsibly and in compliance with applicable laws.

✨ Decoy – fooling scammers, so you don’t have to.

**Disclaimer**: This tool is designed to waste spam callers' time and should only be used for legitimate purposes. Always comply with local laws and regulations regarding automated phone systems.
