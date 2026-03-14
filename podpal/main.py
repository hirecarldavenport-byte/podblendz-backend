import os
from podpal import db
from podpal.blend import blend_transcript
from podpal.audio.tts import generate_audio

def main():
    while True:
        print("\n=== Podcast Pal (Minimal) ===")
        print("(1 / c)   Add transcript for an episode")
        print("(2 / c2)  View transcript for an episode")
        print("(3 / l)   List transcripts")
        print("(4 / e)   Edit transcript")
        print("(5 / x)   Export transcript")
        print("(6 / s)   Search transcripts")
        print("(7 / d)   Delete transcript")
        print("(8 / xa)  Export ALL transcripts")
        print("(9 / bkp) Backup database")
        print("(10 / b)  Blend transcript and generate audio")
        print("(0)       Exit")

        action = input("> ").strip().lower()

        # -----------------------------
        # Transcript actions
        # -----------------------------

        if action in ("1", "c"):
            episode_id = input("Episode id for transcript: ").strip()
            text = input("Paste transcript text:\n")
            db.save_transcript(episode_id, text)
            print("Transcript saved.")

        elif action in ("2", "c2"):
            episode_id = input("Episode id to view: ").strip()
            transcript = db.get_transcript(episode_id)
            if transcript:
                print("\n--- Transcript ---\n")
                print(transcript.text)
                print("\n------------------\n")
            else:
                print("No transcript found.")

        elif action in ("3", "l"):
            transcripts = db.list_transcripts()
            print("\n--- Transcript List ---")
            for t in transcripts:
                print(f"- {t.episode_id}")
            print("------------------------")

        elif action in ("4", "e"):
            episode_id = input("Episode id to edit: ").strip()
            transcript = db.get_transcript(episode_id)
            if not transcript:
                print("No transcript found.")
                continue
            print("Current text:")
            print(transcript.text)
            new_text = input("\nEnter new text:\n")
            db.save_transcript(episode_id, new_text)
            print("Transcript updated.")

        elif action in ("5", "x"):
            episode_id = input("Episode id to export: ").strip()
            transcript = db.get_transcript(episode_id)
            if not transcript:
                print("No transcript found.")
                continue
            path = f"media/exports/{episode_id}.txt"
            os.makedirs("media/exports", exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(transcript.text)
            print(f"Transcript exported to {path}")

        elif action in ("6", "s"):
            term = input("Search term: ").strip().lower()
            results = db.search_transcripts(term)
            print("\n--- Search Results ---")
            for r in results:
                print(f"- {r.episode_id}")
            print("----------------------")

        elif action in ("7", "d"):
            episode_id = input("Episode id to delete: ").strip()
            db.delete_transcript(episode_id)
            print("Transcript deleted.")

        elif action in ("8", "xa"):
            os.makedirs("media/exports", exist_ok=True)
            for t in db.list_transcripts():
                path = f"media/exports/{t.episode_id}.txt"
                with open(path, "w", encoding="utf-8") as f:
                    f.write(t.text)
            print("All transcripts exported.")

        elif action in ("9", "bkp"):
            db.backup()
            print("Database backed up.")

        # -----------------------------
        # Blend + Audio
        # -----------------------------

        elif action in ("10", "b"):
            episode_id = input("Episode id to blend: ").strip()
            transcript = db.get_transcript(episode_id)

            if not transcript:
                print("No transcript found.")
                continue

            blended_text = blend_transcript(transcript.text)
            print("\n--- Blended Text ---\n")
            print(blended_text)
            print("\n---------------------\n")

            audio_path = generate_audio(blended_text)
            print(f"Audio created at: {audio_path}")

            try:
                os.startfile(audio_path)
            except Exception:
                pass

        elif action == "0":
            print("Goodbye!")
            break

        else:
            print("Unknown option.")

if __name__ == "__main__":
    main()