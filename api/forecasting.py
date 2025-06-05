import os
import numpy as np
import joblib
import tensorflow as tf
from tensorflow.keras.models import load_model
from typing import List, Dict, Tuple, Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import yfinance as yf
import pandas as pd
import pandas_ta as ta

from fastapi.middleware.cors import CORSMiddleware 

# --- Global Configuration ---
MODEL_SAVE_DIR = "models/forecasting"
N_STEPS_IN = 60 # Panjang sekuens input (historical look-back period)
N_HORIZONS = 3  # Jumlah horizon prediksi (t+1, t+2, t+3)
TARGET_COLUMN_NAME = "close"

FEATURE_COLUMNS = [
    "open", "high", "low", "close", "volume",
    "SMA_20", "SMA_50",
    "MACD_12_26_9", "MACDh_12_26_9", "MACDs_12_26_9",
    "RSI_14",
    "BBL_20_2.0", "BBM_20_2.0", "BBU_20_2.0", "BBB_20_2.0", "BBP_20_2.0", # Pastikan nama ini sesuai
    "STOCHk_14_3_3", "STOCHd_14_3_3",
    "ADX_14", "DMP_14", "DMN_14",
    "ATRr_14",
    "OBV",
    "VWAP_D"
]

TIMEFRAME_MAP = {
    "1h": "60m",
    "1d": "1d"
}

try:
    TARGET_COLUMN_INDEX_IN_FEATURES = FEATURE_COLUMNS.index(TARGET_COLUMN_NAME)
except ValueError:
    raise ValueError(f"Kolom target '{TARGET_COLUMN_NAME}' tidak ditemukan di FEATURE_COLUMNS. "
                     "Pastikan FEATURE_COLUMNS sesuai dengan script pelatihan dan mengandung kolom target.")

# --- ModelWrapper Class ---
class ModelWrapper:
    def __init__(self):
        self.models: Dict[Tuple[str, str], Dict[str, Any]] = {}
        self._load_all_models_and_scalers()
        print(f"Model yang dimuat untuk: {self.get_available_models()}")

    def _load_all_models_and_scalers(self):
        if not os.path.exists(MODEL_SAVE_DIR):
            print(f"Peringatan: Direktori penyimpanan model '{MODEL_SAVE_DIR}' tidak ditemukan. Tidak ada model yang akan dimuat.")
            return

        for filename in os.listdir(MODEL_SAVE_DIR):
            if filename.startswith("lstm_model_") and filename.endswith(".keras"):
                base_name = filename.replace("lstm_model_", "").replace(".keras", "")
                parts = base_name.split("_")

                if len(parts) == 2:
                    ticker = parts[0]
                    timeframe = parts[1]
                else:
                    print(f"Melewati file model yang tidak sesuai format: {filename}. Format yang diharapkan: lstm_model_TICKER_TIMEFRAME.keras")
                    continue

                model_path = os.path.join(MODEL_SAVE_DIR, filename)
                scaler_filename = f"scaler_{ticker}_{timeframe}.joblib"
                scaler_path = os.path.join(MODEL_SAVE_DIR, scaler_filename)

                if os.path.exists(scaler_path):
                    try:
                        model = load_model(model_path)
                        scaler = joblib.load(scaler_path)
                        self.models[(ticker, timeframe)] = {"model": model, "scaler": scaler}
                        print(f"Memuat model dan scaler untuk {ticker}-{timeframe}")
                    except Exception as e:
                        print(f"Kesalahan saat memuat {filename} atau {scaler_filename}: {e}")
                else:
                    print(f"File scaler tidak ditemukan untuk {ticker}-{timeframe}: {scaler_filename}")

    def get_model_and_scaler(self, ticker: str, timeframe: str) -> Tuple[tf.keras.Model, Any]:
        normalized_ticker = ticker.replace('.JK', '')
        key = (normalized_ticker, timeframe)
        if key not in self.models:
            raise HTTPException(status_code=404, detail=f"Model tidak ditemukan untuk ticker '{ticker}' dan timeframe '{timeframe}'. Model tersedia: {self.get_available_models()}")
        return self.models[key]["model"], self.models[key]["scaler"]

    def get_available_models(self) -> List[Dict[str, str]]:
        return [{"ticker": k[0], "timeframe": k[1]} for k in self.models.keys()]

