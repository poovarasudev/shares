# 📈 Money Control Stock Analyzer

A comprehensive Streamlit-based stock analysis application that aggregates data from multiple sources including Google Sheets, databases, and APIs. Built with a modular architecture to support easy integration of new data sources.

![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![Streamlit](https://img.shields.io/badge/streamlit-1.52+-red.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## 📋 Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [Project Structure](#-project-structure)
- [Adding Data Sources](#-adding-data-sources)
- [Development](#-development)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [License](#-license)

## ✨ Features

### 📊 Market Overview
- **Comprehensive Data Table**: View all tracked companies with sortable columns
- **Column Visibility Controls**: Show/hide columns based on your needs
  - Default visible: Company Name, Sector, Industry, Cost, M-Score, TTM PE, Analyst Rating
  - Hidden by default: SC ID, Status, TTM EPS, P/B, Sector PE, Analyst Count, PE vs Sector %, Analyst Confidence
- **Advanced Filtering**:
  - Text search by company name or SC ID
  - Multi-select category filters (Sector, Industry, Status)
  - Numeric range sliders (M-Score, PE Ratio)
  - Result count display
  - One-click filter reset
- **Smart Sorting**: Dual dropdowns for column selection and sort order
  - Choose from 14+ sortable columns (Company Name, M-Score, Cost, PE vs Sector %, TTM PE, TTM EPS, P/B, Analyst Rating, etc.)
  - Toggle between ascending (↑) and descending (↓) order
- **Pagination**: Navigate through large datasets efficiently (15 items per page)
- **Multiple View Modes**: Switch between Table and Card views
- **PE Value Highlighting**: Automatic color coding for PE values
  - 🟢 Green: Undervalued (PE ≥20% cheaper than sector)
  - 🟡 Amber: Fair valuation (within sector range)
  - 🔴 Red: Overvalued (PE ≥20% more expensive than sector)
  - PE vs Sector % with colored indicators in card view
- **Data Export**: Download filtered results as CSV

### 🏢 Company Details
- **Comprehensive Company Profile**:
  - Real-time price with change indicators
  - 6 key financial metrics (M-Score, Cost, TTM EPS, TTM PE, P/B, Sector PE)
  - Company strengths analysis
  - Seasonality analysis with data tables
  - Analyst ratings breakdown with distribution charts
- **Navigation**: Quick back button to market overview
- **Deep Linking**: Shareable URLs for specific companies

### 🔌 Modular Data Sources
- **Google Sheets Integration**: Public sheet CSV export with retry logic
- **Extensible Architecture**: Easy addition of new sources
  - Database connectors (PostgreSQL, MySQL, SQLite)
  - REST API integrations
  - File imports (CSV, Excel, JSON)
- **Centralized Registry**: Manage multiple data sources from one place
- **Smart Caching**: 15-minute TTL with manual refresh option

## 🏗 Architecture

### Design Principles

1. **Separation of Concerns**: Clear separation between data, business logic, and presentation
2. **Modularity**: Data sources are pluggable modules following a common interface
3. **Scalability**: Built to handle multiple data sources and large datasets
4. **Maintainability**: Well-organized code structure with comprehensive documentation

### Component Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Streamlit UI Layer                    │
│  (app.py + pages/)                                       │
└────────────────┬────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────┐
│              Data Source Registry                        │
│  (Manages multiple data sources)                         │
└────┬──────────────────────────────────────────┬─────────┘
     │                                           │
┌────▼─────────────┐  ┌──────────────────┐  ┌──▼──────────┐
│ Google Sheets    │  │ Database         │  │ REST API    │
│ Source           │  │ Source           │  │ Source      │
└──────────────────┘  └──────────────────┘  └─────────────┘
```

## 📦 Installation

### Prerequisites

- Python 3.9 or higher
- pip (Python package manager)
- Virtual environment (recommended)

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd shares
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv .venv
   
   # On macOS/Linux:
   source .venv/bin/activate
   
   # On Windows:
   .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and add your configuration:
   ```env
   STOCK_GOOGLE_SHEET_URL=your_google_sheets_url_here
   ```

5. **Run the application**
   ```bash
   streamlit run app.py
   ```

6. **Access the application**
   - Local: http://localhost:8501
   - Network: http://YOUR_IP:8501

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Google Sheets Configuration
STOCK_GOOGLE_SHEET_URL=https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit

# Database Configuration (Optional)
DB_HOST=localhost
DB_PORT=5432
DB_NAME=stocks
DB_USER=username
DB_PASSWORD=password

# API Configuration (Optional)
API_BASE_URL=https://api.example.com
API_KEY=your_api_key_here
```

### Application Settings

Edit `config/constants.py` to customize:

- **Display Settings**: Items per page, cards per row
- **Column Definitions**: Default visible/hidden columns
- **Filter Options**: Available filters and ranges
- **Data Source Settings**: Cache TTL, retry attempts
- **UI Theme**: Colors, styling constants

## 🚀 Usage

### Starting the Application

```bash
# Standard run
streamlit run app.py

# Run on specific port
streamlit run app.py --server.port 8502

# Run with specific address
streamlit run app.py --server.address 0.0.0.0
```

### Basic Workflow

1. **Home Page**: Overview of available reports and data sources
2. **Market Overview**: 
   - Use filters in sidebar to narrow down companies
   - Configure visible columns using the "Configure Columns" expander
   - Sort data using the sort dropdown
   - Export filtered data using the "Export CSV" button
   - Click on a row or "Details" button to view company details
3. **Company Details**:
   - View comprehensive financial metrics
   - Analyze strengths and seasonality
   - Review analyst ratings
   - Navigate back using the back button

### Keyboard Shortcuts

- `Ctrl/Cmd + R`: Refresh the page
- `Ctrl/Cmd + K`: Focus search box (browser default)

## 📁 Project Structure

```
shares/
├── app.py                          # Main entry point (landing page)
│
├── pages/                          # Streamlit multipage structure
│   ├── 1_📈_Market_Overview.py    # Stock list with filters & sorting
│   └── 2_🏢_Company_Details.py    # Company detail view
│
├── data_sources/                   # Modular data source handlers
│   ├── __init__.py                 # Module exports
│   ├── base.py                     # Abstract base class & config
│   ├── google_sheets.py            # Google Sheets implementation
│   ├── processors.py               # Derived column processors
│   └── registry.py                 # Central source registry
│
├── config/                         # Application configuration
│   ├── __init__.py
│   └── constants.py                # All app constants & thresholds
│
├── utils/                          # Utility functions
│   └── charts.py                   # Chart/visualization helpers
│
├── .env                            # Environment variables (not in git)
├── .env.example                    # Example environment file
├── requirements.txt                # Python dependencies
└── README.md                       # This file
```

## 🔌 Adding Data Sources

### 1. Create a New Data Source

Create a new file in `data_sources/` (e.g., `database.py`):

```python
from .base import DataSourceBase, DataSourceConfig
import pandas as pd

class DatabaseSource(DataSourceBase):
    """Data source for SQL databases."""
    
    def __init__(self, config: DataSourceConfig):
        super().__init__(config)
        self.connection_string = config.connection_params.get('connection_string')
    
    def connect(self) -> bool:
        """Establish database connection."""
        try:
            # Your connection logic here
            return True
        except Exception as e:
            return False
    
    def fetch_data(self) -> pd.DataFrame:
        """Fetch data from database."""
        query = """
            SELECT * FROM stocks 
            WHERE status = 'active'
        """
        # Execute query and return DataFrame
        return pd.read_sql(query, self.connection)
```

### 2. Register the Data Source

In `app.py`, add to the `init_data_sources()` function:

```python
from data_sources.database import DatabaseSource

@st.cache_resource
def init_data_sources():
    # Existing Google Sheets source...
    
    # Add new database source
    db_config = DataSourceConfig(
        name="my_database",
        source_type="database",
        connection_params={
            'connection_string': os.getenv('DB_CONNECTION_STRING')
        },
        cache_ttl=600,
        json_columns=['metrics'],
        numeric_columns=['price', 'pe_ratio'],
    )
    db_source = DatabaseSource(db_config)
    DataSourceRegistry.register("my_database", db_source)
    
    return True
```

### 3. Use the Data Source

In your page:

```python
from data_sources.registry import DataSourceRegistry, load_cached_data

# Get the source
source = DataSourceRegistry.get("my_database")

# Load data with caching
df = load_cached_data("my_database", source)
```

## 🔧 Derived Columns & Processors

Derived columns are computed metrics that add analytical value to your data. The framework supports pluggable "processors" that can be configured per data source, allowing different sheets to have different computations.

### Available Processors

**`compute_pe_vs_sector(df)`**: Compares company PE ratio against sector average
- **Adds columns**:
  - `pe_vs_sector_pct`: Percentage difference (-20% = 20% cheaper than sector)
  - `pe_vs_sector_flag`: Categorical label (Cheap/Fair/Expensive/Unknown)
- **Used for**: Identifying undervalued or overvalued companies

**`compute_analyst_confidence(df)`**: Calculates analyst consensus strength
- **Adds columns**:
  - `analyst_confidence_score`: Numeric 0-100 score combining count + rating
  - `analyst_confidence`: Bucket label (High/Medium/Low/Unknown)
- **Used for**: Assessing analyst agreement on stock recommendations

### Configuring Processors per Data Source

Pass the `derived_processors` parameter when creating a data source:

```python
from data_sources import (
    create_google_sheets_source,
    compute_pe_vs_sector,
    compute_analyst_confidence,
    STOCK_ANALYSIS_PROCESSORS,  # Pre-configured list
    NO_PROCESSORS,  # Empty list for no derived columns
)

# Default: includes both PE and analyst processors
money_control = create_google_sheets_source(
    name="money_control",
    sheet_url=GOOGLE_SHEET_URL,
    sheet_tab="Money Control Stocks List",
    # derived_processors defaults to STOCK_ANALYSIS_PROCESSORS
)

# No derived columns
raw_data = create_google_sheets_source(
    name="raw_data",
    sheet_url=GOOGLE_SHEET_URL,
    sheet_tab="Raw Data",
    derived_processors=NO_PROCESSORS,
)

# Custom: only PE comparison
value_sheet = create_google_sheets_source(
    name="value_stocks",
    sheet_url=GOOGLE_SHEET_URL,
    sheet_tab="Value Picks",
    derived_processors=[compute_pe_vs_sector],
)
```

### Creating Custom Processors

Create your own processor function following this pattern:

```python
import pandas as pd
from typing import Optional

def my_custom_processor(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add custom derived columns to the DataFrame.
    
    Args:
        df: Input DataFrame
        
    Returns:
        DataFrame with new columns added
    """
    df = df.copy()  # Always work on a copy
    
    # Example: Add a simple metric
    df['my_metric'] = df['cost'] * df['m_score']
    
    return df

# Use it in a data source
custom_source = create_google_sheets_source(
    name="custom",
    sheet_url=url,
    sheet_tab="Sheet1",
    derived_processors=[my_custom_processor, compute_pe_vs_sector],
)
```

### Threshold Configuration

Processor behavior is controlled by constants in `config/constants.py`:

```python
# PE comparison thresholds
PE_CHEAP_PCT = 20  # Mark "Cheap" if PE ≤ -20%
PE_DELTA_PCT = 20  # Mark "Expensive" if PE ≥ +20%

# Analyst confidence settings
ANALYST_COUNT_CAP = 10  # Cap analyst count at 10 for scoring
ANALYST_SCORE_WEIGHTS = {
    'Strong Buy': 1.0,
    'Buy': 0.8,
    'Hold': 0.5,
    'Sell': 0.0,
}
ANALYST_CONFIDENCE_BUCKETS = {'high': 70, 'medium': 40}  # Score thresholds
```

Update these values to fine-tune when companies are marked as Cheap/Expensive or High/Medium/Low analyst confidence.

## 🛠 Development

### Setting Up Development Environment

```bash
# Install development dependencies
pip install -r requirements.txt
pip install pytest black flake8 mypy

# Run linter
flake8 .

# Format code
black .

# Type checking
mypy .
```

### Code Style Guidelines

- **PEP 8** compliance for Python code
- **Type hints** for function parameters and return types
- **Docstrings** for all classes and functions (Google style)
- **Meaningful variable names** - be descriptive
- **Comments** for complex logic

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html
```

### Adding New Pages

1. Create a new file in `pages/` with the format: `N_emoji_Page_Name.py`
   - `N` is the order number (3, 4, 5...)
   - Emoji is optional but recommended for visual appeal
   
2. Add page configuration:
   ```python
   import streamlit as st
   
   st.set_page_config(
       page_title="My Page",
       page_icon="📊",
       layout="wide"
   )
   ```

3. Implement your page content in a `main()` function

4. The page will automatically appear in the sidebar navigation

### Sorting in Market Overview

The Market Overview uses a dual-dropdown sorting interface:
- **Column Dropdown**: Select which column to sort by (14+ options)
- **Direction Dropdown**: Toggle between ↑ Ascending and ↓ Descending

This is more intuitive than a single combined dropdown and allows quick direction changes without reselecting the column.

## 🐛 Troubleshooting

### Common Issues

#### Navigation not showing in sidebar
- Ensure pages are in the `pages/` folder
- Check that page files follow the naming convention: `N_emoji_Name.py`
- Restart the Streamlit server

#### Data not loading
- Check `.env` file exists and has correct values
- Verify Google Sheet is publicly accessible
- Check terminal for error messages
- Use "Refresh Data" button in sidebar

#### Import errors
- Ensure virtual environment is activated
- Reinstall dependencies: `pip install -r requirements.txt`
- Check Python version: `python --version` (should be 3.9+)

#### Cache issues
- Clear cache manually: Use "Refresh Data" button
- Clear Streamlit cache: Press 'C' in the browser
- Restart the application

### Debug Mode

Run with debug logging:

```bash
streamlit run app.py --logger.level=debug
```

## 📊 Performance Tips

1. **Use caching effectively**: Data is cached for 15 minutes by default
2. **Limit displayed rows**: Use pagination for large datasets
3. **Optimize filters**: Apply filters progressively
4. **Monitor memory**: Check terminal for memory usage warnings
5. **Database indexes**: Ensure your database queries use indexed columns

## 🔒 Security Considerations

1. **Environment Variables**: Never commit `.env` to version control
2. **API Keys**: Store all credentials in environment variables
3. **Data Access**: Ensure Google Sheets are properly secured
4. **Input Validation**: All user inputs are sanitized
5. **SQL Injection**: Use parameterized queries for database sources

## 🚀 Deployment

### Streamlit Cloud

1. Push code to GitHub repository
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your repository
4. Add secrets in Streamlit Cloud dashboard
5. Deploy!

### Docker

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8501
CMD ["streamlit", "run", "app.py"]
```

Build and run:
```bash
docker build -t stock-analyzer .
docker run -p 8501:8501 stock-analyzer
```

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

### Contribution Guidelines

- Write clear commit messages
- Add tests for new features
- Update documentation as needed
- Follow the existing code style
- Ensure all tests pass before submitting PR

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Authors

- **Your Name** - *Initial work* - [GitHub Profile](https://github.com/yourusername)

## 🙏 Acknowledgments

- [Streamlit](https://streamlit.io) - The amazing framework that makes this possible
- [Pandas](https://pandas.pydata.org) - Data manipulation and analysis
- [Money Control](https://www.moneycontrol.com) - Stock market data source

## 📞 Support

For support, email support@example.com or open an issue in the GitHub repository.

## 🗺 Roadmap

### Version 2.0 (Q2 2026)
- [ ] Real-time data updates via WebSocket
- [ ] Portfolio tracking and management
- [ ] Advanced stock screener with custom filters
- [ ] Email/SMS alerts for price changes
- [ ] Multi-language support

### Version 2.1 (Q3 2026)
- [ ] Machine learning price predictions
- [ ] Technical analysis indicators
- [ ] Comparison tool for multiple stocks
- [ ] Export reports as PDF

### Future Enhancements
- [ ] Mobile app (React Native)
- [ ] API for third-party integrations
- [ ] Social features (share analysis, comments)
- [ ] Integration with trading platforms

---

**Made with ❤️ using Streamlit**

For more information, visit our [documentation](https://docs.example.com) or join our [community](https://community.example.com).
