import pyttsx3

class VoiceOutput:
    def __init__(self):
        self.engine = pyttsx3.init()
        self._configure()

    def _configure(self):
        voices = self.engine.getProperty('voices')
        rate = self.engine.getProperty('rate')
        self.engine.setProperty('rate', rate - 20)
        for voice in voices:
            if 'english' in voice.name.lower():
                self.engine.setProperty('voice', voice.id)
                break

    def speak(self, text):
        print(f"[SMILES OUTPUT]: {text}")
        self.engine.say(text)
        self.engine.runAndWait()
