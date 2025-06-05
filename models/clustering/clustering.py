from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

import pandas as pd
import seaborn as sns
import pickle
import plotly.express as px
import matplotlib.pyplot as plt
import io
import base64
from pathlib import Path
import numpy as np
import logging

from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
app = FastAPI(title="Stock Analysis API", version="1.0.0")

# === KONFIGURASI CORS (UNTUK DEBUGGING) ===
origins = ["*"] # Izinkan semua untuk debugging, PERKETAT untuk produksi

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)
# === AKHIR KONFIGURASI CORS ===

CLUSTER_EPS_DATA_PATH = BASE_DIR / 'cluster_eps_kmeans.pkl'
CLUSTER_ROE_DATA_PATH = BASE_DIR / 'cluster_roe_kmeans.pkl'
KMEANS_EPS_MODEL_PATH = BASE_DIR / 'kmeans_eps_model.pkl'
KMEANS_ROE_MODEL_PATH = BASE_DIR / 'kmeans_roe_model.pkl'

TABLE_COLUMN_MAP = {
    'ticker': "Ticker",
    'netincometocommon': "Net Income",
    'shareoutstanding': "Shares Out",
    'EPS': "EPS",
    'cluster': "Cluster EPS",
    'keterangan': "Keterangan EPS",
    'ROE': "ROE",
    'cluster_roe': "Cluster ROE",
    'keterangan_roe': "Keterangan ROE"
}
SOURCE_TABLE_COLUMNS = list(TABLE_COLUMN_MAP.keys())
DISPLAY_TABLE_HEADERS = list(TABLE_COLUMN_MAP.values())

class DummyKMeans:
    def __init__(self, n_clusters=2):
        self.n_clusters = n_clusters
    def predict(self, X):
        if len(X) == 0: return np.array([])
        return np.array([i % self.n_clusters for i in range(len(X))])

