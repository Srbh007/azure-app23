Sure, here's a suggested README file for your project:
markdownCopy# Azure App

This is a Flask-based web application that allows users to search for information and get responses from an AI assistant. The application uses Azure OpenAI API to generate responses to user queries.

## Features

1. **User Authentication**: Users can register and login to the application.
2. **Chat History**: Users can view their previous chat history and search for past queries.
3. **PDF Previews**: If a PDF file related to the user's query exists, the application can display a preview of the PDF.
4. **Embedded Websites**: The application can provide a link to a relevant website for certain keywords.
5. **AI-powered Responses**: The application uses the Azure OpenAI API to generate responses to user queries.

## Installation

1. Clone the repository:
git clone https://github.com/Srbh007/AZURE-APP.git
Copy2. Install the required dependencies:
pip install -r requirements.txt
Copy3. Create a `.env` file in the project root directory and add the following environment variables:
AZURE_OPENAI_API_KEY=<your_azure_openai_api_key>
Copy4. Run the application:
python app.py
Copy5. Access the application in your web browser at `http://localhost:5000`.

## Configuration

The application's configuration is stored in the `config.py` file. You can modify the following settings:

- `AZURE_OPENAI_API_KEY`: Your Azure OpenAI API key.
- `AZURE_OPENAI_ENDPOINT`: The endpoint URL for your Azure OpenAI deployment.
- `DEPLOYMENT_NAME`: The name of your Azure OpenAI deployment.
- `API_VERSION`: The API version to use for the Azure OpenAI API.
- `PDF_FOLDER`: The path to the folder containing PDF files related to your application.

## Usage

1. Register a new user or login with an existing account.
2. Use the search bar to enter a query.
3. The application will display the response from the AI assistant, along with any relevant PDF previews or embedded website links.
4. The chat history will be stored for the logged-in user, and can be accessed from the "Ghat" page.

## Contributing

If you find any issues or want to contribute to the project, please feel free to create a new issue or submit a pull request on the [GitHub repository](https://github.com/Srbh007/AZURE-APP).

## License

This project is licensed under the [MIT License](LICENSE).
