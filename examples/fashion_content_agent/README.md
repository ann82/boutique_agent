# Fashion Content Agent

An AI-powered system for analyzing fashion images and generating marketing content. The system uses GPT-4 Vision for image analysis and GPT-4 for content generation, with optimized API handling and async processing.

## Architecture Diagram

```mermaid
graph TD
    A[User (Streamlit Web UI)] -->|Image URL, Sheet Selection| B(FashionContentAgent)
    B --> C[VisionAgent (GPT-4 Vision)]
    B --> D[ContentAgent (GPT-4)]
    B --> E[GoogleSheetsStorage]
    E -->|Store/Read| F[(Google Sheets)]
    C -->|Vision Analysis| B
    D -->|Generated Content| B
    B -->|Results, Sheet Link| A
```

- **User** interacts with the Streamlit UI, providing an image URL and selecting/creating a Google Sheet.
- **FashionContentAgent** orchestrates the workflow: calls the VisionAgent, then the ContentAgent, and manages storage.
- **VisionAgent** uses GPT-4 Vision to analyze the image.
- **ContentAgent** uses GPT-4 to generate marketing content based on the vision analysis.
- **GoogleSheetsStorage** saves results to the selected Google Sheet.

## Recent Optimizations

### Performance Improvements
- **Async/Await Support**: All API calls now use async/await for better performance
- **Connection Pooling**: Implemented connection pooling with aiohttp for efficient API requests
- **Parallel Processing**: Vision analysis and content generation now run in parallel
- **Optimized JSON Parsing**: Improved JSON extraction and validation
- **Batch Processing**: Google Sheets operations now support batch processing
- **Rate Limiting**: Enhanced async rate limiting with proper concurrency control
- **Duplicate Prevention**: Automatic checking and skipping of duplicate image URLs

### Memory Optimization
- **Resource Management**: Proper cleanup of resources and connections
- **Optimized Data Structures**: Removed redundant data structures
- **Efficient String Operations**: Optimized string handling and JSON operations

### Error Handling
- **Enhanced Error Recovery**: Improved error handling and retry mechanisms
- **Better Error Messages**: More descriptive error messages for debugging
- **Graceful Shutdown**: Proper cleanup on application shutdown

### Code Structure
- **Type Hints**: Added comprehensive type hints throughout the codebase
- **Documentation**: Improved docstrings and code comments
- **Modular Design**: Better separation of concerns and component isolation

## Responsible AI & Security

### Data Privacy
- User-provided image URLs and generated content are only stored in the user's selected Google Sheet and are not shared with third parties.
- No personal data is collected or stored beyond what the user provides for content generation.
- All API keys and credentials are managed via environment variables and never hardcoded.

### User Control & Transparency
- Users can review, edit, and delete their content in Google Sheets at any time.
- The Streamlit UI makes it clear what data is being processed and where it is stored.
- Users can select or create new sheets for each session, ensuring separation of data as desired.

### Bias & Fairness
- The system uses OpenAI's GPT-4 models, which are trained on diverse datasets but may still reflect societal biases.
- Users are encouraged to review and edit generated content for fairness, inclusivity, and appropriateness before publishing.
- The project maintainers welcome feedback and contributions to improve fairness and reduce bias.

### Security Best Practices
- All secrets (API keys, credentials) are stored in a `.env` file and never committed to source control.
- Google Sheets access is limited to the service account and explicitly shared users.
- The codebase avoids direct file uploads and only processes public image URLs.
- Dependencies are managed via `requirements.txt` and should be kept up to date.

## Features

- **Fast Image Analysis**: Optimized vision processing with efficient API batching
- **Smart Content Generation**: Context-aware content creation for fashion marketing
- **Async Processing**: High-performance async implementation with connection pooling
- **Rate Limiting**: Built-in rate limiting to prevent API quota issues
- **Google Sheets Integration**: Automatic content storage in Google Sheets
- **Dynamic Sheet Selection**: Choose or create a Google Sheet for each session
- **Custom Sheet Naming**: Name your sheets (e.g., "Fashion Content Agent - Tharang") and reuse them
- **Clean, Minimal Columns**: Only the most relevant fields are stored, with clear, capitalized headers
- **Optimized Performance**: Latest optimizations for faster processing and better resource usage
- **Smart Sheet Management**: Reuses existing sheets instead of creating new ones for the same name
- **Sheet Caching**: Efficient caching of spreadsheet IDs for faster access
- **Automatic Headers**: New sheets are created with proper column headers and formatting
- **Key Features Column**: Separate column for storing notable features and accessories
- **Duplicate Prevention**: Automatically checks and skips duplicate image URLs to prevent redundant entries

