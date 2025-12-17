# Trust & Safety Newsletter - Web UI

**Modern web interface for browsing, searching, and managing Trust & Safety newsletters**

Built with Flask, Bootstrap 5, and Chart.js.

---

## Features

### 📊 **Dashboard**
- Overview metrics (total newsletters, articles, quality scores)
- Trend charts (articles and quality over time)
- Recent newsletters list
- Quick actions

### 📰 **Newsletter Browser**
- Browse all newsletters with filtering
- Filter by date range, status, sort order
- Pagination support
- Preview cards with metrics

### 👁️ **Newsletter Viewer**
- Full newsletter display with markdown rendering
- Sidebar with metrics and workflow info
- Agent trace viewer (transparency)
- Export and share options

### 🔍 **Search**
- Full-text search across all newsletters
- Keyword highlighting in results
- Quick navigation to matching newsletters

### ▶️ **Manual Generation**
- Trigger newsletter generation on demand
- Real-time status updates
- Progress tracking
- Completion notifications

### 🎨 **Modern UI**
- Responsive design (works on mobile)
- Dark mode support
- Bootstrap 5 styling
- Chart.js visualizations
- Smooth animations

---

## Quick Start

### **1. Install Dependencies**

```bash
# From project root
pip install -r requirements.txt
```

### **2. Start Web UI**

```bash
# Simple start
python start_web_ui.py

# Or with custom port
FLASK_PORT=8000 python start_web_ui.py

# Debug mode
FLASK_DEBUG=true python start_web_ui.py
```

### **3. Access Web UI**

Open your browser to: **http://localhost:5000**

---

## Configuration

### Environment Variables

```bash
# Flask Configuration
FLASK_PORT=5000                          # Port (default: 5000)
FLASK_DEBUG=false                        # Debug mode (default: false)
FLASK_SECRET_KEY=your-secret-key         # Secret key (change in production!)

# Newsletter Output
TS_NEWSLETTER_OUTPUT_DIR=./output/newsletters  # Newsletter storage location
```

### Creating `.env` file:

```bash
# Copy example
cp .env.example .env

# Edit .env
nano .env
```

---

## API Endpoints

The Web UI provides a RESTful API:

### Newsletters

```
GET  /api/newsletters              # List all newsletters
GET  /api/newsletters/:id          # Get specific newsletter
GET  /api/newsletters/:id/download # Download newsletter
```

### Analytics

```
GET  /api/analytics/summary        # Overall statistics
GET  /api/analytics/trends         # Trend data
```

### Search

```
GET  /api/search?q=<query>         # Search newsletters
```

### Generation

```
POST /api/generate                 # Trigger generation
GET  /api/generate/status/:job_id  # Check generation status
```

### Configuration

```
GET  /api/config                   # Get configuration (safe subset)
```

---

## Development

### File Structure

```
ts_newsletter/web_ui/
├── app.py                  # Flask application
├── requirements.txt        # Web UI specific deps
├── templates/              # HTML templates
│   ├── base.html           # Base template
│   ├── dashboard.html      # Dashboard page
│   ├── newsletters.html    # Browse newsletters
│   ├── newsletter_view.html # View single newsletter
│   ├── search.html         # Search interface
│   ├── generate.html       # Manual generation
│   └── analytics.html      # Analytics page
└── static/                 # Static assets
    ├── css/
    │   └── style.css       # Custom styles
    └── js/
        └── main.js         # JavaScript utilities
```

### Adding New Pages

1. **Create template** in `templates/`:
```html
{% extends "base.html" %}
{% block title %}My Page{% endblock %}
{% block content %}
  <!-- Your content -->
{% endblock %}
```

2. **Add route** in `app.py`:
```python
@app.route('/mypage')
def mypage():
    return render_template('mypage.html')
```

3. **Update navigation** in `base.html`

### Customizing Styles

Edit `static/css/style.css`:

```css
/* Add your custom styles */
.my-custom-class {
    /* ... */
}
```

### Adding Features

Common patterns:

**API Endpoint:**
```python
@app.route('/api/my-endpoint')
def my_endpoint():
    # Your logic
    return jsonify({
        'success': True,
        'data': {}
    })
```

**JavaScript Function:**
```javascript
async function myFunction() {
    const response = await fetch('/api/my-endpoint');
    const data = await response.json();
    // Handle data
}
```

---

## Production Deployment

### Using Gunicorn

```bash
# Install Gunicorn
pip install gunicorn

# Run with Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 ts_newsletter.web_ui.app:app
```

### Using systemd

Create `/etc/systemd/system/ts-newsletter-ui.service`:

```ini
[Unit]
Description=Trust & Safety Newsletter Web UI
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/bert-for-inference
Environment="FLASK_PORT=5000"
Environment="TS_NEWSLETTER_OUTPUT_DIR=/path/to/output"
ExecStart=/path/to/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 ts_newsletter.web_ui.app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable ts-newsletter-ui
sudo systemctl start ts-newsletter-ui
```

### Nginx Reverse Proxy

```nginx
server {
    listen 80;
    server_name newsletter.yourdomain.com;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

---

## Security

### Production Checklist

- [ ] Change `FLASK_SECRET_KEY` from default
- [ ] Disable debug mode (`FLASK_DEBUG=false`)
- [ ] Use HTTPS (SSL/TLS)
- [ ] Set up authentication (if needed)
- [ ] Configure CORS properly
- [ ] Use Gunicorn/uWSGI (not Flask dev server)
- [ ] Set up rate limiting
- [ ] Enable logging and monitoring

### Authentication (Optional)

The Web UI currently has no authentication. To add:

1. Install Flask-Login:
```bash
pip install flask-login
```

2. Add authentication logic to `app.py`

3. Protect routes with `@login_required` decorator

---

## Troubleshooting

### Port Already in Use

```bash
# Find process using port 5000
lsof -i :5000

# Kill process
kill -9 <PID>

# Or use different port
FLASK_PORT=8000 python start_web_ui.py
```

### Cannot Find Newsletters

Check output directory:
```bash
# Set correct path
export TS_NEWSLETTER_OUTPUT_DIR=/path/to/newsletters

# Or create output dir
mkdir -p ./output/newsletters
```

### Styling Not Loading

Clear browser cache:
- Chrome/Edge: Ctrl+Shift+R
- Firefox: Ctrl+F5
- Safari: Cmd+Option+R

### API Returns 404

Ensure Flask app is running:
```bash
# Check logs
tail -f logs/ts_newsletter.log

# Verify routes
flask routes
```

---

## Browser Support

- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+
- ✅ Mobile browsers (iOS Safari, Chrome Mobile)

---

## Contributing

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-flask

# Run tests
pytest ts_newsletter/web_ui/tests/
```

### Code Style

```bash
# Format code
black ts_newsletter/web_ui/

# Lint
flake8 ts_newsletter/web_ui/
```

---

## Changelog

### v1.0.0 (December 2025)
- Initial release
- Dashboard with analytics
- Newsletter browser and viewer
- Search functionality
- Manual generation interface
- Dark mode support
- Responsive design

---

## Support

For issues or questions:
- GitHub Issues: [Repository URL]
- Documentation: `ts_newsletter/README.md`
- Internal Support: [Contact Information]

---

**Built with:** Flask, Bootstrap 5, Chart.js, marked.js
**License:** [Your License]
