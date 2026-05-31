import csv
import io
import json


def to_csv_bytes(items: list[str], header: str = "value") -> bytes:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([header])
    writer.writerows([[item] for item in items])
    return buf.getvalue().encode("utf-8")


def to_json_bytes(items: list[str]) -> bytes:
    return json.dumps(items, indent=2).encode("utf-8")


def clipboard_html(text: str) -> str:
    safe = text.replace("\\", "\\\\").replace("`", "\\`").replace("$", "\\$")
    return f"""
    <button onclick="
      navigator.clipboard.writeText(`{safe}`).then(function() {{
        this.textContent = '✓ Copied!';
        this.style.borderColor = '#10b981';
        this.style.color = '#10b981';
        setTimeout(() => {{
          this.textContent = '📋 Copy to Clipboard';
          this.style.borderColor = '#4d8bf5';
          this.style.color = '#4d8bf5';
        }}, 2000);
      }}.bind(this));
    " style="
      width:100%;background:#1a2332;color:#4d8bf5;
      border:1px solid #4d8bf5;padding:8px 16px;
      border-radius:8px;cursor:pointer;font-size:14px;
      font-family:sans-serif;transition:all .2s;
    ">📋 Copy to Clipboard</button>
    """
