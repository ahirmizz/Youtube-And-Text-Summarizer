# YouTube & Text Summarizer
# Streamlit web app that extracts YouTube transcripts and uses Groq LLM
# to generate detailed summaries, key points, and insights.

import os
import re
import requests
import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled
from groq import Groq
from summary import summarize_text

# ----- PAGE CONFIGURATION -----
st.set_page_config(
    page_title="YouTube & Text Summarizer | Annabelle Hirmiz",
    page_icon="icon.png",
    layout="centered"
)

# ----- FONT & STYLE -----
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inria+Sans:wght@400;700&display=swap');

html, body, p, span, div {
    font-family: 'Inria Sans', sans-serif !important;
    font-weight: 400 !important;
}

h1, h2, h3 {
    font-family: 'Inria Sans', sans-serif !important;
    font-weight: 700 !important;
}

/* Dropdown Menu Styling */            
div[data-baseweb="select"] * {
    font-weight: 700 !important;
}
        
/* Background */     
.stApp {
    display: flex;
    justify-content: center;
    align-items: flex-start;
    padding-top: 40px;
        
    background: linear-gradient(-45deg, 
            #7ec8c5, 
            #58b0c8,
            #a7ffd6,
            #f9d786,
            #f66f7c,
            #8c79d1, 
            #d068b6, 
            #e67d7d
    );
    background-size: 800% 800%;
    animation: gradient 30s ease infinite;

                  
.block-container {
    background: rgba(255, 255, 255, 0.9);
    padding: 3rem;
    border-radius: 15px;
    max-width: 800px;
    width: 100%;
    margin: auto;
}

/* Background gradient animation */
@keyframes gradient {
    0% {
        background-position: 0% 50%;
    }
    50% {
        background-position: 100% 50%;
    }
    100% {
        background-position: 0% 50%;
    }
}
</style>
""", unsafe_allow_html=True)


# ----- SESSION STATE -----
if "summary_data" not in st.session_state:
    st.session_state["summary_data"] = None

if "text_summary" not in st.session_state:
    st.session_state["text_summary"] = None


# ----- SELECT MODE -----
mode = st.selectbox(
    "Select a Summarizer",
    ["YouTube Video Summarizer", "Text Summarizer"]
)

# ----- HELPER FUNCTIONS -----
def extract_video_id(url):
    """Extracts YouTube video ID from multiple URL formats."""
    patterns = [
        r"v=([^&]+)",                       # Standard YouTube URL
        r"youtu\.be/([^?&]+)",              # Shortened YouTube URL
        r"youtube\.com/shorts/([^?&]+)"     # YouTube Shorts URL
    ]

    for p in patterns:
        m = re.search(p, url)
        if m:   
            return m.group(1)
        
    return url.strip()                     # fallback if no match found
    
    
def fetch_video_metadata(video_id):
    """Fetches basic video metadata (title, author, and thumbnail) using YouTube oEmbed API."""
    oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
    try:
        r = requests.get(oembed_url)
            
        if r.status_code == 200:
            data = r.json()
            return {
                "title": data.get("title"),
                "author": data.get("author_name"),
                "thumbnail": data.get("thumbnail_url")
            }
    except Exception:
        return None

def extract_section(title, text):
    """Extracts a specific section from the LLM response based on its markdown header."""
    pattern = rf"### {title}\n(.+?)(?=###|$)"
    match = re.search(pattern, text, re.DOTALL)
    return match.group(1).strip() if match else "Not found."


# ----- YOUTUBE SUMMARIZER -----
if mode == "YouTube Video Summarizer":
    st.session_state.text_summary = None

    st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)
    st.markdown("""
        <h1 style="
            color: black;
            text-align: center;
            margin-top: 1rem;
            margin-bottom: 2rem;
        ">
            YouTube Video Summarizer
        </h1>
        """,
        unsafe_allow_html=True
    )
    st.write("""
            Turn long YouTube videos into clear insights in seconds.
            This tool automatically extracts the video transcript
            and generates a concise summary, key bullet points,
            and actionable takeaways.
            """
    )
    
    # ----- USER INPUT -----
    url = st.text_input(
        "Paste YouTube URL or Video ID:",
        placeholder="Enter the YouTube URL you want to summarize..."
    )
    
    summarize_clicked = st.button("Summarize Video")

    if summarize_clicked:
        st.session_state.text_summary = None
        
        if not url:
            st.error("Please enter a valid YouTube URL")
            st.stop()

        video_id = extract_video_id(url)

        # ----- TRANSCRIPT -----
        try:
            with st.spinner("Fetching transcript..."):
                ytt_api = YouTubeTranscriptApi()
                transcript_obj = ytt_api.fetch(video_id)
                raw_list = transcript_obj.to_raw_data()
                full_text = " ".join([seg["text"] for seg in raw_list])

        except TranscriptsDisabled:
            st.error("This video has no transcripts.")
            st.stop()

        except Exception as e:
            st.error("Unable to fetch transcript")

            if "RequestBlocked" in str(e):
                st.info(
                    "This video cannot be processed because YouTube blocks transcript access "
                    "from cloud apps. Please enter a different video or paste the transcript manually."
                )
            else:
                st.info("This video may not have captions available.")
            
            manual_text = st.text_area("Paste transcript manually:", height=150)

            if manual_text:
                with st.spinner("Generating summary..."):
                    summary = summarize_text(manual_text)
                    st.session_state.text_summary = summary
                    st.success("Summary generated from pasted transcript!")
                    st.write(summary)
            st.stop()

        st.success("Transcript fetched!")

        # ----- API KEY -----
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            st.error("Missing GROQ API KEY")
            st.stop()

        client = Groq(api_key=api_key)

        # Prompt
        prompt = f"""
        Summarize the following YouTube transcript.

        Provide:
        ### Short Summary
        3-5 sentences.

        ### Key Bullet Points
        Bullet point list.

        ### Actionable Insights
        Practical insights.

        Transcript:
        {full_text}
        """

        # ----- LLM -----
        with st.spinner("Generating summary..."):
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
            )

            summary_raw = response.choices[0].message.content
            metadata = fetch_video_metadata(video_id)

            st.session_state.summary_data = {
                "full_text": full_text,
                "summary_raw": summary_raw,
                "metadata": metadata,
                "video_id": video_id,
                "short_summary": extract_section("Short Summary", summary_raw),
                "bullet_points": extract_section("Key Bullet Points", summary_raw),
                "insights": extract_section("Actionable Insights", summary_raw)
            }

        # ----- DISPLAY RESULTS -----
        if st.session_state.summary_data:
            data = st.session_state.summary_data

            if data["metadata"]:
                st.image(data["metadata"]["thumbnail"], use_column_width=True)
                st.subheader(data["metadata"]["title"])
                st.caption(f"Channel: {data['metadata']['author']}")

                tab1, tab2, tab3, tab4, tab5 = st.tabs(
                    ["📝 Short Summary", "📌 Key Points", "💡 Insights", "🗒️ Transcript", "⬇️ Download"]
                )

                with tab1:
                    st.write(data["short_summary"])
                
                with tab2:
                    st.write(data["bullet_points"])
                
                with tab3:
                    st.write(data["insights"])

                with tab4:
                    st.write(data["full_text"])

                with tab5:
                    st.download_button(
                        "Download Summary",
                        data=data["summary_raw"],
                        file_name=f"{data['video_id']}_summary.txt",
                        mime="text/plain",
                        use_container_width=True
                    )
                
                if st.button("🔄 Reset"):
                    st.session_state.summary_data = None
                    st.rerun()


# ----- TEXT SUMMARIZER -----
elif mode == "Text Summarizer":
        st.session_state.text_summary = None

        st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)
        st.markdown("""
            <h1 style="
                color: black;
                text-align: center;
                margin-top: 1rem;
                margin-bottom: 2rem;
            ">
                Text Summarizer
            </h1>
            """,
            unsafe_allow_html=True
        )
        st.write("""
                Instantly condense long passages into meaningful summaries.
                Paste any text and the tool will generate a clear overview
                of the main ideas.
                """
        )

        text_input = st.text_area(
            "Paste your text below:",
            placeholder="Enter the text you want to summarize...",
            height=200,
        )

        if st.button("Summarize Text"):

            if not text_input.strip():
                st.warning("Please enter text.")
            else:
                with st.spinner("Summarizing..."):
                    summary = summarize_text(text_input)
                    st.session_state.text_summary = summary
            
            if st.session_state.text_summary:
                st.success("Summary has been successfully generated!")
                st.write(st.session_state.text_summary)