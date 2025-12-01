from flask import Flask, render_template, request, Response, jsonify
from flask_cors import CORS
import json
import queue
import sounddevice as sd
import vosk
import difflib
import os
import random
import sqlite3
from datetime import datetime
import time

app = Flask(__name__)
CORS(app)


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASETS_PATH = os.path.join(BASE_DIR, "datasets")
DB_PATH = os.path.join(BASE_DIR, "speech_results.db")


MODELS = {
    "en": os.path.join(BASE_DIR, "vosk-model-small-en-us-0.15"),
    "hi": os.path.join(BASE_DIR, "vosk-model-small-hi-0.22")
}

audio_queue = queue.Queue()


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT,
                    language TEXT,
                    mode TEXT,
                    score INTEGER,
                    total INTEGER,
                    date_time TEXT
                )''')
    conn.commit()
    conn.close()

def save_result(username, language, mode, score, total):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO results (username, language, mode, score, total, date_time) VALUES (?, ?, ?, ?, ?, ?)",
              (username, language, mode, score, total, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()


def load_prompts(language, mode):
    filename_map = {
        ("en", "word"): "english_words.txt",
        ("en", "sentence"): "english_sentences.txt",
        ("hi", "word"): "hindi_words.txt",
        ("hi", "sentence"): "hindi_sentences.txt"
    }
    
    filename = filename_map.get((language, mode))
    if not filename:
        return []
    
    path = os.path.join(DATASETS_PATH, filename)
    if not os.path.exists(path):
        print(f"⚠️ Dataset not found: {path}")
        # Create sample data if file doesn't exist
        return ["hello", "world", "computer", "python", "programming", "technology", "artificial", "intelligence", "software", "developer"]
    
    with open(path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]
    
    if not lines:
        return ["hello", "world", "computer", "python", "programming"]
    
    return random.sample(lines, min(10, len(lines)))


def audio_callback(indata, frames, time_info, status):
    if status:
        print(f"Audio status: {status}")
    audio_queue.put(bytes(indata))


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/test-setup', methods=['GET'])
def test_setup():
    """Test if everything is set up correctly"""
    issues = []
    
    
    for lang, path in MODELS.items():
        if not os.path.exists(path):
            issues.append(f"Model not found: {lang} at {path}")
    
    
    if not os.path.exists(DATASETS_PATH):
        issues.append(f"Datasets folder not found: {DATASETS_PATH}")
    
    # Test audio
    try:
        devices = sd.query_devices()
        default_input = sd.query_devices(kind='input')
    except Exception as e:
        issues.append(f"Audio error: {str(e)}")
    
    return jsonify({
        "status": "ok" if not issues else "error",
        "issues": issues,
        "datasets_path": DATASETS_PATH,
        "models": MODELS
    })

@app.route('/api/start-test', methods=['POST'])
def start_test():
    try:
        data = request.get_json()
        username = data.get('username', 'Guest')
        language = data.get('language', 'en')
        mode = data.get('mode', 'word')
        
        print(f"\n{'='*50}")
        print(f"Starting test for {username}")
        print(f"Language: {language}, Mode: {mode}")
        print(f"{'='*50}\n")
        
    except Exception as e:
        print(f"Error parsing request: {e}")
        return jsonify({"error": "Invalid request"}), 400
    
    def generate():
        try:
            model_path = MODELS.get(language)
            
            # Check model
            if not model_path or not os.path.exists(model_path):
                error_msg = f"Model not found at: {model_path}"
                print(f"❌ {error_msg}")
                yield f"data: {json.dumps({'type': 'error', 'message': error_msg})}\n\n"
                return
            
            # Load model
            print(f"Loading model from: {model_path}")
            try:
                model = vosk.Model(model_path)
                print("✓ Model loaded successfully")
            except Exception as e:
                error_msg = f"Model load error: {str(e)}"
                print(f"❌ {error_msg}")
                yield f"data: {json.dumps({'type': 'error', 'message': error_msg})}\n\n"
                return
            
            # Load prompts
            prompts = load_prompts(language, mode)
            if not prompts:
                error_msg = "No prompts available"
                print(f"❌ {error_msg}")
                yield f"data: {json.dumps({'type': 'error', 'message': error_msg})}\n\n"
                return
            
            print(f"✓ Loaded {len(prompts)} prompts")
            
            score = 0
            total = len(prompts)
            
            # Start audio stream
            print("Starting audio stream...")
            try:
                stream = sd.RawInputStream(
                    samplerate=16000,
                    blocksize=8000,
                    dtype="int16",
                    channels=1,
                    callback=audio_callback
                )
                stream.start()
                print("✓ Audio stream started")
            except Exception as e:
                error_msg = f"Audio error: {str(e)}"
                print(f"❌ {error_msg}")
                yield f"data: {json.dumps({'type': 'error', 'message': error_msg})}\n\n"
                return
            
            # Process each prompt
            for i, prompt in enumerate(prompts, 1):
                print(f"\n--- Word {i}/{total}: '{prompt}' ---")
                
                yield f"data: {json.dumps({'type': 'prompt', 'index': i, 'total': total, 'text': prompt})}\n\n"
                time.sleep(0.3)
                
                attempts = 0
                max_attempts = 5
                word_cleared = False
                
                while attempts < max_attempts and not word_cleared:
                    attempts += 1
                    print(f"Attempt {attempts}/{max_attempts}")
                    
                    # Clear audio queue
                    while not audio_queue.empty():
                        try:
                            audio_queue.get_nowait()
                        except:
                            break
                    
                    # Create new recognizer for each attempt
                    recognizer = vosk.KaldiRecognizer(model, 16000)
                    
                    yield f"data: {json.dumps({'type': 'listening', 'attempt': attempts, 'max_attempts': max_attempts})}\n\n"
                    
                    # Listen for speech (5 second timeout)
                    spoken = ""
                    start_time = time.time()
                    timeout = 5
                    
                    while time.time() - start_time < timeout:
                        try:
                            data = audio_queue.get(timeout=0.1)
                            if recognizer.AcceptWaveform(data):
                                result = json.loads(recognizer.Result())
                                text = result.get("text", "").strip()
                                if text:
                                    spoken = text
                                    print(f"Recognized: '{spoken}'")
                                    break
                        except queue.Empty:
                            continue
                    
                    
                    if not spoken:
                        print("⏱️ No speech detected")
                        yield f"data: {json.dumps({'type': 'timeout', 'attempt': attempts})}\n\n"
                        time.sleep(0.5)
                        continue
                    
                    # Calculate similarity
                    similarity = difflib.SequenceMatcher(None, prompt.lower(), spoken.lower()).ratio()
                    print(f"Similarity: {similarity:.2%}")
                    
                    if similarity >= 0.7:
                        score += 1
                        word_cleared = True
                        print("✅ Correct!")
                        yield f"data: {json.dumps({'type': 'correct', 'spoken': spoken, 'expected': prompt, 'similarity': round(similarity, 2)})}\n\n"
                        time.sleep(1)
                    else:
                        print("❌ Incorrect")
                        yield f"data: {json.dumps({'type': 'incorrect', 'spoken': spoken, 'expected': prompt, 'similarity': round(similarity, 2), 'attempt': attempts, 'max_attempts': max_attempts})}\n\n"
                        time.sleep(0.8)
                
                if not word_cleared:
                    print("⏭️ Max attempts reached, moving on")
                    yield f"data: {json.dumps({'type': 'failed', 'text': prompt})}\n\n"
                    time.sleep(0.8)
            
            # Stop audio stream
            stream.stop()
            stream.close()
            print("✓ Audio stream stopped")
            
            # Save results
            save_result(username, language, mode, score, total)
            
            print(f"\n{'='*50}")
            print(f"Test Complete! Score: {score}/{total}")
            print(f"{'='*50}\n")
            
            yield f"data: {json.dumps({'type': 'complete', 'score': score, 'total': total})}\n\n"
            
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            print(f"❌ {error_msg}")
            import traceback
            traceback.print_exc()
            yield f"data: {json.dumps({'type': 'error', 'message': error_msg})}\n\n"
    
    return Response(generate(), mimetype='text/event-stream')

@app.route('/api/leaderboard', methods=['GET'])
def leaderboard():
    try:
        if not os.path.exists(DB_PATH):
            init_db()
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT username, language, mode, score, total, date_time FROM results ORDER BY score DESC, id DESC LIMIT 10")
        rows = c.fetchall()
        conn.close()
        return jsonify([{"username": r[0], "language": r[1], "mode": r[2], "score": r[3], "total": r[4], "date_time": r[5]} for r in rows])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    init_db()
    print("\n" + "="*60)
    print("🎤 Speech Recognition Server Starting...")
    print("="*60)
    print(f"Database: {DB_PATH}")
    print(f"Datasets: {DATASETS_PATH}")
    print(f"English Model: {MODELS['en']}")
    print(f"Hindi Model: {MODELS['hi']}")
    print("="*60)
    print("\n✓ Server running at http://localhost:5000")
    print("✓ Press Ctrl+C to stop\n")
    
    app.run(debug=True, threaded=True, port=5000, use_reloader=False)