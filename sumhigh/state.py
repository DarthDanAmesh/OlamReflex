# state.py
import reflex as rx
import asyncio

# state.py
import os
import requests
import json

class State(rx.State):
    # The current question being asked.
    question: str

    # Keep track of the chat history as a list of (question, answer) tuples.
    chat_history: list[tuple[str, str]]

    @rx.event
    async def answer(self):
        # Use local Ollama API for Llama 3.2
        ollama_url = "http://localhost:11434/api/chat"
        
        # Prepare the request payload
        payload = {
            "model": "llama3.2",
            "messages": [
                {"role": "user", "content": self.question}
            ],
            "stream": True
        }
        
        # Start the answer and update chat history
        answer = ""
        self.chat_history.append((self.question, answer))
        self.question = ""
        yield
        
        # Stream the response
        try:
            response = requests.post(
                ollama_url, 
                json=payload, 
                stream=True
            )
            
            # Process streamed response
            for line in response.iter_lines():
                if line:
                    # Parse the JSON response
                    decoded_line = line.decode('utf-8')
                    try:
                        chunk = json.loads(decoded_line)
                        
                        # Check if the chunk contains content
                        if 'message' in chunk and 'content' in chunk['message']:
                            content = chunk['message']['content']
                            answer += content
                            self.chat_history[-1] = (
                                self.chat_history[-1][0],
                                answer,
                            )
                            yield
                        
                        # Check for stream completion
                        if chunk.get('done', False):
                            break
                    
                    except json.JSONDecodeError:
                        # Handle potential JSON parsing errors
                        continue
        
        except Exception as e:
            # Error handling
            print(f"Error in Ollama API call: {e}")
            self.chat_history[-1] = (
                self.chat_history[-1][0],
                "Error processing response"
            )
            yield