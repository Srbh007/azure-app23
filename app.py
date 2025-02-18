import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import requests
import os
import PyPDF2
import re
import openai
from azure.identity import DefaultAzureCredential
from flask_migrate import Migrate


app = Flask(__name__, static_folder='static')
app.config.from_object('config.Config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

from sqlalchemy import inspect

def initialize_database():
    """Initialize database with proper permissions"""
    with app.app_context():
        try:
            # Ensure instance directory exists
            os.makedirs(app.config['INSTANCE_PATH'], exist_ok=True)
            logger.info(f"Created instance directory at {app.config['INSTANCE_PATH']}")

            # Set directory permissions
            os.chmod(app.config['INSTANCE_PATH'], 0o777)
            logger.info("Set instance directory permissions")
            
            # Create necessary directories
            for directory in [app.config['PDF_FOLDER'], app.config['UPLOAD_FOLDER']]:
                os.makedirs(directory, exist_ok=True)
                os.chmod(directory, 0o777)
                logger.info(f"Created and set permissions for {directory}")
            
            # Initialize database
            db_path = os.path.join(app.config['INSTANCE_PATH'], 'site.db')
            if not os.path.exists(db_path):
                db.create_all()
                logger.info(f"Created database at {db_path}")
                os.chmod(db_path, 0o666)
                logger.info("Set database file permissions")
            else:
                logger.info("Database already exists")
            
            # Verify database using SQLAlchemy inspect
            inspector = inspect(db.engine)
            if not inspector.has_table("users"):  # Check if "users" table exists
                db.create_all()
                logger.info("Database tables created successfully.")

            return True
        except Exception as e:
            logger.error(f"Database initialization error: {str(e)}")
            logger.exception("Detailed traceback:")
            return False


# Initialize database
if not initialize_database():
    logger.error("Failed to initialize database")
    if os.environ.get('FLASK_ENV') == 'production':
        raise RuntimeError("Database initialization failed in production")

# OpenAI Configuration with error handling
try:
    openai.api_type = "azure"
    openai.api_key = app.config['AZURE_OPENAI_API_KEY']
    openai.api_base = app.config['AZURE_OPENAI_ENDPOINT']
    openai.api_version = app.config['API_VERSION']
    DEPLOYMENT_NAME = app.config['DEPLOYMENT_NAME']
    logger.info("OpenAI configuration loaded successfully")
except Exception as e:
    logger.error(f"Error loading OpenAI configuration: {str(e)}")
    raise

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    email = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(200), nullable=False)
    chats = db.relationship('Chat', backref='user', lazy=True)

class Chat(db.Model):
    __tablename__ = 'chats'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    query = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text, nullable=False)
    pdf_preview = db.Column(db.Boolean, default=False)
    embedded_website = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

def clean_response(text):
    text = re.sub(r'[\*\#]', '', text)
    return text.strip()
