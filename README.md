# EcoStyle: AI Wardrobe Buddy

## Overview
EcoStyle is an AI-powered wardrobe management app that helps users organize clothing, get outfit suggestions, and make sustainable fashion choices using Streamlit and Google's Gemini AI.

## Features
- **Virtual Closet**: Upload clothing photos for AI analysis and sustainability scoring
- **Outfit Suggestions**: Get personalized outfit combinations based on weather and occasion
- **Sustainability Dashboard**: Track your wardrobe's environmental impact

## Installation
1. Clone repository and create virtual environment
2. Install dependencies: `pip install streamlit google-generativeai pillow pandas`
3. Configure Google API key in `.streamlit/secrets.toml` or via the sidebar

## Usage
Run with: `streamlit run app.py`

## Troubleshooting
- **Value Errors**: Fixed extraction of numeric values from sustainability scores
- **Image Analysis**: Ensure photos clearly show clothing items

## Dependencies
- Python 3.7+
- Streamlit
- Google Generative AI
- PIL/Pillow
- Pandas
