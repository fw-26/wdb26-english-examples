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
        print("DB Schema created")

        cur.execute("""
            DROP VIEW IF EXISTS guests_view;
            CREATE VIEW guests_view AS
                SELECT 
                    g.id, 
                    g.firstname, 
                    g.lastname, 
                    COALESCE(g.address, ''),
                    g.firstname || ' ' || g.lastname AS guest_name,
                    (SELECT count(*) 
                        FROM bookings
                        WHERE guest_id = g.id
                            AND dateto < now()
                        ) as previous_visits
                FROM guests g;

            CREATE OR REPLACE VIEW bookings_view AS
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
        """)
        print("DB Views created")