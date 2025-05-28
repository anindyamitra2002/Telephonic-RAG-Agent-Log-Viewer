import streamlit as st
import pandas as pd
from datetime import datetime, time, timedelta
import pytz
from dateutil import parser
from call_logs_reader import fetch_call_logs

# Timezone for IST
IST_TIMEZONE = pytz.timezone('Asia/Kolkata')

# Language mapping dictionary
LANGUAGE_MAPPING = {
    'bn-IN': 'Bengali', 'en-IN': 'English', 'en-US': 'English (US)', 'gu-IN': 'Gujarati',
    'hi-IN': 'Hindi', 'kn-IN': 'Kannada', 'ml-IN': 'Malayalam', 'mr-IN': 'Marathi',
    'od-IN': 'Odia', 'pa-IN': 'Punjabi', 'ta-IN': 'Tamil', 'te-IN': 'Telugu'
}

# Set page configuration to wide layout
st.set_page_config(layout="wide")

# Title
st.title("Call Logs Viewer")

# Display current date and time in IST
current_time = datetime.now(IST_TIMEZONE).strftime("%A, %B %d, %Y %I:%M %p")
st.write(f"Current date and time: {current_time} IST")

# Initialize session state variables
if 'logs' not in st.session_state:
    st.session_state.logs = []
if 'prev_start_date' not in st.session_state:
    st.session_state.prev_start_date = None
if 'prev_end_date' not in st.session_state:
    st.session_state.prev_end_date = None
if 'fetched' not in st.session_state:
    st.session_state.fetched = False

# Date inputs with default values (last 7 days)
default_start_date = (datetime.now(IST_TIMEZONE) - timedelta(days=7)).date()
default_end_date = datetime.now(IST_TIMEZONE).date()
start_date = st.date_input("From Date", value=default_start_date)
end_date = st.date_input("To Date", value=default_end_date)

# Clear logs if date range changes
if start_date != st.session_state.prev_start_date or end_date != st.session_state.prev_end_date:
    st.session_state.logs = []
    st.session_state.fetched = False
    st.session_state.prev_start_date = start_date
    st.session_state.prev_end_date = end_date

# Fetch logs button
if st.button("Fetch Logs"):
    with st.spinner("Fetching logs..."):
        try:
            start_datetime = datetime.combine(start_date, time.min).replace(tzinfo=IST_TIMEZONE)
            end_datetime = datetime.combine(end_date, time.max).replace(tzinfo=IST_TIMEZONE)
            logs = fetch_call_logs(start_datetime, end_datetime)
            st.session_state.logs = logs
            st.session_state.fetched = True
        except Exception as e:
            st.error(f"Error fetching logs: {e}")

# Display content based on session state
if st.session_state.logs:
    # Process logs into a DataFrame with all metadata details
    log_data = []
    for log in st.session_state.logs:
        metadata = log['metadata']
        # Map language codes to full names
        stt_language = LANGUAGE_MAPPING.get(metadata['STT_language'], metadata['STT_language'])
        tts_language = LANGUAGE_MAPPING.get(metadata['TTS_language'], metadata['TTS_language'])
        # Format timestamps and duration
        start_time = parser.isoparse(log['call_timestamps']['start']).strftime("%Y-%m-%d %H:%M:%S")
        end_time = parser.isoparse(log['call_timestamps']['end']).strftime("%Y-%m-%d %H:%M:%S")
        duration = f"{log['call_duration']['minutes']} min {log['call_duration']['seconds']} sec"
        # Include all metadata fields
        log_dict = {
            "Start Time": start_time,
            "End Time": end_time,
            "Duration": duration,
            "Phone Number": metadata['phone_number'],
            "LLM Model": metadata['LLM_model'],
            "LLM Provider": metadata['LLM_provider'],
            "LLM Temperature": metadata['LLM_temperature'],
            "STT Language": stt_language,
            "STT Model": metadata['STT_model'],
            "STT Provider": metadata['STT_provider'],
            "TTS Language": tts_language,
            "TTS Provider": metadata['TTS_provider'],
            "TTS Voice": metadata['TTS_voice'],
            "Auto End Call": metadata['auto_end_call'],
            "Background Sound": metadata['background_sound'],
            "Is Allow Interruptions": metadata['is_allow_interruptions'],
            "Use Retrieval": metadata['use_retrieval'],
            "VAD Min Silence": metadata['vad_min_silence'],
        }
        log_data.append(log_dict)
    df = pd.DataFrame(log_data)

    # Call analysis section
    st.write("### Call Statistics")
    num_calls = len(st.session_state.logs)
    total_duration = sum(log['call_duration']['total_seconds'] for log in st.session_state.logs)
    avg_duration = total_duration / num_calls if num_calls > 0 else 0
    stt_languages = [log['metadata']['STT_language'] for log in st.session_state.logs]
    tts_languages = [log['metadata']['TTS_language'] for log in st.session_state.logs]
    stt_lang_counts = pd.Series(stt_languages).value_counts()
    tts_lang_counts = pd.Series(tts_languages).value_counts()

    # Display statistics in columns
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Calls", num_calls)
    with col2:
        st.metric("Average Duration (seconds)", round(avg_duration, 2))
    with col3:
        most_common_stt = stt_lang_counts.index[0] if not stt_lang_counts.empty else "N/A"
        st.write(f"Most Common STT Language: {LANGUAGE_MAPPING.get(most_common_stt, most_common_stt)}")

    # Language distribution charts
    st.write("STT Language Distribution:")
    st.bar_chart(stt_lang_counts.rename(index=LANGUAGE_MAPPING))
    st.write("TTS Language Distribution:")
    st.bar_chart(tts_lang_counts.rename(index=LANGUAGE_MAPPING))

    # Display table with all metadata
    st.write("### Call Logs")
    st.dataframe(df)

    # Selectbox for detailed view
    options = [f"{parser.isoparse(log['call_timestamps']['start']).strftime('%Y-%m-%d %H:%M:%S')} - {log['metadata']['phone_number']}" for log in st.session_state.logs]
    selected_index = st.selectbox("Select a log to view details", options=range(len(st.session_state.logs)), format_func=lambda i: options[i])
    if selected_index is not None:
        selected_log = st.session_state.logs[selected_index]
        with st.expander("LLM System Prompt"):
            st.text(selected_log['metadata']['LLM_system_prompt'])
        with st.expander("First Message"):
            st.text(selected_log['metadata']['first_message'])
        with st.expander("Conversation Transcript"):
            transcript_text = "\n".join([f"{msg['role'].capitalize()}: {msg['content']}" for msg in selected_log['conversation_transcript']])
            st.text(transcript_text)
elif st.session_state.fetched:
    st.info("No logs found in the selected date range.")
else:
    st.info("Please select a date range and click 'Fetch Logs' to retrieve call logs.")