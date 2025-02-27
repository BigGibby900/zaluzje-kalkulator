from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import pandas as pd
import math
import os

app = FastAPI()

# Pozwolenie na połączenia z frontendem
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dodanie obsługi plików statycznych (np. index.html)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def read_root():
    return FileResponse("static/index.html")

# Sprawdzenie, czy plik cennik.xlsx istnieje
file_path = "cennik.xlsx"
if not os.path.exists(file_path):
    raise FileNotFoundError("Brak pliku cennik.xlsx! Upewnij się, że plik jest dostępny.")

# Wczytujemy cennik z pliku Excel
df = pd.read_excel(file_path, sheet_name="Cennik", index_col=0)
df = df.dropna(how="all")
df.columns = pd.to_numeric(df.columns, errors="coerce")  # Zamiana szerokości na liczby
df.index = pd.to_numeric(df.index, errors="coerce")  # Zamiana wysokości na liczby
df = df.dropna().astype(float)

def round_up(value, step=10):
    return math.ceil(value / step) * step

def get_price(width, height):
    rounded_width = round_up(width, 10)
    rounded_height = round_up(height, 10)
    available_widths = sorted(df.columns)
    available_heights = sorted(df.index)

    if rounded_height > max(available_heights):
        return None, None, None, "Podana wysokość jest zbyt duża – brak takiej żaluzji w ofercie."
    
    nearest_width = next((w for w in available_widths if w >= rounded_width), None)
    nearest_height = next((h for h in available_heights if h >= rounded_height), None)

    if nearest_width is None:
        return None, None, None, "Podana szerokość jest zbyt duża – brak takiej żaluzji w ofercie."

    try:
        price = df.at[nearest_height, nearest_width]
    except KeyError:
        return None, None, None, "Brak ceny dla podanych wymiarów."
    
    return round(price), nearest_width, nearest_height, None

@app.get("/cena/")
def get_cena(wysokosc: int, szerokosc: int):
    price, nearest_width, nearest_height, error_message = get_price(szerokosc, wysokosc)
    if error_message:
        return {"error": error_message}
    return {
        "wysokosc": wysokosc, 
        "szerokosc": szerokosc, 
        "cena": price, 
        "zaokraglona_szerokosc": nearest_width, 
        "zaokraglona_wysokosc": nearest_height
    }

# Uruchamianie serwera w Render
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10000)
