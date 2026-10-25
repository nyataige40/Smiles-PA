import speech_recognition as sr


class VoiceInput:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        # Bound the remote Google request so a slow or unavailable connection
        # cannot leave the assistant stuck after it hears a phrase.
        self.recognizer.operation_timeout = 6
        self.recognizer.pause_threshold = 0.8
        self.recognizer.phrase_threshold = 0.3
        self.recognizer.non_speaking_duration = 0.5
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.dynamic_energy_adjustment_damping = 0.15
        self.recognizer.dynamic_energy_ratio = 1.5
        self.calibrate()

    def calibrate(self):
        try:
            with self.microphone as source:
                print("[SMILES]: Calibrating microphone for 1 second...")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
            # Avoid an extra threshold increase that can cause quiet speech to
            # be ignored, especially when dynamic thresholding is enabled.
        except Exception as e:
            print(f"[SMILES]: Microphone calibration failed: {e}")

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
            print(f"[SMILES]: Speech service error (check internet connection): {e}")
            return None
        except Exception as e:
            print(f"[SMILES]: Microphone/recognition error: {e}")
            return None

    def listen_passive(self):
        # Wait for a wake word and an optional command in one breath.
        return self._listen_core(timeout=5, phrase_time_limit=5, verbose=False)

    def listen_active(self):
        return self._listen_core(timeout=5, phrase_time_limit=8, verbose=True)
