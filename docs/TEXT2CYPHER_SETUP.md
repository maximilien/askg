# Text2Cypher Setup Guide

This guide explains how to set up the text2cypher functionality to convert natural language queries into Cypher queries using OpenAI's GPT-4o-mini model.

## Overview

The text2cypher functionality enhances the MCP server search by:
- Converting natural language queries into optimized Cypher queries
- Using OpenAI's GPT-4o-mini model for intelligent query understanding
- Providing intelligent fallback to keyword-based search when LLM queries are too restrictive
- Improving search relevance and accuracy with text-first scoring
- Ensuring users always get relevant results regardless of query complexity

## Setup Instructions

### 1. Get OpenAI API Key

1. Visit [OpenAI Platform](https://platform.openai.com/api-keys)
2. Sign in or create an account
3. Create a new API key
4. Copy the API key (it starts with `sk-`)

### 2. Set Environment Variable

You can set the API key in several ways:

#### Option A: Create .env file (Recommended)
Create a `.env` file in the project root:
```bash
# OpenAI API Configuration
OPENAI_API_KEY=your_actual_api_key_here

# Optional: Override default model
# OPENAI_MODEL=gpt-4o-mini

# Optional: Set custom temperature for text-to-cypher conversion
# TEXT2CYPHER_TEMPERATURE=0.1
```

#### Option B: Set environment variable directly
```bash
export OPENAI_API_KEY=your_actual_api_key_here
```

#### Option C: Set in your shell profile
Add to `~/.bashrc`, `~/.zshrc`, or equivalent:
```bash
export OPENAI_API_KEY=your_actual_api_key_here
```

### 3. Install Dependencies

The required dependencies are already included in `requirements.txt` and `pyproject.toml`:

```bash
pip install openai python-dotenv
```

Or using uv:
```bash
uv add openai python-dotenv
```

## Usage

Once set up, the text2cypher functionality will automatically:

1. **Convert queries**: Natural language queries are converted to Cypher using GPT-4o-mini
2. **Optimize search**: LLM-generated queries are more intelligent and context-aware
3. **Intelligent fallback**: When LLM queries are too restrictive or return no results, automatically falls back to keyword-based search
4. **Text-first relevance**: Prioritizes actual text matches over popularity scores for better accuracy
5. **Log details**: Search metadata includes information about the conversion method and fallback usage

### Example Queries

The system can now handle complex queries like:

- **Simple**: "Find database servers"
- **Complex**: "Find popular AI servers that can process images and have high download counts"
- **Specific**: "Show me file system servers that support both read and write operations"
- **Contextual**: "What are the best monitoring tools for cloud services?"
- **Crypto-related**: "Find crypto servers", "popular servers for crypto"
- **Mixed complexity**: "What are the best cryptocurrency servers?"

**Query Processing Examples:**
- **"crypto"** → Returns crypto-related servers (crypto-mcp-server, gibber-mcp, armor-crypto-mcp)
- **"popular servers for crypto"** → Falls back to keyword search, returns crypto-related servers
- **"Find crypto servers"** → Falls back to keyword search, returns crypto-related servers
- **"database servers"** → Returns database-related servers (prisma, blog, etc.)

## Configuration Options

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | Required | Your OpenAI API key |
| `OPENAI_MODEL` | `gpt-4o-mini` | Model to use for conversion |
| `TEXT2CYPHER_TEMPERATURE` | `0.1` | Temperature for LLM responses |

### Model Selection

The system uses `gpt-4o-mini` by default, which provides:
- Fast response times
- Good query understanding
- Cost-effective pricing
- Reliable performance

## Testing

Run the tests to verify the setup:

```bash
pytest tests/test_text2cypher.py -v
```

## Troubleshooting

### Common Issues

1. **"OpenAI API key not found"**
   - Ensure the API key is set in environment variables
   - Check that the `.env` file is in the project root
   - Verify the key starts with `sk-`

2. **"OpenAI library not available"**
   - Install the OpenAI library: `pip install openai`
   - Check that the installation was successful

3. **API errors**
   - Verify your API key is valid
   - Check your OpenAI account has sufficient credits
   - Ensure you have access to the GPT-4o-mini model

4. **Fallback to keyword search**
   - This is normal behavior when LLM is unavailable
   - Check logs for specific error messages
   - Verify network connectivity to OpenAI

5. **Cypher syntax errors**
   - The system automatically cleans markdown formatting from LLM responses
   - If you see syntax errors, check that the LLM is returning valid Cypher
   - The system falls back to keyword search if Cypher generation fails

6. **Queries returning same results**
   - The system now uses text-first relevance scoring to ensure different queries return different results
   - Fallback queries require actual text matches (`text_score > 0`)
   - Popularity scores are heavily reduced to prevent overwhelming text relevance

### Logs

The system logs detailed information about:
- Query conversion attempts
- Cypher query generation
- Fallback scenarios
- Search metadata

Check the logs to understand what's happening during searches.

## Performance

### Cost Considerations

- GPT-4o-mini is cost-effective (~$0.00015 per 1K input tokens)
- Typical queries use ~100-200 tokens
- Intelligent fallback reduces unnecessary LLM calls when queries are too restrictive

### Response Times

- LLM conversion: ~1-3 seconds
- Keyword fallback: ~0.1 seconds
- Overall search: ~2-5 seconds
- Fallback detection: ~0.5 seconds (tests LLM query results before falling back)

## Security

- API keys are loaded from environment variables
- No API keys are logged or stored in plain text
- Fallback mechanisms ensure service availability
- All queries are sent to OpenAI's secure API

## Future Enhancements

Potential improvements:
- Caching of converted queries
- Custom model fine-tuning
- Multi-language support
- Query optimization feedback
- A/B testing of conversion methods
- Enhanced query understanding for complex natural language
- Integration with server details modal for better context
- Graph-based query suggestions
- Visual query builder interface
- Advanced graph analytics and metrics 