def load_data_and_models_core():
    eps_df, roe_df, eps_model_obj, roe_model_obj, merged_df = None, None, None, None, None
    eps_data_actually_loaded, roe_data_actually_loaded = False, False

    try:
        with open(CLUSTER_EPS_DATA_PATH, 'rb') as f: eps_df = pickle.load(f)
        if isinstance(eps_df, pd.DataFrame) and not eps_df.empty:
            eps_data_actually_loaded = True
            if not all(col in eps_df.columns for col in ['ticker', 'EPS', 'cluster']):
                logger.warning(f"Kolom penting EPS mungkin hilang di {CLUSTER_EPS_DATA_PATH}.")
        else:
            logger.warning(f"{CLUSTER_EPS_DATA_PATH} kosong/invalid. Pakai dummy EPS.")
            eps_df = None
    except Exception as e:
        logger.error(f"Error load EPS data {CLUSTER_EPS_DATA_PATH}: {e}. Pakai dummy EPS.")
        eps_df = None

    if eps_df is None:
        eps_data_actually_loaded = False
        eps_df = pd.DataFrame({
            'ticker': [f'SahamD_EPS{i}' for i in range(1, 6)], 'EPS': [1.0, 0.5, 2.0, 0.8, 3.0],
            'cluster': [0, 1, 0, 1, 0], 'netincometocommon': [100, 50, 200, 80, 300],
            'shareoutstanding': [100, 100, 100, 100, 100]})
        logger.info("Dummy EPS data dibuat.")

    try:
        with open(CLUSTER_ROE_DATA_PATH, 'rb') as f: roe_df = pickle.load(f)
        if isinstance(roe_df, pd.DataFrame) and not roe_df.empty:
            roe_data_actually_loaded = True
            if 'cluster' in roe_df.columns and 'cluster_roe' not in roe_df.columns:
                roe_df.rename(columns={'cluster': 'cluster_roe'}, inplace=True)
            if not all(col in roe_df.columns for col in ['ticker', 'ROE', 'cluster_roe']):
                logger.warning(f"Kolom penting ROE mungkin hilang di {CLUSTER_ROE_DATA_PATH}.")
        else:
            logger.warning(f"{CLUSTER_ROE_DATA_PATH} kosong/invalid. Pakai dummy ROE.")
            roe_df = None
    except Exception as e:
        logger.error(f"Error load ROE data {CLUSTER_ROE_DATA_PATH}: {e}. Pakai dummy ROE.")
        roe_df = None

    if roe_df is None:
        roe_data_actually_loaded = False
        roe_df_data = {'ticker': [f'SahamD_ROE{i}' for i in range(1, 6)],
                       'ROE': [0.15, 0.05, 0.20, 0.08, 0.25], 'cluster_roe': [0, 1, 0, 1, 0]}
        roe_df = pd.DataFrame(roe_df_data)
        if not eps_df[eps_df['ticker'].str.startswith('SahamD_EPS')].empty and len(roe_df) == len(eps_df):
            roe_df['ticker'] = eps_df['ticker'].str.replace('EPS', 'ROE').head(len(roe_df))
        logger.info("Dummy ROE data dibuat.")

    try:
        with open(KMEANS_EPS_MODEL_PATH, 'rb') as f: eps_model_obj = pickle.load(f)
    except Exception: eps_model_obj = DummyKMeans(n_clusters=2); logger.warning(f"Pakai dummy model EPS.")
    try:
        with open(KMEANS_ROE_MODEL_PATH, 'rb') as f: roe_model_obj = pickle.load(f)
    except Exception: roe_model_obj = DummyKMeans(n_clusters=2); logger.warning(f"Pakai dummy model ROE.")

    if 'ticker' not in eps_df.columns or 'ticker' not in roe_df.columns:
        logger.critical("Kolom 'ticker' hilang. Merge mungkin tidak akurat.")
        merged_df = eps_df.copy()
        if 'ROE' not in merged_df.columns: merged_df['ROE'] = roe_df['ROE'].values if 'ROE' in roe_df.columns and len(roe_df) == len(merged_df) else 0.0
        if 'cluster_roe' not in merged_df.columns: merged_df['cluster_roe'] = roe_df['cluster_roe'].values if 'cluster_roe' in roe_df.columns and len(roe_df) == len(merged_df) else 0
    else:
        eps_df['ticker'] = eps_df['ticker'].astype(str)
        roe_df['ticker'] = roe_df['ticker'].astype(str)
        merged_df = pd.merge(eps_df, roe_df[['ticker'] + ([col for col in ['ROE', 'cluster_roe'] if col in roe_df.columns])], on='ticker', how='outer')
        logger.info(f"Data digabung. Shape: {merged_df.shape}")

    for col_key in SOURCE_TABLE_COLUMNS:
        if col_key not in merged_df.columns:
            if col_key in ['EPS', 'ROE', 'netincometocommon', 'shareoutstanding']: merged_df[col_key] = 0.0
            elif col_key in ['cluster', 'cluster_roe']: merged_df[col_key] = 0
            else: merged_df[col_key] = "N/A"
    
    num_cols = ['EPS', 'ROE', 'netincometocommon', 'shareoutstanding']
    clust_cols = ['cluster', 'cluster_roe']
    for col in num_cols: merged_df[col] = pd.to_numeric(merged_df[col], errors='coerce').fillna(0.0)
    for col in clust_cols: merged_df[col] = pd.to_numeric(merged_df[col], errors='coerce').fillna(0).astype(int)
    if 'ticker' in merged_df.columns: merged_df['ticker'] = merged_df['ticker'].fillna("UnknownTicker").astype(str)
    else: merged_df['ticker'] = [f"UnknownTicker{i}" for i in range(len(merged_df))]

    return merged_df, eps_model_obj, roe_model_obj, eps_data_actually_loaded, roe_data_actually_loaded

class ClusterStat(BaseModel):
    id: int; label: str; count: int; avg_metric: str; recommendation: str