## Sheet Columns

Newly created Google Sheets will have the following columns (with the first character capitalized):

- Title
- Description
- Caption
- Hashtags
- Alt Text
- Platform
- Image URL
- Key Features
- Vision Analysis

The headers are formatted with:
- Dark gray background
- White text
- Bold font
- Centered alignment
- Font size 12

## Performance Optimizations

- **Connection Pooling**: Efficient connection reuse with keep-alive
- **Request Batching**: Smart batching of API requests
- **Async Processing**: Pure async/await implementation
- **Timeout Handling**: Configurable timeouts for all operations
- **Error Recovery**: Robust error handling and retries
- **Parallel Processing**: Concurrent execution of vision analysis and content generation
- **Resource Management**: Efficient handling of connections and resources
- **Memory Optimization**: Reduced memory footprint and improved garbage collection
- **Sheet Caching**: Efficient caching of spreadsheet IDs for faster access
- **Smart Sheet Reuse**: Reuses existing sheets instead of creating new ones

## Setup

1. **Install Dependencies**:
```bash
pip install -r requirements.txt
```

2. **Environment Variables**:
Create a `.env` file with:
```
OPENAI_API_KEY=your_openai_api_key
GOOGLE_CREDENTIALS_FILE=path_to_credentials.json
GOOGLE_SHARE_EMAIL=your_email@domain.com
```

3. **Google Sheets Setup**:
- Create a Google Cloud Project
- Enable Google Sheets API
- Create service account credentials
- Download credentials JSON file
- Share your Google Sheet with the service account email

## Usage

### 1. **Run the Application**:
```bash
streamlit run main.py
```

### 2. **Sheet Selection and Creation**
- At the top of the Streamlit app, use the **Google Sheet Selection** section:
  - **Select an existing sheet** from the dropdown (all sheets starting with "Fashion Content Agent" are listed).
  - **Or enter a new sheet name** (e.g., `Fashion Content Agent - Tharang`) and click **Use Selected Sheet** to create and use it.
- The app will use your selected or newly created sheet for all content operations.

### 3. **Input Image URL**
- Enter the URL of a fashion image when prompted.
- The system will:
  - Analyze the image
  - Generate marketing content
  - Store results in your selected Google Sheet
  - Display the output and a direct link to your sheet in the app

## Configuration

Key configuration options in `config.py`:
- `VISION_MODEL`: GPT-4 Vision model name
- `CONTENT_MODEL`: GPT-4 model name
- `DEFAULT_TONE`: Default content tone
- `DEFAULT_PLATFORM`: Default social platform
- `RATE_LIMITS`: API rate limits
- `API_TIMEOUT`: Timeout for API requests
- `API_MAX_RETRIES`: Maximum number of retry attempts
- `CONNECTION_POOL_SIZE`: Size of the connection pool
- `GOOGLE_SHEETS_BATCH_SIZE`: Number of rows to process in one batch
- `CACHE_ENABLED`: Enable/disable caching
- `CACHE_TTL`: Cache time-to-live in seconds
- `CACHE_MAX_SIZE`: Maximum number of cached items

## Troubleshooting

### Google Sheets Link Points to Wrong Sheet
- Make sure you have selected or created the correct sheet in the **Google Sheet Selection** section before generating content.
- The app now always uses the selected or newly created sheet for saving and linking.

### Sheet Not Visible or Not Editable
- Ensure your email is set in `GOOGLE_SHARE_EMAIL` in your `.env` file.
- The service account must have permission to share and edit the sheet.
- If you want to be the owner, both the service account and your email must be in the same Google Workspace domain, and admin must allow ownership transfer.

### Other Common Issues
- **API errors**: Check your API keys and credentials.
- **Image not loading**: Make sure the image URL is public and direct (for Google Drive, use the direct download format).
- **Duplicate entries**: The system automatically skips duplicate image URLs. If you need to process the same image again, use a different URL or contact support.

## Sheet Management
- You can create as many sheets as you want, and switch between them at any time using the UI.
- All new content will be saved to the currently selected sheet.
- The system now reuses existing sheets with the same name instead of creating new ones.
- Sheet IDs are cached for faster access and better performance.
- New sheets are automatically created with proper column headers.

---

Made with ❤️ by the Fashion Content Agent team

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License