import streamlit as st
import pandas as pd
import os
import random
from datetime import datetime, timedelta, time as dt_time
from database import SessionLocal, TemperatureForecast

# Constants
CSV_FILE = "temperature_datas.csv"
FALLBACK_MIN = 32.0
FALLBACK_MAX = 60.0

# Define regions and cities
regions_cities = {
    "NCR": ["Manila", "Quezon City", "Pasig"],
    "CAR": ["Baguio", "La Trinidad"],
    "Region I": ["San Fernando", "Laoag"],
    "Region II": ["Tuguegarao", "Ilagan"],
    "Region III": ["San Fernando", "Balanga"],
    "Region IV-A": ["Calamba", "Lucena"],
    "Region IV-B": ["Puerto Princesa", "Calapan"],
    "Region V": ["Legazpi", "Naga"],
    "Region VI": ["Iloilo City", "Bacolod"],
    "Region VII": ["Cebu City", "Tagbilaran"],
    "Region VIII": ["Tacloban", "Catbalogan"],
    "Region IX": ["Zamboanga City", "Dipolog"],
    "Region X": ["Cagayan de Oro", "Malaybalay"],
    "Region XI": ["Davao City", "Tagum"],
    "Region XII": ["Koronadal", "Kidapawan"],
    "Region XIII": ["Butuan", "Surigao"],
    "BARMM": ["Cotabato City", "Marawi"]
}

# Generate sample CSV if not found or empty
def generate_initial_csv():
    today = datetime.now().date()
    dates = [today + timedelta(days=i) for i in range(5)]
    hours = [f"{h:02d}:00" for h in range(24)]
    rows = []

    for region, cities in regions_cities.items():
        for city in cities:
            for date in dates:
                for hour in hours:
                    temp = round(random.uniform(FALLBACK_MIN, FALLBACK_MAX), 1)
                    max_temp = round(temp + random.uniform(1.0, 3.0), 1)
                    rows.append({
                        "region": region,
                        "city": city,
                        "date": date.strftime("%Y-%m-%d"),
                        "time": hour,
                        "temperature": temp,
                        "max_temperature": max_temp
                    })
    df = pd.DataFrame(rows)
    df.to_csv(CSV_FILE, index=False)

# Create file if missing or empty
if not os.path.exists(CSV_FILE) or os.stat(CSV_FILE).st_size == 0:
    generate_initial_csv()

# Load data
try:
    df = pd.read_csv(CSV_FILE)
except Exception as e:
    st.error(f"Failed to read CSV: {e}")
    st.stop()

# Streamlit UI
st.title("🌤️ Philippine Temperature Forecasting")

if 'region' not in df.columns or 'city' not in df.columns:
    st.error("CSV missing 'region' or 'city' columns.")
    st.stop()

regions = sorted(df['region'].dropna().unique())
selected_region = st.selectbox("Select Region", regions)

filtered_cities = df[df['region'] == selected_region]['city'].dropna().unique()
selected_city = st.selectbox("Select City", sorted(filtered_cities))

selected_date = st.date_input("Select Forecast Date", datetime.now().date())

if "selected_time" not in st.session_state:
    st.session_state.selected_time = datetime.now().time().replace(minute=0, second=0)

selected_time = st.time_input("Select Forecast Time", value=st.session_state.selected_time)
st.session_state.selected_time = selected_time

# Format for matching
selected_time_str = selected_time.strftime("%H:%M")
selected_date_str = selected_date.strftime("%Y-%m-%d")

# Key for caching randomized forecast
forecast_key = f"{selected_region}_{selected_city}_{selected_date_str}_{selected_time_str}"

# Filter historical data
filtered = df[
    (df['region'] == selected_region) &
    (df['city'] == selected_city) &
    (df['date'] == selected_date_str) &
    (df['time'] == selected_time_str)
]

# Forecast logic
if forecast_key not in st.session_state:
    if filtered.empty:
        st.warning("⚠️ No historical data found. Automatically forecasting temperature.")
        predicted_temp = round(random.uniform(FALLBACK_MIN, FALLBACK_MAX), 1)
        predicted_max_temp = round(predicted_temp + random.uniform(1.0, 3.0), 1)
    else:
        predicted_temp = round(filtered['temperature'].mean(), 1)
        predicted_max_temp = round(filtered['max_temperature'].mean(), 1)

    # Store once per session key
    st.session_state[forecast_key] = {
        "temperature": predicted_temp,
        "max_temperature": predicted_max_temp
    }

# Retrieve from cache
predicted_temp = st.session_state[forecast_key]["temperature"]
predicted_max_temp = st.session_state[forecast_key]["max_temperature"]

# Display forecast
st.metric("Forecasted Temperature (°C)", f"{predicted_temp:.1f}°C")
st.metric("Forecasted Max Temperature (°C)", f"{predicted_max_temp:.1f}°C")

# Save forecast
if st.button("Save Forecast"):
    # Save to database
    session = SessionLocal()
    try:
        new_record = TemperatureForecast(
            region=selected_region,
            city=selected_city,
            date=selected_date,
            time=selected_time,
            temperature=float(predicted_temp),
            max_temperature=float(predicted_max_temp)
        )
        session.add(new_record)
        session.commit()
    except Exception as e:
        st.error(f"❌ Failed to save to database: {e}")
    finally:
        session.close()

    # Save to CSV
    new_row = pd.DataFrame([{
        "region": selected_region,
        "city": selected_city,
        "date": selected_date_str,
        "time": selected_time_str,
        "temperature": predicted_temp,
        "max_temperature": predicted_max_temp
    }])

    if os.path.exists(CSV_FILE):
        new_row.to_csv(CSV_FILE, mode='a', header=False, index=False)
    else:
        new_row.to_csv(CSV_FILE, index=False)

    st.success("✅ Forecast saved to database and CSV.")
