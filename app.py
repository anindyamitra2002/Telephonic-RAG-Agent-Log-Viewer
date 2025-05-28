import streamlit as st
import pandas as pd
from datetime import datetime, time, timedelta
import pytz
from dateutil import parser
import plotly.express as px
import plotly.graph_objects as go
from call_logs_reader import fetch_call_logs

# Custom CSS for better styling
st.set_page_config(
    layout="wide",
    page_title="Call Analytics Dashboard",
    page_icon="📊",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding: 0rem 1rem;
    }
    .stMetric {
        padding: 1rem;
        border-radius: 0.5rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
    }
    .dataframe {
        font-size: 0.9em;
    }
    .dataframe th {
        padding: 0.5em;
        text-align: left;
    }
    .dataframe td {
        padding: 0.5em;
    }
    .stMarkdown {
        font-size: 1.1em;
    }
    .conversation-text {
        white-space: pre-wrap;
        font-family: 'Segoe UI', sans-serif;
    }
    .conversation-text strong {
        color: #1f77b4;
        font-size: 1.1em;
    }
    </style>
""", unsafe_allow_html=True)

# Timezone for IST
IST_TIMEZONE = pytz.timezone('Asia/Kolkata')

# Language mapping dictionary
LANGUAGE_MAPPING = {
    'bn-IN': 'Bengali', 'en-IN': 'English', 'en-US': 'English (US)', 'gu-IN': 'Gujarati',
    'hi-IN': 'Hindi', 'kn-IN': 'Kannada', 'ml-IN': 'Malayalam', 'mr-IN': 'Marathi',
    'od-IN': 'Odia', 'pa-IN': 'Punjabi', 'ta-IN': 'Tamil', 'te-IN': 'Telugu'
}

# Color schemes for charts
COLOR_SCHEMES = {
    'main': px.colors.qualitative.Set1,  # Professional distinct colors
    'sequential': px.colors.sequential.Plasma,  # Modern sequential colors
    'diverging': px.colors.diverging.Spectral,  # Professional diverging colors
    'qualitative': px.colors.qualitative.Pastel,  # Soft professional colors
    'accent': px.colors.qualitative.Dark2,  # Dark professional colors
    'highlight': px.colors.qualitative.Set2  # Highlight colors for important data
}

# Custom color sequences for specific charts
CHART_COLORS = {
    'cost': ['#1f77b4', '#2ca02c', '#ff7f0e'],  # Professional blue, green, orange
    'language': ['#2ecc71', '#27ae60', '#16a085', '#1abc9c', '#48c9b0'],  # Professional green shades
    'provider': ['#8e44ad', '#9b59b6', '#af7ac5', '#c39bd3', '#d7bde2'],  # Professional purple shades
    'model': ['#e67e22', '#f39c12', '#f5b041', '#f8c471', '#fad7a0'],  # Professional orange shades
    'time': ['#16a085', '#1abc9c', '#48c9b0', '#76d7c4', '#a3e4d7']  # Professional teal shades
}

# Title and current time
st.title("📊 Call Analytics Dashboard")
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

# Date range selector in sidebar
with st.sidebar:
    st.header("📅 Date Range")
    start_date = st.date_input("From Date", value=(datetime.now(IST_TIMEZONE) - timedelta(days=7)).date())
    end_date = st.date_input("To Date", value=datetime.now(IST_TIMEZONE).date())
    
    if st.button("Fetch Logs", type="primary", use_container_width=True):
        with st.spinner("Fetching logs..."):
            try:
                start_datetime = datetime.combine(start_date, time.min).replace(tzinfo=IST_TIMEZONE)
                end_datetime = datetime.combine(end_date, time.max).replace(tzinfo=IST_TIMEZONE)
                logs = fetch_call_logs(start_datetime, end_datetime)
                st.session_state.logs = logs
                st.session_state.fetched = True
                st.session_state.prev_start_date = start_date
                st.session_state.prev_end_date = end_date
            except Exception as e:
                st.error(f"Error fetching logs: {e}")

# Clear logs if date range changes
if start_date != st.session_state.prev_start_date or end_date != st.session_state.prev_end_date:
    st.session_state.logs = []
    st.session_state.fetched = False

# Display content based on session state
if st.session_state.logs:
    # Process logs into a DataFrame
    log_data = []
    for log in st.session_state.logs:
        metadata = log['metadata']
        stt_language = LANGUAGE_MAPPING.get(metadata['STT_language'], metadata['STT_language'])
        tts_language = LANGUAGE_MAPPING.get(metadata['TTS_language'], metadata['TTS_language'])
        start_time = parser.isoparse(log['call_timestamps']['start'])
        end_time = parser.isoparse(log['call_timestamps']['end'])
        duration_minutes = log['call_duration']['total_seconds'] / 60
        
        # Calculate costs
        llm_cost = duration_minutes * metadata.get('LLM_cost_per_min', 0)
        stt_cost = duration_minutes * metadata.get('STT_cost_per_min', 0)
        tts_cost = duration_minutes * metadata.get('TTS_cost_per_min', 0)
        total_cost = duration_minutes * metadata.get('total_cost_per_min', 0)
        
        log_dict = {
            "Date": start_time.date(),
            "Start Time": start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "End Time": end_time.strftime("%Y-%m-%d %H:%M:%S"),
            "Duration (min)": round(duration_minutes, 2),
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
            "LLM Cost (USD)": round(llm_cost, 4),
            "STT Cost (USD)": round(stt_cost, 4),
            "TTS Cost (USD)": round(tts_cost, 4),
            "Total Cost (USD)": round(total_cost, 4),
            "Auto End Call": metadata['auto_end_call'],
            "Background Sound": metadata['background_sound'],
            "Is Allow Interruptions": metadata['is_allow_interruptions'],
            "Use Retrieval": metadata['use_retrieval'],
            "VAD Min Silence": metadata['vad_min_silence'],
            "Conversation": log['conversation_transcript'],
            "Audio URL": log['audio_file']['sas_url'],
            "System Prompt": metadata['LLM_system_prompt'],
            "First Message": metadata['first_message']
        }
        log_data.append(log_dict)
    
    df = pd.DataFrame(log_data)

    # Call Statistics Section
    st.header("📈 Call Statistics")
    col1, col2, col3, col4 = st.columns(4)
    
    total_calls = len(df)
    total_duration = df['Duration (min)'].sum()
    total_cost = df['Total Cost (USD)'].sum()
    avg_duration = total_duration / total_calls if total_calls > 0 else 0
    
    with col1:
        st.metric("Total Calls", f"{total_calls:,}")
    with col2:
        st.metric("Total Duration", f"{total_duration:.1f} min")
    with col3:
        st.metric("Average Duration", f"{avg_duration:.1f} min")
    with col4:
        st.metric("Total Cost", f"${total_cost:.2f}")

    # Call Analysis Section
    st.header("📊 Call Analysis")
    
    # Create tabs for different analyses
    tab1, tab2, tab3, tab4 = st.tabs(["Cost Analysis", "Language Distribution", "Time Analysis", "Model Usage"])
    
    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            # Cost breakdown pie chart
            cost_breakdown = {
                'LLM Cost': df['LLM Cost (USD)'].sum(),
                'STT Cost': df['STT Cost (USD)'].sum(),
                'TTS Cost': df['TTS Cost (USD)'].sum()
            }
            fig_cost = px.pie(
                values=list(cost_breakdown.values()),
                names=list(cost_breakdown.keys()),
                title="Cost Distribution (USD)",
                color_discrete_sequence=COLOR_SCHEMES['qualitative']
            )
            fig_cost.update_traces(
                textposition='inside',
                textinfo='percent+label',
                marker=dict(line=dict(color='#FFFFFF', width=1))
            )
            fig_cost.update_layout(
                title_font=dict(size=20, color='#2C3E50'),
                legend_font=dict(size=12),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig_cost, use_container_width=True)
        
        with col2:
            # Cost per call over time
            fig_cost_time = px.line(
                df.groupby('Date')['Total Cost (USD)'].sum().reset_index(),
                x='Date',
                y='Total Cost (USD)',
                title="Daily Cost Trend (USD)",
                color_discrete_sequence=COLOR_SCHEMES['qualitative']
            )
            fig_cost_time.update_layout(
                title_font=dict(size=20, color='#2C3E50'),
                xaxis_title_font=dict(size=12),
                yaxis_title_font=dict(size=12),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(gridcolor='#E5E8E8'),
                yaxis=dict(gridcolor='#E5E8E8')
            )
            st.plotly_chart(fig_cost_time, use_container_width=True)
    
    with tab2:
        col1, col2 = st.columns(2)
        with col1:
            # STT Language distribution
            fig_stt = px.pie(
                df,
                names='STT Language',
                title="STT Language Distribution",
                color_discrete_sequence=COLOR_SCHEMES['qualitative']
            )
            fig_stt.update_traces(
                textposition='inside',
                textinfo='percent+label',
                marker=dict(line=dict(color='#FFFFFF', width=1))
            )
            fig_stt.update_layout(
                title_font=dict(size=20, color='#2C3E50'),
                legend_font=dict(size=12),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig_stt, use_container_width=True)
        
        with col2:
            # TTS Voice distribution
            tts_counts = df['TTS Voice'].value_counts().reset_index()
            tts_counts.columns = ['TTS Voice', 'Count']
            fig_tts = px.bar(
                tts_counts,
                x='TTS Voice',
                y='Count',
                title="TTS Voice Distribution",
                color_discrete_sequence=COLOR_SCHEMES['qualitative']
            )
            fig_tts.update_layout(
                title_font=dict(size=20, color='#2C3E50'),
                xaxis_title_font=dict(size=12),
                yaxis_title_font=dict(size=12),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(gridcolor='#E5E8E8'),
                yaxis=dict(gridcolor='#E5E8E8')
            )
            st.plotly_chart(fig_tts, use_container_width=True)
    
    with tab3:
        col1, col2 = st.columns(2)
        with col1:
            # Call duration distribution
            fig_duration = px.histogram(
                df,
                x='Duration (min)',
                title="Call Duration Distribution",
                color_discrete_sequence=COLOR_SCHEMES['qualitative'],
                nbins=20
            )
            fig_duration.update_layout(
                title_font=dict(size=20, color='#2C3E50'),
                xaxis_title_font=dict(size=12),
                yaxis_title_font=dict(size=12),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(gridcolor='#E5E8E8'),
                yaxis=dict(gridcolor='#E5E8E8')
            )
            st.plotly_chart(fig_duration, use_container_width=True)
        
        with col2:
            # Calls over time
            calls_over_time = df.groupby('Date').size().reset_index()
            calls_over_time.columns = ['Date', 'Number of Calls']
            fig_time = px.line(
                calls_over_time,
                x='Date',
                y='Number of Calls',
                title="Calls Over Time",
                color_discrete_sequence=COLOR_SCHEMES['qualitative']
            )
            fig_time.update_layout(
                title_font=dict(size=20, color='#2C3E50'),
                xaxis_title_font=dict(size=12),
                yaxis_title_font=dict(size=12),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(gridcolor='#E5E8E8'),
                yaxis=dict(gridcolor='#E5E8E8')
            )
            st.plotly_chart(fig_time, use_container_width=True)
    
    with tab4:
        col1, col2 = st.columns(2)
        with col1:
            # LLM Model distribution
            llm_counts = df['LLM Model'].value_counts().reset_index()
            llm_counts.columns = ['LLM Model', 'Count']
            fig_llm = px.bar(
                llm_counts,
                x='LLM Model',
                y='Count',
                title="LLM Model Distribution",
                color_discrete_sequence=COLOR_SCHEMES['qualitative']
            )
            fig_llm.update_layout(
                title_font=dict(size=20, color='#2C3E50'),
                xaxis_title_font=dict(size=12),
                yaxis_title_font=dict(size=12),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(gridcolor='#E5E8E8'),
                yaxis=dict(gridcolor='#E5E8E8')
            )
            st.plotly_chart(fig_llm, use_container_width=True)
        
        with col2:
            # Provider distribution
            fig_provider = px.pie(
                df,
                names='LLM Provider',
                title="LLM Provider Distribution",
                color_discrete_sequence=COLOR_SCHEMES['qualitative']
            )
            fig_provider.update_traces(
                textposition='inside',
                textinfo='percent+label',
                marker=dict(line=dict(color='#FFFFFF', width=1))
            )
            fig_provider.update_layout(
                title_font=dict(size=20, color='#2C3E50'),
                legend_font=dict(size=12),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig_provider, use_container_width=True)

    # Call Logs Section with Filters
    st.header("📋 Call Logs")
    
    # Advanced Filters with specified options
    with st.expander("🔍 Advanced Filters", expanded=True):
        # First row of filters
        row1_col1, row1_col2, row1_col3, row1_col4 = st.columns(4)
        with row1_col1:
            phone_filter = st.text_input("Phone Number", placeholder="Enter phone number")
        with row1_col2:
            date_filter = st.date_input(
                "Date",
                value=None,
                min_value=df['Date'].min(),
                max_value=df['Date'].max()
            )
        with row1_col3:
            stt_language_filter = st.selectbox(
                "STT Language",
                ["All"] + sorted(df['STT Language'].unique().tolist())
            )
        with row1_col4:
            llm_model_filter = st.selectbox(
                "LLM Model",
                ["All"] + sorted(df['LLM Model'].unique().tolist())
            )

        # Second row of filters
        row2_col1, row2_col2, row2_col3, row2_col4 = st.columns(4)
        with row2_col1:
            tts_provider_filter = st.selectbox(
                "TTS Provider",
                ["All"] + sorted(df['TTS Provider'].unique().tolist())
            )
        with row2_col2:
            stt_provider_filter = st.selectbox(
                "STT Provider",
                ["All"] + sorted(df['STT Provider'].unique().tolist())
            )
        with row2_col3:
            llm_provider_filter = st.selectbox(
                "LLM Provider",
                ["All"] + sorted(df['LLM Provider'].unique().tolist())
            )
        with row2_col4:
            use_retrieval_filter = st.selectbox(
                "Use Retrieval",
                ["All", "Yes", "No"]
            )

    # Apply filters
    filtered_df = df.copy()
    
    # Apply phone number filter
    if phone_filter and phone_filter.strip():
        filtered_df = filtered_df[filtered_df['Phone Number'].str.contains(phone_filter.strip(), case=False, regex=False)]
    
    # Apply date filter
    if date_filter:
        filtered_df = filtered_df[filtered_df['Date'] == date_filter]
    
    # Apply language filter
    if stt_language_filter != "All":
        filtered_df = filtered_df[filtered_df['STT Language'] == stt_language_filter]
    
    # Apply provider filters
    if tts_provider_filter != "All":
        filtered_df = filtered_df[filtered_df['TTS Provider'] == tts_provider_filter]
    if stt_provider_filter != "All":
        filtered_df = filtered_df[filtered_df['STT Provider'] == stt_provider_filter]
    if llm_provider_filter != "All":
        filtered_df = filtered_df[filtered_df['LLM Provider'] == llm_provider_filter]
    
    # Apply LLM model filter
    if llm_model_filter != "All":
        filtered_df = filtered_df[filtered_df['LLM Model'] == llm_model_filter]
    
    # Apply use retrieval filter
    if use_retrieval_filter != "All":
        use_retrieval_value = use_retrieval_filter == "Yes"
        filtered_df = filtered_df[filtered_df['Use Retrieval'] == use_retrieval_value]

    # Display the filtered dataframe with all metadata columns
    display_columns = [
        "Date", "Start Time", "Duration (min)", "Phone Number", 
        "LLM Model", "LLM Provider", "LLM Temperature",
        "STT Language", "STT Model", "STT Provider",
        "TTS Language", "TTS Provider", "TTS Voice",
        "LLM Cost (USD)", "STT Cost (USD)", "TTS Cost (USD)", "Total Cost (USD)",
        "Auto End Call", "Background Sound", "Is Allow Interruptions",
        "Use Retrieval", "VAD Min Silence"
    ]
    
    # Format the dataframe with markdown
    styled_df = filtered_df[display_columns].sort_values('Date', ascending=False)
    styled_df = styled_df.style.format({
        'Duration (min)': '{:.2f}',
        'LLM Temperature': '{:.2f}',
        'LLM Cost (USD)': '${:.4f}',
        'STT Cost (USD)': '${:.4f}',
        'TTS Cost (USD)': '${:.4f}',
        'Total Cost (USD)': '${:.4f}',
        'VAD Min Silence': '{:.2f}'
    })
    
    st.dataframe(
        styled_df,
        use_container_width=True,
        hide_index=True
    )

    # Detailed view for selected log
    st.subheader("Detailed Log View")
    options = [f"{log['Start Time']} - {log['Phone Number']}" for log in filtered_df.to_dict('records')]
    selected_index = st.selectbox("Select a log to view details", options=range(len(filtered_df)), format_func=lambda i: options[i])
    
    if selected_index is not None:
        selected_log = filtered_df.iloc[selected_index]
        col1, col2 = st.columns(2)
        with col1:
            with st.expander("System Prompt"):
                st.markdown(f"```\n{selected_log['System Prompt']}\n```")
            with st.expander("First Message"):
                st.markdown(f"```\n{selected_log['First Message']}\n```")
        with col2:
            with st.expander("Conversation Transcript"):
                # Create a container for the transcript
                transcript_container = st.container()
                
                # Display each message with proper formatting
                for msg in selected_log['Conversation']:
                    role = msg['role'].capitalize()
                    content = msg['content']
                    
                    # Create two columns for role and content
                    role_col, content_col = transcript_container.columns([1, 4])
                    
                    # Display role in bold
                    with role_col:
                        st.markdown(f"**{role}:**", unsafe_allow_html=True)
                    
                    # Display content
                    with content_col:
                        st.text(content)
                    
            with st.expander("Audio Recording"):
                st.audio(selected_log['Audio URL'])

elif st.session_state.fetched:
    st.info("No logs found in the selected date range.")
else:
    st.info("Please select a date range and click 'Fetch Logs' to retrieve call logs.")