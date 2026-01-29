from flask import Flask, request, Response, stream_with_context
import subprocess
import shutil
import sys
import os
import imageio_ffmpeg

app = Flask(__name__)

# 🛠️ الحل السحري: إضافة FFmpeg لمسار النظام أوتوماتيكياً
os.environ["PATH"] += os.pathsep + os.path.dirname(imageio_ffmpeg.get_ffmpeg_exe())

# تحديد مسار yt-dlp
YTDLP_CMD = shutil.which("yt-dlp") or "yt-dlp"

@app.route('/download')
def download():
    url = request.args.get('url')
    if not url:
        return "No URL provided (Server is Running!)", 400

    print(f"Processing: {url}", file=sys.stderr)

    # الأمر الموجه لـ yt-dlp
    cmd = [
        YTDLP_CMD,
        url,
        "-f", "bestaudio[ext=m4a]/bestaudio/best",  # الآن يمكننا طلب m4a بأمان لوجود ffmpeg
        "-o", "-",
        "--quiet",
        "--no-playlist",
        "--no-warnings",
        "--geo-bypass",
        "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    ]

    # تشغيل العملية
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def generate():
        # نقرأ أول قطعة للتأكد من وجود بيانات
        first_chunk = proc.stdout.read(4096)
        
        # لو مفيش بيانات من البداية، يبقى حصل خطأ
        if not first_chunk:
            stderr = proc.stderr.read()
            error_msg = stderr.decode() if stderr else "Unknown Error"
            print(f"❌ Error: {error_msg}", file=sys.stderr)
            # نبعت الخطأ للمستخدم عشان نعرف السبب
            yield f"Error: {error_msg}".encode()
            return

        # لو فيه بيانات، نبعتها ونكمل الباقي
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

    return Response(stream_with_context(generate()), mimetype="audio/mp4")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)