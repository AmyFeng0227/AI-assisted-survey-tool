# AI-Assisted Survey Tool

An intelligent survey processing system that uses AI to automatically extract and categorize answers from audio recordings of survey responses. The tool features advanced chunking strategies, real-time processing, and comprehensive evaluation capabilities.

## 🚀 Features

### Core Functionality
- **Audio Processing**: Convert audio recordings to text using OpenAI Whisper
- **Intelligent Chunking**: Process long transcripts in optimal chunks with configurable overlap
- **AI-Powered Answer Extraction**: Use GPT models to extract structured answers from transcript chunks
- **Real-time Processing**: Streamlit-based web interface for interactive processing
- **Answer Validation**: Compare AI-extracted answers with human-validated responses

### Advanced Features
- **Configurable Chunking**: Adjust sentence count and overlap for optimal performance
- **Evaluation Framework**: Comprehensive testing of different chunking strategies
- **Batch Processing**: Run multiple evaluations across different configurations
- **Progress Tracking**: Real-time progress indicators and detailed logging
- **Export Capabilities**: Download results as Excel files with formatted data

### Evaluation & Analysis
- **Performance Metrics**: Accuracy, response time, token usage analysis
- **Statistical Analysis**: Trimmed means, outlier detection, comprehensive reporting
- **Multi-round Testing**: Run evaluations across multiple rounds for reliability
- **Summary Generation**: Automated averaging and reporting of evaluation results

## 📊 Evaluation Results

Based on comprehensive testing across multiple configurations:

### Top Performing Configurations
| Configuration | Accuracy | Response Time | Token Usage |
|---------------|----------|---------------|-------------|
| 4 sentences, 2 overlap | 80.3% | 7.03s | 137,336 tokens |
| 12 sentences, 2 overlap | 78.7% | 11.57s | 33,543 tokens |
| 20 sentences, 2 overlap | 77.3% | 24.10s | 18,824 tokens |

### Key Findings
- **Overlap of 2** generally performs better than 0 or 4 overlap
- **Smaller sentence counts** (4-12) with overlap of 2 show the best accuracy
- **Token usage** increases significantly with smaller sentence sizes due to more chunks
- **Response times** are generally faster with smaller sentence sizes

## 🛠️ Installation

### Prerequisites
- Python 3.8 or higher
- OpenAI API key
- Audio processing capabilities

### Setup
1. **Clone the repository**
   ```bash
   git clone https://github.com/AmyFeng0227/AI-assisted-survey-tool.git
   cd AI-assisted-survey-tool
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file in the root directory:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ```

## 🚀 Usage

### Web Interface (Recommended)
```bash
streamlit run main.py
```
Access the application at `http://localhost:8501`

### Command Line Interface
```bash
# Process a single recording
python run_evaluation.py

# Run batch evaluations
python run_batch_evaluation.py

# Generate evaluation summaries
python evaluation/summarize_evaluation_results.py
```

### Configuration
Adjust chunking parameters in `app/config.py`:
```python
n_sentences = 12  # Number of sentences per chunk
n_overlap = 2     # Number of overlapping sentences between chunks
```

## 📁 Project Structure

```
surveytool/
├── app/                          # Core application modules
│   ├── audio.py                  # Audio processing and transcription
│   ├── config.py                 # Configuration settings
│   ├── evaluation.py             # Evaluation and metrics calculation
│   ├── main_workflow.py          # Main processing workflow
│   ├── prompt.py                 # AI prompt generation
│   ├── survey.py                 # Survey data processing
│   └── answer.py                 # Answer extraction and validation
├── data/                         # Data storage
│   ├── recordings/               # Audio files
│   ├── surveys/                  # Survey templates
│   └── answers.json              # AI-generated answers
├── evaluation/                   # Evaluation framework
│   ├── evaluation_results_round*.jsonl  # Evaluation results
│   ├── evaluation_results_summary.jsonl # Averaged results
│   ├── log_chunks.jsonl          # Detailed processing logs
│   ├── answers_human.json        # Human-validated answers
│   └── summarize_evaluation_results.py  # Summary generation
├── ui/                          # User interface
│   ├── survey_app.py            # Streamlit application
│   └── styles.css               # Custom styling
├── main.py                      # Main application entry point
├── run_evaluation.py            # Evaluation script
├── run_batch_evaluation.py      # Batch evaluation script
└── requirements.txt             # Python dependencies
```

## 🔧 Configuration

### Chunking Parameters
- **n_sentences**: Number of sentences per chunk (4-20 recommended)
- **n_overlap**: Overlapping sentences between chunks (0-4 recommended)
- **Total chunks**: Automatically calculated based on transcript length

### Evaluation Parameters
- **Accuracy metrics**: TP_TN, FP_W, FP_U, FN calculations
- **Performance metrics**: RTT (response time), token usage, retry counts
- **Statistical analysis**: Trimmed means with 10% outlier removal

## 📈 Performance Analysis

### Response Time Analysis
- **Trimmed Mean RTT**: Calculated by removing top/bottom 10% of response times
- **Total Processing Time**: RTT × Total chunks for complete transcript processing
- **Retry Analysis**: Tracks failed requests and retry attempts

### Accuracy Metrics
- **TP_TN**: True positives and true negatives (correct answers)
- **FP_W**: False positives - wrong answers
- **FP_U**: False positives - unnecessary answers
- **FN**: False negatives - missing answers

## 🧪 Evaluation Framework

### Running Evaluations
1. **Single Round**: `python run_evaluation.py`
2. **Batch Processing**: `python run_batch_evaluation.py`
3. **Summary Generation**: `python evaluation/summarize_evaluation_results.py`

### Evaluation Data
- **Round Results**: Individual evaluation rounds stored in JSONL format
- **Summary Results**: Averaged results across multiple rounds
- **Detailed Logs**: Per-chunk processing details for analysis

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- OpenAI for providing the GPT API and Whisper transcription service
- Streamlit for the web application framework
- The research community for evaluation methodologies

## 📞 Support

For questions or issues, please open an issue on GitHub or contact the development team.

---

**Note**: This tool is designed for research and evaluation purposes. Ensure compliance with data privacy regulations when processing survey responses. 