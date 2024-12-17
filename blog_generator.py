import os
import json
import markdown
import yaml
import traceback
from datetime import datetime
from pathlib import Path

class BlogGenerator:
    def __init__(self, content_dir='content/blog', output_dir='blog'):
        self.content_dir = content_dir
        self.output_dir = output_dir
        self.posts = []
        print(f"Initializing BlogGenerator with content_dir: {content_dir}, output_dir: {output_dir}")
        
    def parse_frontmatter(self, content):
        """Parse YAML frontmatter from markdown content"""
        metadata = {
            'title': '',
            'date': datetime.now().strftime('%Y-%m-%d'),
            'tags': [],
            'description': ''
        }
        
        if content.startswith('---'):
            try:
                parts = content.split('---', 2)[1:]
                if len(parts) >= 2:
                    fm = yaml.safe_load(parts[0])
                    if fm:
                        # Handle date conversion
                        if 'date' in fm:
                            if hasattr(fm['date'], 'strftime'):  # datetime object
                                fm['date'] = fm['date'].strftime('%Y-%m-%d')
                            elif isinstance(fm['date'], str):
                                # Try to parse the date string
                                try:
                                    date_obj = datetime.strptime(fm['date'], '%Y-%m-%d')
                                    fm['date'] = date_obj.strftime('%Y-%m-%d')
                                except ValueError:
                                    print(f"Warning: Could not parse date {fm['date']}, using current date")
                                    fm['date'] = datetime.now().strftime('%Y-%m-%d')
                        metadata.update(fm)
                    content = parts[1].strip()
                    return metadata, content
            except yaml.YAMLError as e:
                print(f"Error parsing frontmatter: {e}")
        
        return metadata, content

    def process_post(self, file_path):
        """Process a single blog post"""
        print(f"Processing post: {file_path}")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                print(f"Read {len(content)} bytes from {file_path}")

            # Parse frontmatter and content
            metadata, content = self.parse_frontmatter(content)
            print(f"Parsed metadata: {metadata}")
            
            # If no title in frontmatter, use filename
            if not metadata['title']:
                metadata['title'] = Path(file_path).stem.replace('-', ' ').title()

            # Convert markdown to HTML
            html_content = markdown.markdown(
                content,
                extensions=['extra', 'codehilite', 'fenced_code', 'tables']
            )
            print(f"Converted markdown to HTML: {len(html_content)} bytes")

            # Ensure tags is a list
            if isinstance(metadata['tags'], str):
                metadata['tags'] = [tag.strip() for tag in metadata['tags'].split(',')]
            elif not isinstance(metadata['tags'], list):
                metadata['tags'] = []

            # Create post object
            post = {
                'title': metadata['title'],
                'date': metadata['date'],
                'tags': metadata['tags'],
                'description': metadata['description'] or self.generate_description(content),
                'content': html_content,
                'slug': Path(file_path).stem.replace(' ', '-')  # Replace spaces with hyphens
            }
            print(f"Created post object: {post['title']}")

            return post
        except Exception as e:
            print(f"Error processing {file_path}:")
            print(traceback.format_exc())
            raise

    def generate_description(self, content):
        """Generate a description from the content if none provided"""
        text = content.split('\n')[0]  # Get first paragraph
        return text[:150] + '...' if len(text) > 150 else text

    def generate_posts(self):
        """Generate all blog posts"""
        print("Starting blog generation...")
        self.posts = []
        content_path = Path(self.content_dir)
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        print(f"Created output directory: {self.output_dir}")

        # Process all markdown files
        markdown_files = list(content_path.glob('*.md'))
        print(f"Found {len(markdown_files)} markdown files")
        
        for file_path in markdown_files:
            try:
                post = self.process_post(file_path)
                self.posts.append(post)
                print(f"Successfully processed: {file_path}")
            except Exception as e:
                print(f"Error processing {file_path}: {e}")
                continue

        # Sort posts by date
        self.posts.sort(key=lambda x: x['date'], reverse=True)
        print(f"Sorted {len(self.posts)} posts by date")

        # Save posts data
        posts_json_path = os.path.join(self.output_dir, 'posts.json')
        with open(posts_json_path, 'w', encoding='utf-8') as f:
            json.dump(self.posts, f, ensure_ascii=False, indent=2)
            print(f"Saved posts data to: {posts_json_path}")

        # Generate individual post files
        for post in self.posts:
            try:
                post_path = os.path.join(self.output_dir, f"{post['slug']}.html")
                with open(post_path, 'w', encoding='utf-8') as f:
                    f.write(self.generate_post_html(post))
                print(f"Generated HTML file: {post_path}")
            except Exception as e:
                print(f"Error generating HTML for {post['title']}:")
                print(traceback.format_exc())

    def generate_post_html(self, post):
        """Generate HTML for a single post"""
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{post['title']} - Pete Oswald's Blog</title>
    <link rel="stylesheet" href="../styles.css">
    <meta name="description" content="{post['description']}">
</head>
<body>
    <div class="nav-container">
        <nav>
            <a href="../index.html" class="nav-brand">Pete Oswald</a>
            <ul class="nav-links">
                <li><a href="../index.html">Home</a></li>
                <li><a href="../resume.html">Resume</a></li>
                <li><a href="../blog.html" class="active">Blog</a></li>
                <li><a href="../links.html">Links</a></li>
            </ul>
        </nav>
    </div>

    <div class="container">
        <article class="blog-post">
            <header class="post-header">
                <h1>{post['title']}</h1>
                <div class="post-meta">
                    <time>{post['date']}</time>
                    <div class="tags">
                        {' '.join(f'<span class="tag">{tag}</span>' for tag in post['tags'])}
                    </div>
                </div>
            </header>
            <div class="post-content">
                {post['content']}
            </div>
        </article>
    </div>

    <footer>
        <p> 2024 Pete Oswald. All rights reserved.</p>
    </footer>
</body>
</html>"""

if __name__ == '__main__':
    try:
        print("Starting blog generation process...")
        generator = BlogGenerator()
        generator.generate_posts()
        print("Blog generation completed successfully!")
    except Exception as e:
        print("Error during blog generation:")
        print(traceback.format_exc())
