from supabase import create_client, Client

SUPABASE_URL = "postgresql://postgres:Sevana%401995@db.dnwfdswyuqahzmkgewui.supabase.co:5432/postgres"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRud2Zkc3d5dXFhaHpta2dld3VpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTE4MTIyNDYsImV4cCI6MjA2NzM4ODI0Nn0.8cqoifJ_F9S7JnHvFLBwgiVlB8lGgUCTUqPilHblXS8"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
