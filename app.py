from flask import Flask, request, Response, stream_with_context
import subprocess
import shutil
import sys
import os
import imageio_ffmpeg

app = Flask(__name__)

# إضافة FFmpeg للمسار
os.environ["PATH"] += os.pathsep + os.path.dirname(imageio_ffmpeg.get_ffmpeg_exe())
YTDLP_CMD = shutil.which("yt-dlp") or "yt-dlp"

@app.route('/download')
def download():
    url = request.args.get('url')
    if not url:
        return "No URL provided", 400

    print(f"Processing: {url}", file=sys.stderr)

    # 👇 إعدادات الأمر مع خدعة الأندرويد لتجاوز الحظر 👇
    cmd = [
        YTDLP_CMD,
        url,
        "-f", "bestaudio[ext=m4a]/bestaudio", # نطلب M4A عشان يكون متوافق مع جيميني
        "-o", "-",
        "--quiet",
        "--no-playlist",
        "--no-warnings",
        "--geo-bypass",
        # ⚠️ السطرين القادمين هما الحل السحري لتخطي رسالة Sign in
        "--extractor-args", "youtube:player_client=android", # انتحال شخصية تطبيق أندرويد
        "--user-agent", "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
    ]

    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def generate():
        # قراءة أول قطعة للتأكد من نجاح الاتصال
        first_chunk = proc.stdout.read(4096)
        
        if not first_chunk:
            # لو مفيش بيانات، نقرأ رسالة الخطأ ونبعتها
            stderr = proc.stderr.read()
            error_msg = stderr.decode() if stderr else "Unknown Error"
            print(f"❌ Error Log: {error_msg}", file=sys.stderr)
            yield f"Server Error: {error_msg}".encode()
            return

        yield first_chunk
        try:
            while True:
                chunk = proc.stdout.read(4096)
                if not chunk:
                    break
                yield chunk
            proc.stdout.close()
            proc.wait()
        except GeneratorExit:
            proc.terminate()

    # الرد بصيغة m4a
    return Response(stream_with_context(generate()), mimetype="audio/mp4")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)