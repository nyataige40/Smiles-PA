import sys


def main():
    print("=" * 50)
    print("  SMILES - Smart Machine Interface & Local")
    print("  Execution System v1.0.0")
    print("=" * 50)
    print("[SMILES]: Initializing system...")
    try:
        from smiles.voice_input import VoiceInput
        from smiles.voice_output import VoiceOutput
        from smiles.core import IntentParser, SystemExecutor

        tts = VoiceOutput()
        voice_input = VoiceInput()
        intent_parser = IntentParser()
        executor = SystemExecutor(tts)

        print("[SMILES]: Listening for 'Jarvis' or 'Smiles'.")
        print("[SMILES]: After activation, you can give several commands in a row.")
        print("[SMILES]: Say 'go to sleep' to exit.")

        state = "passive"
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
                        try:
                            executor.execute(intent_data)
                        except Exception as e:
                            print(f"[SMILES]: Command failed: {e}")
                            tts.speak("Sorry, I couldn't complete that command.")
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
                    print("[SMILES]: No follow-up heard; waiting for the wake word.")
                    continue

                if "go to sleep" in command:
                    tts.speak("Going to sleep. Goodbye, sir.")
                    break

                intent_data = intent_parser.parse(command)
                try:
                    executor.execute(intent_data)
                except Exception as e:
                    print(f"[SMILES]: Command failed: {e}")
                    tts.speak("Sorry, I couldn't complete that command.")
                # Stay active for the next request. A 5 second silence returns
                # to passive wake-word listening in listen_active's caller.
                continue
    except KeyboardInterrupt:
        print("\n[SMILES]: Keyboard interrupt received. Shutting down...")
    except Exception as e:
        print(f"[SMILES]: Startup/runtime error: {e}")
    finally:
        print("[SMILES]: System halted.")


if __name__ == "__main__":
    main()
    sys.exit(0)
