# YouTube & Text Summarizer

A web application that summarizes YouTube videos and long pieces of text using the Groq API and Llama 3.3. Users can paste a YouTube link or their own text to generate summaries and key takeaways through a simple Streamlit interface.

**Live Demo:** [https://youtube-text-summary.streamlit.app](https://youtube-text-summary.streamlit.app)

---

## 🚀 Features

### ▶️ YouTube Video Summarizer

- Paste a YouTube URL or video ID
- Supports standard YouTube links, shortened URLs, and YouTube Shorts
- Retrieves the video title, channel name, thumbnail, and transcript
- Generates:
  - Short Summary
  - Key Bullet Points
  - Actionable Insights
- Allows users to paste a transcript manually if one cannot be retrieved
- Download summaries as a `.txt` file

### 📝 Text Summarizer

- Summarizes long pieces of text
- Creates a clear, concise summary
- Works for articles, notes, reports, essays, and other documents

### ⚙️ Application

- Built with Streamlit
- Uses custom CSS for styling
- Stores results using Streamlit Session State
- Simple and easy-to-use interface

---

## 🧰 Tech Stack

| Component | Used For |
|-----------|----------|
| **Python 3.10+** | Application logic |
| **Streamlit** | User interface |
| **Groq API** | Text summarization using `llama-3.3-70b-versatile` |
| **YouTube Transcript API** | Retrieving YouTube transcripts |
| **Requests** | Fetching video metadata |
| **Regex** | Parsing YouTube URLs |
| **HTML & CSS** | Custom interface styling |

---

## 📂 Project Structure

```text
youtube_text_summarizer/
│── app.py               # Main Streamlit application
│── summary.py           # Text summarization functions
│── requirements.txt     # Project dependencies
└── README.md
```

---

## 🖥️ How It Works

### YouTube Video Summarizer

1. Paste a YouTube URL or video ID.
2. The application retrieves the transcript.
3. The transcript is sent to the Groq API.
4. The model generates:
   - Short Summary
   - Key Bullet Points
   - Actionable Insights
5. View the results or download the summary as a text file.

If a transcript cannot be retrieved, users can paste the transcript manually.

### Text Summarizer

1. Select **Text Summarizer**.
2. Paste any text.
3. The text is sent to the Groq API.
4. A concise summary is generated and displayed.

---

## ▶️ Run Locally

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_GITHUB_USERNAME/youtube-text-summarizer.git
cd youtube-text-summarizer
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set your Groq API key

**Mac/Linux**

```bash
export GROQ_API_KEY="your_api_key_here"
```

**Windows PowerShell**

```powershell
$env:GROQ_API_KEY="your_api_key_here"
```

### 4. Run the application

```bash
streamlit run app.py
```

---

## 💡 Key Implementation Details

- Used Streamlit Session State to preserve generated summaries while interacting with the application.
- Parsed different YouTube URL formats using regular expressions.
- Displayed video metadata including the title, channel name, and thumbnail.
- Organized generated content into separate sections for summaries, key points, and insights.
- Added a manual transcript option when automatic transcript retrieval is unavailable.
- Allowed users to download generated summaries as text files.
