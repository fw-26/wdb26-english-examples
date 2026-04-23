import os, psycopg

DATABASE_URL = os.getenv("DATABASE_URL")

def get_conn():
    return psycopg.connect(DATABASE_URL, autocommit=True, row_factory=psycopg.rows.dict_row)

def create_schema():
    with get_conn() as conn, conn.cursor() as cur:
        # Create the schema
        cur.execute("""
            -- Add pgcrypto
            CREATE EXTENSION IF NOT EXISTS pgcrypto;
                    
            ----------
            -- ROOMS
            ----------
            CREATE TABLE IF NOT EXISTS rooms (
                id SERIAL PRIMARY KEY,
                room_number INT NOT NULL,
                created_at TIMESTAMP DEFAULT now()
            );
                    
            -- add columns
            ALTER TABLE rooms ADD COLUMN IF NOT EXISTS room_type VARCHAR;
            ALTER TABLE rooms ADD COLUMN IF NOT EXISTS price NUMERIC NOT NULL DEFAULT 0;

            ----------
            -- Guests
            ----------
            CREATE TABLE IF NOT EXISTS guests (
                id SERIAL PRIMARY KEY,
                firstname VARCHAR NOT NULL,
                lastname VARCHAR NOT NULL,
                address VARCHAR,
                created_at TIMESTAMP DEFAULT now()
            );
            ALTER TABLE guests ADD COLUMN IF NOT EXISTS api_key VARCHAR DEFAULT encode(gen_random_bytes(32), 'hex');

            ----------
            -- Bookings
            ----------
            CREATE TABLE IF NOT EXISTS bookings (
                id SERIAL PRIMARY KEY,
                guest_id INT REFERENCES guests(id),
                room_id INT REFERENCES rooms(id),
                datefrom DATE NOT NULL DEFAULT now(),
                dateto DATE NOT NULL DEFAULT now()+1,
                info VARCHAR,
                created_at TIMESTAMP DEFAULT now()
            );
                    
            ALTER TABLE bookings ALTER COLUMN dateto SET DEFAULT now()::date+1;
            ALTER TABLE bookings ADD COLUMN IF NOT EXISTS stars INT


        """)