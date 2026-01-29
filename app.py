from flask import Flask, request, Response, stream_with_context
import subprocess
import shutil
import sys

app = Flask(__name__)

# نحدد مسار yt-dlp
YTDLP_CMD = shutil.which("yt-dlp") or "yt-dlp"

@app.route('/download')
def download():
    url = request.args.get('url')
    if not url:
        return "No URL provided", 400

    print(f"Processing: {url}", file=sys.stderr)

    # التعديل هنا: شيلنا شرط [ext=m4a] عشان منحتجش ffmpeg
    # بنطلب 'bestaudio' بس، وهو يجي زي ما يجي (غالباً webm أو m4a)
    cmd = [
        YTDLP_CMD,
        url,
        "-f", "bestaudio",         # أفضل صوت خام بدون تحويل
        "-o", "-",                 # الإخراج المباشر
        "--quiet",
        "--no-playlist",
        "--no-warnings",
        "--geo-bypass",
        "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    ]

    # تشغيل العملية مع توجيه الأخطاء للوج
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def generate():
        try:
            # نقرأ البيانات ونبعتها
            while True:
                chunk = proc.stdout.read(4096)
                if not chunk:
                    break
                yield chunk
            
            # بعد ما يخلص، نشوف لو كان فيه أخطاء
            stderr_output = proc.stderr.read()
            if stderr_output:
                print(f"yt-dlp Error Log: {stderr_output.decode()}", file=sys.stderr)
                
            proc.stdout.close()
            proc.wait()
        except GeneratorExit:
            proc.terminate()

    # غيرنا النوع لـ audio/mpeg أو audio/webm لضمان التوافق
    return Response(stream_with_context(generate()), mimetype="audio/webm")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)