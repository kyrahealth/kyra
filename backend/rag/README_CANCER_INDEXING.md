# Cancer Research UK Indexing System

This system extracts and embeds all cancer-related content from the Cancer Research UK website into a vector database for use with the RAG (Retrieval-Augmented Generation) system.

## Overview

The Cancer Research UK indexing system consists of several components:

1. **`build_cancer_research_index.py`** - Basic indexer for Cancer Research UK sitemap
2. **`advanced_cancer_indexer.py`** - Advanced indexer with better filtering and processing
3. **`run_cancer_indexing.py`** - Simple runner script
4. **`test_cancer_indexing.py`** - Test script to verify the indexing process

## Features

### Advanced Indexer (`advanced_cancer_indexer.py`)

- **Multi-format sitemap support**: Handles both HTML and XML sitemaps
- **Intelligent filtering**: Only processes cancer-related content using keyword matching
- **Robust error handling**: Retry logic and graceful failure handling
- **Progress tracking**: Detailed logging and statistics
- **Caching**: Saves downloaded HTML files to avoid re-downloading
- **Rate limiting**: Respectful delays between requests

### Key Features

- **Cancer-specific filtering**: Uses comprehensive keyword lists to identify relevant content
- **Dual collection support**: Works alongside existing NHS data
- **Enhanced text processing**: Better HTML-to-text conversion with title extraction
- **Statistics tracking**: Saves detailed processing statistics to JSON file

## Usage

### Prerequisites

1. Ensure you have the required dependencies installed:
   ```bash
   pip install requests beautifulsoup4 chromadb llama-index openai python-dotenv
   ```

2. Set your OpenAI API key:
   ```bash
   export OPENAI_API_KEY="your-api-key-here"
   ```

### Running the Indexer

#### Option 1: Use the runner script (recommended)
```bash
cd backend/rag
python run_cancer_indexing.py
```

#### Option 2: Run the advanced indexer directly
```bash
cd backend/rag
python advanced_cancer_indexer.py
```

#### Option 3: Run the basic indexer
```bash
cd backend/rag
python build_cancer_research_index.py
```

### Testing the Results

After indexing, you can test the results:

```bash
cd backend/rag
python test_cancer_indexing.py
```

This will:
- Verify that documents were indexed correctly
- Test RAG integration with sample queries
- Show processing statistics

## Configuration

### Key Configuration Options

In `advanced_cancer_indexer.py`, you can modify:

- **`MAX_PAGES`**: Maximum number of pages to process (default: 2000)
- **`REQUEST_DELAY`**: Delay between requests in seconds (default: 0.5)
- **`TIMEOUT`**: Request timeout in seconds (default: 30)
- **`CANCER_KEYWORDS`**: List of keywords to identify cancer-related content
- **`CANCER_CATEGORIES`**: URL categories to focus on

### Cancer Keywords

The system uses these keywords to identify cancer-related content:

```python
CANCER_KEYWORDS = [
    'cancer', 'tumour', 'tumor', 'oncology', 'carcinoma', 'sarcoma', 
    'leukemia', 'lymphoma', 'melanoma', 'screening', 'diagnosis',
    'treatment', 'symptoms', 'prevention', 'research', 'clinical',
    'therapy', 'chemotherapy', 'radiotherapy', 'surgery', 'biopsy',
    'metastasis', 'remission', 'prognosis', 'staging', 'grade',
    'mammogram', 'colonoscopy', 'endoscopy', 'biomarker', 'immunotherapy'
]
```

### Cancer Categories

The system focuses on these URL categories:

```python
CANCER_CATEGORIES = [
    'about-cancer', 'cancer-types', 'causes', 'symptoms', 'diagnosis',
    'treatment', 'living-with-cancer', 'research', 'clinical-trials',
    'prevention', 'screening', 'statistics', 'information'
]
```

## Output

### Files Generated

1. **HTML files**: Downloaded pages saved in `backend/rag/html/`
2. **Vector database**: ChromaDB files in `backend/rag/chroma_db/`
3. **Statistics**: Processing stats saved to `backend/rag/processing_stats.json`

### Collections Created

- **`cancer_research_docs`**: Cancer Research UK content
- **`nhs_docs`**: Existing NHS content (preserved)

## Integration with RAG System

The updated RAG service (`backend/app/services/rag.py`) now:

1. **Searches both collections**: NHS and Cancer Research UK
2. **Combines results**: Merges and ranks results from both sources
3. **Enhanced filtering**: Better domain-specific filtering
4. **Improved context**: More comprehensive context for medical queries

### Example Usage

```python
from app.services.rag import get_rag_context_weighted

# Search for cancer-related information
context, score, sources = get_rag_context_weighted(
    "What are the symptoms of breast cancer?"
)

if context:
    print(f"Found relevant information (score: {score:.3f})")
    print(f"Sources: {sources}")
else:
    print("No relevant information found")
```

## Monitoring and Debugging

### Logging

The system provides detailed logging:

- **URL extraction**: Shows how many URLs were found in sitemaps
- **Filtering progress**: Shows which URLs are being checked
- **Download progress**: Shows download status for each page
- **Processing status**: Shows text extraction and embedding progress
- **Final statistics**: Shows summary of processed documents

### Statistics File

After indexing, check `processing_stats.json` for detailed statistics:

```json
{
  "total_urls_found": 1500,
  "relevant_urls_found": 450,
  "successfully_processed": 420,
  "failed_urls": ["url1", "url2"],
  "final_embedded_count": 420,
  "timestamp": 1703123456.789
}
```

## Troubleshooting

### Common Issues

1. **OpenAI API Key not set**
   ```
   ❌ OPENAI_API_KEY is NOT set – export it or put it in .env first.
   ```
   Solution: Set your OpenAI API key as an environment variable.

2. **Network timeouts**
   ```
   ⚠️ Attempt 1 failed for https://...: timeout
   ```
   Solution: Increase `TIMEOUT` value or check network connectivity.

3. **No relevant URLs found**
   ```
   ❌ No relevant URLs found
   ```
   Solution: Check if the sitemap URL is accessible or modify keyword lists.

4. **Memory issues with large datasets**
   Solution: Reduce `MAX_PAGES` or process in smaller batches.

### Performance Tips

1. **Use caching**: The system caches downloaded HTML files to avoid re-downloading
2. **Adjust delays**: Modify `REQUEST_DELAY` to balance speed vs. server load
3. **Monitor progress**: Check the console output for detailed progress information
4. **Test incrementally**: Use the test script to verify results before full deployment

## Security and Ethics

- **Rate limiting**: Built-in delays to respect server resources
- **Robots.txt compliance**: Manual implementation of respectful crawling
- **Error handling**: Graceful failure handling to avoid overwhelming servers
- **Data usage**: Only processes publicly available content

## Future Enhancements

Potential improvements:

1. **Incremental updates**: Only process new/changed pages
2. **Better filtering**: Use ML models for content classification
3. **Multi-language support**: Process content in different languages
4. **Real-time updates**: Set up automated periodic indexing
5. **Content validation**: Verify medical accuracy of indexed content

## Support

For issues or questions:

1. Check the troubleshooting section above
2. Review the processing statistics in `processing_stats.json`
3. Test with the verification script
4. Check console output for detailed error messages

The system is designed to be robust and provide detailed feedback to help diagnose and resolve any issues. 