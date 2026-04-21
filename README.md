# 🔬 ResearchMind - Multi-Agent AI Research System

A powerful multi-agent AI system that automatically researches, scrapes, synthesizes, and critiques content on any topic using LangChain and Google Gemini.

**Status**: ✅ Fully functional | **Framework**: LangChain + Streamlit | **LLM**: Google Gemini 2.5 Flash Lite

---

## 🎯 Project Overview

ResearchMind orchestrates **4 specialized AI agents** that work together to deliver comprehensive research reports:

1. **🔍 Search Agent** - Finds recent, reliable information from the web
2. **📄 Reader Agent** - Scrapes and extracts deep content from URLs  
3. **✍️ Writer Agent** - Synthesizes findings into a structured research report
4. **🧐 Critic Agent** - Reviews and scores the report with constructive feedback

### Workflow
```
User Input (Topic)
    ↓
Search Agent [Web Search]
    ↓
Reader Agent [URL Scraping & Parsing]
    ↓
Writer Agent [Report Synthesis]
    ↓
Critic Agent [Quality Review]
    ↓
Final Report + Feedback
```

---

## ✨ Features

- ✅ **Parallel Web Scraping** - ThreadPoolExecutor + async/await support for multiple URLs
- ✅ **Intelligent Content Extraction** - BeautifulSoup with smart HTML parsing
- ✅ **Rate Limiting** - Respectful delays between API calls
- ✅ **Error Handling** - Graceful fallbacks for failed steps
- ✅ **Beautiful UI** - Streamlit app with real-time pipeline visualization
- ✅ **Markdown Export** - Download research reports as `.md` files
- ✅ **Modular Architecture** - Easily swap agents, tools, or LLM models

---

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Google Gemini API key (free at https://aistudio.google.com/app/apikey)
- Tavily API key (free at https://tavily.com)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/multi-agent-research-system.git
   cd multi-agent-research-system
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   # Windows
   .venv\Scripts\activate
   # macOS/Linux
   source .venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and add:
   ```env
   GEMINI_API_KEY=your-api-key-here
   TAVILY_API_KEY=your-tavily-key-here
   ```

### Usage

#### Option 1: Terminal Pipeline
```bash
python pipeline.py
# Enter a research topic when prompted
```

Example:
```
Enter a research topic: Latest advances in quantum computing
```

#### Option 2: Streamlit Web App (Recommended)
```bash
streamlit run app.py
```

Then open http://localhost:8501 in your browser.

---

## 📁 Project Structure

```
multi-agent-research-system/
├── README.md              # This file
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
├── .gitignore            # Git ignore rules
│
├── pipeline.py           # Main research pipeline (CLI)
├── app.py                # Streamlit web interface
├── agents.py             # Agent definitions & chains
├── tools.py              # Tool implementations
│
└── .venv/                # Virtual environment (auto-created)
```

### Core Files

| File | Purpose |
|------|---------|
| `pipeline.py` | Orchestrates the 4-step research workflow (CLI version) |
| `app.py` | Beautiful Streamlit UI with real-time pipeline visualization |
| `agents.py` | Builds LangChain agents + prompt chains for writer/critic |
| `tools.py` | Implements search_web() and scrape_url() tools with parallel scraping |

---

## 🛠️ How Each Component Works

### 1. Search Agent (`search_web` tool)
- Uses **Tavily API** for web search
- Returns top 5 results with title, URL, snippet, and relevance score
- Keeps results concise to avoid token overload

### 2. Reader Agent (`scrape_url` tool)
- Extracts URLs from search results
- Scrapes each URL using requests + BeautifulSoup
- Smart HTML parsing (removes nav, footer, scripts)
- Returns content with **source URLs clearly labeled**
- **Parallel scraping** for 5+ URLs using ThreadPoolExecutor

### 3. Writer Chain
- Receives combined search results + scraped content
- Generates structured research report:
  - Introduction
  - Key Findings (bullet points)
  - Conclusion
  - References (with URLs)

### 4. Critic Chain
- Reviews the generated report
- Provides score (1-10)
- Lists strengths/weaknesses
- Suggests improvements
- One-line verdict

---

## ⚙️ Configuration

### Model Settings
Edit `agents.py` to change the LLM model:

```python
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite",  # Change model here
    temperature=0.3,                # Lower = more deterministic
    max_retries=1,                  # Fail fast on quota errors
    timeout=20                      # Request timeout (seconds)
)
```

### Rate Limiting
The pipeline includes 2-second delays between agent calls. Adjust in `pipeline.py`:

```python
time.sleep(2)  # Change this value
```

---

## 🐛 Troubleshooting

### Error: "429 Too Many Requests"
**Cause**: Hit daily or minute-based quota limit
**Solution**:
- Wait until quota resets (UTC midnight for daily limit)
- Upgrade to paid plan
- Create new API key with fresh quota

### Error: "Invalid API Key"
**Cause**: Missing or wrong credentials
**Solution**:
```bash
# Check .env file
cat .env

# Verify keys are set correctly
echo $GEMINI_API_KEY
echo $TAVILY_API_KEY
```

### Streamlit not showing results
**Cause**: Session state not updating
**Solution**:
```bash
# Clear Streamlit cache
rm -rf ~/.streamlit/cache
streamlit run app.py --logger.level=debug
```

### URLs not in scraped content
**Cause**: Reader agent not using scrape_url tool
**Solution**: Check reader agent prompt in `agents.py` includes explicit instruction to scrape URLs

---

## 🎓 Learning & Extending

### Modify the Research Workflow
Edit `pipeline.py` to add custom steps:

```python
# Add a new agent
my_agent = build_custom_agent()
result = my_agent.invoke({"messages": [...]})
```

### Create Custom Tools
Add to `tools.py`:

```python
@tool
def my_custom_tool(input_param: str) -> str:
    """Tool description for the LLM"""
    # Your implementation here
    return result

# Then use in agents.py:
def build_my_agent():
    return agents.create_agent(model=llm, tools=[my_custom_tool])
```

### Change Prompts
Edit prompt templates in `agents.py`:

```python
writer_prompt = ChatPromptTemplate.from_messages([
    ('system', 'Your custom system prompt here'),
    ('human', 'Your custom instruction here')
])
```

---

## 📦 Dependencies

Key packages (see `requirements.txt` for full list):
- **langchain** - Agent orchestration framework
- **langchain-google-genai** - Google Gemini integration
- **google-genai** - Official Google Gemini SDK
- **streamlit** - Web UI framework
- **beautifulsoup4** - HTML parsing
- **tavily-python** - Web search API
- **tenacity** - Retry logic with exponential backoff
- **aiohttp** - Async HTTP requests

---

## 📊 Example Output

### Search Results
```
Title: Quantum Computing Breakthroughs 2025
URL: https://example.com/quantum-2025
Snippet: Latest developments in quantum error correction...
Score: 0.95
```

### Scraped Content
```
Source URL: https://example.com/quantum-2025
================================================================================
[Full article content here with proper formatting]
```

### Final Report
```
# Quantum Computing 2025 - Research Report

## 1. Introduction
Quantum computing has made significant strides...

## 2. Key Findings
- Error correction rates improved by 40%
- New hardware platforms announced
- Industry investment reached $2B

## 3. Conclusion
The field is entering a practical phase...

## 4. References
- https://example.com/quantum-2025
- https://research.org/quantum-study
```

### Critic Feedback
```
1. Score: 8/10
2. Strengths:
   - Well-structured report
   - Good source diversity
3. Weaknesses:
   - Missing recent developments from Q2 2025
4. Suggestions:
   - Add more quantitative data
   - Include expert quotes
```
