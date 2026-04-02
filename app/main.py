from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from app.db import get_conn, create_schema

app = FastAPI()

origins = ["*"] # Change to the real front end origin in production

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

create_schema()

# Main route for this API
@app.get("/")
def read_root(): 
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT version() ")
        result = cur.fetchone()

    return { "msg": f"Hotel API!", "db_status": result }

# List all rooms 
@app.get("/rooms")
def get_rooms(): 
    rooms = [
        { "room_number": 101, "room_type": "single room", "price": 80 },
        { "room_number": 202, "room_type": "double room", "price": 120 },
        { "room_number": 404, "room_type": "suite", "price": 500 }
    ]
    return rooms

# Create booking
@app.post("/bookings")
def create_booking():
    return { "msg": "Booking created!"}




