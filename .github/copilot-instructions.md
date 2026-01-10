# Copilot Instructions for Money Control Stock Analyzer

## Project Overview
This is a Streamlit-based stock analysis application that aggregates data from multiple sources (Google Sheets, databases, APIs). It follows a modular architecture with a centralized data source registry pattern.

**Key Stack**: Python 3.9+, Streamlit 1.52+, Pandas, gspread, python-dotenv

## Architecture & Data Flow

### Core Pattern: Pluggable Data Sources
The application uses a **registry pattern** for managing multiple data sources:

```
DataSourceRegistry → [GoogleSheetsSource] → Data transformation → UI pages
```

- **`data_sources/base.py`**: Abstract base class (`DataSourceBase`) that all sources inherit from. Requires implementing `connect()`, `fetch_data()`, and caching logic.
- **`data_sources/registry.py`**: Central registry managing source registration and caching (15-min TTL default).
- **`data_sources/google_sheets.py`**: Implements Google Sheets integration with column configuration and retry logic.

**Key principle**: When adding new data sources, always:
1. Inherit from `DataSourceBase`
2. Implement required abstract methods
3. Register via `DataSourceRegistry.register(name, source_instance)`

### Configuration Management
- **`config/constants.py`**: Centralized configuration file containing:
  - Google Sheets URL and tab name (from `.env`)
  - Column definitions: `JSON_COLUMNS`, `NUMERIC_COLUMNS`, `FILTER_COLUMNS`, `TABLE_COLUMNS`
  - Each uses snake_case internally; display names handled separately

### UI Layer (Pages)
- **`Home.py`**: Entry point that initializes data sources
- **`pages/1_📈_Market_Overview.py`**: Main data viewing interface (516 lines) with:
  - Dynamic column visibility controls
  - Multi-filter support (sector, industry, status)
  - Text search (company_name, scId)
  - Pagination (15 items/page)
  - CSV export via Streamlit's native download
  - Table and Card view modes
- **`pages/2_🏢_Company_Details.py`**: Company-specific deep dive with financial metrics and analyst ratings

## Developer Workflows

### Running the Application
```bash
streamlit run Home.py
```
App runs on `http://localhost:8501` by default.

### Adding a New Data Source
1. Create new file in `data_sources/` (e.g., `database.py`)
2. Inherit from `DataSourceBase` and implement abstract methods
3. Register in `Home.py` via `init_data_sources()` function
4. Reference the existing `google_sheets.py` as a template

### Configuration & Secrets
- Use `.env` file for sensitive data (Google Sheets URL, database credentials)
- Constants referenced via `config.constants.GOOGLE_SHEET_URL`, etc.
- Load via `python-dotenv` in `constants.py`

### Testing Data Transformations
- Most column transformations happen in `GoogleSheetsSource.transform_data()` (snake_case conversion, JSON parsing)
- Use `_to_snake()` helper in page files for display name normalization
- Test with filtered DataFrames before passing to UI components

## Project-Specific Patterns & Conventions

### Naming & Types
- **Internal columns**: snake_case (e.g., `company_name`, `m_score`, `analyst_final_rating`)
- **Display names**: Title Case with symbols (e.g., "TTM PE", "M-Score")
- **JSON columns**: Stored as JSON strings, parsed on load (see `JSON_COLUMNS` in constants)
- **Numeric columns**: Must be explicitly declared for type conversion

### Streamlit Patterns
- **Session state**: Used for pagination (`current_page`), column visibility (`visible_columns`), filters
- **Caching**: `@st.cache_data` for data operations, manual TTL management in registry (900s default)
- **Column configs**: Use `st.column_config.LinkColumn()` for URLs, standard columns for metrics

### Data Flow for Filters
- Sector, Industry, Status dropdowns → DataFrame filtering → Paginated display
- Search box filters across multiple columns (`search_columns` config)
- Numeric range sliders for `m_score` and `ttm_pe`
- **Reset filters**: Clears session state variables

### Column Visibility Logic
- Defined in `COLUMN_DEFINITIONS` with defaults (see page 1)
- Default visible: Company Name, Sector, Industry, Cost, M-Score, TTM PE, Analyst Rating
- Hidden: SC ID, Status, TTM EPS, P/B, Sector PE, Analyst Count
- Toggle stored in session state, not persisted across sessions

## Integration Points & Dependencies

### External Services
- **Google Sheets**: Read via public CSV export URL + retry logic (see `google_sheets.py`)
- **Streamlit Cloud**: No special considerations; environment variables via Secrets tab

### Cross-Component Communication
- Pages retrieve data via `DataSourceRegistry.get_data("money_control")`
- Caching layer prevents redundant fetches within TTL window
- Column metadata flows from constants → source config → page display

### Key Dependencies
- `streamlit`: UI framework (multipage apps, widgets, caching)
- `pandas`: Data manipulation and filtering
- `gspread`: Google Sheets API (installed but not currently used; CSV export used instead)
- `streamlit-js-eval`: JavaScript bridge for advanced interactions
- `python-dotenv`: Environment variable management

## Common Tasks

### Changing Display Columns
Edit `COLUMN_DEFINITIONS` in `pages/1_📈_Market_Overview.py` (lines ~30-45) or add to `config/constants.py` `TABLE_COLUMNS`.

### Adding a New Filter
1. Add column name to `FILTER_COLUMNS` in `config/constants.py`
2. Add filter widget in Market Overview page using `st.multiselect()`
3. Filter DataFrame before pagination

### Debugging Data Issues
- Check column names are snake_case internally
- Verify `JSON_COLUMNS` and `NUMERIC_COLUMNS` match actual sheet structure
- Use `st.dataframe(df.dtypes)` or `st.write(df.head())` to inspect data in browser

### Performance Optimization
- Increase cache TTL in `registry.py` for high-frequency fetches
- Implement `@st.cache_data` for expensive transformations
- Use `st.session_state` instead of widget keys for state management to avoid reruns

## Code Style & Practices

- Snake_case for functions/variables
- Docstrings for modules, classes, functions (as seen in `base.py`, `Home.py`)
- Type hints on public methods (see `DataSourceBase` abstract methods)
- Comments for "why" not "what"—code should be self-documenting
- Use `const.` prefix to reference configuration values

## Notes for AI Agents

- **Modularity is critical**: Always extend via the registry pattern, not hardcoding sources
- **Column metadata is declarative**: Update constants, not scattered logic
- **Session state is stateless across reruns**: Don't assume persistence without explicit saving
- **Pandas operations are preferred**: Use native ops over loops for transformations
