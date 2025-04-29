# Fashion Content Agent

> Project: Fashion Content Agent, Python (Streamlit UI + OpenAI Vision/Content Integration)

![Image](https://github.com/user-attachments/assets/dd1da762-5dd1-48b7-a7a8-9d55891e7559)

## Overview

The Fashion Content Agent is an AI-powered application that automates the process of analyzing fashion images and generating boutique-quality product descriptions and marketing content.  
Designed especially for boutique stores offering Indian and Western styles, the agent leverages GPT-4o models to analyze uploaded images, infer style, materials, and key features, and produce ready-to-publish catalog metadata and social media content.

Built with Python, Streamlit, and OpenAI Vision APIs, this system helps boutiques scale their catalog creation and marketing operations quickly, efficiently, and responsibly.

---

## Key Features

-  **Vision Analysis**: Extract style, color, material, season, and key features from fashion images using GPT-4o model.
- **Marketing Content Generation**: Automatically generate boutique-style product titles, descriptions, captions, hashtags, and alt text.
- **Structured JSON Outputs**: Organize all extracted metadata and marketing content for easy catalog integration.
- **Google Sheets Integration**: Save generated outputs directly into a Google Sheet for management and publishing.
- **Performance Optimization**: Async processing, connection pooling, batching, and caching for efficient API usage.
- **Responsible AI Practices**: Clear user control, data privacy, and transparent processing.

---

## Architecture Diagram

<img width="1251" alt="Image" src="https://github.com/user-attachments/assets/a0697df4-718a-41fc-8c81-635432ac2da7" />

High-level architecture of the Fashion Content Generation Agent System. The system uses GPT-4o model for content and vision analysis, supported by a local file-based cache and persistent storage in Google Sheets. Responsible AI and workflow optimization modules ensure secure, efficient, and transparent processing.

## How It Works
1. User uploads one or more fashion images or provides image URLs via the Streamlit UI.
2. The agent analyzes each image using the VisionAgent (GPT-4o).
3. Based on the vision output, the ContentAgent generates product marketing content.
4. Outputs are structured into JSON format and saved into a Google Sheet.
5. Caching and optimization modules improve speed and prevent duplicate processing.

## Responsible AI module ensures monitoring, transparency, and secure logging.
_Technologies Used_
            • Python 3.10+
            • Streamlit (for the UI)
            • OpenAI GPT-4o API (for vision analysis and content generation)
            • Google Sheets API (for storage)
            • Local File-based Cache (for caching outputs)
            • Mermaid.js (for architecture diagrams)

## Responsible AI and Data Privacy

User data (image URLs and generated content) is only stored in user-selected Google Sheets.
No personal or private data is collected beyond what is needed for content generation.
Clear indicators and permissions for data usage.
Monitoring module captures logs and operations transparently.

## Setup Instructions
1. Clone the repository:
   ```bash
   git clone [repository-url]
   cd fashion-content-agent
   ```

2. Set up a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Install test dependencies (optional):
   ```bash
   pip install -r tests/requirements-test.txt
   ```

5. Set environment variables Create a .env file with:
   ```bash
      OPENAI_API_KEY=your_openai_key
      GOOGLE_CREDENTIALS_FILE=path/to/google-credentials.json
      GOOGLE_SHARE_EMAIL=your-google-account@email.com
   ```

6. Run the Streamlit application:
   ```bash
   streamlit run app.py
   ```

## Example Outputs
{
  "Title": "Blossom Dreams Indo-Western Dress",
  "Description": "Celebrate the season in a breezy Indo-western fusion crafted from lightweight georgette and hand-embroidered silk panels. A rose pink base blooms with emerald accents, perfect for spring festivities.",
  "Caption": "Spring into style 🌸✨ Meet our 'Blossom Dreams' dress — tradition with a modern twist! #BoutiqueFashion",
  "Hashtags": ["#IndoWestern", "#SpringStyle", "#BoutiqueFashion"],
  "Alt_text": "Rose pink Indo-western dress with emerald floral embroidery",
  "Platform": "Instagram",
  "Image URL":"https://drive.google.com/file/d/ldshfsjdfjsdbfjsdhfshdflshdlf/view?usp=sharing,
  "Key Features":"'floral embroidery', 'sheer full sleeves', 'statement choker and earrings'",
   "Generated At": "2025-04-28 17:35:59",
   "Vision Analysis": "{'style': '', 'colors': [], 'materials': ['], 'occasion': 'festive', 'season': 'festive season', 'key_features': [], 
    'brand_style': ''}"
}

