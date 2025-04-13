# app.py
import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(layout="wide", page_title="Weekly Color Management - Mutoh 924")
st.title("🎨 Weekly Color Management - Mutoh 924 Printers")

# Sidebar
printer = st.sidebar.selectbox("Select Printer", [f"Mutoh 924 #{i+1}" for i in range(10)])
week = st.sidebar.text_input("Date (e.g., 01/01/2025)", value="enter date")
uploaded_file = st.sidebar.file_uploader("Upload Spectro Data (.csv or .txt)", type=["csv", "txt"])

# Load reference file
try:
    ref_data = pd.read_csv("g7_reference_lab.csv")
    ref_data.columns = ref_data.columns.str.strip()  # Clean column names
except Exception as e:
    st.error(f"⚠️ Could not load G7 reference data: {e}")
    st.stop()

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file, sep=",", header=0, engine="python")
        df.columns = df.columns.str.strip()  # Clean column names

        # Failsafe: split columns if improperly parsed
        if len(df.columns) == 1 and "," in df.columns[0]:
            df = pd.DataFrame([x.split(",") for x in df[df.columns[0]]])
            df.columns = ["Patch", "L", "a", "b"]
            df[["L", "a", "b"]] = df[["L", "a", "b"]].apply(pd.to_numeric)
            df.columns = df.columns.str.strip()

    except Exception as e:
        st.error(f"❌ Could not read uploaded file: {e}")
        st.stop()

    st.subheader(f"📋 Uploaded Data for {printer} - Week {week}")
    st.write("🔍 Uploaded Columns:", df.columns.tolist())
    st.dataframe(df)

    st.write("📌 Reference Columns:", ref_data.columns.tolist())

    if all(col in df.columns for col in ["L", "a", "b"]) and all(col in ref_data.columns for col in ["L", "a", "b"]):
        try:
            df["DeltaE"] = ((df["L"] - ref_data["L"])**2 +
                            (df["a"] - ref_data["a"])**2 +
                            (df["b"] - ref_data["b"])**2) ** 0.5

            if "Patch" not in df.columns:
                df["Patch"] = df.index

            fig = px.bar(df, x="Patch", y="DeltaE", color="DeltaE", title="ΔE Deviation from Reference")
            st.plotly_chart(fig, use_container_width=True)

            st.metric("Max ΔE", f"{df['DeltaE'].max():.2f}")
            st.metric("Average ΔE", f"{df['DeltaE'].mean():.2f}")
            st.metric("Pass/Fail", "✅ Pass" if df["DeltaE"].max() <= 5 else "❌ Fail")

            if st.button("📁 Log This Report"):
                df["Printer"] = printer
                df["Week"] = week
                os.makedirs("logs", exist_ok=True)
                df.to_csv(f"logs/{printer.replace(' ', '_')}_{week}.csv", index=False)
                st.success("✅ Report logged successfully!")
        except Exception as e:
            st.error(f"Error calculating ΔE: {e}")
    else:
        st.error("❌ Both uploaded file and reference must contain 'L', 'a', and 'b' columns.")
else:
    st.info("👈 Upload a color measurement file to begin.")
