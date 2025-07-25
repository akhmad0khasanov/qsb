# Write code yourself, not AI
import streamlit as st
import plotly as pl 
import pandas as pd

my_data = input('Upload CSV: ')

st.write("""
My first app Hello World
""")

df = pd.read_csv("my_data")
st.line_chart(df)