## Future Work
Direct integration with Shopify for automated product listing
Multi-language marketing content generation
Accessory recommendation system based on outfit analysis
Instagram/Facebook auto-scheduling support
Expansion to use Azure Blob Storage / S3 for media persistence

## Recent Optimizations

### URL Handling Improvements
- **Smart URL Normalization**: Automatically converts different Google Drive URL formats to a consistent direct download format
- **Robust Duplicate Detection**: Compares normalized URLs to prevent duplicate entries regardless of URL format
  - Early duplicate check before processing
  - Clear user feedback for duplicate URLs
  - Normalized comparison of both current and existing URLs
  - Detailed debug logging for URL comparison process
- **Google Drive Integration**: Handles various Google Drive URL formats:
  - Sharing URLs (e.g., `drive.google.com/file/d/[ID]/view`)
  - Direct download URLs (e.g., `drive.google.com/uc?export=download&id=[ID]`)
- **URL Validation**: Enhanced validation for image URLs with proper error handling

### Testing Improvements
- **Enhanced Test Coverage**: Improved test suite with proper mocking of external services
- **URL Validation Mocking**: Added mocks for image URL validation to prevent actual HTTP requests during tests
- **Duplicate URL Testing**: Comprehensive test cases for duplicate URL detection and handling:
  - Test for basic duplicate detection
  - Test for duplicate in empty sheet
  - Test for duplicate in non-existent sheet
  - Test for error handling during duplicate check
- **Error Scenario Coverage**: Added tests for various error scenarios and edge cases
- **Async Test Support**: Proper async/await testing with pytest-asyncio

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
- **Duplicate Prevention**: Automatically checks and skips duplicate image URLs to prevent redundant entries, with support for:
  - Different URL formats (sharing vs. direct download)
  - Google Drive URLs
  - Case-insensitive matching
  - Normalized URL comparison

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

## Testing

### Running Tests
```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_main.py -v

# Run tests with coverage
python -m pytest tests/ --cov=. -v
```

### Test Structure
The test suite is organized into several key areas:
- **Main Agent Tests**: Testing the core FashionContentAgent functionality
- **Storage Tests**: Testing Google Sheets integration and duplicate handling
- **Cache Tests**: Testing caching mechanisms and performance optimizations
- **Validation Tests**: Testing input validation and error handling

### Test Features
- **Mocked Services**: All external services (OpenAI, Google Sheets) are properly mocked
- **Async Testing**: Uses pytest-asyncio for testing async functions
- **Error Scenarios**: Comprehensive testing of error cases and edge conditions
- **Duplicate Detection**: Tests for proper handling of duplicate image URLs
- **Input Validation**: Tests for URL validation and content format checking

### Best Practices
- Tests use proper fixtures and mocks to avoid external dependencies
- Each test focuses on a single piece of functionality
- Tests are deterministic and don't rely on external services
- Clear test names and documentation for maintainability
- Proper setup and teardown of test resources

## Usage

### 1. **Run the Application**:
```bash
streamlit run app.py
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
- `VISION_MODEL`: GPT-4o model name (default: "gpt-4o")
- `CONTENT_MODEL`: GPT-4o model name (default: "gpt-4o")
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

### Image URL Issues
- **Google Drive URLs**: The system automatically converts Google Drive sharing URLs to direct download URLs
- **Duplicate URLs**: The system checks for duplicates using normalized URLs to prevent redundant entries
- **URL Formats**: Supports various URL formats including:
  - Direct image URLs
  - Google Drive sharing URLs
  - Google Drive direct download URLs
- **Invalid URLs**: Clear error messages are provided for invalid or inaccessible image URLs

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