import speech_recognition as sr


class VoiceInput:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        # Tune thresholds to cut background noise without missing speech
        self.recognizer.pause_threshold = 0.8
        self.recognizer.phrase_threshold = 0.3
        self.recognizer.non_speaking_duration = 0.5
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.dynamic_energy_adjustment_damping = 0.15
        self.recognizer.dynamic_energy_ratio = 1.5
        self.calibrate()

    def calibrate(self):
        with self.microphone as source:
            print("[SMILES]: Calibrating ambient noise...")
            self.recognizer.adjust_for_ambient_noise(source, duration=2)
        # Raise threshold above ambient level to suppress room hum / fan noise
        self.recognizer.energy_threshold *= 1.25

    def _listen_core(self, timeout, phrase_time_limit, verbose=False):
        try:
            with self.microphone as source:
                if verbose:
                    print("[SMILES]: Listening...")
                audio = self.recognizer.listen(
                    source, timeout=timeout, phrase_time_limit=phrase_time_limit
                )
            text = self.recognizer.recognize_google(audio)
            if verbose:
                print(f"[SMILES INPUT]: {text}")
            return text.lower()
        except sr.WaitTimeoutError:
            return None
        except sr.UnknownValueError:
            if verbose:
                print("[SMILES]: Could not understand audio.")
            return None
        except sr.RequestError as e:
            if verbose:
                print(f"[SMILES]: Speech service error: {e}")
            return None
        except Exception as e:
            if verbose:
                print(f"[SMILES]: Microphone error: {e}")
            return None

    def listen_passive(self):
        # Long enough to capture "Jarvis open notepad" in one breath
        return self._listen_core(timeout=5, phrase_time_limit=5, verbose=False)

    def listen_active(self):
        return self._listen_core(timeout=5, phrase_time_limit=8, verbose=True)
