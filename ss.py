import requests

url = "https://api.vapi.ai/assistant/{id}"

payload = {
    "transcriber": {
        "provider": "deepgram",
        "model": "nova-2",
        "language": "bg",
        "smartFormat": True,
        "keywords": ["<string>"]
    },
    "model": {
        "messages": [
            {
                "content": "<string>",
                "role": "assistant"
            }
        ],
        "tools": [
            {
                "async": True,
                "messages": [
                    {
                        "type": "request-start",
                        "content": "<string>",
                        "conditions": [
                            {
                                "value": "<string>",
                                "operator": "eq",
                                "param": "<string>"
                            }
                        ]
                    }
                ],
                "type": "dtmf",
                "function": {
                    "name": "<string>",
                    "description": "<string>",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": ["<string>"]
                    }
                },
                "server": {
                    "timeoutSeconds": 20,
                    "url": "<string>",
                    "secret": "<string>"
                }
            }
        ],
        "toolIds": ["<string>"],
        "provider": "anyscale",
        "model": "<string>",
        "temperature": 1,
        "knowledgeBase": {
            "provider": "canonical",
            "topK": 5.5,
            "fileIds": ["<string>"]
        },
        "maxTokens": 525,
        "emotionRecognitionEnabled": True,
        "numFastTurns": 1
    },
    "voice": {
        "inputPreprocessingEnabled": True,
        "inputReformattingEnabled": True,
        "inputMinCharacters": 30,
        "inputPunctuationBoundaries": ["。", "，", ".", "!", "?", ";", ")", "،", "۔", "।", "॥", "|", "||", ",", ":"],
        "fillerInjectionEnabled": True,
        "provider": "azure",
        "voiceId": "andrew",
        "speed": 1.25
    },
    "firstMessageMode": "assistant-speaks-first",
    "recordingEnabled": True,
    "hipaaEnabled": True,
    "clientMessages": ["conversation-update", "function-call", "hang", "model-output", "speech-update", "status-update", "transcript", "tool-calls", "user-interrupted", "voice-input"],
    "serverMessages": ["conversation-update", "end-of-call-report", "function-call", "hang", "speech-update", "status-update", "tool-calls", "transfer-destination-request", "user-interrupted"],
    "silenceTimeoutSeconds": 30,
    "responseDelaySeconds": 0.4,
    "llmRequestDelaySeconds": 0.1,
    "llmRequestNonPunctuatedDelaySeconds": 1.5,
    "numWordsToInterruptAssistant": 5,
    "maxDurationSeconds": 1800,
    "backgroundSound": "office",
    "backchannelingEnabled": True,
    "backgroundDenoisingEnabled": True,
    "modelOutputInMessagesEnabled": True,
    "transportConfigurations": [
        {
            "provider": "twilio",
            "timeout": 60,
            "record": True,
            "recordingChannels": "mono"
        }
    ],
    "name": "<string>",
    "blockId": "<string>",
    "block": {
        "messages": [
            {
                "conditions": [
                    {
                        "type": "model-based",
                        "instruction": "<string>"
                    }
                ],
                "type": "block-start",
                "content": "<string>"
            }
        ],
        "inputSchema": {
            "type": "string",
            "items": {},
            "properties": {},
            "description": "<string>",
            "required": ["<string>"]
        },
        "outputSchema": {
            "type": "string",
            "items": {},
            "properties": {},
            "description": "<string>",
            "required": ["<string>"]
        },
        "type": "workflow",
        "steps": [
            {
                "block": {
                    "messages": [
                        {
                            "conditions": [
                                {
                                    "type": "model-based",
                                    "instruction": "<string>"
                                }
                            ],
                            "type": "block-start",
                            "content": "<string>"
                        }
                    ],
                    "inputSchema": {
                        "type": "string",
                        "items": {},
                        "properties": {},
                        "description": "<string>",
                        "required": ["<string>"]
                    },
                    "outputSchema": {
                        "type": "string",
                        "items": {},
                        "properties": {},
                        "description": "<string>",
                        "required": ["<string>"]
                    },
                    "type": "conversation",
                    "instruction": "<string>",
                    "name": "<string>"
                },
                "type": "handoff",
                "destinations": [
                    {
                        "type": "step",
                        "conditions": [
                            {
                                "type": "model-based",
                                "instruction": "<string>"
                            }
                        ],
                        "stepName": "<string>"
                    }
                ],
                "name": "<string>",
                "blockId": "<string>",
                "input": {}
            }
        ],
        "id": "<string>",
        "orgId": "<string>",
        "createdAt": "2023-11-07T05:31:56Z",
        "updatedAt": "2023-11-07T05:31:56Z",
        "name": "<string>"
    },
    "firstMessage": "<string>",
    "voicemailDetection": {
        "provider": "twilio",
        "voicemailDetectionTypes": ["machine_end_beep", "machine_end_silence"],
        "enabled": True,
        "machineDetectionTimeout": 31,
        "machineDetectionSpeechThreshold": 3500,
        "machineDetectionSpeechEndThreshold": 2750,
        "machineDetectionSilenceTimeout": 6000
    },
    "voicemailMessage": "<string>",
    "endCallMessage": "<string>",
    "endCallPhrases": ["<string>"],
    "metadata": {},
    "serverUrl": "<string>",
    "serverUrlSecret": "<string>",
    "analysisPlan": {
        "summaryPrompt": "<string>",
        "summaryRequestTimeoutSeconds": 10.5,
        "structuredDataRequestTimeoutSeconds": 10.5,
        "successEvaluationPrompt": "<string>",
        "successEvaluationRubric": "NumericScale",
        "successEvaluationRequestTimeoutSeconds": 10.5,
        "structuredDataPrompt": "<string>",
        "structuredDataSchema": {
            "type": "string",
            "items": {},
            "properties": {},
            "description": "<string>",
            "required": ["<string>"]
        }
    },
    "artifactPlan": {"videoRecordingEnabled": True},
    "messagePlan": {
        "idleMessages": ["<string>"],
        "idleMessageMaxSpokenCount": 5.5,
        "idleTimeoutSeconds": 17.5
    }
}
headers = {
    "Authorization": "Bearer <token>",
    "Content-Type": "application/json"
}

response = requests.request("PATCH", url, json=payload, headers=headers)

print(response.text)