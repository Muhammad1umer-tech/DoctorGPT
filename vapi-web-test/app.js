import Vapi from "@vapi-ai/web";
import axios from 'axios';

(function () {
  const NativeWebSocket = window.WebSocket;

  function CustomWebSocket(url, protocols) {
    const ws = new NativeWebSocket(url, protocols);

    ws.addEventListener("error", function (event) {
      console.error("WebSocket error observed:", event);
      console.log("Error")
      handleError("WebSocket error. Please check your network connection.");
    });

    ws.addEventListener("close", function (event) {
      console.log("WebSocket closed:", event);
      // handleError("WebSocket connection closed. Please try again.");
    });

    return ws;
  }

  CustomWebSocket.prototype = NativeWebSocket.prototype;
  window.WebSocket = CustomWebSocket;
})();


const vapi = new Vapi("091e4b78-977e-440a-b8e5-14ca3d1f7505"); 

let callStartTime;
let timerInterval;
let isCalling = false; 
let outgoingCallSound;

vapi.onResult = function (result) {
  const outputElement = document.getElementById("output");
  if (outputElement) {
    outputElement.innerText = result.text;
  }
};

vapi.onError = function (error) {
  console.error(error);
  handleError(`Error: ${error.message || "An unknown error occurred."}`);
  clearInterval(timerInterval);
  updateTimer("");
  updateButtonState(false);
  isCalling = false;
  updateCallStatus("Call ended");
  stopOutgoingCallSound();
};

// Handle Vapi call events
vapi.on("call-start", () => {
      updateCallStatus("Call connected");

      console.log("Call connected")
      callStartTime = Date.now();
      timerInterval = setInterval(updateTimer, 1000);
      isCalling = true;
      updateButtonState(true);
      stopOutgoingCallSound();
});

vapi.on("call-end", () => {
  console.log("call end")
  updateCallStatus("Call ended");
  clearInterval(timerInterval);
  updateTimer("");
  updateButtonState(false);
  isCalling = false;
  stopOutgoingCallSound();
});

// Handle custom errors from Vapi
vapi.on("error", (error) => {
  console.error(error);
  handleError(`Error: ${error.errorMsg || "An unknown error occurred."}`);
  stopOutgoingCallSound();
});

document.addEventListener("DOMContentLoaded", () => {
  outgoingCallSound = document.getElementById("outgoingCallSound");
  const startButton = document.getElementById("startButton");
  const stopButton = document.getElementById("stopButton");
  var call_id = ''
  if (startButton) {
    startButton.addEventListener("click", async function () {
      if (isCalling) return;
      console.log("Start button clicked");
      updateCallStatus("Calling...");
      updateButtonState(true);
      playOutgoingCallSound();

      // axios.post('https://15fb-203-128-11-19.ngrok-free.app/free-slots')
      // .then(res=>{
      //   console.log(res, "free slots axios called")
      //   // const options = {method: 'GET', headers: {Authorization: 'Bearer a19109bb-65bd-45b0-b5f2-94a26d5f2956'}};
      //   // axios('https://api.vapi.ai/assistant/36720a00-0b59-406b-a814-bf3437e0f985', options)
      //   //   .then(response => console.log((response['data']['model']['messages'][0]['content'])))
      //   //   .catch(err => console.error(err));
      // })
      // .catch(error=>{
      //   console.log("free-slots error", error)
      // })
      

      // Get personaId from URL
      const urlParams = new URLSearchParams(window.location.search);
      const personaId = urlParams.get('personaId') || 'default';
      try {
        //await vapi.start(`e2eeb87f-661e-4dce-bd57-4068d8a90ca2-${personaId}`); // Replace with your actual Assistant ID

        const response = await vapi.start(`98d0d135-81cc-47ed-86f5-3e9cbb43e157`); // Replace with your actual Assistant ID
        call_id = response['id']

        updateButtonState(false);
        isCalling = false;
        updateCallStatus("Call failed");
        stopOutgoingCallSound();
      
      } catch (error) {
        handleError(
          `Error starting call: ${
            error.message || "An unknown error occurred."
          }`
        );
       
      }
    });
  }

  if (stopButton) {
    stopButton.addEventListener("click", async function () {
      if (!isCalling) return;
      console.log("Stop button clicked");
      try {
        await vapi.stop();
        updateCallStatus("Call ended");
        clearInterval(timerInterval);
        updateTimer("");
        updateButtonState(false);
        isCalling = false;
        stopOutgoingCallSound();

        // axios.post("https://15fb-203-128-11-19.ngrok-free.app/transcript", {call_id: call_id})
        // .then(res=>{
        //   console.log("transcript:", res.data)
        // })
        // .catch(error => {
        //   console.log("transcript error", error)
        // })

        // axios.get(`https://api.vapi.ai/call/${call_id}`, {
        //   headers: {
        //     'Authorization': `Bearer ${'a19109bb-65bd-45b0-b5f2-94a26d5f2956'}`
        //   }
        // })
        // .then(response => {
        //   console.log("transcript", response.data);
        // })
        // .catch(error => {
        //   console.error('Error fetching the call data:', error);
        // });


      } catch (error) {
        handleError(
          `Error stopping call: ${
            error.message || "An unknown error occurred."
          }`
        );
      }
    });
  }
});

function playOutgoingCallSound() {
  if (outgoingCallSound) {
    outgoingCallSound
      .play()
      .catch((e) => console.error("Error playing sound:", e));
  }
}

function stopOutgoingCallSound() {
  if (outgoingCallSound) {
    outgoingCallSound.pause();
    outgoingCallSound.currentTime = 0;
  }
}

function updateTimer() {
  const timerElement = document.getElementById("timer");
  if (timerElement && callStartTime) {
    const elapsedSeconds = Math.floor((Date.now() - callStartTime) / 1000);
    timerElement.innerText = `${Math.floor(elapsedSeconds / 60)}:${String(
      elapsedSeconds % 60
    ).padStart(2, "0")}`;
  }
}

function updateButtonState(isCallActive) {
  const startButton = document.getElementById("startButton");
  const stopButton = document.getElementById("stopButton");
  if (startButton) startButton.disabled = isCallActive;
  if (stopButton) stopButton.disabled = !isCallActive;
}

function handleError(message) {
  console.error(message);
  updateCallStatus(message);
  stopOutgoingCallSound();
}

function updateCallStatus(status) {
  const callStatusElement = document.getElementById("callStatus");
  if (callStatusElement) {
    callStatusElement.innerText = status;
  }
}

// Global error handler for WebSocket errors
window.addEventListener("error", (event) => {
  if (event.message.includes("WebSocket")) {
    handleError(
      "WebSocket connection error. Please check your network and try again."
    );
  }
});

window.addEventListener("unhandledrejection", (event) => {
  if (
    event.reason &&
    event.reason.message &&
    event.reason.message.includes("WebSocket")
  ) {
    handleError(
      "WebSocket connection error. Please check your network and try again."
    );
  }
});
