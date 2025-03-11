import streamlit as st
from chatbot import create_chatbot

# Set up Streamlit UI
st.title("My Chatbot 🤖")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User input
user_input = st.text_input("Type your message...")

if user_input:
    # Display user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Generate bot response (Replace this with your chatbot logic)
    response = f"Bot says: {user_input[::-1]}"  # Placeholder response
    st.session_state.messages.append({"role": "assistant", "content": response})
    
    with st.chat_message("assistant"):
        st.markdown(response)


# run streamlit run streamlit_bot.py