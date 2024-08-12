# main.py
from fastapi import FastAPI
import datetime
import os
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pytz
from collections import defaultdict
from fastapi.middleware.cors import CORSMiddleware
import requests
from pydantic import BaseModel
import time
from groq import Groq
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # List of allowed origins
    allow_credentials=True,
    allow_methods=["*"],  # List of allowed methods, e.g., ["GET", "POST"]
    allow_headers=["*"],  # List of allowed headers
)

def get_free_slots(service, calendar_id='primary'):
    local_tz = pytz.timezone('Asia/Karachi')
    now = datetime.datetime.now(local_tz)

    free_slots = []

    for day_offset in range(3):
        day_start = (now + datetime.timedelta(days=day_offset)).replace(hour=9, minute=0, second=0, microsecond=0)
        day_end = (now + datetime.timedelta(days=day_offset)).replace(hour=17, minute=0, second=0, microsecond=0)
        
        day_start_iso = day_start.isoformat()
        day_end_iso = day_end.isoformat()

        events_result = service.events().list(calendarId=calendar_id, timeMin=day_start_iso,
                                              timeMax=day_end_iso, singleEvents=True,
                                              orderBy='startTime').execute()
        events = events_result.get('items', [])

        busy_times = []
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))
            busy_times.append((start, end))

        # Sort the busy times based on start time
        busy_times.sort()

        current_time = day_start

        # If there are no events, the whole day is free
        if not busy_times:
            free_slots.append((current_time, day_end))
        else:
            for busy_start, busy_end in busy_times:
                busy_start = datetime.datetime.fromisoformat(busy_start)
                busy_end = datetime.datetime.fromisoformat(busy_end)
                
                if current_time < busy_start:
                    free_slots.append((current_time, busy_start))
                current_time = max(current_time, busy_end)

            if current_time < day_end:
                free_slots.append((current_time, day_end))

    # Organize free slots into ranges
    slots = defaultdict(list)
    for start, end in free_slots:
        dt_start = start.astimezone(local_tz)
        dt_end = end.astimezone(local_tz)
        date_key = dt_start.strftime('%A, %d %B, %Y')
        time_range = f"{dt_start.strftime('%I:%M %p')} to {dt_end.strftime('%I:%M %p')}, "
        slots[date_key].append(time_range)

    # Convert defaultdict to regular dict
    slots = dict(slots)

    return slots

def authenticate_google_account(SCOPES):
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

def book_slot(start_time, end_time, summary, description):
    
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    creds = authenticate_google_account(SCOPES)
    service = build('calendar', 'v3', credentials=creds)
    event = {
        'summary': summary,
        'description': description,
        'start': {
            'dateTime': start_time.isoformat(),
            'timeZone': 'UTC',
        },
        'end': {
            'dateTime': end_time.isoformat(),
            'timeZone': 'UTC',
        },
    }

    event_result = service.events().insert(calendarId='primary', body=event).execute()
    print("Booked.", event_result)
        
    return event_result

def vapi_system_prompt(free_slots):
    print("before upatae",get_system_prompt())

    system_prompt = f"""
    You are a voice virtual assistant responsible for scheduling appointments for Dr. Smith, who is available Monday to Friday from 9 AM to 5 PM.

    Tone: Keep your tone of voice assistant and use words like umm, uh to keep it realistic and prohibit the response that does not align with voice format. 
    Lets do it Step by Step:
    1. Learn the available slots timing well. The available slots timing are {str(free_slots)}.
    2. Be clear about the day and then its available timings when telling  the avaibale slots to the caller.
    3. When confirming a appointment, must clarify the name and contact and reason for visit.
    4. Before confirmation a appointment, repeat the appointment details and get it verfied from caller.
    5. Remind the patient to arrive 10 minutes early and bring any relevant medical records.

    Note: If user's asked slot is not available then suggest him/her other available slot for today or tomorrow.

    """    

    # system_prompt += str(free_slots)
    # print(system_prompt)

    url = "https://api.vapi.ai/assistant/36720a00-0b59-406b-a814-bf3437e0f985"
    payload = {
        
        "model": {
            "messages": [
                {
                    "content": system_prompt,
                    "role": "system"
                }
            ],
            "provider":"openai",
            "model":"gpt-4o"
            
            }
        }
    headers = {
        "Authorization": "Bearer a19109bb-65bd-45b0-b5f2-94a26d5f2956",
        "Content-Type": "application/json"
    }
    response = requests.request("PATCH", url, json=payload, headers=headers)
    print("\n respinse of req \n",response)
    get_system_prompt()
    # print("post-vapi", response.text)

