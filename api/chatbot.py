import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import create_client, Client
from dotenv import load_dotenv
import google.generativeai as genai
import re
from typing import Optional, List

load_dotenv()

app = FastAPI(
    title="StockWise Indonesia API",
    description="Indonesian Stock Information Chatbot API",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request/response
class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    reply: str

class CompanySearchRequest(BaseModel):
    search_term: str

class CompanyResponse(BaseModel):
    company: Optional[dict] = None
    found: bool
    message: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    service: str
    supabase_connected: bool
    gemini_configured: bool

class ErrorResponse(BaseModel):
    error: str

# Inisialisasi Klien Supabase
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")

supabase: Client = None
if url and key:
    supabase: Client = create_client(url, key)
    print("Koneksi Supabase Berhasil.")
else:
    print("Peringatan: SUPABASE_URL dan SUPABASE_KEY tidak diatur. Fungsi Supabase tidak akan bekerja.")

# Inisialisasi Gemini
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY harus diatur di file .env")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash-preview-04-17-thinking')

# SYSTEM PROMPT STOCKWISE INDONESIA
STOCKWISE_SYSTEM_PROMPT = """
# SYSTEM PROMPT - Indonesian Stock Information Chatbot

## PRIMARY IDENTITY & ROLE
Anda adalah **"StockWise Indonesia"** - seorang ahli pasar modal Indonesia yang berpengalaman dengan kemampuan analisis data tinggi. Anda memiliki akses ke database komprehensif perusahaan-perusahaan yang terdaftar di Bursa Efek Indonesia (BEI) dan mampu mengakses informasi real-time dari berbagai sumber terpercaya.

## CORE MISSION
Memberikan informasi faktual, akurat, dan mudah dipahami tentang perusahaan-perusahaan publik Indonesia kepada investor, analis, dan masyarakat umum dengan pendekatan yang profesional namun ramah.

## DATA ACCESS HIERARCHY & RAG WORKFLOW

### 🔄 **PRIORITY 1: DATABASE SUPABASE (UTAMA)**
**SELALU prioritaskan data dari database internal dengan struktur:**
- `ticker`: Kode saham (format: XXXX.JK)
- `longname`: Nama lengkap perusahaan
- `address1`: Alamat perusahaan
- `sector`: Sektor industri
- `website`: Website resmi
- `phone`: Nomor telepon
- `longbusinesssummary`: Ringkasan bisnis lengkap

**WORKFLOW DATABASE QUERY:**
1. Identifikasi ticker saham dari pertanyaan user
2. Query database untuk semua kolom yang tersedia
3. Strukturkan informasi berdasarkan data yang ditemukan
4. Tandai setiap informasi dengan **[Data Internal]**

### 🌐 **PRIORITY 2: EXTERNAL SOURCES (FALLBACK)**
Gunakan HANYA jika data database kosong/tidak lengkap:
- Website resmi perusahaan
- Laporan keuangan publik (annual report, quarterly report)
- Press release resmi perusahaan
- Platform finansial terpercaya (IDX, Reuters, Bloomberg)
- Berita finansial kredibel

**EXTERNAL DATA PROTOCOL:**
- Tandai dengan **[Sumber: Nama Sumber]**
- Selalu verifikasi kredibilitas sumber
- Prioritaskan informasi terbaru dan official

## RESPONSE STRUCTURE & FORMAT

### 📋 **TEMPLATE RESPONSE PROFIL PERUSAHAAN:**

```
# [NAMA PERUSAHAAN] ([TICKER])

## Informasi Dasar
**Sektor:** [Sektor Industri] [Data Internal]
**Alamat:** [Alamat Lengkap] [Data Internal]
**Website:** [URL Website] [Data Internal]
**Kontak:** [Nomor Telepon] [Data Internal]

## Profil Bisnis
[Ringkasan bisnis yang mudah dipahami berdasarkan longbusinesssummary]
[Data Internal]

## Informasi Tambahan
[Jika ada data dari sumber eksternal, cantumkan di sini dengan sumber yang jelas]

---
💡 **Catatan:** Informasi ini bersifat faktual dan tidak merupakan rekomendasi investasi.
```

## COMMUNICATION GUIDELINES

### 🗣️ **TONE & LANGUAGE:**
- **Bahasa Utama:** Indonesia (formal namun friendly)
- **Multilingual:** Adaptasi bahasa sesuai bahasa user
- **Level:** Expert-friendly - gunakan istilah teknis tapi jelaskan dengan sederhana
- **Approach:** Edukatif, informatif, tidak menggurui

### 💬 **RESPONSE PRINCIPLES:**
1. **Faktual Only:** Tidak memberikan saran investasi atau prediksi harga
2. **Transparency:** Jujur tentang keterbatasan data
3. **Clarity:** Gunakan paragraf terstruktur, hindari wall of text
4. **Comprehensiveness:** Berikan konteks yang cukup untuk pemahaman

### ⚠️ **TRANSPARENCY PROTOCOL:**
- Jika data tidak tersedia: "Maaf, informasi [spesifik] untuk [perusahaan] tidak tersedia dalam database kami saat ini."
- Jika menggunakan sumber eksternal: Selalu cantumkan sumber dengan jelas
- Jika informasi mungkin outdated: Berikan disclaimer tentang kemungkinan perubahan

## SPECIAL SCENARIOS HANDLING

### 📊 **KETIKA DATA KOSONG/TERBATAS:**
```
"Berdasarkan database internal kami, informasi untuk [TICKER] terbatas. 
Yang tersedia: [list data yang ada]

Saya akan mencari informasi tambahan dari sumber terpercaya untuk melengkapi profil perusahaan ini..."
```

### 🔄 **KETIKA TICKER TIDAK DITEMUKAN:**
```
"Ticker [XXXX] tidak ditemukan dalam database perusahaan BEI kami. 
Kemungkinan:
1. Ticker salah eja
2. Perusahaan sudah delisting
3. Belum terdaftar dalam sistem

Bisa bantu konfirmasi nama perusahaan atau ticker yang dimaksud?"
```

### 🌍 **MULTILINGUAL ADAPTATION:**
- Deteksi bahasa user dari query
- Respond dalam bahasa yang sama
- Pertahankan akurasi informasi lintas bahasa
- Gunakan terminologi finansial yang tepat sesuai bahasa

## QUALITY ASSURANCE CHECKLIST

✅ **Sebelum Response:**
- [ ] Data internal sudah dicek maksimal?
- [ ] Sumber eksternal (jika ada) kredibel?
- [ ] Informasi ditandai dengan sumber yang jelas?
- [ ] Bahasa sesuai dengan user query?
- [ ] Format terstruktur dan mudah dibaca?
- [ ] Disclaimer investasi disertakan?

---

**ACTIVATION PHRASE:** "Saya siap membantu Anda mencari informasi perusahaan-perusahaan publik Indonesia. Silakan tanyakan profil perusahaan yang ingin Anda ketahui!"
"""

def extract_potential_tickers(text: str) -> List[str]:
    """
    Ekstrak kemungkinan ticker dari teks user.
    Mencari pola 4 huruf kapital diikuti .JK atau tanpa .JK
    """
    # Pattern untuk ticker Indonesia: 4 huruf + optional .JK
    ticker_patterns = re.findall(r'\b[A-Z]{4}(?:\.JK)?\b', text.upper())
    return ticker_patterns

def search_company_in_supabase(search_term: str) -> Optional[dict]:
    """
    Fungsi untuk mencari data perusahaan di Supabase.
    Mengembalikan data perusahaan jika ditemukan, jika tidak None.
    """
    if not supabase:
        print("Pencarian Supabase dilewati: Koneksi tidak ada.")
        return None

    try:
        # Normalize search term
        search_term = search_term.strip()
        
        # 1. Coba cari berdasarkan Ticker (dengan atau tanpa .JK)
        ticker_search = search_term.upper()
        if not ticker_search.endswith('.JK') and len(ticker_search) == 4:
            ticker_search += '.JK'
            
        response_ticker = supabase.table('company_info').select("*").ilike('ticker', ticker_search).execute()
        if response_ticker.data:
            return response_ticker.data[0]

        # 2. Coba cari berdasarkan ticker tanpa .JK
        if ticker_search.endswith('.JK'):
            ticker_without_jk = ticker_search[:-3]
            response_ticker2 = supabase.table('company_info').select("*").ilike('ticker', f'{ticker_without_jk}.JK').execute()
            if response_ticker2.data:
                return response_ticker2.data[0]

        # 3. Cari berdasarkan Long Name (partial match)
        response_name = supabase.table('company_info').select("*").ilike('longname', f'%{search_term}%').execute()
        if response_name.data:
            return response_name.data[0]

        return None

    except Exception as e:
        print(f"Error saat mencari di Supabase: {e}")
        return None

def search_multiple_companies(search_terms: List[str]) -> List[dict]:
    """
    Mencari beberapa perusahaan sekaligus
    """
    companies = []
    for term in search_terms:
        company = search_company_in_supabase(term)
        if company:
            companies.append(company)
    return companies

def format_company_data_for_prompt(company_data: dict) -> str:
    """
    Format data perusahaan untuk prompt yang lebih terstruktur
    """
    if not company_data:
        return ""
    
    formatted_data = f"""
--- DATA PERUSAHAAN DARI DATABASE INTERNAL BEI ---
Ticker: {company_data.get('ticker', 'N/A')}
Nama Perusahaan: {company_data.get('longname', 'N/A')}
Sektor: {company_data.get('sector', 'N/A')}
Website: {company_data.get('website', 'N/A')}
Telepon: {company_data.get('phone', 'N/A')}
Alamat: {company_data.get('address1', 'N/A')}
Ringkasan Bisnis: {company_data.get('longbusinesssummary', 'Tidak tersedia')}
--- AKHIR DATA INTERNAL ---
"""
    return formatted_data

def create_chat_session_with_system_prompt():
    """
    Membuat chat session baru dengan system prompt StockWise
    """
    return model.start_chat(
        history=[
            {
                "role": "user",
                "parts": [STOCKWISE_SYSTEM_PROMPT]
            },
            {
                "role": "model", 
                "parts": ["Saya siap membantu Anda mencari informasi perusahaan-perusahaan publik Indonesia. Silakan tanyakan profil perusahaan yang ingin Anda ketahui!"]
            }
        ]
    )

@app.post('/gemini_chat', response_model=ChatResponse)
async def gemini_chat_handler(request: ChatRequest):
    """
    Endpoint utama yang mengintegrasikan StockWise Indonesia system prompt
    dengan pencarian database Supabase
    """
    user_message = request.message

    if not user_message:
        raise HTTPException(status_code=400, detail="Silakan ajukan pertanyaan tentang perusahaan publik Indonesia.")

    try:
        # LANGKAH 1: Ekstrak kemungkinan ticker dari pesan
        potential_tickers = extract_potential_tickers(user_message)
        
        # LANGKAH 2: Cari perusahaan berdasarkan ticker atau nama
        company_data = None
        
        # Coba cari berdasarkan ticker yang diekstrak
        for ticker in potential_tickers:
            company_data = search_company_in_supabase(ticker)
            if company_data:
                break
        
        # Jika tidak ada ticker yang cocok, coba cari berdasarkan seluruh pesan
        if not company_data:
            company_data = search_company_in_supabase(user_message)

        # LANGKAH 3: Buat chat session dengan system prompt
        chat_session = create_chat_session_with_system_prompt()
        
        # LANGKAH 4: Siapkan prompt berdasarkan apakah data ditemukan atau tidak
        if company_data:
            # Jika data perusahaan ditemukan, berikan konteks lengkap
            formatted_company_data = format_company_data_for_prompt(company_data)
            final_prompt = f"""
{formatted_company_data}

PERTANYAAN USER: {user_message}

Berikan respons sesuai dengan format dan guidelines StockWise Indonesia. Gunakan Data Internal yang tersedia di atas dan tandai dengan [Data Internal].
"""
            print(f"INFO: Data perusahaan ditemukan untuk: {company_data.get('longname', 'N/A')}")
        else:
            # Jika tidak ada data spesifik, tetap gunakan StockWise persona
            final_prompt = f"""
PERTANYAAN USER: {user_message}

Tidak ada data spesifik perusahaan yang ditemukan dalam database internal. Berikan respons sesuai dengan persona StockWise Indonesia dan guidelines yang telah ditetapkan.
"""
            print("INFO: Tidak ada data perusahaan spesifik ditemukan")

        # LANGKAH 5: Kirim ke Gemini
        response = chat_session.send_message(final_prompt)
        
        return ChatResponse(reply=response.text)

    except Exception as e:
        print(f"Error in gemini_chat_handler: {e}")
        raise HTTPException(status_code=500, detail="Maaf, terjadi kesalahan saat memproses permintaan Anda. Silakan coba lagi.")

@app.post('/company_search', response_model=CompanyResponse)
async def company_search(request: CompanySearchRequest):
    """
    Endpoint khusus untuk pencarian perusahaan langsung
    """
    search_term = request.search_term
    
    if not search_term:
        raise HTTPException(status_code=400, detail="Parameter search_term diperlukan")
    
    try:
        company_data = search_company_in_supabase(search_term)
        if company_data:
            return CompanyResponse(company=company_data, found=True)
        else:
            return CompanyResponse(found=False, message="Perusahaan tidak ditemukan")
    
    except Exception as e:
        print(f"Error in company_search: {e}")
        raise HTTPException(status_code=500, detail="Terjadi kesalahan saat mencari perusahaan")

@app.get('/health', response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint
    """
    return HealthResponse(
        status="healthy",
        service="StockWise Indonesia API",
        supabase_connected=supabase is not None,
        gemini_configured=GEMINI_API_KEY is not None
    )

# Optional: Add root endpoint for API info
@app.get('/')
async def read_root():
    return {
        "message": "StockWise Indonesia API",
        "version": "1.0.0",
        "description": "Indonesian Stock Information Chatbot API",
        "endpoints": {
            "POST /gemini_chat": "Main chatbot endpoint",
            "POST /company_search": "Direct company search",
            "GET /health": "Health check",
            "GET /docs": "API documentation (Swagger UI)",
            "GET /redoc": "API documentation (ReDoc)"
        }
    }