# Net Worth Calculator

## Overview

The **Net Worth Calculator** is a Streamlit-based web application that helps users track, visualize, and analyze their personal assets and liabilities over time. It provides interactive dashboards, analytics, and historical tracking to give a clear picture of your financial health.

---

## Features

- **Add, Edit, and Delete Assets/Liabilities:**  
  Easily manage your financial entries with intuitive forms.

- **Category & Subcategory Tracking:**  
  Organize your assets and liabilities by category and subcategory for detailed analysis.

- **Historical Tracking:**  
  Every change to an entry is logged, allowing you to see how your finances evolve over time.

- **Interactive Dashboards:**  
  Visualize net worth, cash flow, and category trends with interactive Plotly charts.

- **Analytics:**  
  View top assets, liabilities, monthly/yearly trends, and more.

---

## File Structure

```
networthcalculator/
│
├── src/
│   └── networthcalculator/
│       ├── app.py                # Main Streamlit application
│       ├── db_utils.py           # Database connection and utility functions
│       
│
├── requirements.txt              # Python dependencies
├── .gitignore                    # Files and folders to ignore in git
└── README.md                     # This file
```

---

## Python Files Explained

### `app.py`
- The main entry point for the Streamlit app.
- Handles user interface, navigation, and calls functions from other modules for database operations and analytics.

### `db_utils.py`
- Contains functions for connecting to the SQLite database.
- Handles creation of tables, insertion, updates, deletions, and history logging.

### `analytics.py`
- Provides functions for generating analytics and visualizations.
- Includes logic for calculating net worth, cash flow, trends, and category breakdowns.

---

## How to Use

1. **Install dependencies:**
   ```
   pip install -r requirements.txt
   ```

2. **Run the app:**
   ```
   streamlit run src/networthcalculator/app.py
   ```

3. **Add your assets and liabilities, and explore the dashboards!**

---

## Customization

- You can adjust categories, add new analytics, or modify the database schema as needed for your personal finance tracking.

---

## License

MIT License

---
