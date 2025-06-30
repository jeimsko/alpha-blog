from flask import Flask, render_template, request, redirect, url_for
import json
import os
from datetime import datetime
import markdown

app = Flask(__name__)
POSTS_FILE = "posts.json"

# 글 목록 로딩
def load_posts():
    if not os.path.exists(POSTS_FILE):
        return []
    with open(POSTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

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

@app.route('/post/<int:post_id>')
def post_detail(post_id):
    posts = load_posts()
    if 0 <= post_id < len(posts):
        post = posts[post_id]
        post['content'] = markdown.markdown(post['content'], extensions=['fenced_code', 'tables'])
        return render_template('post_detail.html', post=post)
    else:
        return '글이 존재하지 않습니다', 404

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


if __name__ == "__main__":
    app.run(debug=True)
