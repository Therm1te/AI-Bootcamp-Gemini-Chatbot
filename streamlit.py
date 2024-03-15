import streamlit as st
import google.generativeai as genai
from amadeus import Client, ResponseError
import os
from dotenv import load_dotenv, find_dotenv
import requests

PROMPT = """
SYSTEM MESSAGE: You are a chatbot designed to assist users with their queries about their travelplan to different cities within Pakistan only. User will ask you about this information. Making sure that the flight details prompt given by you is correct as per user query if not, then respond with "No Flights Available".
START OF CHAT: Now introduce yourself.
"""

r_PROMPT = """
Your task is to extract a parameter from USER INPUT. User will ask you about the weather of a certain city. You have to identify the city name and respond only with that city name.
USER INPUT: {}
"""

aio_flight_PROMPT = """
Your task is to extract 3 parameters from the USER INPUT. User will tell you the Departure City, Arrival City, and Departure Date. You have to identify the Departure city name, Arrival City Name and Departure Date and respond only with the Departure City Name, Arrival City Name, and Departure Date. The Departure Date should be in the YYYY/MM/DD format. Create a python list and store value of Departure City Name in the list index 0, store the Arrival City Name value in the list index 1, store the Departure Date value in list index 2.
USER INPUT: {}
"""

departure_city_PROMPT = """
Your task is to extract a parameter from the USER INPUT. User will tell you the Departure City, Arrival City, and Departure Date. You have to identify the Departure city name and respond only with the IATA Airport Code of the Departure City.
USER INPUT: {}
"""
arrival_city_PROMPT = """
Your task is to extract a parameter from the USER INPUT. User will tell you the Departure City, Arrival City, and Departure Date. You have to identify the Arrival City Name and respond only with the IATA Airport Code of the Arrival City.
USER INPUT: {}
"""

departure_date_PROMPT = """
Your task is to extract a parameter from the USER INPUT. User will tell you the Departure City, Arrival City, and Departure Date. You have to identify the Departure Date and respond only with the Departure Date in the YYYY-MM-DD format.
USER INPUT: {}
"""

# Initialize Gemini-Pro 
load_dotenv(find_dotenv())
genai.configure()
model = genai.GenerativeModel('gemini-1.0-pro-latest')
amadeus = Client(client_id = os.getenv("client_id"), client_secret = os.getenv("client_secret"))

def get_traveldata(departure_city, arrival_city, departure_date, adults=1):
    response = amadeus.shopping.flight_offers_search.get(
        originLocationCode=str(departure_city),
        destinationLocationCode=str(arrival_city),
        departureDate=str(departure_date),
        adults=adults)
    best_flight = response.data[0]
    flight_ticket_data = {
        "departure_airportcode" : best_flight.get("itineraries")[0].get("segments")[0].get("departure").get("iataCode"),
        "arrival_airportcode" : best_flight.get("itineraries")[0].get("segments")[0].get("arrival").get("iataCode"),
        "departure_time" : best_flight.get("itineraries")[0].get("segments")[0].get("departure").get("at"),
        "arrival_time" : best_flight.get("itineraries")[0].get("segments")[0].get("arrival").get("at"),
        "flight_carriercode" : best_flight.get("itineraries")[0].get("segments")[0].get("carrierCode"),
        "flight_number" : best_flight.get("itineraries")[0].get("segments")[0].get("number"),
        "price_currency" : best_flight.get("price").get("currency"),
        "price" : best_flight.get("price").get("grandTotal"),
        "cabin_class" : best_flight.get("travelerPricings")[0].get("fareDetailsBySegment")[0].get("cabin"),
        "available_seats" : best_flight.get("numberOfBookableSeats"),
        "last_booking_date" : best_flight.get("lastTicketingDate")
    }
    return flight_ticket_data



# Gemini uses 'model' for assistant; Streamlit uses 'assistant'
def role_to_streamlit(role):
  if role == "model":
    return "assistant"
  else:
    return role

# Add a Gemini Chat history object to Streamlit session state
if "chat" not in st.session_state:
    st.session_state.chat = model.start_chat(history = [])
    st.session_state.chat.send_message(PROMPT)

# Display Form Title
st.title("Chat with Google Gemini-1.0-Pro!")

# Display chat messages from history above current input box
for message in st.session_state.chat.history[1:]:
    with st.chat_message(role_to_streamlit(message.role)):
        st.markdown(message.parts[0].text)

# Accept user's next message, add to context, resubmit context to Gemini
if prompt := st.chat_input("I possess a well of knowledge. What would you like to know?"):
    # Display user's last message
    st.chat_message("user").markdown(prompt)

#    f_response = model.generate_content(r_PROMPT.format(prompt))
#    print(f_response.text)

    departure_city_response = model.generate_content(departure_city_PROMPT.format(prompt))
    #st.write(str(departure_city_response.text))

    arrival_city_response = model.generate_content(arrival_city_PROMPT.format(prompt))
    #st.write(str(arrival_city_response.text))

    departure_date_response = model.generate_content(departure_date_PROMPT.format(prompt))
    #st.write(str(departure_date_response.text))

    ff_response = get_traveldata(departure_city_response.text, arrival_city_response.text, departure_date_response.text)
    #st.write(ff_response)
    print(str(ff_response))
    crresponse = requests.get('https://v6.exchangerate-api.com/v6/13766065a1a612690dfb5e98/latest/EUR')
    crdata = crresponse.json()
    crrate = crdata.get("conversion_rates").get("PKR")
    currencyconvert = int(float(ff_response.get("price"))) * int(crrate)
    ff_response["price"] = str(currencyconvert)
    ff_response["price_currency"] = "PKR"
    # Send user entry to Gemini and read the response
    response = st.session_state.chat.send_message(prompt+"\n\nRESPONSE FROM THE AIR TRAFFIC CONTROL CENTER:\n"+str(ff_response))
    
    # Display last 
    with st.chat_message("assistant"):
        st.markdown(response.text)
