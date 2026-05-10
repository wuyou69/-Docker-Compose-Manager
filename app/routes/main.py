from flask import Blueprint, render_template, session, redirect, url_for, jsonify, request, current_app
import os
import docker
from datetime import datetime
import requests

# Create blueprint
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Home page"""
    if 'user_id' not in session:
        return redirect(url_for('main.login_page'))
    return render_template('index.html')

@main_bp.route('/login')
def login_page():
    """Login page"""
    if 'user_id' in session:
        return redirect(url_for('main.index'))
    return render_template('login.html')

@main_bp.route('/api/system-info', methods=['GET'])
def get_system_info():
    """Get system information"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    # Get Docker compose version
    docker_compose_version = check_docker_compose_version()
    
    # Check mirror availability
    mirrors_status = check_mirrors()
    
    # Get app version
    app_version = os.environ.get('APP_VERSION', '1.0.0')
    
    return jsonify({
        'docker_compose_version': docker_compose_version,
        'mirrors_status': mirrors_status,
        'app_version': app_version,
        'current_time': datetime.utcnow().isoformat()
    })

def check_docker_compose_version():
    """Check Docker Compose version"""
    import subprocess
    try:
        # Try v2 first
        result = subprocess.run(['docker', 'compose', 'version'], 
                               capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            return {'version': 'v2', 'details': result.stdout.strip()}
        
        # Try v1
        result = subprocess.run(['docker-compose', 'version'], 
                               capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            return {'version': 'v1', 'details': result.stdout.strip()}
        
        return {'version': 'unknown', 'error': 'Docker Compose not found'}
    except Exception as e:
        return {'version': 'error', 'error': str(e)}

def check_mirrors():
    """Check mirror availability"""
    mirrors = [
        'https://docker.1ms.run',
        'https://docker.1panel.live'
    ]
    status = {}
    
    for mirror in mirrors:
        try:
            response = requests.head(mirror, timeout=3)
            status[mirror] = {'available': response.status_code < 400, 'status_code': response.status_code}
        except Exception as e:
            status[mirror] = {'available': False, 'error': str(e)}
    
    return status

@main_bp.route('/api/docker-stats', methods=['GET'])
def get_docker_stats():
    """Get Docker stats"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        client = docker.from_env()
        containers = client.containers.list(all=True)
        # 尝试获取镜像列表，不使用dangling参数
        images = client.images.list()
        
        # 进一步过滤，只保留有标签的顶层镜像
        top_level_images = []
        for image in images:
            if hasattr(image, 'tags') and image.tags:  # 有标签的镜像
                top_level_images.append(image)
        
        return jsonify({
            'containers_count': len(containers),
            'running_containers_count': len([c for c in containers if c.status == 'running']),
            'images_count': len(top_level_images)
        })
    except Exception as e:
        import traceback
        return jsonify({'error': f'Failed to get Docker stats: {str(e)}', 'traceback': traceback.format_exc()}), 500

@main_bp.route('/api/containers', methods=['GET'])
def get_containers():
    """Get all containers with details"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        client = docker.from_env()
        containers = client.containers.list(all=True)
        
        containers_list = []
        for container in containers:
            containers_list.append({
                'id': container.id,
                'name': container.name,
                'status': container.status,
                'image': container.image.tags[0] if container.image.tags else container.image.id,
                'created': container.attrs['Created'],
                'ports': container.attrs['NetworkSettings']['Ports']
            })
        
        return jsonify(containers_list)
    except Exception as e:
        return jsonify({'error': f'Failed to get containers: {str(e)}'}), 500

@main_bp.route('/api/images', methods=['GET'])
def get_images():
    """Get all images with details"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        client = docker.from_env()
        # 尝试获取镜像列表，不使用dangling参数
        images = client.images.list()
        
        images_list = []
        for image in images:
            if hasattr(image, 'tags') and image.tags:  # 只保留有标签的顶层镜像
                # 安全获取attrs属性
                attrs = getattr(image, 'attrs', {})
                images_list.append({
                    'id': getattr(image, 'id', ''),
                    'tags': image.tags,
                    'repo_tags': image.tags,  # 兼容前端使用repo_tags的地方
                    'created': attrs.get('Created', 'N/A'),
                    'size': attrs.get('Size', 0),
                    'virtual_size': attrs.get('VirtualSize', 0)
                })
        
        return jsonify(images_list)
    except Exception as e:
        import traceback
        return jsonify({'error': f'Failed to get images: {str(e)}', 'traceback': traceback.format_exc()}), 500

@main_bp.route('/api/container/<container_id>/logs', methods=['GET'])
def get_container_logs(container_id):
    """Get container logs (last 1000 lines)"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        client = docker.from_env()
        container = client.containers.get(container_id)
        
        # 获取最近1000条日志，不使用流式传输
        logs = container.logs(stdout=True, stderr=True, tail=1000)
        
        # 返回日志内容
        return current_app.response_class(
            logs.decode('utf-8'),
            mimetype='text/plain; charset=utf-8'
        )
    except Exception as e:
        import traceback
        return jsonify({'error': f'Failed to get container logs: {str(e)}', 'traceback': traceback.format_exc()}), 500

@main_bp.route('/api/settings/gitee-token', methods=['GET'])
def get_gitee_token():
    """Get GitHub token from session."""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    token = session.get('gitee_token', '')
    return jsonify({
        'success': True,
        'token': token,
        'has_token': bool(token)
    })

@main_bp.route('/api/settings/gitee-token', methods=['POST'])
def set_gitee_token():
    """Set GitHub token in session."""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.json
    if not data or 'token' not in data:
        return jsonify({'error': 'Token is required'}), 400
    
    token = data['token'].strip()
    
    # Store token in session
    session['gitee_token'] = token
    
    return jsonify({
        'success': True,
        'message': 'GitHub token saved successfully',
        'has_token': bool(token)
    })

@main_bp.route('/api/settings/gitee-token', methods=['DELETE'])
def clear_gitee_token():
    """Clear GitHub token from session."""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    # Remove token from session
    if 'gitee_token' in session:
        del session['gitee_token']
    
    return jsonify({
        'success': True,
        'message': 'GitHub token cleared successfully',
        'has_token': False
    })