def get_system_prompt():
    url = "https://api.vapi.ai/assistant/36720a00-0b59-406b-a814-bf3437e0f985"
    headers = {"Authorization": "Bearer a19109bb-65bd-45b0-b5f2-94a26d5f2956"}
    response = requests.request("GET", url, headers=headers)
    parsed_data = response.json()

    # Extract content
    content = parsed_data['model']['messages'][0]['content']
    print("GETTING SYSTEM PROMPT\n",content)

class TranscriptRequest(BaseModel):
    call_id: str
    
@app.post("/transcript")
def transcript(request: TranscriptRequest):
    print(request.call_id)
    url = f"https://api.vapi.ai/call/{request.call_id}"
    headers = {"Authorization": f"Bearer a19109bb-65bd-45b0-b5f2-94a26d5f2956"}
    

    time.sleep(10)

    response = requests.request("GET", url, headers=headers)
    
    print(response.status_code)
    if response.status_code != 200:
        return jsonify({"error": "Failed to fetch transcript"}), response.status_code
        
    transcript = response.json().get("transcript")
    print(transcript)
    langchain_model(transcript)
    return transcript
    

@app.get("/free-slots")
def read_free_slots():
    print("read_free_slots")
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    creds = authenticate_google_account(SCOPES)
    service = build('calendar', 'v3', credentials=creds)
    free_slots = get_free_slots(service)
    vapi_system_prompt(free_slots)

    return JSONResponse(content={"free_slots": free_slots})


def langchain_model(transcript):
    chat = ChatGroq(temperature=0, groq_api_key="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", model_name="llama3-8b-8192")
    
    prompt = f"""I have given you that text that is delimited by triple backticks \
    Give me the free slot, time and data that user and AI has agreed on to book an apointment or follow up. \
    format of date and time should be like 09 August 2024, 9:00AM to 10:00AM \
    just give me date and time only, i dont need any other text. (no more text other than date and time)\
    firstly, if AI and user has agreed on some date and time to book an apointment then give me date and time \
    other wise give me NULL
    text: ```{transcript}```
    """
    prompt_template = ChatPromptTemplate.from_template(prompt)
    custom_messages = prompt_template.format_messages(
                    transcript=transcript)

    date = chat(custom_messages)
    if date.content == 'NULL':
        print("Not agreed on")
    else:
        print("langchain model", date.content)
        date_part, time_range = str(date.content).split(", ", 1)

        start_time_str, end_time_str = time_range.split(" to ")

        start_datetime_str = f"{date_part}, {start_time_str}"
        end_datetime_str = f"{date_part}, {end_time_str}"

        date_format = "%d %B %Y, %I:%M%p"

        start_datetime = datetime.datetime.strptime(start_datetime_str, date_format)
        end_datetime = datetime.datetime.strptime(end_datetime_str, date_format)

        tz = pytz.timezone('Asia/Karachi')
        start_datetime = tz.localize(start_datetime)
        end_datetime = tz.localize(end_datetime)

        # Print the datetime in the desired format
        print(f"{start_datetime.isoformat()} - {end_datetime.isoformat()}")
        book_slot(start_datetime, end_datetime, "Booked", "Booked slot")



# langchain_model("""AI: Hello? This is Mary from doctor ai assistant. How can I assist you today?
# User: Schedule by appointment for today, around 2 PM to 3 PM.
# AI: Sorry. There are no available slots for today. The next available slots are for Friday.
# User: Okay. Give me start for Friday from 2 PM to 3 PM.
# AI: Sorry. This slot is already booked. The available slots on
# User: What about 1 to 2 PM?
# AI: The available slots on Friday, August ninth, 20 24 are from 9 AM to 3 PM and from 4 PM to 5 PM. Could we book the appointment?
# User: Chris, okay. Bookmaster from 2 PM to 3 PM.
# AI: Sorry. This slot is already booked. The remaining available slots on Friday, 0 9 August 20 24, are from 9 AM to 2 PM. To 3 PM.
# User: Okay. Book my slot for 9 AM to 10. AM.
# AI: Your appointment is now scheduled for Friday, 0 9 August 20 24.
# User: Thank you.
# AI: From 9 AM.""")


# read_free_slots()
