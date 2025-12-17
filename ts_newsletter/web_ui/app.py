"""
Flask Web UI for Trust & Safety Newsletter Automation
Provides web interface for browsing, searching, and generating newsletters
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path

from flask import Flask, render_template, jsonify, request, send_file
from flask_cors import CORS

# Import our newsletter system (will be available after setup)
# from ts_newsletter.config_loader import get_config
# from ts_newsletter.llm_client import LLMClientFactory
# from ts_newsletter.agents.orchestrator_agent import OrchestratorAgent


app = Flask(__name__)
CORS(app)

# Configuration
app.config['OUTPUT_DIR'] = os.getenv('TS_NEWSLETTER_OUTPUT_DIR', './output/newsletters')
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')


# ============================================================================
# Newsletter Management Endpoints
# ============================================================================

@app.route('/')
def index():
    """Main dashboard"""
    return render_template('dashboard.html')


@app.route('/newsletters')
def newsletters():
    """Browse newsletters"""
    return render_template('newsletters.html')


@app.route('/newsletter/<newsletter_id>')
def newsletter_view(newsletter_id):
    """View specific newsletter"""
    return render_template('newsletter_view.html')


@app.route('/search')
def search():
    """Search interface"""
    return render_template('search.html')


@app.route('/analytics')
def analytics():
    """Analytics dashboard"""
    return render_template('analytics.html')


@app.route('/generate')
def generate():
    """Manual generation interface"""
    return render_template('generate.html')


@app.route('/api/newsletters')
def list_newsletters():
    """List all newsletters with metadata"""
    output_dir = Path(app.config['OUTPUT_DIR'])
    newsletters = []

    if output_dir.exists():
        # Find all newsletter markdown files
        for file in sorted(output_dir.glob('newsletter_*.md'), reverse=True):
            # Extract date from filename
            date_str = file.stem.replace('newsletter_', '')

            # Load corresponding summary JSON
            summary_file = output_dir / f'summary_{date_str}.json'
            summary_data = {}
            if summary_file.exists():
                with open(summary_file, 'r') as f:
                    summary_data = json.load(f)

            # Get file stats
            stats = file.stat()

            newsletters.append({
                'id': date_str,
                'date': date_str,
                'filename': file.name,
                'size': stats.st_size,
                'created': datetime.fromtimestamp(stats.st_ctime).isoformat(),
                'modified': datetime.fromtimestamp(stats.st_mtime).isoformat(),
                'metrics': summary_data.get('metrics', {}),
                'status': summary_data.get('workflow_state', {}).get('status', 'unknown')
            })

    return jsonify({
        'success': True,
        'newsletters': newsletters,
        'total': len(newsletters)
    })


@app.route('/api/newsletters/<newsletter_id>')
def get_newsletter(newsletter_id):
    """Get full newsletter content"""
    output_dir = Path(app.config['OUTPUT_DIR'])

    # Load markdown
    md_file = output_dir / f'newsletter_{newsletter_id}.md'
    if not md_file.exists():
        return jsonify({'success': False, 'error': 'Newsletter not found'}), 404

    with open(md_file, 'r') as f:
        content = f.read()

    # Load summary
    summary_file = output_dir / f'summary_{newsletter_id}.json'
    summary_data = {}
    if summary_file.exists():
        with open(summary_file, 'r') as f:
            summary_data = json.load(f)

    # Load traces if available
    traces_file = output_dir / f'traces_{newsletter_id}.json'
    traces_data = None
    if traces_file.exists():
        with open(traces_file, 'r') as f:
            traces_data = json.load(f)

    return jsonify({
        'success': True,
        'id': newsletter_id,
        'content': content,
        'summary': summary_data,
        'traces': traces_data
    })


@app.route('/api/newsletters/<newsletter_id>/download')
def download_newsletter(newsletter_id):
    """Download newsletter as markdown"""
    output_dir = Path(app.config['OUTPUT_DIR'])
    md_file = output_dir / f'newsletter_{newsletter_id}.md'

    if not md_file.exists():
        return jsonify({'success': False, 'error': 'Newsletter not found'}), 404

    return send_file(
        md_file,
        as_attachment=True,
        download_name=f'newsletter_{newsletter_id}.md',
        mimetype='text/markdown'
    )


# ============================================================================
# Analytics Endpoints
# ============================================================================

@app.route('/api/analytics/summary')
def analytics_summary():
    """Get overall analytics summary"""
    output_dir = Path(app.config['OUTPUT_DIR'])

    total_newsletters = 0
    total_articles = 0
    avg_quality_score = 0
    threat_types = {}

    if output_dir.exists():
        summary_files = list(output_dir.glob('summary_*.json'))
        total_newsletters = len(summary_files)

        quality_scores = []

        for summary_file in summary_files:
            with open(summary_file, 'r') as f:
                data = json.load(f)

                metrics = data.get('metrics', {})
                total_articles += metrics.get('articles_collected', 0)

                if metrics.get('quality_score'):
                    quality_scores.append(metrics['quality_score'])

        if quality_scores:
            avg_quality_score = sum(quality_scores) / len(quality_scores)

    return jsonify({
        'success': True,
        'total_newsletters': total_newsletters,
        'total_articles': total_articles,
        'avg_quality_score': round(avg_quality_score, 2),
        'threat_types': threat_types,
        'period_days': 90  # Last 90 days
    })


@app.route('/api/analytics/trends')
def analytics_trends():
    """Get trend data over time"""
    output_dir = Path(app.config['OUTPUT_DIR'])

    trends = []

    if output_dir.exists():
        for summary_file in sorted(output_dir.glob('summary_*.json')):
            date_str = summary_file.stem.replace('summary_', '')

            with open(summary_file, 'r') as f:
                data = json.load(f)

                metrics = data.get('metrics', {})

                trends.append({
                    'date': date_str,
                    'articles': metrics.get('articles_collected', 0),
                    'quality_score': metrics.get('quality_score', 0),
                    'high_priority': 0  # TODO: Extract from data
                })

    return jsonify({
        'success': True,
        'trends': trends
    })


# ============================================================================
# Search Endpoints
# ============================================================================

@app.route('/api/search')
def search_newsletters():
    """Search across all newsletters"""
    query = request.args.get('q', '').lower()

    if not query:
        return jsonify({'success': False, 'error': 'No query provided'}), 400

    output_dir = Path(app.config['OUTPUT_DIR'])
    results = []

    if output_dir.exists():
        for md_file in output_dir.glob('newsletter_*.md'):
            date_str = md_file.stem.replace('newsletter_', '')

            with open(md_file, 'r') as f:
                content = f.read()

                # Simple search - check if query in content
                if query in content.lower():
                    # Find context around match
                    lines = content.split('\n')
                    matching_lines = [
                        (i, line) for i, line in enumerate(lines)
                        if query in line.lower()
                    ]

                    snippets = []
                    for line_num, line in matching_lines[:3]:  # First 3 matches
                        # Get context (line before and after)
                        start = max(0, line_num - 1)
                        end = min(len(lines), line_num + 2)
                        context = '\n'.join(lines[start:end])
                        snippets.append(context[:200])

                    results.append({
                        'id': date_str,
                        'date': date_str,
                        'matches': len(matching_lines),
                        'snippets': snippets
                    })

    return jsonify({
        'success': True,
        'query': query,
        'results': results,
        'total': len(results)
    })


# ============================================================================
# Generation Endpoints
# ============================================================================

@app.route('/api/generate', methods=['POST'])
def trigger_generation():
    """Manually trigger newsletter generation"""
    # TODO: Implement async generation with status tracking

    return jsonify({
        'success': True,
        'status': 'queued',
        'message': 'Newsletter generation started',
        'job_id': 'gen_' + datetime.now().strftime('%Y%m%d_%H%M%S')
    })


@app.route('/api/generate/status/<job_id>')
def generation_status(job_id):
    """Get status of newsletter generation"""
    # TODO: Implement status tracking

    return jsonify({
        'success': True,
        'job_id': job_id,
        'status': 'in_progress',  # queued, in_progress, completed, failed
        'progress': 45,  # percentage
        'current_phase': 'Analysis',
        'eta_seconds': 120
    })


# ============================================================================
# Configuration Endpoints
# ============================================================================

@app.route('/api/config')
def get_config():
    """Get current configuration (safe subset)"""
    # TODO: Load from config.yaml and return safe subset

    return jsonify({
        'success': True,
        'config': {
            'search_provider': 'duckduckgo',
            'llm_model': 'gpt-5',
            'target_articles': 8,
            'min_relevance': 7.0
        }
    })


# ============================================================================
# Main
# ============================================================================

def main():
    """Run Flask development server"""
    port = int(os.getenv('FLASK_PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'

    print("="*60)
    print("Trust & Safety Newsletter - Web UI")
    print("="*60)
    print(f"\nStarting server on http://localhost:{port}")
    print(f"Debug mode: {debug}")
    print(f"Output directory: {app.config['OUTPUT_DIR']}")
    print()

    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )


if __name__ == '__main__':
    main()
