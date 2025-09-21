#!/bin/bash

# Spam Detection Server - External Access Setup Script
# This script helps configure your server for external access

echo "🚀 Spam Detection Server - External Access Setup"
echo "=================================================="

# Get current IP information
LOCAL_IP=$(hostname -I | awk '{print $1}')
PUBLIC_IP=$(curl -s ifconfig.me 2>/dev/null || echo "Unable to determine")

echo ""
echo "📍 Network Information:"
echo "   Local IP:  $LOCAL_IP"
echo "   Public IP: $PUBLIC_IP"
echo "   Port:      5000"
echo ""

# Check if server is running
if curl -s http://localhost:5000/health > /dev/null 2>&1; then
    echo "✅ Server is running locally"
else
    echo "❌ Server is not running. Start with: python app.py"
    exit 1
fi

# Test network access
if curl -s http://$LOCAL_IP:5000/health > /dev/null 2>&1; then
    echo "✅ Server accessible via network IP"
else
    echo "⚠️  Server not accessible via network IP - check firewall"
fi

echo ""
echo "🔧 Setup Instructions:"
echo ""

# Firewall instructions
echo "1. Configure Firewall (if needed):"
echo "   # UFW (Ubuntu/Debian):"
echo "   sudo ufw allow 5000"
echo ""
echo "   # Firewalld (CentOS/RHEL/Fedora):"
echo "   sudo firewall-cmd --permanent --add-port=5000/tcp"
echo "   sudo firewall-cmd --reload"
echo ""
echo "   # iptables:"
echo "   sudo iptables -A INPUT -p tcp --dport 5000 -j ACCEPT"
echo ""

# Production deployment
echo "2. Production Deployment:"
echo "   # Install gunicorn for production:"
echo "   pip install gunicorn"
echo ""
echo "   # Run with gunicorn (production):"
echo "   gunicorn -w 4 -b 0.0.0.0:5000 app:create_app()"
echo ""
echo "   # Or use systemd service (recommended):"
echo "   sudo cp spam-detection.service /etc/systemd/system/"
echo "   sudo systemctl enable spam-detection"
echo "   sudo systemctl start spam-detection"
echo ""

# Access URLs
echo "3. Access URLs:"
echo "   Local:    http://localhost:5000"
echo "   Network:  http://$LOCAL_IP:5000"
if [ "$PUBLIC_IP" != "Unable to determine" ]; then
    echo "   External: http://$PUBLIC_IP:5000"
fi
echo ""

# API Testing
echo "4. Test External Access:"
echo "   # Health check:"
echo "   curl http://$LOCAL_IP:5000/health"
echo ""
echo "   # Spam detection:"
echo "   curl -X POST http://$LOCAL_IP:5000/api/layer1/check_spam \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"From\": \"+18004419593\"}'"
echo ""

# Security recommendations
echo "🔒 Security Recommendations:"
echo "   - Use HTTPS in production (reverse proxy with nginx/apache)"
echo "   - Implement rate limiting"
echo "   - Use authentication for sensitive endpoints"
echo "   - Monitor access logs"
echo "   - Keep dependencies updated"
echo ""

echo "🎉 Setup complete! Your spam detection server is ready for external access."