# Your existing keyword_links dictionary
keyword_links = {
    "Arduino": ["https://blog.arduino.cc/", "https://www.instructables.com/howto/Arduino/"],
    "Bluetooth Controlled Robot Car": ["https://circuitdigest.com/bluetooth-projects", "https://www.electronicshub.org/bluetooth-controlled-car-using-arduino/"],
    "IoT": ["https://www.iotforall.com/", "https://www.hackster.io/iot/projects"],
    "Capacitor": ["https://www.allaboutcircuits.com/textbook/direct-current/chpt-13/capacitors/", "https://www.electronics-tutorials.ws/capacitor/cap_1.html"],
    "Robotics": ["https://www.robotshop.com/community/blog", "https://robohub.org/"],
    "Robotics Algorithms": ["https://towardsdatascience.com/tagged/robotics", "https://blogs.mathworks.com/robotics/"],
    "Circuit": ["https://www.electronicshub.org/", "https://circuitdigest.com/"],
    "Lead Acid Battery": ["https://batteryuniversity.com/article/bu-201-lead-acid-battery", "https://www.sciencedirect.com/topics/engineering/lead-acid-battery"],
    "Electrolytic Capacitors": ["https://www.electronics-tutorials.ws/capacitor/cap_7.html", "https://www.eevblog.com/"],
    "Ceramic Capacitors": ["https://www.electronics-tutorials.ws/capacitor/cap_3.html", "https://components101.com/articles/ceramic-capacitor-types-and-applications"],
    "Electrolytic vs. Ceramic Capacitors": ["https://www.electronics-notes.com/articles/electronic_components/capacitors/capacitor-types-ceramic-electrolytic-tantalum.php", "https://www.arrow.com/en/research-and-events/articles/electrolytic-vs-ceramic-capacitors"],
    "Node MCU": ["https://randomnerdtutorials.com/tag/nodemcu/", "https://maker.pro/esp8266/tutorials"],
    "Lithium Ion Battery": ["https://batteryuniversity.com/learn/article/lithium_based_batteries", "https://www.electronics-notes.com/articles/electronic_components/battery-technology/lithium-ion-li-ion.php"],
    "Line Follower Robot": ["https://www.robotshop.com/community/forum/t/line-follower-robots/27408", "https://www.instructables.com/howto/line+follower+robot/"],
    "Home Automation": ["https://www.home-assistant.io/blog/", "https://circuitdigest.com/home-automation-projects"],
    "ESP8266": ["https://randomnerdtutorials.com/esp8266-web-server/", "https://www.electronicwings.com/nodemcu/esp8266"],
    "capacitor":["https://www.allaboutcircuits.com/textbook/direct-current/chpt-13/capacitors/", "https://www.electronics-tutorials.ws/capacitor/cap_1.html"],
     "arduino": ["https://blog.arduino.cc/", "https://www.instructables.com/howto/Arduino/"],
    "bluetooth controlled robot car": ["https://circuitdigest.com/bluetooth-projects", "https://www.electronicshub.org/bluetooth-controlled-car-using-arduino/"],
    "iot": ["https://www.iotforall.com/", "https://www.hackster.io/iot/projects"],
    "capacitor": ["https://www.allaboutcircuits.com/textbook/direct-current/chpt-13/capacitors/", "https://www.electronics-tutorials.ws/capacitor/cap_1.html"],
    "robotics": ["https://www.robotshop.com/community/blog", "https://robohub.org/"],
    "robotics algorithms": ["https://towardsdatascience.com/tagged/robotics", "https://blogs.mathworks.com/robotics/"],
    "circuit": ["https://www.electronicshub.org/", "https://circuitdigest.com/"],
    "lead acid battery": ["https://batteryuniversity.com/article/bu-201-lead-acid-battery", "https://www.sciencedirect.com/topics/engineering/lead-acid-battery"],
    "electrolytic capacitors": ["https://www.electronics-tutorials.ws/capacitor/cap_7.html", "https://www.eevblog.com/"],
    "ceramic capacitors": ["https://www.electronics-tutorials.ws/capacitor/cap_3.html", "https://components101.com/articles/ceramic-capacitor-types-and-applications"],
    "electrolytic vs. ceramic capacitors": ["https://www.electronics-notes.com/articles/electronic_components/capacitors/capacitor-types-ceramic-electrolytic-tantalum.php", "https://www.arrow.com/en/research-and-events/articles/electrolytic-vs-ceramic-capacitors"],
    "node mcu": ["https://randomnerdtutorials.com/tag/nodemcu/", "https://maker.pro/esp8266/tutorials"],
    "lithium ion battery": ["https://batteryuniversity.com/learn/article/lithium_based_batteries", "https://www.electronics-notes.com/articles/electronic_components/battery-technology/lithium-ion-li-ion.php"],
    "line follower robot": ["https://www.robotshop.com/community/forum/t/line-follower-robots/27408", "https://www.instructables.com/howto/line+follower+robot/"],
    "home automation": ["https://www.home-assistant.io/blog/", "https://circuitdigest.com/home-automation-projects"],
    "esp8266": ["https://randomnerdtutorials.com/esp8266-web-server/", "https://www.electronicwings.com/nodemcu/esp8266"],
    "capacitor":["https://www.allaboutcircuits.com/textbook/direct-current/chpt-13/capacitors/", "https://www.electronics-tutorials.ws/capacitor/cap_1.html"],
     "bluetooth controlled robot car": ["https://circuitdigest.com/bluetooth-projects", "https://www.electronicshub.org/bluetooth-controlled-car-using-arduino/"],
    "iot": ["https://www.iotforall.com/", "https://www.hackster.io/iot/projects"],
    "capacitors": ["https://www.allaboutcircuits.com/textbook/direct-current/chpt-13/capacitors/", "https://www.electronics-tutorials.ws/capacitor/cap_1.html"],
    "robo": ["https://www.robotshop.com/community/blog", "https://robohub.org/"],
    "robo algo": ["https://towardsdatascience.com/tagged/robotics", "https://blogs.mathworks.com/robotics/"],
    "circuits": ["https://www.electronicshub.org/", "https://circuitdigest.com/"],
    "lead  battery": ["https://batteryuniversity.com/article/bu-201-lead-acid-battery", "https://www.sciencedirect.com/topics/engineering/lead-acid-battery"],
    "electric capacitors": ["https://www.electronics-tutorials.ws/capacitor/cap_7.html", "https://www.eevblog.com/"],
    "ceramic": ["https://www.electronics-tutorials.ws/capacitor/cap_3.html", "https://components101.com/articles/ceramic-capacitor-types-and-applications"],
    "electrolytic vs. ceramic": ["https://www.electronics-notes.com/articles/electronic_components/capacitors/capacitor-types-ceramic-electrolytic-tantalum.php", "https://www.arrow.com/en/research-and-events/articles/electrolytic-vs-ceramic-capacitors"],
    "nodemcu": ["https://randomnerdtutorials.com/tag/nodemcu/", "https://maker.pro/esp8266/tutorials"],
    "lithium battery": ["https://batteryuniversity.com/learn/article/lithium_based_batteries", "https://www.electronics-notes.com/articles/electronic_components/battery-technology/lithium-ion-li-ion.php"],
    "line follow robot": ["https://www.robotshop.com/community/forum/t/line-follower-robots/27408", "https://www.instructables.com/howto/line+follower+robot/"],
    "automatic home": ["https://www.home-assistant.io/blog/", "https://circuitdigest.com/home-automation-projects"],
    "chip": ["https://randomnerdtutorials.com/esp8266-web-server/", "https://www.electronicwings.com/nodemcu/esp8266"],
    "capacitor types":["https://www.allaboutcircuits.com/textbook/direct-current/chpt-13/capacitors/", "https://www.electronics-tutorials.ws/capacitor/cap_1.html"],

}


