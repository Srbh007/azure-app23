import os
from dotenv import load_dotenv
import secrets

# Load environment variables from the .env file
load_dotenv()

class Config:
    # General Flask settings
    SECRET_KEY = secrets.token_hex(16)
    DEBUG = os.environ.get('FLASK_ENV') != 'production'

    # Database configuration
    if os.environ.get('FLASK_ENV') == 'production':
        # Use /home/data directory which is writable in Azure
        INSTANCE_PATH = '/home/data/instance'
        SQLALCHEMY_DATABASE_URI = f'sqlite:///{INSTANCE_PATH}/site.db'
        UPLOAD_FOLDER = '/home/data/uploads'
    else:
        # In development (local), use the instance folder in the root project directory
        INSTANCE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
        SQLALCHEMY_DATABASE_URI = f'sqlite:///{INSTANCE_PATH}/site.db'
        UPLOAD_FOLDER = 'uploads'

    # SQLAlchemy settings
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,  # Enable connection pool pre-ping
        'pool_recycle': 3600,   # Recycle connections every hour
    }

    # Azure OpenAI API settings (Loaded from .env file)
    AZURE_OPENAI_API_KEY = os.getenv('AZURE_OPENAI_API_KEY')
    AZURE_OPENAI_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT')
    DEPLOYMENT_NAME = os.getenv('DEPLOYMENT_NAME')
    API_VERSION = "2024-05-01-preview"

    # PDF folder path
    if os.environ.get('FLASK_ENV') == 'production':
        PDF_FOLDER = '/home/data/pdfs'
    else:
        PDF_FOLDER = 'data'

    # Additional settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'pdf', 'txt', 'doc', 'docx'}

    # Flask session settings
    SESSION_TYPE = 'filesystem'
    SESSION_FILE_DIR = os.path.join(INSTANCE_PATH, 'flask_session')
    PERMANENT_SESSION_LIFETIME = 1800  # 30 minutes

    # Logging configuration
    LOG_FILE = os.path.join(INSTANCE_PATH, 'app.log')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_LEVEL = 'INFO'

    @staticmethod
    def init_app(app):
        """Initialize application configuration"""
        # Create necessary directories
        os.makedirs(app.config['INSTANCE_PATH'], exist_ok=True)
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        os.makedirs(app.config['PDF_FOLDER'], exist_ok=True)
        os.makedirs(app.config['SESSION_FILE_DIR'], exist_ok=True)

        # Set up file permissions in production
        if os.environ.get('FLASK_ENV') == 'production':
            try:
                # Set directory permissions
                for directory in [app.config['INSTANCE_PATH'], 
                                app.config['UPLOAD_FOLDER'],
                                app.config['PDF_FOLDER'],
                                app.config['SESSION_FILE_DIR']]:
                    if os.path.exists(directory):
                        os.chmod(directory, 0o777)

                # Set database file permissions
                db_path = os.path.join(app.config['INSTANCE_PATH'], 'site.db')
                if os.path.exists(db_path):
                    os.chmod(db_path, 0o666)
            except Exception as e:
                app.logger.error(f"Error setting permissions: {str(e)}")