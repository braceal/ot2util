# Pi Server 
This is the potential server code for the Raspberry Pi's working on top of the OT2's. 

### Requirements 
```bash
pip install fastapi 
pip install "uvicorn[standard]"
pip install opencv-python
```

### Running the Server 
1. Navigate to `camera_server/` folder 
2. Run command `uvicorn server:app --reload` to start the server on ip `127.0.0.1` with port `8000` 

Visit `http://127.0.0.1:8000/docs` to view the auto-generated OpenAPI docs and testing webpage. You can execute example commands there and see responses and what not. 

### Running the Example Client 
This assumes you have not modified the ip/port of the `uvicorn` server. 

`python example_client.py` will execute a script that tests some endpoints. 

- The first endpoint tested is the status endpoint, will tell you if the camera/cameras are operational. Can either leave with no path parameters, or put the camera id in the path parameter to see if the camera is working. 

- The second endpoint tested is the `get_image` endpoint. This one will pull up a screen with an image taken from your webcam. This part of the code demonstrates how we would use it in the ot2util. Press the key `q` to exit this and run the next command. 

- The final endpoint tests `get_image/1` with a camera id (I assume) that does not have a camera attatched to it. This just demonstrates we can handle camera errors without the server crashing. 
