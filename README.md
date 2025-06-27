# Evilginx API Wrapper

A Flask-based REST API wrapper for Evilginx, providing programmatic access to Evilginx phishing toolkit functionality. This wrapper enables automated management of phishlets, lures, and session capture through a clean HTTP interface.

## ⚠️ **Legal Disclaimer**

**This tool is intended for authorized security testing and educational purposes only.** 

- ✅ **Legal Use Cases**: Penetration testing with proper authorization, security research, educational demonstrations
- ❌ **Illegal Use**: Unauthorized phishing attacks, credential theft, malicious activities
- 📋 **Your Responsibility**: Ensure you have explicit written permission before testing against any systems
- 🏛️ **Compliance**: Follow all applicable laws and regulations in your jurisdiction

**The authors assume no responsibility for misuse of this software.**

## 🚀 Features

- **RESTful API**: Clean HTTP interface for Evilginx operations
- **Phishlet Management**: Create, configure, and manage phishing templates
- **Lure Generation**: Automated creation and management of phishing URLs
- **Session Monitoring**: Track and retrieve captured authentication sessions
- **Token Authentication**: Secure API access with bearer token authentication
- **Structured Output**: JSON responses with parsed data from Evilginx output
- **Logging**: Comprehensive logging for debugging and audit trails
- **HTTPS Support**: Built-in SSL/TLS support for secure communication

## 📦 Installation

### Prerequisites
- Python 3.7+
- Evilginx installed and configured
- Root/sudo access (required for Evilginx)
- Valid SSL certificates (for production)

### Setup
```bash
# Clone the repository
git clone https://github.com/yourusername/evilginx-api-wrapper.git
cd evilginx-api-wrapper

# Install Python dependencies
pip install flask pexpect

# Set environment variables
export EVILGINX_API_TOKEN="your_secure_api_token_here"

# Ensure Evilginx is installed and accessible
which evilginx
# Should return: /usr/local/bin/evilginx
```

### Configuration
```bash
# Create required directories
mkdir -p /app/phishlets
mkdir -p /app/logs

# Copy your phishlets to the phishlets directory
cp /path/to/your/phishlets/* /app/phishlets/

# Set proper permissions
chmod +x evilginx_api.py
```

## 🔧 Configuration

### Environment Variables
| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `EVILGINX_API_TOKEN` | API authentication token | `dev_token_replace_in_production` | Yes |
| `EVILGINX_BIN` | Path to Evilginx binary | `/usr/local/bin/evilginx` | No |
| `EVILGINX_PHISHLETS_PATH` | Path to phishlets directory | `/app/phishlets` | No |

### Production Configuration
```bash
# Generate a secure API token
export EVILGINX_API_TOKEN=$(openssl rand -hex 32)

# Use production-ready SSL certificates
# Place your SSL cert and key files appropriately
```

## 💻 Usage

### Starting the API Server
```bash
# Development mode (with auto-reload)
python evilginx_api.py

# Production mode (recommended)
gunicorn -w 4 -b 0.0.0.0:8443 --certfile=cert.pem --keyfile=key.pem evilginx_api:app
```

### Authentication
All API endpoints (except `/health`) require authentication via Bearer token:

```bash
# Set your API token
export API_TOKEN="your_secure_api_token_here"

# Include in requests
curl -H "Authorization: Bearer $API_TOKEN" https://localhost:8443/api/phishlets
```

## 📡 API Endpoints

### Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "ok"
}
```

### Execute Custom Commands
```http
POST /api/commands
```

**Request Body:**
```json
{
  "commands": [
    "phishlets",
    "lures", 
    "sessions"
  ]
}
```

**Response:**
```json
{
  "commands_ran": ["phishlets", "lures", "sessions"],
  "transcript": "Evilginx command output...",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Phishlet Management

#### List Phishlets
```http
GET /api/phishlets
```

**Response:**
```json
{
  "phishlets": [
    {
      "name": "office365",
      "status": "enabled",
      "visibility": "visible", 
      "hostname": "login.company-portal.com",
      "unauth_url": "https://login.company-portal.com"
    }
  ],
  "raw_output": "Raw evilginx output...",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### Create/Configure Phishlet
```http
POST /api/phishlets
```

**Request Body:**
```json
{
  "name": "test-campaign",
  "template": "office365",
  "domain": "secure-login.com"
}
```

**Response:**
```json
{
  "name": "test-campaign",
  "template": "office365",
  "domain": "secure-login.com",
  "hostname": "test-campaign.secure-login.com",
  "success": true,
  "created_at": "2024-01-15T10:30:00Z",
  "raw_output": "Evilginx configuration output..."
}
```

### Lure Management

#### List Lures
```http
GET /api/lures
```

**Response:**
```json
{
  "lures": [
    {
      "id": "1",
      "phishlet": "office365",
      "hostname": "login.secure-portal.com", 
      "path": "/AbCdEf",
      "redirector": "",
      "redirect_url": "https://office.com",
      "paused": "false",
      "og": ""
    }
  ],
  "raw_output": "Raw evilginx output...",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### Create Lure
```http
POST /api/lures
```

**Request Body:**
```json
{
  "phishlet_name": "office365"
}
```

**Response:**
```json
{
  "id": "2",
  "phishlet": "office365",
  "hostname": "login.secure-portal.com",
  "path": "/XyZ123",
  "url": "https://login.secure-portal.com/XyZ123",
  "created_at": "2024-01-15T10:30:00Z",
  "raw_output": "Lure creation output..."
}
```

### Session Management

#### List Captured Sessions
```http
GET /api/sessions
```

**Response:**
```json
{
  "sessions": [
    {
      "id": "1",
      "raw": "[1] [user@company.com] [password123] [tokens] @ 192.168.1.100",
      "tokens": {
        "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIs...",
        "refresh_token": "1//04_refresh_token_here...",
        "session_id": "abc123def456"
      }
    }
  ],
  "raw_output": "Raw sessions output...",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## 🛠️ Examples

### Python Client Example
```python
import requests
import json

class EvilginxAPI:
    def __init__(self, base_url, api_token):
        self.base_url = base_url
        self.headers = {
            'Authorization': f'Bearer {api_token}',
            'Content-Type': 'application/json'
        }
    
    def list_phishlets(self):
        response = requests.get(f"{self.base_url}/api/phishlets", 
                              headers=self.headers, verify=False)
        return response.json()
    
    def create_campaign(self, name, template, domain):
        data = {
            "name": name,
            "template": template, 
            "domain": domain
        }
        response = requests.post(f"{self.base_url}/api/phishlets",
                               headers=self.headers, json=data, verify=False)
        return response.json()
    
    def create_lure(self, phishlet_name):
        data = {"phishlet_name": phishlet_name}
        response = requests.post(f"{self.base_url}/api/lures",
                               headers=self.headers, json=data, verify=False)
        return response.json()
    
    def get_sessions(self):
        response = requests.get(f"{self.base_url}/api/sessions",
                              headers=self.headers, verify=False)
        return response.json()

# Usage example
api = EvilginxAPI("https://localhost:8443", "your_api_token")

# Set up a phishing campaign
campaign = api.create_campaign("finance-test", "office365", "secure-finance.com")
print(f"Campaign created: {campaign['hostname']}")

# Create a lure
lure = api.create_lure("office365")
print(f"Phishing URL: {lure['url']}")

# Check for captured sessions
sessions = api.get_sessions()
print(f"Captured {len(sessions['sessions'])} sessions")
```

### Bash/cURL Examples
```bash
#!/bin/bash

API_TOKEN="your_api_token_here"
BASE_URL="https://localhost:8443"

# List current phishlets
curl -k -H "Authorization: Bearer $API_TOKEN" \
     "$BASE_URL/api/phishlets"

# Create a new phishing campaign
curl -k -H "Authorization: Bearer $API_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"name":"test","template":"office365","domain":"secure-login.com"}' \
     "$BASE_URL/api/phishlets"

# Generate a phishing lure
curl -k -H "Authorization: Bearer $API_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"phishlet_name":"office365"}' \
     "$BASE_URL/api/lures"

# Check captured sessions
curl -k -H "Authorization: Bearer $API_TOKEN" \
     "$BASE_URL/api/sessions"
```

## 🔒 Security Considerations

### API Security
- **Strong Authentication**: Use cryptographically secure API tokens
- **HTTPS Only**: Never run without SSL/TLS in production
- **Token Rotation**: Regularly rotate API tokens
- **Access Logging**: Monitor API access and usage patterns
- **Rate Limiting**: Consider implementing rate limiting for production use

### Operational Security
- **Isolated Environment**: Run in isolated containers or VMs
- **Network Segmentation**: Limit network access to necessary services only
- **Log Management**: Securely store and monitor logs
- **Regular Updates**: Keep Evilginx and dependencies updated

### Legal and Ethical Guidelines
- **Written Authorization**: Always obtain explicit written permission
- **Scope Limitations**: Stay within authorized testing scope
- **Data Handling**: Securely handle any captured credentials
- **Responsible Disclosure**: Follow responsible disclosure practices

## 🚨 Troubleshooting

### Common Issues

**"Evilginx not found" error**
```bash
# Verify Evilginx installation
which evilginx

# Check if it's in the expected location
ls -la /usr/local/bin/evilginx

# Update the EVILGINX_BIN environment variable if needed
export EVILGINX_BIN="/path/to/your/evilginx"
```

**"Permission denied" when starting**
```bash
# Evilginx typically requires root privileges
sudo python evilginx_api.py

# Or run with appropriate user permissions
sudo -u evilginx python evilginx_api.py
```

**"SSL certificate errors"**
```bash
# For development, use self-signed certificates
# For production, use proper SSL certificates

# Generate self-signed cert for testing
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes
```

**"API token authentication failed"**
```bash
# Verify your token is set correctly
echo $EVILGINX_API_TOKEN

# Check the Authorization header format
curl -H "Authorization: Bearer $API_TOKEN" ...
```

### Debug Mode
```bash
# Enable debug logging
export FLASK_DEBUG=1
python evilginx_api.py

# Check application logs
tail -f /app/logs/evilginx_repl.log
```

### Evilginx Communication Issues
```bash
# Test Evilginx directly
/usr/local/bin/evilginx -p /app/phishlets -developer

# Check if phishlets are loading correctly
ls -la /app/phishlets/

# Verify network connectivity and DNS resolution
```

## 🏗️ Architecture

### Components
- **Flask API Server**: REST API endpoints and request handling
- **Pexpect Interface**: Communication with Evilginx CLI
- **Output Parser**: Structured data extraction from Evilginx output
- **Authentication Layer**: Token-based API security
- **Logging System**: Comprehensive audit and debug logging

### Data Flow
1. **Client Request** → API Endpoint
2. **Authentication** → Token Validation  
3. **Command Translation** → Evilginx CLI Commands
4. **Execution** → Pexpect Process Management
5. **Output Parsing** → Structured JSON Response
6. **Response** → Client

### Scalability Considerations
- **Process Management**: Consider process pooling for high load
- **Caching**: Cache frequently accessed data (phishlet lists, etc.)
- **Load Balancing**: Multiple API instances behind a load balancer
- **Database Integration**: Store session data in persistent storage

## 🤝 Contributing

### Development Setup
```bash
git clone https://github.com/yourusername/evilginx-api-wrapper.git
cd evilginx-api-wrapper

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install development dependencies
pip install flask pexpect pytest black flake8

# Run tests
pytest tests/

# Format code
black evilginx_api.py

# Lint code  
flake8 evilginx_api.py
```

### Areas for Improvement
- **Error Handling**: Enhanced error detection and recovery
- **Output Parsing**: More robust parsing of Evilginx output
- **Rate Limiting**: API rate limiting and throttling
- **WebSocket Support**: Real-time session monitoring
- **Database Integration**: Persistent storage for campaigns and sessions
- **GUI Interface**: Web-based management interface

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚖️ Legal and Ethical Use

### Authorized Testing Only
This tool should only be used for:
- **Authorized penetration testing** with explicit written consent
- **Security research** in controlled environments  
- **Educational purposes** with proper supervision
- **Red team exercises** within organizational boundaries

### Prohibited Uses
- Unauthorized access to systems or accounts
- Credential theft or identity fraud
- Any malicious or illegal activities
- Testing without explicit written permission

### Best Practices
- Obtain written authorization before any testing
- Clearly define scope and boundaries
- Securely handle any captured data
- Follow responsible disclosure practices
- Comply with all applicable laws and regulations

## 🔗 Related Tools

- **[Evilginx](https://github.com/kgretzky/evilginx2)**: The core phishing toolkit
- **[GoPhish](https://getgophish.com/)**: Alternative phishing framework
- **[Social-Engineer Toolkit](https://github.com/trustedsec/social-engineer-toolkit)**: Social engineering framework
- **[King Phisher](https://github.com/rsmusllp/king-phisher)**: Phishing campaign toolkit
- **[Modlishka](https://github.com/drk1wi/Modlishka)**: Reverse proxy phishing tool

## 📞 Support

For issues, questions, or contributions:

1. **Check existing issues** on GitHub
2. **Review the troubleshooting section** above
3. **Create a detailed issue** with:
   - Error messages and logs
   - Steps to reproduce
   - Environment details (OS, Python version, Evilginx version)
   - Expected vs. actual behavior

## 🏆 Acknowledgments

- **Evilginx developers** for the core phishing toolkit
- **Flask community** for the web framework
- **Security research community** for methodologies and best practices
- **Pexpect developers** for the process automation library

---

**Remember: With great power comes great responsibility. Use this tool ethically and legally.** ⚖️🔒