@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')

            # Input validation
            if not all([username, email, password]):
                return render_template('register.html', error="All fields are required")
            
            # Email format validation
            if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                return render_template('register.html', error="Invalid email format")
            
            # Check if user exists
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                return render_template('register.html', error="Email already registered")

            # Create new user
            password_hash = generate_password_hash(password)
            new_user = User(username=username, email=email, password=password_hash)
            
            # Log database path and permissions
            db_path = os.path.join(app.config['INSTANCE_PATH'], 'site.db')
            logger.info(f"Database path: {db_path}")
            if os.path.exists(db_path):
                logger.info(f"Database file permissions: {oct(os.stat(db_path).st_mode)[-3:]}")
            
            db.session.add(new_user)
            db.session.commit()
            
            logger.info(f"User registered successfully: {email}")
            return redirect(url_for('login'))

        except Exception as e:
            db.session.rollback()
            logger.error(f"Registration error: {str(e)}")
            logger.exception("Detailed traceback:")
            return render_template('register.html', error="Registration failed. Please try again.")

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    try:
        if request.method == 'POST':
            logger.info("Login POST method called.")  # DEBUG LOG 1

            email = request.form['email']
            password = request.form['password']

            logger.info(f"Form data received: email={email}, password={password}")  # DEBUG LOG 2

            user = User.query.filter_by(email=email).first()
            logger.info(f"User query result: {user}")  # DEBUG LOG 3

            if user and check_password_hash(user.password, password):
                session['user_id'] = user.id
                logger.info(f"User logged in successfully: {email}")  # DEBUG LOG 4
                return redirect(url_for('ghat'))
            
            logger.warning(f"Failed login attempt: email={email}")  # DEBUG LOG 5
            return render_template('login.html', error="Invalid credentials. Please try again.")
    except Exception as e:
        logger.error(f"Error in login route: {str(e)}")  # DEBUG LOG 6
        return render_template('login.html', error="An error occurred during login. Please try again.")
    return render_template('login.html')


