import streamlit as st
import spacy
from openai import OpenAI
import os
from dotenv import load_dotenv
import asyncio
import sys
import tempfile

# Async fix for Streamlit in Python 3.11+
if sys.version_info >= (3, 11):
    asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())

# Load environment variables
load_dotenv()

# Set page configuration
st.set_page_config(
    page_title="Disney Parks Chatbot",
    page_icon="🏰",
    layout="centered"
)

# Initialize OpenAI API client with new method
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Download spaCy model if not present
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    import subprocess
    st.info("Downloading language model for the first time")
    subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
    nlp = spacy.load("en_core_web_sm")

# Function to convert text to speech using OpenAI TTS
def text_to_speech(text):
    try:
        # Create a temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
        temp_filename = temp_file.name
        temp_file.close()
        
        # Generate speech using OpenAI's TTS
        response = client.audio.speech.create(
            model="tts-1",
            voice="nova",  # A friendly, warm voice good for Disney content
            input=text
        )
        
        # Save to file
        response.stream_to_file(temp_filename)
        
        # Read the file
        with open(temp_filename, 'rb') as f:
            audio_bytes = f.read()
        
        # Clean up
        os.unlink(temp_filename)
        
        return audio_bytes
    except Exception as e:
        st.error(f"Error generating audio: {str(e)}")
        return None

# Sample FAQs with predefined responses
faq_responses = {
    "tickets": "Disney offers a variety of ticket options including single-day, multi-day, and Park Hopper tickets. Prices vary based on the season. Visit the official website for pricing and reservations.",
    "park reservations": "Park reservations are required in addition to tickets for entry. You can make a reservation through My Disney Experience. Make sure to check park availability before purchasing tickets.",
    "best attractions": "Top attractions include Space Mountain, Haunted Mansion, Star Wars: Rise of the Resistance, and Guardians of the Galaxy: Cosmic Rewind. Let me know your interests for a tailored recommendation!",
    "dining reservations": "Advanced Dining Reservations (ADRs) can be made up to 60 days in advance for most restaurants. Popular dining experiences like Cinderella's Royal Table and Be Our Guest require early booking.",
    "genie+": "Genie+ is a paid service that allows you to skip standby lines for certain attractions. It can be purchased through My Disney Experience and is available on a per-day basis. Lightning Lane access is limited, so book early in the day!",
    "transportation": "Disney offers complimentary transportation including buses, Monorail, Skyliner, and boats between parks and resorts. Ride-share services and parking options are also available.",
    "accommodations": "Disney Resorts range from Value to Deluxe categories, each offering unique themes and amenities. Deluxe resorts provide additional perks such as extended evening hours and closer proximity to the parks.",
    "weather policy": "Most attractions remain open during rain, but outdoor rides may temporarily close during storms. Ponchos and umbrellas are recommended for rainy days.",
    "refund policy": "Tickets are generally non-refundable but can be modified. Hotel cancellations depend on booking terms and how far in advance the cancellation is made.",
    "special events": "Disney hosts seasonal events such as Mickey's Not-So-Scary Halloween Party, EPCOT's Food & Wine Festival, and Very Merry Christmas Party. Special tickets may be required."
}

# Function to get response from OpenAI
def get_openai_response(prompt):
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful Disney theme parks expert assistant. Provide accurate, friendly information about Disney parks, resorts rides, attractions, Special Events, and policies. Keep responses concise, exciting, and factual for the customer."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=300,
            temperature=1.0
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Sorry, I couldn't generate a response at the moment. Error: {str(e)}"

# Function to get response from FAQ or OpenAI
def get_response(question):
    question_lower = question.lower()
    
    # Check if any FAQ keywords are in the question
    for key in faq_responses:
        if key in question_lower:
            return faq_responses[key], "FAQ"  # Return response and source
    
    # If no FAQ matches, use OpenAI to generate a response
    prompt = f"Please answer this Disney-related question: {question}"
    response = get_openai_response(prompt)
    return response, "AI"  # Return response and source

# Initialize session state for chat history
if 'messages' not in st.session_state:
    st.session_state.messages = []

# Disney-themed UI
st.title("🏰 Disney Parks Assistant")
st.markdown("Ask me anything about Disney parks, tickets, attractions, or planning tips!")

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Input for user question
if prompt := st.chat_input("What would you like to know about Disney?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Get response and source
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response, source = get_response(prompt)
            
            # Display response with source indicator
            st.markdown(response)
            
            # Add source indicator with appropriate styling
            if source == "FAQ":
                st.caption("ℹ️ This is a predefined answer from our FAQ database")
            else:
                st.caption("🤖 This response was generated by AI")
            
            # Add audio playback with a button
            audio_bytes = text_to_speech(response)
            if audio_bytes:
                st.write("🔊 Listen to response:")
                st.audio(audio_bytes, format="audio/mp3")
    
    # Add assistant response to chat history (include source in a hidden field)
    st.session_state.messages.append({
        "role": "assistant", 
        "content": response,
        "source": source  # Store source for potential future use
    })

# Sidebar with information
with st.sidebar:
    st.image("https://images.pexels.com/photos/3428289/pexels-photo-3428289.jpeg", width=200)
    st.title("About This Bot")
    st.markdown("""
    This Disney Parks Assistant helps you plan your Disney vacation by answering questions about:
    
    - Ticket options and pricing
    - Park reservations
    - Popular attractions
    - Dining reservations
    - Genie+ and Lightning Lane
    - Transportation options
    - Resort accommodations
    - Weather and refund policies
    - Special events and seasonal offerings
    
    Powered by AI to give you the most up-to-date information!
    """)
    
    # Add disclaimer
    st.markdown("---")
    st.caption("Disclaimer: This is an unofficial tool and not affiliated with The Walt Disney Company.")
