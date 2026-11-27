"""生成 PET 聽力測驗音檔（Google TTS，逐句合成 → 男聲降調 → 拼接）。

edge-tts 目前回 403（微軟 DRM token 擋），改用 gTTS。
男聲處理：asetrate 降 12% 再 atempo 補回長度，音高明顯較低但仍自然。

用法：python tools/gen_audio.py
輸出：audio/l1.mp3 ~ l5.mp3
"""
import os
import subprocess
import tempfile

from gtts import gTTS

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "audio")
TMP = tempfile.mkdtemp(prefix="petaud_")

SR = 24000
SILENCE = 0.4
MALE_PITCH = 0.88          # 12% 降調
SPEAK_TLD = "co.uk"        # 英式發音

SCRIPTS = {
    "l1": [
        ("W", "Hi Dan, it's me. Are we still meeting at the station at six?"),
        ("M", "Hi. Could we make it half past six? I finish work late today."),
        ("W", "Sure, half past six. Shall I get the tickets?"),
        ("M", "Yes please. Two returns, thanks."),
        ("W", "OK, see you there."),
    ],
    "l2": [
        ("W", "Excuse me, how much is this sandwich?"),
        ("M", "Four pounds fifty. But if you buy a drink as well, it's five pounds together."),
        ("W", "Oh, that's good. I'll have a coffee too, then."),
        ("M", "Sure. Anything else?"),
        ("W", "No, that's all, thanks."),
    ],
    "l3": [
        ("M", "Did you bring an umbrella?"),
        ("W", "No, I didn't. The forecast said it would be sunny."),
        ("M", "Well, look outside. It's pouring."),
        ("W", "Oh no. We'll have to run to the bus stop."),
        ("M", "Too late. We've missed it. The next one is in twenty minutes."),
    ],
    "l4": [
        ("M", "Hello. I'd like to book a tennis court for Saturday, please."),
        ("W", "Morning or afternoon?"),
        ("M", "Morning, if possible. Around ten o'clock."),
        ("W", "I'm afraid ten is taken. I can do half past nine, or eleven."),
        ("M", "Half past nine is fine. How much is it?"),
        ("W", "Eight pounds an hour. Members pay five."),
        ("M", "I'm not a member, I'm afraid. Can I pay at the desk?"),
        ("W", "Yes, of course. But please arrive ten minutes early. The courts get busy."),
        ("M", "No problem. Thanks very much."),
    ],
    "l5": [
        ("W", "Good morning, everyone. This is a message for passengers travelling to Bristol on the eight fifteen service. "
              "Because of engineering work, this train will now leave from platform six instead of platform two. "
              "It will also stop at Bath, which is not shown on your tickets. "
              "Passengers with heavy luggage should use the lift next to the ticket office. "
              "The cafe on platform six is open, and tea and coffee are free for anyone whose journey is delayed by more than thirty minutes. "
              "We apologise for the inconvenience."),
    ],
}


def ff(args):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error"] + args, check=True)


def synth(spk, text, path):
    raw = path + ".raw.mp3"
    gTTS(text=text, lang="en", tld=SPEAK_TLD, slow=False).save(raw)
    if spk == "M":
        af = f"asetrate={SR}*{MALE_PITCH},aresample={SR},atempo={1/MALE_PITCH:.4f}"
    else:
        af = f"aresample={SR}"
    ff(["-i", raw, "-filter:a", af, "-ar", str(SR), "-ac", "1", "-b:a", "64k", path])


def main():
    os.makedirs(OUT, exist_ok=True)
    silence = os.path.join(TMP, "sil.mp3")
    ff(["-f", "lavfi", "-i", f"anullsrc=r={SR}:cl=mono", "-t", str(SILENCE),
        "-ar", str(SR), "-ac", "1", "-b:a", "64k", silence])

    for name, turns in SCRIPTS.items():
        parts = []
        for i, (spk, text) in enumerate(turns):
            p = os.path.join(TMP, f"{name}_{i}.mp3")
            synth(spk, text, p)
            parts.append(p)
            if i < len(turns) - 1:
                parts.append(silence)
        lst = os.path.join(TMP, f"{name}.txt")
        with open(lst, "w", encoding="utf-8") as f:
            for p in parts:
                f.write("file '%s'\n" % p.replace("\\", "/"))
        dest = os.path.join(OUT, f"{name}.mp3")
        ff(["-f", "concat", "-safe", "0", "-i", lst,
            "-c:a", "libmp3lame", "-b:a", "64k", "-ar", str(SR), "-ac", "1", dest])
        dur = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
             "-of", "default=nw=1:nk=1", dest],
            capture_output=True, text=True,
        ).stdout.strip()
        print(f"{name}.mp3  {os.path.getsize(dest)//1024} KB  {float(dur):.1f}s")


if __name__ == "__main__":
    main()
