from fastapi import FastAPI, Form, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import os
import csv
from datetime import datetime

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE
from fastapi.responses import FileResponse
from PIL import Image, ImageOps
app = FastAPI()

# Enable CORS for all frontend files
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "backend/uploads"
CSV_FILE = "backend/data.csv"

# Create folders if they don't exist
os.makedirs(UPLOAD_DIR, exist_ok=True)
if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, "w", newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            "name", "house", "mobile", "whatsapp", "father", "age",
            "epl", "prev_team", "photo_path"
        ])

# Serve uploaded photos
app.mount("/backend/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
app.mount("/static", StaticFiles(directory="backend"), name="static")

# Route: Registration Form Submission
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

    # Save photo
    with open(file_path, "wb") as f:
        content = await photo.read()
        f.write(content)

    relative_path = f"backend/uploads/{filename}"

    # Save registration data to CSV
    write_header = not os.path.exists(CSV_FILE) or os.path.getsize(CSV_FILE) == 0

    with open(CSV_FILE, "a", newline='') as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow([
                "name", "house", "mobile", "whatsapp", "father", "age", "unit",
                "epl", "prev_team", "photo_path"
            ])
        writer.writerow([
            name, house, mobile, whatsapp, father, age, unit, epl, prev_team, relative_path
        ])

    return JSONResponse({"message": "✅ Registration successful!"})

# Route: Admin JSON Data
@app.get("/admin-data")
def get_admin_data():
    data = []
    with open(CSV_FILE, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    return data

# Route: Download CSV File
@app.get("/download-csv")
def download_csv():
    return FileResponse(CSV_FILE, media_type='text/csv', filename="registered_players.csv")


@app.get("/download-ppt")
def download_ppt():
    prs = Presentation()
    blank_layout = prs.slide_layouts[6]
    logo_path = "backend/logo.png"  # Place your logo here

    with open(CSV_FILE, "r", newline='') as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader):
            slide = prs.slides.add_slide(blank_layout)

            # Alternate background color
            card = slide.shapes.add_shape(
                MSO_SHAPE.RECTANGLE, Inches(0.3), Inches(0.3), Inches(9), Inches(6.5)
            )
            card.fill.solid()
            bg_color = RGBColor(235, 245, 255) if idx % 2 == 0 else RGBColor(250, 250, 250)
            card.fill.fore_color.rgb = bg_color
            card.line.color.rgb = RGBColor(180, 180, 180)

            # Title (Player Name)
            title_box = slide.shapes.add_textbox(Inches(0.5), Inches(0.5), Inches(8), Inches(1))
            p = title_box.text_frame.paragraphs[0]
            p.text = row["name"]
            p.font.size = Pt(32)
            p.font.bold = True
            p.font.color.rgb = RGBColor(0, 70, 140)

#             # Player Info
#             info = f"""
# Unit: {row['unit']}
# House: {row['house']}
# Mobile: {row['mobile']}
# WhatsApp: {row['whatsapp']}
# Father's Name: {row['father']}
# Age: {row['age']}
# EPL 2.0: {row['epl']}
# Previous Team: {row['prev_team'] or '-'}
# """
#             info_box = slide.shapes.add_textbox(Inches(0.5), Inches(1.5), Inches(5), Inches(4))
#             tf = info_box.text_frame
#             tf.word_wrap = True
#             for line in info.strip().split("\n"):
#                 para = tf.add_paragraph()
#                 para.text = line
#                 para.font.size = Pt(18)
#                 para.font.color.rgb = RGBColor(40, 40, 40)

            # Player Info (clean and focused)
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
                p = tf.add_paragraph()
                p.text = f"{label}: {value}"
                p.font.size = Pt(22)
                p.font.bold = True
                p.font.color.rgb = RGBColor(30, 30, 30)

            # Logo (top-right)
            if os.path.exists(logo_path):
                slide.shapes.add_picture(logo_path, Inches(7.5), Inches(0.3), width=Inches(1.5))

            # Footer
            footer_box = slide.shapes.add_textbox(Inches(0.3), Inches(6.6), Inches(9), Inches(0.5))
            para = footer_box.text_frame.paragraphs[0]
            para.text = "EPL Tournament 2025"
            para.font.size = Pt(14)
            para.font.color.rgb = RGBColor(100, 100, 100)
            para.alignment = PP_ALIGN.CENTER

            # Photo with border (right side)
            photo_path = row["photo_path"]
            if os.path.exists(photo_path):
                # Add border using Pillow
                with Image.open(photo_path) as img:
                    bordered = ImageOps.expand(img, border=5, fill='black')
                    temp_path = f"backend/_temp_{idx}.jpg"
                    bordered.save(temp_path)

                slide.shapes.add_picture(temp_path, Inches(6.2), Inches(1.8), width=Inches(2.5), height=Inches(2.5))

    output_file = "backend/player_data.pptx"
    prs.save(output_file)

    return FileResponse(output_file, media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation", filename="players.pptx")
