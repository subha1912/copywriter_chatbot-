import streamlit as st
from agent import ask   

st.set_page_config(page_title="Copywriter AI", page_icon="✍️", layout="wide")

st.title("✍️ Copywriter AI Agent")
st.write("Generate ads, blogs, LinkedIn posts, resumes, captions, posters & more.")

# Input box
user_input = st.text_area("Enter your request:", height=150, placeholder="e.g., Write a LinkedIn post about AI in marketing")

if st.button("Generate"):
    if user_input.strip():
        with st.spinner("Generating..."):
            output = ask(user_input)
        st.success("Here’s your result:")
        st.write(output)
    else:
        st.warning("Please type something before hitting Generate.")