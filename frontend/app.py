from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

# Set your Gemini API key from .env file
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

@app.route('/parse', methods=['POST'])
def parse_nl():
    data = request.json
    query = data.get('query', '')
    prompt = f"""
    Extract the following parameters from the user's transportation routing request:
    - Source location
    - Destination locations (list)
    - Load/weight for each destination (list)
    - Vehicle constraints (capacity, type, etc.)
    Return only valid JSON, using double quotes for all keys and string values. Do not include any text before or after the JSON.

    User request: {query}
    """
    try:
        try:
            model = genai.GenerativeModel('models/gemini-1.5-flash-latest')
            response = model.generate_content([prompt])
            import re, json as pyjson
            match = re.search(r'\{.*\}', response.text, re.DOTALL)
            if match:
                json_str = match.group(0)
                try:
                    result = pyjson.loads(json_str)
                except Exception:
                    # Fallback: replace single quotes with double quotes
                    json_str_fixed = json_str.replace("'", '"')
                    result = pyjson.loads(json_str_fixed)
            else:
                result = {"error": "Could not parse response"}
        except Exception as model_error:
            # If model not found, list available models
            models = genai.list_models()
            available = [m.name for m in models]
            result = {"error": str(model_error), "available_models": available}
    except Exception as e:
        result = {"error": str(e)}
    print(jsonify)
    return jsonify(result)

if __name__ == '__main__':
    app.run(port=3000, debug=True)
