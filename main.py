import argparse
import sys


EXIT_PHRASES = {"go to sleep", "stop assistant", "quit", "exit"}


def _answer(agent, message, tts=None):
    print("[SMILES]: Thinking...")
    try:
        answer = agent.respond(message)
    except Exception as e:
        print(f"[SMILES]: Gemini request failed: {e}")
        answer = "Sorry, I couldn't reach my assistant service. Please try again."
    print(f"[SMILES]: {answer}")
    if tts:
        tts.speak(answer)


def _run_text_chat(agent):
    print("[SMILES]: Text chat is ready. Type 'quit' to exit.")
    while True:
        try:
            message = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if message.lower() in EXIT_PHRASES:
            return
        if message:
            _answer(agent, message)


def main():
    arg_parser = argparse.ArgumentParser(description="Run the SMILES desktop assistant.")
    arg_parser.add_argument(
        "--text",
        action="store_true",
        help="Use typed chat instead of the microphone and speaker.",
    )
    args = arg_parser.parse_args()

    print("=" * 50)
    print("  SMILES - Smart Machine Interface & Local")
    print("  Gemini Personal Assistant")
    print("=" * 50)
    print("[SMILES]: Initializing system...")
    agent = None
    try:
        from smiles.agent import SmilesAgent

        agent = SmilesAgent()
        if args.text:
            _run_text_chat(agent)
            return

        from smiles.voice_input import VoiceInput
        from smiles.voice_output import VoiceOutput

        tts = VoiceOutput()
        voice_input = VoiceInput()

        print("[SMILES]: Listening for 'Jarvis' or 'Smiles'.")
        print("[SMILES]: Ask a question or give a command after activation.")
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
                        print(f"[SMILES]: Wake word + command detected: '{command_after_wake}'")
                        if command_after_wake.lower().strip(" .!?") in EXIT_PHRASES:
                            tts.speak("Going to sleep. Goodbye, sir.")
                            break
                        _answer(agent, command_after_wake, tts)
                        continue
                    else:
                        state = "active"
                        tts.speak("Yes, sir?")
                continue

            if state == "active":
                command = voice_input.listen_active()
                if not command:
                    state = "passive"
                    print("[SMILES]: No follow-up heard; waiting for the wake word.")
                    continue

                if command.lower().strip(" .!?") in EXIT_PHRASES:
                    tts.speak("Going to sleep. Goodbye, sir.")
                    break

                _answer(agent, command, tts)
                # Stay active for the next request. A 5 second silence returns
                # to passive wake-word listening in listen_active's caller.
                continue
    except KeyboardInterrupt:
        print("\n[SMILES]: Keyboard interrupt received. Shutting down...")
    except Exception as e:
        print(f"[SMILES]: Startup/runtime error: {e}")
    finally:
        if agent is not None:
            agent.close()
        print("[SMILES]: System halted.")


if __name__ == "__main__":
    main()
    sys.exit(0)
