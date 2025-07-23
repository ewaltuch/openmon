"""
Export chiptune music from BeepBox CLI JSON to .wav/.ogg for Open-Mon.
Usage: python scripts/beepbox2wav.py input.json output.wav
"""
import sys
import subprocess

def beepbox_to_wav(json_path, wav_path):
    # Requires beepbox-cli installed and in PATH
    cmd = ["beepbox-cli", "export", json_path, wav_path]
    subprocess.run(cmd, check=True)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python scripts/beepbox2wav.py input.json output.wav")
        sys.exit(1)
    beepbox_to_wav(sys.argv[1], sys.argv[2])
