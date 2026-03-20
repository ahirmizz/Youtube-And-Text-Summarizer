import os
import re
import traceback
import requests
import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled
from groq import Groq
from summary import summarize_text

# Streamlit page configuration
st.set_page_config(
    page_title="YouTube & Text Summarizer | Annabelle Hirmiz",
    page_icon="favicon_icon.png",
    layout="centered"
)

# Header Font
st.markdown("""
<style>

@import url('https://fonts.googleapis.com/css2?family=Inria+Sans:wght@700&display=swap');

h1 {
    font-family: 'Inria Sans', sans-serif;
    font-weight: 700;
    letter-spacing: -0.5px;
}
</style>
""", unsafe_allow_html=True)


# Animated Gradient Background
st.markdown("""
<style>

.stApp {
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
    animation: gradient 30s ease infinite
}

/* gradient movement */
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

# Allocate Memory - Initialize values in session state
if "summary_data" not in st.session_state:
    st.session_state["summary_data"] = None

if "text_summary" not in st.session_state:
    st.session_state["text_summary"] = None

# Main tabs
tab_options = ["YouTube Video Summarizer", "Text Summarizer"]

tab1, tab2 = st.tabs(tab_options)

# Tab 1 - YouTube Video Summarizer
with tab1:
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

    st.markdown("""
<style>
.main {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 80vh; /* leave space for header */
    flex-direction: column;
}

.block-container {
    background: rgba(255,255,255,0.85);
    padding: 5rem;
    border-radius: 15px;
    max-width: 900px;
    width: 90%;
    box-shadow: 0 8px 30px rgba(0,0,0,0.2);
}
</style>
""", unsafe_allow_html=True)

    

    # Helper Functions 
    def extract_video_id(url):
        # List of regex patterns to match different YouTube URL formats
        patterns = [
            r"v=([^&]+)",                        # Standard YouTube URL
            r"youtu\.be/([^?&]+)",              # Shortened YouTube URL
            r"youtube\.com/shorts/([^?&]+)"     # YouTube Shorts URL
        ]

        # Loops through each pattern to find a match
        for p in patterns:
            m = re.search(p, url)               # Search for pattern in the URL
            if m:   
                return m.group(1)               # If a mach is found, returns the captured video ID (first group)
        
        # If no pattern matched, returns the original URL stripped of extra spaces
        return url.strip()
    
    
    def fetch_video_metadata(video_id):
        # Build YouTube oEmbed API URL using the video ID
        oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
        try:
            r = requests.get(oembed_url)       # Sends request to YouTube
            
            # Check if request was successful (200 = OK)
            if r.status_code == 200:
                data = r.json()

                # Returns selected metadata fields
                return {
                    "title": data.get("title"),
                    "author": data.get("author_name"),
                    "thumbnail": data.get("thumbnail_url")
                }
        except Exception:
            return None 
    

    def extract_section(title, text):
        pattern = rf"### {title}\n(.+?)(?=###|$)"
        match = re.search(pattern, text, re.DOTALL)
        return match.group(1).strip() if match else "Not found."
    
    # Input
    url = st.text_input(
        "Paste YouTube URL or Video ID:",
        placeholder="Enter the YouTube URL you want to summarize..."
    )
    
    summarize_clicked = st.button("Summarize Video")

    if summarize_clicked:
        if not url:
            st.error("Please enter a valid YouTube URL")
            st.stop()

        video_id = extract_video_id(url)

        try:
            with st.spinner("Fetching transcript..."):
                ytt_api = YouTubeTranscriptApi()
                transcript_obj = ytt_api.fetch(video_id)
                raw_list = transcript_obj.to_raw_data()
                full_text = "".join([seg["text"] for seg in raw_list])

        except TranscriptsDisabled:
            st.error("This video has no transcripts.")
            st.stop()

        except Exception:
            st.error("Failed to retrieve transcript.")
            st.code(traceback.format_exc())
            st.stop()

        st.success("Transcript fetched!")

        client = Groq(api_key=os.getenv("GROQ_API_KEY"))

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

        # Display Results
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



# TAB 2 - TEXT SUMMARIZER
with tab2:
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
