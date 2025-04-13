# src/app/ui.py
import streamlit as st

def create_ui():
    """
    Creates the Streamlit UI components for the Project SHADOW application.

    Returns:
        tuple: Contains (query, agent_level, submit_button) user inputs
    """
    # Sidebar for agent level selection (remains the same)
    with st.sidebar:
        st.markdown("## Agent Settings")
        agent_level = st.selectbox(
            "Select your clearance level:",
            options=["Level 1 (Low)", "Level 2 (Medium)", "Level 3 (High)"],
            index=0
        )

        st.markdown("---")
        st.markdown("### About Project SHADOW")
        st.markdown("""
        This application provides secure access to classified information
        based on your clearance level. Only authorized personnel can
        access sensitive information.
        """)

    # Header and description (move below sidebar setup if preferred, but fine here)
    st.title("Project SHADOW")
    st.subheader("Secure Hierarchical Access to Document Operations Workflow")
    st.markdown("---") # Add a separator

    # Main area for query input using columns
    st.markdown("## Information Retrieval System")

    # Create columns for input field and button
    col1, col2 = st.columns([6, 1]) # Adjust ratio as needed (e.g., 5, 1 or 7, 1)

    with col1:
        query = st.text_area(
            "Enter your query:",
            height=100, # Adjust height if needed
            max_chars=500,
            placeholder="What information are you looking for?",
            label_visibility="collapsed" # Hide the label above the text area
        )

    with col2:
        # Add some vertical space to better align button with text area (adjust as needed)
        st.write("") # Add a little space
        st.write("") # Add a little space
        submit_button = st.button(
            "Submit", # Use shorter text for the button
            use_container_width=True,
            key="submit_query" # Add a key for better state management
            )

    return query, agent_level, submit_button