@app.route('/health')
def health_check():
    try:
        # Try to query the database
        User.query.first()
        db_path = os.path.join(app.config['INSTANCE_PATH'], 'site.db')
        
        health_data = {
            'status': 'healthy',
            'database': 'connected',
            'database_path': db_path,
            'instance_path': app.config['INSTANCE_PATH'],
            'permissions': {
                'instance_dir': oct(os.stat(app.config['INSTANCE_PATH']).st_mode)[-3:],
                'database': oct(os.stat(db_path).st_mode)[-3:] if os.path.exists(db_path) else 'not_found',
                'pdf_folder': oct(os.stat(app.config['PDF_FOLDER']).st_mode)[-3:],
                'upload_folder': oct(os.stat(app.config['UPLOAD_FOLDER']).st_mode)[-3:]
            }
        }
        
        return jsonify(health_data)
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'database_path': app.config['SQLALCHEMY_DATABASE_URI'],
            'instance_path': app.config['INSTANCE_PATH']
        }), 500

@app.route('/ghat')
def ghat():
    if 'user_id' in session:
        return render_template('ghat.html')
    return redirect(url_for('login'))

@app.route('/chat', methods=['GET', 'POST'])
def chat():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    
    try:
        if request.method == 'POST':
            query = request.form.get('query', '').strip()
            if not query:
                return jsonify({'error': 'Query cannot be empty'}), 400
                
            response_data = process_search_query(query, user_id)
            return jsonify(response_data)
            
        else:
            query = request.args.get('query', '')
            chat_history = db.session.query(Chat).filter(Chat.user_id == user_id).order_by(Chat.timestamp.desc()).all()
            
            if query:
                response_data = process_search_query(query, user_id)
                return render_template('chat.html', 
                                    chat_history=chat_history,
                                    current_query=query,
                                    current_response=response_data)
            
            return render_template('chat.html', chat_history=chat_history)
            
    except Exception as e:
        logger.error(f"Error in chat route: {str(e)}")
        if request.method == 'POST':
            return jsonify({'error': 'An error occurred processing your request'}), 500
        return render_template('chat.html', error="An error occurred. Please try again.")

def process_search_query(query, user_id):
    try:
        response_data = {"pdf_embed_url": "", "embedded_website": "", "ai_response": ""}

        # Check for PDF
        pdf_path = os.path.join(app.config['PDF_FOLDER'], f"{query}.pdf")
        if os.path.exists(pdf_path):
            response_data["pdf_embed_url"] = url_for('serve_pdf', filename=f"{query}.pdf")
        
        # Check for embedded website
        query_lower = query.lower()
        if query_lower in keyword_links:
            response_data["embedded_website"] = keyword_links[query_lower][0]
        
        # Get AI response
        if query:
            headers = {
                "Content-Type": "application/json",
                "api-key": openai.api_key
            }
            json_body = {
                "messages": [
                    {"role": "system", "content": "You are an AI assistant that helps people find information."},
                    {"role": "user", "content": query}
                ],
                "max_tokens": 800,
                "temperature": 0.7,
                "top_p": 0.95,
                "frequency_penalty": 0,
                "presence_penalty": 0
            }
            try:
                azure_response = requests.post(
                    f"{openai.api_base}openai/deployments/{DEPLOYMENT_NAME}/chat/completions?api-version={openai.api_version}",
                    headers=headers,
                    json=json_body
                )
                if azure_response.status_code == 200:
                    response_content = azure_response.json()
                    clean_text = clean_response(response_content['choices'][0]['message']['content'])
                    response_data["ai_response"] = clean_text
                else:
                    logger.error(f"OpenAI API error: {azure_response.status_code}")
                    response_data["ai_response"] = f"Error: {azure_response.status_code}"
            except Exception as e:
                logger.error(f"Error generating OpenAI response: {str(e)}")
                response_data["ai_response"] = "There was an error generating the response. Please try again later."

        # Store in chat history
        new_chat = Chat(user_id=user_id, query=query, response=response_data["ai_response"])
        db.session.add(new_chat)
        db.session.commit()

        return response_data
    except Exception as e:
        logger.error(f"Error in process_search_query: {str(e)}")
        return {"pdf_embed_url": "", "embedded_website": "", "ai_response": "An error occurred processing your request."}

@app.route('/pdfs/<filename>')
def serve_pdf(filename):
    try:
        return send_from_directory(app.config['PDF_FOLDER'], filename)
    except FileNotFoundError:
        logger.warning(f"PDF not found: {filename}")
        return "PDF not found.", 404

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    logger.info("User logged out")
    return redirect(url_for('login'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)