class DashboardData(BaseModel):
    page_title: str = "Analisis Clustering Saham"; eps_data_loaded: bool; roe_data_loaded: bool
    eps_metric: str = "EPS"; roe_metric: str = "ROE"; eps_scatter_plot_html: str
    eps_bar_chart_base64: Optional[str] = None; eps_cluster_stats_list: List[ClusterStat]
    roe_scatter_plot_html: str; roe_bar_chart_base64: Optional[str] = None
    roe_cluster_stats_list: List[ClusterStat]; table_headers: List[str]
    table_rows: List[Dict[str, Any]]; num_eps_clusters: Optional[str] = "N/A" # Diubah jadi str
    num_roe_clusters: Optional[str] = "N/A" # Diubah jadi str

@app.get("/api/dashboard-data", response_model=DashboardData)
async def get_dashboard_data():
    logger.info("Request diterima untuk /api/dashboard-data")
    try:
        df, kmeans_eps_model, kmeans_roe_model, eps_data_loaded, roe_data_loaded = load_data_and_models_core()
        logger.info(f"Data dimuat. EPS: {eps_data_loaded}, ROE: {roe_data_loaded}. Shape: {df.shape if df is not None else 'None'}")

        # Inisialisasi kolom default jika tidak ada
        for col in ['cluster', 'cluster_roe']: df[col] = pd.to_numeric(df.get(col), errors='coerce').fillna(0).astype(int)
        for col in ['EPS', 'ROE']: df[col] = pd.to_numeric(df.get(col), errors='coerce').fillna(0.0)
        df['keterangan'] = df.get('keterangan', 'Data Tidak Tersedia')
        df['keterangan_roe'] = df.get('keterangan_roe', 'Data Tidak Tersedia')

        # --- Logika Keterangan EPS ---
        if eps_data_loaded and not df.empty and 'EPS' in df.columns and df['EPS'].notna().any():
            try:
                cluster_eps_means = df.groupby('cluster')['EPS'].mean()
                if len(cluster_eps_means) > 1:
                    eps_high_lbl, eps_low_lbl = cluster_eps_means.idxmax(), cluster_eps_means.idxmin()
                    df['keterangan'] = df['cluster'].apply(lambda x: 'EPS Tinggi' if x == eps_high_lbl else ('EPS Rendah' if x == eps_low_lbl else 'EPS Sedang'))
                elif len(cluster_eps_means) == 1: df['keterangan'] = 'EPS Data Tunggal'
                else: df['keterangan'] = 'Data EPS Kurang (A)'
            except Exception as e: logger.error(f"Error keterangan EPS: {e}"); df['keterangan'] = 'Error Keterangan EPS'
        else: df['keterangan'] = 'Data EPS Tidak Ada (B)'
        
        # --- Logika Keterangan ROE ---
        if roe_data_loaded and not df.empty and 'ROE' in df.columns and df['ROE'].notna().any():
            try:
                cluster_roe_means = df.groupby('cluster_roe')['ROE'].mean()
                if len(cluster_roe_means) > 1:
                    roe_high_lbl, roe_low_lbl = cluster_roe_means.idxmax(), cluster_roe_means.idxmin()
                    df['keterangan_roe'] = df['cluster_roe'].apply(lambda x: 'ROE Tinggi' if x == roe_high_lbl else ('ROE Rendah' if x == roe_low_lbl else 'ROE Sedang'))
                elif len(cluster_roe_means) == 1: df['keterangan_roe'] = 'ROE Data Tunggal'
                else: df['keterangan_roe'] = 'Data ROE Kurang (A)'
            except Exception as e: logger.error(f"Error keterangan ROE: {e}"); df['keterangan_roe'] = 'Error Keterangan ROE'
        else: df['keterangan_roe'] = 'Data ROE Tidak Ada (B)'

        # Fallback jika df masih kosong
        if df.empty:
            df = pd.DataFrame([{col_key: "N/A" for col_key in SOURCE_TABLE_COLUMNS}])
            for col_key_fill in ['EPS', 'ROE', 'netincometocommon', 'shareoutstanding']: df[col_key_fill] = 0.0
            for col_key_fill in ['cluster', 'cluster_roe']: df[col_key_fill] = 0
            df['keterangan'], df['keterangan_roe'] = 'Data Tidak Tersedia', 'Data Tidak Tersedia'
            logger.info("DataFrame fallback final digunakan.")

        # Pastikan semua kolom sumber ada
        for col_key in SOURCE_TABLE_COLUMNS:
            if col_key not in df.columns:
                if col_key in ['keterangan', 'keterangan_roe']: df[col_key] = 'Data Tidak Tersedia'
                elif col_key in ['EPS', 'ROE', 'netincometocommon', 'shareoutstanding']: df[col_key] = 0.0
                elif col_key in ['cluster', 'cluster_roe']: df[col_key] = 0
                else: df[col_key] = "N/A"

        # --- EPS Scatter Plot ---
        eps_scatter_plot_html = '<p class="text-center text-gray-500 p-4">Plot scatter EPS tidak dapat dibuat (data awal).</p>' # Default fallback
        num_eps_clusters_val = str(getattr(kmeans_eps_model, "n_clusters", "N/A"))
        try:
            # Kategori harus ada di df['keterangan'] sebelum membuat Categorical
            eps_categories = ['EPS Rendah', 'EPS Tinggi', 'EPS Sedang', 'EPS Data Tunggal', 
                              'Data EPS Kurang (A)', 'Data EPS Tidak Ada (B)', 'Error Keterangan EPS']
            df['keterangan_cat_eps'] = pd.Categorical(df['keterangan'].fillna('Data EPS Tidak Ada (B)'), 
                                                      categories=eps_categories, ordered=True)
            
            logger.info(f"Data untuk plot scatter EPS (head):\n{df[['ticker', 'EPS', 'keterangan', 'keterangan_cat_eps']].head(3)}")
            logger.info(f"Info kolom EPS untuk plot: {df['EPS'].describe()}")
            logger.info(f"Info keterangan_cat_eps untuk plot: {df['keterangan_cat_eps'].value_counts(dropna=False)}")

            # Hanya buat plot jika ada data valid di kolom yang diperlukan
            if not df.empty and 'EPS' in df.columns and df['EPS'].notna().any() and \
               'keterangan_cat_eps' in df.columns and df['keterangan_cat_eps'].notna().any() and \
               len(df['keterangan_cat_eps'].unique()) > 0:

                fig_eps = px.scatter(df, x='EPS', y='keterangan_cat_eps', color='keterangan_cat_eps',
                                   hover_data={'ticker': True, 'EPS': True, 'keterangan': True},
                                   color_discrete_map={cat: px.colors.qualitative.Plotly[i % len(px.colors.qualitative.Plotly)] for i, cat in enumerate(eps_categories)},
                                   height=450, title=f'Clustering EPS ({num_eps_clusters_val} Cluster)')
                fig_eps.update_layout(yaxis_title="Keterangan EPS", xaxis_title="Nilai EPS", plot_bgcolor='white')
                eps_scatter_plot_html = fig_eps.to_html(full_html=False, include_plotlyjs='cdn')
                logger.info(f"Plot scatter EPS dibuat. HTML (awal): {eps_scatter_plot_html[:200]}")
            else:
                logger.warning("Data tidak cukup atau tidak valid untuk membuat plot scatter EPS.")
                eps_scatter_plot_html = '<p class="text-center text-orange-500 p-4">Data tidak cukup untuk visualisasi scatter EPS.</p>'
        except Exception as e:
            logger.error(f"Error membuat plot scatter EPS: {e}", exc_info=True)
            eps_scatter_plot_html = f'<p class="text-center text-red-500 p-4">Error membuat scatter plot EPS: {e}</p>'

        # --- ROE Scatter Plot (struktur serupa dengan EPS) ---
        roe_scatter_plot_html = '<p class="text-center text-gray-500 p-4">Plot scatter ROE tidak dapat dibuat (data awal).</p>'
        num_roe_clusters_val = str(getattr(kmeans_roe_model, "n_clusters", "N/A"))
        try:
            roe_categories = ['ROE Rendah', 'ROE Tinggi', 'ROE Sedang', 'ROE Data Tunggal',
                              'Data ROE Kurang (A)', 'Data ROE Tidak Ada (B)', 'Error Keterangan ROE']
            df['keterangan_cat_roe'] = pd.Categorical(df['keterangan_roe'].fillna('Data ROE Tidak Ada (B)'),
                                                       categories=roe_categories, ordered=True)
            
            logger.info(f"Data untuk plot scatter ROE (head):\n{df[['ticker', 'ROE', 'keterangan_roe', 'keterangan_cat_roe']].head(3)}")
            logger.info(f"Info kolom ROE untuk plot: {df['ROE'].describe()}")
            logger.info(f"Info keterangan_cat_roe untuk plot: {df['keterangan_cat_roe'].value_counts(dropna=False)}")
            
            if not df.empty and 'ROE' in df.columns and df['ROE'].notna().any() and \
               'keterangan_cat_roe' in df.columns and df['keterangan_cat_roe'].notna().any() and \
               len(df['keterangan_cat_roe'].unique()) > 0:

                fig_roe = px.scatter(df, x='ROE', y='keterangan_cat_roe', color='keterangan_cat_roe',
                                   hover_data={'ticker': True, 'ROE': True, 'keterangan_roe': True},
                                   color_discrete_map={cat: px.colors.qualitative.Pastel[i % len(px.colors.qualitative.Pastel)] for i, cat in enumerate(roe_categories)},
                                   height=450, title=f'Clustering ROE ({num_roe_clusters_val} Cluster)')
                fig_roe.update_layout(yaxis_title="Keterangan ROE", xaxis_title="Nilai ROE", plot_bgcolor='white')
                roe_scatter_plot_html = fig_roe.to_html(full_html=False, include_plotlyjs='cdn')
                logger.info(f"Plot scatter ROE dibuat. HTML (awal): {roe_scatter_plot_html[:200]}")
            else:
                logger.warning("Data tidak cukup atau tidak valid untuk membuat plot scatter ROE.")
                roe_scatter_plot_html = '<p class="text-center text-orange-500 p-4">Data tidak cukup untuk visualisasi scatter ROE.</p>'
        except Exception as e:
            logger.error(f"Error membuat plot scatter ROE: {e}", exc_info=True)
            roe_scatter_plot_html = f'<p class="text-center text-red-500 p-4">Error membuat scatter plot ROE: {e}</p>'

        # --- EPS Bar Chart (Ambil dari versi sebelumnya, pastikan try-except ada) ---
        eps_bar_chart_base64 = None
        try:
            if 'EPS' in df.columns and 'ticker' in df.columns and df['ticker'].notna().any():
                df_valid_tickers_eps = df[df['ticker'].notna() & ~df['ticker'].isin(["N/A", "UnknownTicker"]) & df['EPS'].notna()]
                if not df_valid_tickers_eps.empty:
                    df_sorted_eps = df_valid_tickers_eps.sort_values(by='EPS', ascending=False).head(15)
                    if not df_sorted_eps.empty:
                        plt.figure(figsize=(10, 7))
                        ax_eps = sns.barplot(data=df_sorted_eps, x='EPS', y='ticker', palette='viridis')
                        plt.title('Top 15 Saham EPS Tertinggi', fontsize=15)
                        max_val = df_sorted_eps['EPS'].max(); min_val_eps = df_sorted_eps['EPS'].min()
                        offset_eps = (max_val - min_val_eps) * 0.02 if (max_val - min_val_eps) > 0 else 0.02 * abs(max_val) if max_val != 0 else 0.02
                        for i, (val, ticker_val) in enumerate(zip(df_sorted_eps['EPS'], df_sorted_eps['ticker'])):
                            ax_eps.text(val + offset_eps, i, f'{val:.2f}', va='center', fontsize=8)
                        plt.tight_layout(pad=0.5); buf = io.BytesIO(); plt.savefig(buf, format='png', bbox_inches='tight')
                        eps_bar_chart_base64 = base64.b64encode(buf.getvalue()).decode('utf-8'); plt.close()
        except Exception as e: logger.error(f"Error EPS Bar Chart: {e}", exc_info=True)


        # --- ROE Bar Chart (Ambil dari versi sebelumnya, pastikan try-except ada) ---
        roe_bar_chart_base64 = None
        try:
            if 'ROE' in df.columns and 'ticker' in df.columns and df['ticker'].notna().any():
                df_valid_tickers_roe = df[df['ticker'].notna() & ~df['ticker'].isin(["N/A", "UnknownTicker"]) & df['ROE'].notna()]
                if not df_valid_tickers_roe.empty:
                    df_sorted_roe = df_valid_tickers_roe.sort_values(by='ROE', ascending=False).head(15)
                    if not df_sorted_roe.empty:
                        plt.figure(figsize=(10, 7))
                        ax_roe = sns.barplot(data=df_sorted_roe, x='ROE', y='ticker', palette='plasma')
                        plt.title('Top 15 Saham ROE Tertinggi', fontsize=15)
                        max_val_roe = df_sorted_roe['ROE'].max(); min_val_roe = df_sorted_roe['ROE'].min()
                        offset_roe = (max_val_roe - min_val_roe) * 0.02 if (max_val_roe - min_val_roe) > 0 else 0.02 * abs(max_val_roe) if max_val_roe != 0 else 0.002
                        for i, (val, ticker_val) in enumerate(zip(df_sorted_roe['ROE'], df_sorted_roe['ticker'])):
                             ax_roe.text(val + offset_roe, i, f'{val:.2%}', va='center', fontsize=8)
                        plt.tight_layout(pad=0.5); buf = io.BytesIO(); plt.savefig(buf, format='png', bbox_inches='tight')
                        roe_bar_chart_base64 = base64.b64encode(buf.getvalue()).decode('utf-8'); plt.close()
        except Exception as e: logger.error(f"Error ROE Bar Chart: {e}", exc_info=True)

        # --- Statistik Cluster EPS & ROE (Ambil dari versi sebelumnya) ---
        eps_cluster_stats_list, roe_cluster_stats_list = [], []
        try: # EPS Stats
            if 'cluster' in df.columns and 'EPS' in df.columns and df['cluster'].notna().any():
                for cid in sorted(df['cluster'].unique()):
                    subset = df[df['cluster'] == cid]
                    if subset.empty: continue
                    lbl = subset['keterangan'].mode()[0] if not subset['keterangan'].empty and not subset['keterangan'].mode().empty else 'N/A'
                    recom = 'Buy' if lbl == 'EPS Tinggi' else ('Hold' if lbl == 'EPS Rendah' else 'Review')
                    avg_m = subset['EPS'].mean()
                    eps_cluster_stats_list.append(ClusterStat(id=int(cid), label=str(lbl), count=len(subset), avg_metric=f"{avg_m:.2f}" if pd.notna(avg_m) else "N/A", recommendation=str(recom)))
        except Exception as e: logger.error(f"Error EPS Cluster Stats: {e}", exc_info=True)

        try: # ROE Stats
            if 'cluster_roe' in df.columns and 'ROE' in df.columns and df['cluster_roe'].notna().any():
                for cid in sorted(df['cluster_roe'].unique()):
                    subset = df[df['cluster_roe'] == cid]
                    if subset.empty: continue
                    lbl = subset['keterangan_roe'].mode()[0] if not subset['keterangan_roe'].empty and not subset['keterangan_roe'].mode().empty else 'N/A'
                    recom = 'Buy' if lbl == 'ROE Tinggi' else ('Hold' if lbl == 'ROE Rendah' else 'Review')
                    avg_m = subset['ROE'].mean()
                    roe_cluster_stats_list.append(ClusterStat(id=int(cid), label=str(lbl), count=len(subset), avg_metric=f"{avg_m:.2%}" if pd.notna(avg_m) else "N/A", recommendation=str(recom)))
        except Exception as e: logger.error(f"Error ROE Cluster Stats: {e}", exc_info=True)
        
        # --- Data Tabel (Ambil dari versi sebelumnya) ---
        final_table_rows = []
        try:
            if not df.empty:
                for _, row_s in df.iterrows():
                    row_d_orig = row_s.to_dict(); fmt_row = {}
                    for src_c, disp_n in TABLE_COLUMN_MAP.items():
                        val = row_d_orig.get(src_c); f_val = "N/A"
                        if pd.notna(val) and str(val).lower() not in ["unknownticker", "nan", "na", "n/a", "", "none"]:
                            try:
                                if src_c in ['netincometocommon', 'shareoutstanding']: f_val = f"{float(val):,.0f}"
                                elif src_c == 'EPS': f_val = f"{float(val):,.2f}"
                                elif src_c == 'ROE': f_val = f"{float(val):,.2%}"
                                else: f_val = str(val)
                            except ValueError: f_val = str(val) if val is not None else "N/A"
                        fmt_row[disp_n] = f_val
                    final_table_rows.append(fmt_row)
            if not final_table_rows: final_table_rows.append({h: "Data Tidak Tersedia" for h in DISPLAY_TABLE_HEADERS})
        except Exception as e:
            logger.error(f"Error membuat data tabel: {e}", exc_info=True)
            final_table_rows = [{h: "Error Proses Tabel" for h in DISPLAY_TABLE_HEADERS}]


        response_data = DashboardData(
            eps_data_loaded=eps_data_loaded, roe_data_loaded=roe_data_loaded,
            eps_scatter_plot_html=eps_scatter_plot_html, eps_bar_chart_base64=eps_bar_chart_base64,
            eps_cluster_stats_list=eps_cluster_stats_list, roe_scatter_plot_html=roe_scatter_plot_html,
            roe_bar_chart_base64=roe_bar_chart_base64, roe_cluster_stats_list=roe_cluster_stats_list,
            table_headers=DISPLAY_TABLE_HEADERS, table_rows=final_table_rows,
            num_eps_clusters=str(num_eps_clusters_val), num_roe_clusters=str(num_roe_clusters_val)
        )
        logger.info("Data dashboard siap. Mengirim respons.")
        return response_data

    except Exception as e:
        logger.error(f"Kesalahan fatal di get_dashboard_data: {e}", exc_info=True)
        # Mengembalikan HTML error yang aman jika Pydantic model gagal atau error lain terjadi sebelum return
        error_plot_html = f'<p class="text-center text-red-500 p-5">Terjadi kesalahan server saat memproses data: {e}</p>'
        return DashboardData(
            eps_data_loaded=False, roe_data_loaded=False,
            eps_scatter_plot_html=error_plot_html, eps_cluster_stats_list=[],
            roe_scatter_plot_html=error_plot_html, roe_cluster_stats_list=[],
            table_headers=DISPLAY_TABLE_HEADERS, table_rows=[{h: "Error" for h in DISPLAY_TABLE_HEADERS}],
            num_eps_clusters="Error", num_roe_clusters="Error"
        )

if __name__ == '__main__':
    logger.info(f"Mulai aplikasi backend di {BASE_DIR}")
    # (Bagian ini biasanya tidak dijalankan langsung jika pakai `uvicorn main:app ...` di CLI)
    # import uvicorn
    # uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")