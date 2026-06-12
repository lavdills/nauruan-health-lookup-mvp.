# Nauruan Health Lookup MVP - Streamlit Deploy Package v3

This version fixes the Streamlit TypeError caused by blank CSV cells being read as NaN floats.

Upload these extracted files to GitHub:

- app.py
- requirements.txt
- health_lookup_records.csv
- data/health_lookup_records.csv

Then redeploy/reboot the Streamlit app.

The app reads all CSV columns as text using dtype=str and keep_default_na=False, so searches should no longer fail when a record has blank fields.
