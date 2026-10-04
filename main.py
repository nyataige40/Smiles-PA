import sys
from smiles.voice_input import VoiceInput
from smiles.voice_output import VoiceOutput
from smiles.core import IntentParser, SystemExecutor


def main():
    print("=" * 50)
    print("  SMILES - Smart Machine Interface & Local")
    print("  Execution System v1.0.0")
    print("=" * 50)
    print("[SMILES]: Initializing system...")

    tts = VoiceOutput()
    voice_input = VoiceInput()
    intent_parser = IntentParser()
    executor = SystemExecutor(tts)

    print("[SMILES]: Entering passive background listening mode.")
    print("[SMILES]: Say 'Jarvis' or 'Smiles' to activate.")
    print("[SMILES]: Say 'go to sleep' to exit.")

    state = "passive"

    try:
        while True:
            if state == "passive":
                user_input = voice_input.listen_passive()
                if not user_input:
                    continue

                if "jarvis" in user_input or "smiles" in user_input:
                    # Check if the wake word came with a command in the same breath
                    command_after_wake = user_input
                    for wake in ["jarvis", "smiles"]:
                        if wake in command_after_wake:
                            parts = command_after_wake.split(wake, 1)
                            command_after_wake = parts[1].strip() if len(parts) > 1 else ""
                            break

                    if command_after_wake:
                        # Single-breath command: "Jarvis open notepad" -> execute instantly
                        print(f"[SMILES]: Wake word + command detected: '{command_after_wake}'")
                        if "go to sleep" in command_after_wake:
                            tts.speak("Going to sleep. Goodbye, sir.")
                            break
                        intent_data = intent_parser.parse(command_after_wake)
                        executor.execute(intent_data)
                        continue
                    else:
                        # Wake word only: "Jarvis" -> switch to active for follow-up
                        state = "active"
                        tts.speak("Yes, sir?")
                continue

            if state == "active":
                command = voice_input.listen_active()
                if not command:
                    state = "passive"
                    continue

                if "go to sleep" in command:
                    tts.speak("Going to sleep. Goodbye, sir.")
                    break

                intent_data = intent_parser.parse(command)
                executor.execute(intent_data)
                state = "passive"
                continue
    except KeyboardInterrupt:
        print("\n[SMILES]: Keyboard interrupt received. Shutting down...")
    except Exception as e:
        print(f"[SMILES]: Fatal error: {e}")
    finally:
        print("[SMILES]: System halted.")


if __name__ == "__main__":
    main()
    sys.exit(0)
