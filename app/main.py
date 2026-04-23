from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import HTMLResponse
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import date
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

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def validate_key(api_key: str = Depends(api_key_header)):
    if not api_key:
        raise HTTPException(status_code=401, detail={"error": "API Key missing!"})
    
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT * FROM guests WHERE api_key = %s
        """, [api_key] )
        guest = cur.fetchone()
        if not guest:
            raise HTTPException(status_code=401, detail={"error": "Bad API Key!"})
        return guest

# Data model for bookings
class Booking(BaseModel):
    #guest_id: int # this will come from the API Key
    room_id: int
    datefrom: date
    dateto: date
    info: str

# Data model for bookings
class BookingUpdate(BaseModel):
    stars: int

# Main route for this API
@app.get("/")
def read_root(): 
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT version() ")
        result = cur.fetchone()

    return { "msg": f"Hotel API!", "db_status": result }


# List all guests 
@app.get("/guests")
def get_guests(): 
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT 
                g.*,
                (SELECT count(*) 
                    FROM bookings
                    WHERE guest_id = g.id
                        AND dateto < now()
                    ) as previous_visits
            FROM guests g    
            ORDER BY g.lastname
        """)
        guests = cur.fetchall()
    return guests

# List all rooms 
@app.get("/rooms")
def get_rooms(): 
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT * FROM rooms")
        rooms = cur.fetchall()
    return rooms

# Get one room
@app.get("/rooms/{id}")
def get_one_room(id: int): 
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT * 
            FROM rooms 
            WHERE id = %s
        """, (id,)) # <- tuple, list is also fine: [id]
        room = cur.fetchone()
    return room

# List all bookings 
@app.get("/bookings")
def get_bookings(guest: dict = Depends(validate_key)): 
    print(guest)
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT 
                r.room_number,
                g.firstname || ' ' || g.lastname AS guest_name,
                b.dateto - b.datefrom AS nights,
                r.price AS price_per_night,
                (b.dateto - b.datefrom) * r.price AS gross_price,
                CASE
                    WHEN b.dateto - b.datefrom >= 7 THEN 
                        (b.dateto - b.datefrom) * r.price * 0.8
                    ELSE (b.dateto - b.datefrom) * r.price
                END AS total_price,
                b.*
            FROM bookings b
            INNER JOIN rooms r
                ON r.id = b.room_id
            INNER JOIN guests g
                ON g.id = b.guest_id
            WHERE b.guest_id = %s
            ORDER BY b.id DESC        
        """, [guest['id']])
        b = cur.fetchall()
    return b

# Create booking
@app.post("/bookings")
def create_booking(booking: Booking, guest: dict = Depends(validate_key)):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""
            INSERT INTO bookings (
                room_id, 
                guest_id,
                datefrom,
                dateto,
                info
            ) VALUES (
                %s, %s, %s, %s, %s
            ) RETURNING *
        """, [
            booking.room_id, 
            guest['id'],
            booking.datefrom,
            booking.dateto,
            booking.info
        ])
        new_booking = cur.fetchone()
        
    return { 
        "msg": "Booking created!", 
        "id": new_booking['id'],
        "room_id": new_booking['room_id']
    }

# Update booking
@app.put("/bookings/{id}")
def create_booking(id: int, booking: BookingUpdate, guest: dict = Depends(validate_key)):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(""" 
            UPDATE bookings SET
                stars = %s
            WHERE id = %s 
                AND guest_id = %s
            RETURNING *
        """, [booking.stars, id, guest['id']])
        updated_booking = cur.fetchone()
        if not updated_booking:
            raise HTTPException(status_code=404, detail={"error": "Booking not found!"})
        
    return { 
        "msg": "booking updated", "id": updated_booking['id']
    }




