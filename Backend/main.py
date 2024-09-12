# main.py
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from collections import defaultdict
import datetime
import os
import json
import pytz
import requests
import time
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langchain.output_parsers import ResponseSchema, StructuredOutputParser

# Global Variables
global_call_id = None

# FastAPI App Initialization
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Helper Functions
def authenticate_google_account(SCOPES):
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

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
        busy_times = [(event['start'].get('dateTime', event['start'].get('date')),
                       event['end'].get('dateTime', event['end'].get('date'))) for event in events]
        busy_times.sort()
        current_time = day_start

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

    slots = defaultdict(list)
    for start, end in free_slots:
        dt_start = start.astimezone(local_tz)
        dt_end = end.astimezone(local_tz)
        date_key = dt_start.strftime('%A, %d %B, %Y')
        time_range = f"{dt_start.strftime('%I:%M %p')} to {dt_end.strftime('%I:%M %p')}, "
        slots[date_key].append(time_range)

    return dict(slots)

def book_slot(start_time, end_time, summary, description):
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    creds = authenticate_google_account(SCOPES)
    service = build('calendar', 'v3', credentials=creds)
    event = {
        'summary': summary,
        'description': description,
        'start': {'dateTime': start_time.isoformat(), 'timeZone': 'UTC'},
        'end': {'dateTime': end_time.isoformat(), 'timeZone': 'UTC'},
    }
    event_result = service.events().insert(calendarId='primary', body=event).execute()
    print("Booked.", event_result)
    return event_result

def vapi_system_prompt(free_slots):
    system_prompt = f"""
    You are a voice virtual assistant responsible for scheduling appointments for Dr. Smith, who is available Monday to Friday from 9 AM to 5 PM.

    Tone: Keep your tone of voice assistant and use words like umm, uh to keep it realistic and prohibit the response that does not align with voice format. 
    Lets do it Step by Step:
    1. Learn the available slots timing well. The available slots timing are {str(free_slots)}.
    2. Be clear about the day and then its available timings when telling  the avaibale slots to the caller.
    3. When confirming a appointment, must clarify the name and contact and reason for visit.
    4. Remind the patient to arrive 10 minutes early and bring any relevant medical records.
    5. Ensure user give start time and end time before booking an apointment

    Note: If user's asked slot is not available then suggest him/her other available slot for today or tomorrow.
    """
    url = "https://api.vapi.ai/assistant/36720a00-0b59-406b-a814-bf3437e0f985"
    payload = {
        "model": {
            "messages": [{"content": system_prompt, "role": "system"}],
            "provider": "openai",
            "model": "gpt-4o"
        }
    }
    headers = {
        "Authorization": "Bearer a19109bb-65bd-45b0-b5f2-94a26d5f2956",
        "Content-Type": "application/json"
    }
    response = requests.request("PATCH", url, json=payload, headers=headers)
    print("\nResponse of request\n", response)
    get_system_prompt()

def get_system_prompt():
    url = "https://api.vapi.ai/assistant/36720a00-0b59-406b-a814-bf3437e0f985"
    headers = {"Authorization": "Bearer a19109bb-65bd-45b0-b5f2-94a26d5f2956"}
    response = requests.request("GET", url, headers=headers)
    parsed_data = response.json()
    content = parsed_data['model']['messages'][0]['content']
    print("GETTING SYSTEM PROMPT\n", content)

def langcahin_output_parse(transcript):
    review_template = """\
    For the following text, extract the following information:

    Agreed: Did the user agree and book an appointment?\
    Did the AI agent book the appointment successfully?\
    Answer "True" if yes,\
    "False" if not.

    datetime: Extract datetime\
    from the given transcript\
    if appointment is successfully booked answer in the format of \
    start datetime: 09 August 2024, 09:00AM (these are dummy date and time, don't use this)\
    end datetime: 09 August 2024, 10:00AM (these are dummy date and time, don't use this)\
    otherwise answer "None"\

    text: {text}

    {format_instructions}
    """
    prompt_template = ChatPromptTemplate.from_template(review_template)
    agreed_schema = ResponseSchema(name="Agreed", description="Did the user agree and book an appointment? Did the AI agent book the appointment successfully? Answer True if yes, False if not.")
    start_date_schema = ResponseSchema(name="start datetime", description="Extract start datetime from the given transcript if appointment is successfully booked otherwise answer None")
    end_date_schema = ResponseSchema(name="end datetime", description="Extract end datetime from the given transcript if appointment is successfully booked otherwise answer None")
    response_schemas = [agreed_schema, start_date_schema, end_date_schema]
    output_parser = StructuredOutputParser.from_response_schemas(response_schemas)
    format_instructions = output_parser.get_format_instructions()
    prompt = ChatPromptTemplate.from_template(template=review_template)
    messages = prompt.format_messages(text=transcript, format_instructions=format_instructions)
    chat = ChatGroq(temperature=0, groq_api_key="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", model_name="llama3-8b-8192")
    response = chat(messages)
    output_dict = output_parser.parse(response.content)
    print(output_dict)
    if output_dict['Agreed'] == 'False':
        print("Not agreed on")
        return
    date_format = "%d %B %Y, %I:%M%p"
    tz = pytz.timezone('Asia/Karachi')
    start_datetime = datetime.datetime.strptime(output_dict['start datetime'], date_format)
    end_datetime = datetime.datetime.strptime(output_dict['end datetime'], date_format)
    start_datetime = tz.localize(start_datetime)
    end_datetime = tz.localize(end_datetime)
    book_slot(start_datetime, end_datetime, "Booked", "Booked slot")

# Pydantic Models
class TranscriptRequest(BaseModel):
    call_id: str

# API Endpoints
@app.post("/transcript")
def transcript(request: TranscriptRequest):
    print(request.call_id)
    url = f"https://api.vapi.ai/call/{request.call_id}"
    headers = {"Authorization": f"Bearer a19109bb-65bd-45b0-b5f2-94a26d5f2956"}
    time.sleep(10)
    response = requests.request("GET", url, headers=headers)
    print(response.status_code)
    if response.status_code != 200:
        return JSONResponse(content={"error": "Failed to fetch transcript"}, status_code=response.status_code)
    transcript = response.json().get("transcript")
    langcahin_output_parse(transcript)
    return {"transcript": transcript}

@app.post("/current-time")
async def get_current_time(request: Request):
    data = await request.json()
    karachi_tz = pytz.timezone('Asia/Karachi')
    karachi_time = datetime.datetime.now(karachi_tz)
    print(karachi_time.strftime('%I:%M %p'), data["message"]["toolCalls"][0]['id'])
    return {
        "results": [
            {
                "toolCallId": data["message"]["toolCalls"][0]['id'],
                "result": karachi_time.strftime('%I:%M %p')
            }
        ]
    }

@app.post("/get-free-slots")
async def get_free_slots(request: Request):
    data = await request.json()
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    creds = authenticate_google_account(SCOPES)
    service = build('calendar', 'v3', credentials=creds)
    free_slots = get_free_slots(service)
    vapi_system_prompt(free_slots)
    return JSONResponse(content=free_slots)

    