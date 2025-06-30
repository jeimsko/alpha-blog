from flask import Flask, render_template, request, redirect, url_for, abort
import json
import os
from datetime import datetime
import markdown
from markupsafe import Markup
from werkzeug.utils import secure_filename

app = Flask(__name__)
POSTS_JSON_PATH = 'data/posts.json'
POSTS_DIR = 'data/posts'

UPLOAD_FOLDER = 'static/images'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
POSTS_JSON = os.path.join("data", "posts.json") 

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 글 목록 로딩
def load_posts():
    if os.path.exists(POSTS_JSON):
        with open(POSTS_JSON, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_posts(posts):
    with open(POSTS_JSON, "w", encoding="utf-8") as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)

@app.route("/new", methods=["GET", "POST"])
def create_post():
    if request.method == "POST":
        title = request.form["title"]
        thumbnail = request.form.get("thumbnail", "")
        content = request.form["content"]
        created_at = datetime.now().strftime("%Y-%m-%d")

        # 🔽 여기서 파일 업로드 처리
        file = request.files.get("thumb_file")
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(file_path)
            thumbnail = f"/static/images/{filename}"  # 자동 대체


        # 파일명 생성 (제목 기반 slug 또는 index)
        slug = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"{slug}.md"
        filepath = os.path.join(POSTS_DIR, filename)

        # 저장
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        # 목록 갱신
        posts = load_posts()
        posts.insert(0, {
            "title": title,
            "thumbnail": thumbnail,
            "filename": filename,
            "date": created_at
        })
        save_posts(posts)

        return redirect(url_for("home"))

    return render_template("new_post.html")

# 단일 글 로딩
def load_post_by_id(post_id):
    post_path = os.path.join(POSTS_DIR, f"{post_id}.md")
    if not os.path.exists(post_path):
        return None
    with open(post_path, 'r', encoding='utf-8') as f:
        content_md = f.read()
    content_html = markdown(content_md)
    return content_html

# 글 저장
def save_post(post):
    posts = load_posts()
    posts.insert(0, post)  # 최신글 위로
    with open(POSTS_FILE, "w", encoding="utf-8") as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)

@app.route("/")
def index():
    posts = load_posts()
    return render_template("cover.html", posts=posts)


@app.route("/write")
def write():
    return render_template("post_form.html")

@app.route("/create", methods=["POST"])
def create():
    title = request.form.get("title")
    thumbnail = request.form.get("thumbnail")
    content = request.form.get("content")
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M")

    post = {
        "title": title,
        "thumbnail": thumbnail,
        "content": content,
        "created_at": created_at
    }

    save_post(post)
    return redirect(url_for("index"))

@app.route("/post/<int:post_id>")
def post_detail(post_id):
    posts = load_posts()
    if 0 <= post_id < len(posts):
        post = posts[post_id]
        md_path = os.path.join(POSTS_DIR, post["filename"])
        if os.path.exists(md_path):
            with open(md_path, "r", encoding="utf-8") as f:
                raw_content = f.read()
                html_content = Markup(markdown.markdown(raw_content))
                return render_template("post_detail.html", post={
                    "title": post["title"],
                    "thumbnail": post["thumbnail"],
                    "created_at": post["date"],
                    "content": html_content
                }, post_id=post_id)
    return "글이 존재하지 않습니다", 404


@app.route('/delete/<int:post_id>', methods=['POST'])
def delete_post(post_id):
    posts = load_posts()
    if post_id < 0 or post_id >= len(posts):
        return '삭제할 글이 없습니다', 404

    del posts[post_id]
    save_posts(posts)
    return redirect(url_for('index'))

@app.route('/write', methods=['GET', 'POST'])
def write_post():
    thumbnail = request.form.get('thumbnail', '').strip()
    if not thumbnail:
        thumbnail = '/static/default-thumb.jpg'  # 기본 썸네일 경로
 
    if request.method == 'POST':
        posts = load_posts()
        new_post = {
            'title': request.form['title'],
            'content': request.form['content'],
            'date': datetime.now().strftime('%Y-%m-%d'),
            'thumbnail': thumbnail
        }
        posts.insert(0, new_post)  # 최신 글을 위로
        save_posts(posts)
        return redirect(url_for('index'))
    return render_template('form.html')

@app.route('/edit/<int:post_id>', methods=['GET', 'POST'])
def edit_post(post_id):
    posts = load_posts()
    if post_id < 0 or post_id >= len(posts):
        return '글이 존재하지 않습니다', 404

    if request.method == 'POST':
        posts[post_id]['title'] = request.form['title']
        posts[post_id]['content'] = request.form['content']
        thumbnail = request.form.get('thumbnail', '').strip()
        posts[post_id]['thumbnail'] = thumbnail if thumbnail else '/static/default-thumb.jpg'
        save_posts(posts)
        return redirect(url_for('post_detail', post_id=post_id))

    post = posts[post_id]
    return render_template('form.html', post=post, edit=True, post_id=post_id)




@app.route("/robots.txt")
def robots_txt():
    return send_from_directory("static", "robots.txt")

@app.route("/new", methods=["GET", "POST"])
def new_post():
    if request.method == "POST":
        title = request.form["title"]
        content = request.form["content"]
        thumbnail = request.form["thumbnail"]

        now = datetime.now()
        slug = secure_filename(title).lower()
        date_str = now.strftime("%Y-%m-%d")
        filename = f"{date_str}-{slug}.md"
        filepath = os.path.join(DATA_DIR, filename)

        # 저장
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        # posts.json 메타 추가
        post_data = {
            "title": title,
            "thumbnail": thumbnail,
            "date": date_str,
            "filename": filename,
        }

        if os.path.exists(POSTS_JSON):
            with open(POSTS_JSON, "r", encoding="utf-8") as f:
                posts = json.load(f)
        else:
            posts = []

        posts.insert(0, post_data)

        with open(POSTS_JSON, "w", encoding="utf-8") as f:
            json.dump(posts, f, ensure_ascii=False, indent=2)

        flash("글이 등록되었습니다.")
        return redirect(url_for("home"))

    return render_template("new_post.html")

@app.route("/cover")
def cover():
    posts = load_posts()  # ← 이 함수가 posts.json에서 로딩하는지 확인
    return render_template("cover.html", posts=posts)

@app.route("/images/<path:filename>")
def image(filename):
    return send_from_directory("static/images", filename)

if __name__ == "__main__":
     # 개발할 때만 사용!
    app.run(debug=True)
