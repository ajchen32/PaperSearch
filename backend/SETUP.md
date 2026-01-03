# API Key Setup Guide

## Step 1: Get Your Gemini API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey) (or visit https://aistudio.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key" or "Get API Key"
4. Copy the API key that's generated (it will look something like: `AIzaSy...`)

**Note:** Keep this key secret! Don't share it publicly or commit it to version control.

## Step 2: Create Your .env File

**Note:** Semantic Scholar API works without an API key (using direct API links), so you only need the Gemini API key.

1. In the `backend` folder (same folder as `LLMcall.py`), create a new file named `.env` (note the dot at the beginning)
2. Open the `.env` file in a text editor
3. Add the following line, replacing `your_gemini_api_key_here` with your actual API key:

```
GEMINI_API_KEY=AIzaSyYourActualKeyHere
```

**Note:** Semantic Scholar API works without an API key - it uses direct API links.

**Important:** 
- No spaces around the `=` sign
- No quotes around the API key value
- Make sure the file is named exactly `.env` (not `env.txt` or anything else)

## Step 3: Verify Setup

The `.gitignore` file is already configured to prevent your `.env` file from being committed to git, so your API key will stay safe.

## Step 4: Install Dependencies and Run

```bash
# Navigate to the backend folder
cd backend

# Install dependencies
pip install -r requirements.txt

# Run the FastAPI server
uvicorn LLMcall:app --reload
```

The server should start without errors. If you see an error about the API key not being set, double-check that:
- Your `.env` file exists in the `backend` folder
- The file is named exactly `.env` (not `.env.txt`)
- The API key is correctly formatted: `GEMINI_API_KEY=your_key_here`

## Troubleshooting

**Error: "GEMINI_API_KEY environment variable is not set"**
- Make sure the `.env` file is in the same folder as `LLMcall.py`
- Check that the file is named exactly `.env` (some systems hide files starting with a dot)
- Verify the format: `GEMINI_API_KEY=your_key` (no spaces, no quotes)

**Semantic Scholar API:**
- The API works without an API key using direct API links
- No additional setup needed for Semantic Scholar

**Error: "Invalid API key"**
- Make sure you copied the entire API key
- Check that there are no extra spaces or characters
- Try generating a new API key from Google AI Studio