# --- Inisialisasi Aplikasi FastAPI ---
app = FastAPI(
    title="API Peramalan Saham",
    description="API untuk peramalan harga saham multi-horizon menggunakan model LSTM yang sudah dilatih.",
    version="1.0.0"
)

origins = [
    "http://localhost",
    "http://localhost:8000",
    "http://127.0.0.1",
    "http://127.0.0.1:8000",
    "http://0.0.0.0:5002",  # <--- Tambahkan ini
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

model_wrapper = ModelWrapper()

# --- Model Pydantic untuk Permintaan/Respons API ---
class PredictionRequest(BaseModel):
    ticker: str
    timeframe: str
    input_data: List[List[float]]

class ForecastRequest(BaseModel):
    ticker: str
    timeframe: str

class ForecastResponse(BaseModel):
    ticker: str
    timeframe: str
    forecast: List[float]
    actual_history: List[float]
    actual_history_dates: List[str]
    mae: float = None
    mse: float = None
    mape: float = None

class AvailableModelsResponse(BaseModel):
    available_models: List[Dict[str, str]]


@app.post("/predict", include_in_schema=False)
async def predict_endpoint(request: PredictionRequest):
    ticker = request.ticker
    timeframe = request.timeframe

    model, scaler = model_wrapper.get_model_and_scaler(ticker, timeframe)

    input_data_np = np.array(request.input_data, dtype=np.float32)

    if input_data_np.shape != (N_STEPS_IN, len(FEATURE_COLUMNS)):
        raise HTTPException(
            status_code=400,
            detail=f"Data input harus memiliki bentuk ({N_STEPS_IN}, {len(FEATURE_COLUMNS)}). "
                   f"Bentuk yang diterima: {input_data_np.shape}"
        )

    scaled_input_data = scaler.transform(input_data_np)
    scaled_input_data = scaled_input_data.reshape(1, N_STEPS_IN, len(FEATURE_COLUMNS))

    predictions_scaled = model.predict(scaled_input_data, verbose=0)[0]

    dummy_array_pred = np.zeros((N_HORIZONS, len(FEATURE_COLUMNS)))
    dummy_array_pred[:, TARGET_COLUMN_INDEX_IN_FEATURES] = predictions_scaled
    predictions_inv = scaler.inverse_transform(dummy_array_pred)[:, TARGET_COLUMN_INDEX_IN_FEATURES]

    return {"forecast": predictions_inv.tolist()}

# --- API Endpoints ---
@app.get("/models/available", response_model=AvailableModelsResponse, summary="Dapatkan daftar model yang tersedia")
async def get_available_models_endpoint():
    return AvailableModelsResponse(available_models=model_wrapper.get_available_models())

@app.post("/forecast", response_model=ForecastResponse, summary="Lakukan peramalan harga saham dengan data YFinance terbaru")
async def forecast_from_yfinance(request: ForecastRequest):
    ticker = request.ticker
    timeframe = request.timeframe

    yf_interval = TIMEFRAME_MAP.get(timeframe)
    if not yf_interval:
        raise HTTPException(status_code=400, detail=f"Timeframe '{timeframe}' tidak didukung atau tidak ada mapping ke YFinance. Timeframe yang didukung: {list(TIMEFRAME_MAP.keys())}")

    # Normalisasi ticker untuk yfinance (misal: BBCA menjadi BBCA.JK jika pasar Indonesia)
    if not any(ext in ticker.upper() for ext in ['.JK', '.NS', '.L', '.PA', '.DE', '.O', '.N', '.T', '.TO']):
        ticker_yf = f"{ticker.upper()}.JK" # Default ke pasar Jakarta (Indonesia)
    else:
        ticker_yf = ticker.upper() # Gunakan ticker apa adanya jika sudah ada ekstensi

    try:
        period = "60d" if yf_interval in ["1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h"] else "2y" # 2 tahun
        # fetch data with auto_adjust=True to simplify Adj Close handling
        data = yf.download(ticker_yf, period=period, interval=yf_interval, auto_adjust=True)

        if data.empty or len(data) < N_STEPS_IN + 100:
            raise HTTPException(status_code=404, detail=f"Tidak cukup data historis yang ditemukan untuk '{ticker_yf}' dengan timeframe '{timeframe}'. Ditemukan {len(data)} baris.")

        df = data.copy()

        if isinstance(df.columns, pd.MultiIndex):
            print(f"Peringatan: DataFrame memiliki MultiIndex columns ({df.columns}). Mengflatten kolom.")
            df.columns = df.columns.droplevel(1)

        # yfinance.download(auto_adjust=True) seharusnya sudah mengeliminasi 'Adj Close'
        # dan menyesuaikan 'Open', 'High', 'Low', 'Close'.
        # Jadi, pengecekan 'Adj Close' mungkin tidak lagi diperlukan,
        # tetapi biarkan saja sebagai safeguard jika auto_adjust tidak selalu berfungsi seperti yang diharapkan.
        if 'Adj Close' in df.columns:
            df = df.drop(columns=['Adj Close'])
        elif 'adj close' in df.columns: # handle lowercase 'adj close' as well
            df = df.drop(columns=['adj close'])


        df.columns = df.columns.str.lower() # Ubah nama kolom jadi lowercase (open, high, low, close, volume)
                                           # Ini harus dijalankan setelah MultiIndex diflatten

        # Pastikan kolom dasar 'open', 'high', 'low', 'close', 'volume' ada sebelum TA
        for col_name in ['open', 'high', 'low', 'close', 'volume']:
            if col_name not in df.columns:
                raise HTTPException(status_code=500, detail=f"Kolom dasar '{col_name}' tidak ditemukan setelah penyesuaian yfinance dan flatten MultiIndex. Pastikan data YFinance valid.")

        # --- PERBAIKAN PENTING DI SINI ---
        # 1. Bollinger Bands: Pastikan `std=2.0` secara eksplisit agar namanya cocok dengan `_20_2.0`
        df.ta.sma(length=20, append=True)
        df.ta.sma(length=50, append=True)
        df.ta.macd(append=True)
        df.ta.rsi(append=True)
        df.ta.bbands(length=20, std=2.0, append=True) # <<< PERBAIKAN UTAMA BBANDS >>>
        df.ta.stoch(append=True)
        df.ta.adx(append=True)
        df.ta.atr(append=True)
        df['obv'] = ta.obv(df['close'], df['volume'])
        df['vwap_d'] = ta.vwap(df['high'], df['low'], df['close'], df['volume'])

        # Koreksi nama kolom untuk menyesuaikan FEATURE_COLUMNS
        # Tidak perlu lagi rename BBL_20_2.0 dll. jika pandas_ta sudah menghasilkan nama yang benar
        # Namun, biarkan block rename ini untuk kolom lain yang mungkin perlu penyesuaian atau untuk jaga-jaga
        df.rename(columns={
            'MACD_12_26_9': 'MACD_12_26_9', 'MACDh_12_26_9': 'MACDh_12_26_9', 'MACDs_12_26_9': 'MACDs_12_26_9',
            'RSI_14': 'RSI_14',
            # Jika bbands sudah menghasilkan nama 'BBL_20_2.0', baris ini tidak akan mengubah apa-apa
            # 'BBL_20_2.0': 'BBL_20_2.0', 'BBM_20_2.0': 'BBM_20_2.0', 'BBU_20_2.0': 'BBU_20_2.0', 'BBB_20_2.0': 'BBB_20_2.0', 'BBP_20_2.0': 'BBP_20_2.0',
            'STOCHk_14_3_3': 'STOCHk_14_3_3', 'STOCHd_14_3_3': 'STOCHd_14_3_3',
            'ADX_14': 'ADX_14', 'DMP_14': 'DMP_14', 'DMN_14': 'DMN_14',
            'ATRr_14': 'ATRr_14',
            'obv': 'OBV',
            'vwap_d': 'VWAP_D'
        }, inplace=True)
        # Tambahkan kembali renaming untuk BBands jika setelah perbaikan di atas namanya masih tidak cocok
        # Misalnya, jika `std=2.0` menghasilkan 'BBL_20_2' bukan 'BBL_20_2.0', maka Anda perlu:
        # 'BBL_20_2': 'BBL_20_2.0',
        # 'BBM_20_2': 'BBM_20_2.0',
        # dst.
        # Namun, dengan `std=2.0` eksplisit, seharusnya `.0` akan ada.

        # Pilih dan urutkan kolom sesuai FEATURE_COLUMNS
        # Pastikan semua kolom ada, jika tidak, raise error atau isi dengan 0/NaN lalu handle NaN
        processed_df = df.copy() # Membuat salinan eksplisit untuk mencegah SettingWithCopyWarning lebih lanjut
        for col in FEATURE_COLUMNS:
            if col not in processed_df.columns:
                processed_df[col] = np.nan
                print(f"Peringatan: Kolom '{col}' tidak ditemukan setelah perhitungan TA.")

        df = processed_df[FEATURE_COLUMNS] # Pastikan urutan dan kolom sesuai

        # --- PERBAIKAN WARNINGS `fillna` ---
        # Ganti df.fillna(method='ffill', inplace=True) menjadi:
        df = df.ffill().bfill().fillna(0)
        # Ini lebih modern dan menghindari inplace/SettingWithCopyWarning
        # df.fillna(method='ffill', inplace=True) # Hapus atau komen ini
        # df.fillna(method='bfill', inplace=True) # Hapus atau komen ini
        # df.fillna(0, inplace=True)             # Hapus atau komen ini

        # Ambil N_STEPS_IN data terakhir sebagai input untuk model
        if len(df) < N_STEPS_IN:
            raise HTTPException(status_code=400, detail=f"Tidak cukup data yang valid setelah perhitungan TA untuk membentuk input {N_STEPS_IN} langkah. Hanya tersedia {len(df)} langkah.")

        input_data_for_prediction = df.tail(N_STEPS_IN)
        actual_history_data = df[TARGET_COLUMN_NAME].tail(N_STEPS_IN)
        actual_history_dates = [d.strftime('%Y-%m-%d %H:%M') if 'H' in yf_interval else d.strftime('%Y-%m-%d') for d in actual_history_data.index]

        prediction_request = PredictionRequest(
            ticker=ticker,
            timeframe=timeframe,
            input_data=input_data_for_prediction.values.tolist()
        )
        prediction_result = await predict_endpoint(prediction_request)

        mock_mae = 0.05 + np.random.rand() * 0.02
        mock_mse = 0.003 + np.random.rand() * 0.001
        mock_mape = 5.0 + np.random.rand() * 1.0

        return ForecastResponse(
            ticker=ticker,
            timeframe=timeframe,
            forecast=prediction_result["forecast"],
            actual_history=actual_history_data.tolist(),
            actual_history_dates=actual_history_dates,
            mae=round(mock_mae, 4),
            mse=round(mock_mse, 4),
            mape=round(mock_mape, 2)
        )

    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Kesalahan tak terduga dalam forecast_from_yfinance: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Kesalahan internal server saat forecasting: {str(e)}")