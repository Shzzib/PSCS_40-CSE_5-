AI–ML Enabled Bilingual Pronunciation Correction and Speech Therapy System

This project is an offline AI–ML based pronunciation correction system that helps users improve their English and Hindi speaking skills. It provides real-time feedback, accuracy scoring, text-to-speech guidance, and progress tracking using an SQLite database. The system uses Vosk offline speech recognition, SequenceMatcher similarity scoring, and pyttsx3 text-to-speech.

Features
	•	Offline speech recognition (English and Hindi)
	•	Real-time pronunciation evaluation
	•	Instant audio and text feedback
	•	AI-based accuracy scoring
	•	SQLite database for storing results
	•	Works without internet
	•	Lightweight and suitable for low-end systems

Tech Stack
	•	Python 3.10+
	•	Vosk offline speech models
	•	pyttsx3 (text-to-speech)
	•	difflib (similarity matching)
	•	sounddevice (audio recording)
	•	SQLite (local storage)


  Installation
  
  1.  Clone the repository:
  git clone https://github.com/Shzzib/PSCS_40-CSE_5-.git
  cd PSCS_40-CSE_5-

  2.	Install required libraries:
  pip install vosk pyttsx3 sounddevice pyaudio playsound

  3.	Download Vosk models:
  English Model: vosk-model-small-en-us
	Hindi Model: vosk-model-small-hi-in

  Place them in a folder named models inside your project:
  /models/english/
  /models/hindi/

  How to Run

  Run the main program:
  python app.py

  The system will:
	1.	Play the target pronunciation
	2.	Record the user’s speech
	3.	Convert speech to text
	4.	Compare expected vs spoken text
	5.	Generate an accuracy score
	6.	Provide corrective feedback
	7.	Save results in SQLite

Database Structure

Users Table
	•	UserID
	•	Name
	•	Age
	•	PreferredLanguage

Sessions Table
	•	SessionID
	•	UserID
	•	ExpectedText
	•	RecognizedOutput
	•	Accuracy
	•	Timestamp

Performance Summary
	•	English speech accuracy: approx. 94.8%
	•	Hindi speech accuracy: approx. 94.2%
	•	Average response time: 2–3 seconds
	•	Average user improvement: +18% over repeated sessions

Applications
	•	Schools and educational institutions
	•	Therapy centers
	•	Rural learning centers
	•	Home-based self-learning
	•	Language learners (English/Hindi)
	•	Children with articulation issues

Future Enhancements
	•	Phoneme-level pronunciation scoring
	•	More Indian languages
	•	Mobile app version (Android/iOS)
	•	Gamified learning system
	•	Lip-reading and articulation analysis
	•	AI adaptive learning

Contributors
	•	Mohammed Wajihuddin (20221CSE0033)
	•	Zoya Hussain (20221CSE0047)
	•	Fidha Basheer (20221CSE0018)
Guide: Dr. Sampath A K
