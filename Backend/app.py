from fastapi import FastAPI, Request
import datetime
import os
import json
from fastapi.responses import JSONResponse
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
# from google.auth.transport.requests import Request
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
from langchain.output_parsers import ResponseSchema
from langchain.output_parsers import StructuredOutputParser

app = FastAPI()

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
    from google.auth.transport.requests import Request
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


@app.post("/current-time-date")
async def get_current_time_datae(request: Request):
    print("time ", request)
    data = await request.json()  # Parse the incoming JSON data
    
    karachi_tz = pytz.timezone('Asia/Karachi')
    karachi_time = datetime.datetime.now(karachi_tz)

    print(karachi_time.strftime('%I:%M%p, %A, %d %B, %Y'))

    return {
        "results": [
            {
                "toolCallId": data["message"]["toolCalls"][0]['id'],
                "result": karachi_time.strftime(karachi_time.strftime('%I:%M%p, %A, %d %B, %Y'))
            }
        ]
    }

@app.post("/get-free-slots")
async def free_slots(request: Request):
    print("slots ", request)
    data = await request.json() # Parse the incoming JSON data

    SCOPES = ['https://www.googleapis.com/auth/calendar']
    creds = authenticate_google_account(SCOPES)
    service = build('calendar', 'v3', credentials=creds)

    free_slots = get_free_slots(service)

    print(free_slots)
    return {
        "results": [
            {
                "toolCallId": data["message"]["toolCalls"][0]['id'],
                "result": str(free_slots)
            }
        ]
    }

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

@app.post("/book-apointment")
async def book_apointment(request: Request):
    print("book-apointment ")
    data = await request.json() # Parse the incoming JSON data

    print(data['message']['toolCalls'][0]['function']['arguments'])

    output_dict = data['message']['toolCalls'][0]['function']['arguments']

    tz = pytz.timezone('Asia/Karachi')

    date_format = "%d %B %Y, %I:%M%p"
    
    try:
        start_datetime = datetime.datetime.strptime(output_dict['Start date and time'], date_format)
        end_datetime = datetime.datetime.strptime(output_dict['End date and time'], date_format)

    except ValueError:
        date_format = '%d %B %Y, %I:%M %p'
        start_datetime = datetime.datetime.strptime(output_dict['Start date and time'], date_format)
        end_datetime = datetime.datetime.strptime(output_dict['End date and time'], date_format)


    start_datetime = tz.localize(start_datetime)
    end_datetime = tz.localize(end_datetime)    
    book_slot(start_datetime, end_datetime, output_dict['name'], output_dict['email'])


    return  {
        "results": [
            {
                "toolCallId": data["message"]["toolCalls"][0]['id'],
                "result": "successfull"
            }
        ]
    }
