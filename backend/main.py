from fastapi import FastAPI, Form, File, UploadFile, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
import os
import csv
from datetime import datetime
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE
from PIL import Image, ImageOps

app = FastAPI()

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Paths
UPLOAD_DIR = "backend/uploads"
CSV_FILE = "backend/data.csv"
LOGO_PATH = "backend/logo.png"

# Ensure necessary folders exist
os.makedirs(UPLOAD_DIR, exist_ok=True)
if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, "w", newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            "name", "house", "mobile", "whatsapp", "father", "age", "unit",
            "epl", "prev_team", "photo_path"
        ])

# Static mounts
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
app.mount("/static", StaticFiles(directory="frontend"), name="static")
app.mount("/static", StaticFiles(directory="backend"), name="static")

# Serve index.html on root
@app.get("/", response_class=HTMLResponse)
def root():
    return FileResponse("frontend/index.html")

# Serve register.html
@app.get("/register", response_class=HTMLResponse)
def serve_register():
    return FileResponse("frontend/register.html")


# Player Registration Endpoint
@app.post("/register")
async def register(
    name: str = Form(...),
    house: str = Form(...),
    mobile: str = Form(...),
    whatsapp: str = Form(...),
    father: str = Form(...),
    age: int = Form(...),
    unit: str = Form(...),
    epl: str = Form(...),
    prev_team: str = Form(""),
    photo: UploadFile = File(...)
):
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    safe_name = name.replace(" ", "_")
    filename = f"{safe_name}_{timestamp}.jpg"
    file_path = os.path.join(UPLOAD_DIR, filename)

    # Save uploaded photo
    with open(file_path, "wb") as f:
        content = await photo.read()
        f.write(content)

    relative_path = f"uploads/{filename}"  # public path, not full backend/

    # Save data to CSV
    with open(CSV_FILE, "a", newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            name, house, mobile, whatsapp, father, age, unit, epl, prev_team, relative_path
        ])

    return JSONResponse({"message": "✅ Registration successful!"})


# Admin data endpoint (returns JSON)
@app.get("/admin-data")
def get_admin_data():
    data = []
    with open(CSV_FILE, "r") as f:
        reader = csv.DictReader(f)
        data = list(reader)
    return data


# CSV download
@app.get("/download-csv")
def download_csv():
    return FileResponse(CSV_FILE, media_type='text/csv', filename="registered_players.csv")


# PPT download
@app.get("/download-ppt")
def download_ppt():
    prs = Presentation()
    blank_layout = prs.slide_layouts[6]

    with open(CSV_FILE, "r", newline='') as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader):
            slide = prs.slides.add_slide(blank_layout)

            # Background card
            card = slide.shapes.add_shape(
                MSO_SHAPE.RECTANGLE, Inches(0.3), Inches(0.3), Inches(9), Inches(6.5)
            )
            card.fill.solid()
            bg_color = RGBColor(235, 245, 255) if idx % 2 == 0 else RGBColor(250, 250, 250)
            card.fill.fore_color.rgb = bg_color
            card.line.color.rgb = RGBColor(180, 180, 180)

            # Player name
            title_box = slide.shapes.add_textbox(Inches(0.5), Inches(0.5), Inches(8), Inches(1))
            p = title_box.text_frame.paragraphs[0]
            p.text = row["name"]
            p.font.size = Pt(32)
            p.font.bold = True
            p.font.color.rgb = RGBColor(0, 70, 140)

            # Info section
            info_box = slide.shapes.add_textbox(Inches(0.5), Inches(1.5), Inches(5.8), Inches(4.5))
            tf = info_box.text_frame
            tf.clear()
            fields = [
                ("Unit", row["unit"]),
                ("House", row["house"]),
                ("Father's Name", row["father"]),
                ("Age", row["age"]),
                ("Previous Team", row["prev_team"] or "N/A"),
                ("Base Value", "30")
            ]
            for label, value in fields:
                para = tf.add_paragraph()
                para.text = f"{label}: {value}"
                para.font.size = Pt(22)
                para.font.bold = True
                para.font.color.rgb = RGBColor(30, 30, 30)

            # Logo
            if os.path.exists(LOGO_PATH):
                slide.shapes.add_picture(LOGO_PATH, Inches(7.5), Inches(0.3), width=Inches(1.5))

            # Footer
            footer_box = slide.shapes.add_textbox(Inches(0.3), Inches(6.6), Inches(9), Inches(0.5))
            para = footer_box.text_frame.paragraphs[0]
            para.text = "EPL Tournament 2025"
            para.font.size = Pt(14)
            para.font.color.rgb = RGBColor(100, 100, 100)
            para.alignment = PP_ALIGN.CENTER

            # Player Photo with border
            photo_path = os.path.join("backend", row["photo_path"].replace("uploads/", "uploads/"))
            if os.path.exists(photo_path):
                with Image.open(photo_path) as img:
                    bordered = ImageOps.expand(img, border=5, fill='black')
                    temp_path = f"backend/_temp_{idx}.jpg"
                    bordered.save(temp_path)
                slide.shapes.add_picture(temp_path, Inches(6.2), Inches(1.8), width=Inches(2.5), height=Inches(2.5))

    output_file = "backend/player_data.pptx"
    prs.save(output_file)

    return FileResponse(output_file, media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation", filename="players.pptx")
