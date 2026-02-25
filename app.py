# Standard library
import os
import re
import traceback

# Third-party library
import streamlit as st
import requests
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled
from groq import Groq

# Local project file
from summary import summarize_text

# Streamlit page configuration
st.set_page_config(
    page_title="YouTube & Text Summarizer",
    layout="centered"
)

# Allocate Memory - Initialize values in session state
if "summary_data" not in st.session_state:
    st.session_state["summary_data"] = None

if "text_summary" not in st.session_state:
    st.session_state["text_summary"] = None


# Main tabs
tab1, tab2 = st.tabs(["YouTube Summarizer", "Text Summarizer"])

# Tab 1 - YouTube Summarizer
with tab1:
    st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)

    st.markdown(
        """<h1 style="color:#1f77b4; text-align:center;">
            YouTube Video Summarizer
        </h1>
        """,
        unsafe_allow_html=True
    )

    # Helper Functions 

    """
    Extracts the unique YouTube video ID from a given URL.

    Supports multiple YouTube URL formats, including:
    - Standard watch links (e.g., https://www.youtube.com/watch?v=VIDEO_ID)
    - Shortened links (e.g., https://youtu.be/VIDEO_ID)
    - Shorts links (e.g., https://youtube.com/shorts/VIDEO_ID)

    Returns:
        str: The video ID if found, otherwise returns the original URL stripped of whitespace.
    """

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
    



    """
    Fetches basic metadata for a YouTube video using the oEmbed endpoint.

    Retrieves publicly available video information without requiring an API key,
    including:
    - Video title
    - Channel (author) name
    - Thumbnail URL

    Args:
        video_id (str): The unique YouTube video ID.

    Returns:
        dict or None:
            A dictionary containing "title", "author", and "thumbnail"
            if the request is successful.
            Returns None if the request fails or metadata cannot be retrieved.
    """
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
    url = st.text_input("Paste YouTube URL or Video ID")
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