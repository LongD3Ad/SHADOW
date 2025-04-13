# app.py
import logging
import streamlit as st
from src.app.ui import create_ui
from src.app.backend import process_query
# In backend.py or app.py
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')

def main():
    """Main entry point for the Project SHADOW application."""
    st.set_page_config(
        page_title="Project SHADOW",
        page_icon="️‍",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Apply custom CSS for professional styling
    st.markdown("""
        <style>
        /* --- Keep all the previous styles --- */

        /* Overall App Styling */
        .stApp {
            background-color: #f0f2f6; /* Light grey background */
            color: #1E293B; /* Darker default text */
        }

        /* Warning Message Styling */
        div[data-testid="stAlert"][data-alert-type="warning"] {
            background-color: #FEF3C7; /* Warmer yellow background */
            color: #92400E; /* Darker amber text for better contrast */
            border: 1px solid #FCD34D; /* Amber border */
            border-radius: 8px;
            padding: 1rem;
            font-weight: 500;
            box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
        }
        div[data-testid="stAlert"][data-alert-type="warning"] svg {
            fill: #92400E;
        }

        /* Sidebar Styling */
        .stSidebar {
            background-color: #262730;
        }
        .stSidebar h2, .stSidebar h3, .stSidebar label, .stSidebar .stMarkdown {
            color: #FAFAFA;
        }
        .stSidebar .stSelectbox > div[data-baseweb="select"] > div {
            background-color: #4B5563;
            border-radius: 8px;
            border: 1px solid #52525B;
        }
        .stSidebar .stSelectbox div[data-baseweb="select"] > div > div {
            color: #FAFAFA;
        }
        .stSidebar .stSelectbox svg {
            fill: #FAFAFA;
        }

        /* Main Content Area */
        h1, h2, h3 {
            color: #1E293B;
        }

        /* Input Text Area Styling */
        .stTextArea textarea {
            border: 1px solid #D1D5DB;
            border-radius: 8px;
            background-color: #FFFFFF;
            color: #1E293B;
            min-height: 100px;
            font-size: 1rem;
        }
        .stTextArea textarea::placeholder {
            color: #9CA3AF;
        }

        /* Submit Button Styling */
        div[data-testid="stVerticalBlock"] div:has(> div[data-testid="stHorizontalBlock"]) > div:nth-child(2) button[kind="primary"] {
            background-color: #0284c7;
            color: white;
            border: none;
            border-radius: 8px;
            padding: 0.5rem 1rem;
            transition: background-color 0.3s ease;
            height: 42px;
            margin-top: 28px; /* Adjust this margin to vertically align */
            font-weight: 500;
        }
        div[data-testid="stVerticalBlock"] div:has(> div[data-testid="stHorizontalBlock"]) > div:nth-child(2) button[kind="primary"]:hover {
            background-color: #0369a1;
        }
        div[data-testid="stVerticalBlock"] div:has(> div[data-testid="stHorizontalBlock"]) > div:nth-child(2) button[kind="primary"]:active {
            background-color: #075985;
        }

        /* Response Container Styling */
        .response-container {
            background-color: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 10px;
            padding: 25px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
            margin-top: 25px;
        }
        .response-container h3 {
            color: #1E293B;
            margin-bottom: 15px;
            padding-bottom: 5px;
            border-bottom: 1px solid #e5e7eb;
        }
        .response-container .stExpander {
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            margin-top: 15px;
            background-color: #f9fafb;
        }
        .response-container .stExpander header {
            font-weight: 500;
            color: #374151;
        }

        /* --- NEW STYLES FOR ALERT BOXES --- */

        /* Style for st.error (optional, but good for consistency) */
        div[data-testid="stAlert"][data-alert-type="error"] {
            background-color: #FEF2F2; /* Light red background */
            color: #B91C1C; /* Dark red text */
            border: 1px solid #FECACA; /* Soft red border */
            border-radius: 8px;
            padding: 1rem;
        }
         div[data-testid="stAlert"][data-alert-type="error"] svg {
            fill: #B91C1C;
        }

        /* Style for st.info (if you use it) */
        div[data-testid="stAlert"][data-alert-type="info"] {
            background-color: #EFF6FF; /* Light blue background */
            color: #1E40AF; /* Dark blue text */
            border: 1px solid #BFDBFE; /* Soft blue border */
            border-radius: 8px;
            padding: 1rem;
        }
         div[data-testid="stAlert"][data-alert-type="info"] svg {
            fill: #1E40AF;
        }

        /* Style for st.success (if you use it) */
        div[data-testid="stAlert"][data-alert-type="success"] {
            background-color: #F0FDF4; /* Light green background */
            color: #15803D; /* Dark green text */
            border: 1px solid #BBF7D0; /* Soft green border */
            border-radius: 8px;
            padding: 1rem;
        }
         div[data-testid="stAlert"][data-alert-type="success"] svg {
            fill: #15803D;
        }


        </style>
    """, unsafe_allow_html=True)

    # --- Rest of the app logic remains the same ---
    query, agent_level, submit_button = create_ui()

    if submit_button and query:
        with st.spinner("Processing your query..."):
            # Replace with your actual backend call
            response, explanation, status = process_query(query, agent_level)

            if status == "success":
                st.markdown("<div class='response-container'>", unsafe_allow_html=True)
                st.markdown("### Response")
                st.write(response)
                with st.expander("View retrieval details"):
                    st.markdown("#### Source Information")
                    st.write(explanation)
                st.markdown("</div>", unsafe_allow_html=True)
            elif status == "access_denied":
                # Uses the st.error style defined above
                st.error("Access Denied — Clearance Insufficient")
            elif status == "no_results":
                 # Uses the st.warning style defined above
                st.warning("No matching information found for your query.")
            elif status == "error": # Example for generic error
                 # Uses the st.error style defined above
                st.error("An error occurred during processing. Please try again.")
            else: # Fallback if status is unexpected
                st.error("An unexpected response status was received.")

    elif submit_button and not query:
         # Uses the st.warning style defined above
        st.warning("Please enter a query before submitting.")


if __name__ == "__main__":
    main()