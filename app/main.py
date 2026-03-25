from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

app = FastAPI()

my_name = "Fredde"

# Main route for this API
@app.get("/")
def read_root(): 
    # f-string concatenation
    return { "msg": f"Hello {my_name}"}

# What is my ip 
@app.get("/api/ip")
def api_ip(request: Request): 
    # f-string concatenation
    return { "ip": request.client.host }

@app.get("/ip", response_class=HTMLResponse)
def html_ip(request: Request):
    return f"<h1>Your IP is {request.client.host}</h1>"




