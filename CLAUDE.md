# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

GPU monitoring and task management platform for single-server deployments with multiple NVIDIA GPUs. Runs directly on the host system without Docker.

**Key Architecture**: Django web app + background scheduler + SQLite database + direct host execution

## Development Commands

### Setup and Deployment

```bash
# Initial deployment
./deploy.sh

# Start platform
./start.sh

# Stop platform
./stop.sh

# Activate virtual environment
source venv/bin/activate

# Run Django commands
python manage.py <command>

# Create superuser
python manage.py createsuperuser

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput
```

### Deployment Options

The platform can run in three modes:

**1. Manual Start (No sudo required)**
- Use `./start.sh` and `./stop.sh` scripts
- Services run in background with nohup
- Must manually restart after reboot
- Best for: Development, testing, temporary deployments

**2. User-level Systemd (No sudo required)**
- Services managed with `systemctl --user` commands
- Auto-starts on user login (not on boot)
- No root privileges needed
- Services stop when user logs out (unless lingering enabled)
- Best for: Single-user systems, development servers, sudo-restricted environments

**3. System-level Systemd (Requires sudo)**
- Services managed with `sudo systemctl` commands
- Auto-starts on system boot
- Runs as specified user but managed by root
- Services persist across user sessions
- Best for: Production servers, multi-user systems, always-on deployments

**Enabling user services on boot:**
```bash
# Allow user services to run without login session (requires sudo once)
sudo loginctl enable-linger $(whoami)
```

### Development Server

```bash
# Start Django dev server only
source venv/bin/activate
python manage.py runserver 0.0.0.0:8888

# Start scheduler only
source venv/bin/activate
python scheduler.py

# Start both (recommended)
./start.sh
```

### Testing GPU Detection

```bash
# Test nvidia-smi
nvidia-smi

# Test GPU info collection
source venv/bin/activate
python -c "
import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gpu_monitor.settings')
django.setup()
from gpu_app.utils import get_local_gpu_info
print(get_local_gpu_info())
"

# Check GPU database
python manage.py shell -c "
from gpu_app.models import GPUInfo
for gpu in GPUInfo.objects.all():
    print(f'GPU {gpu.index}: {gpu.name} - {gpu.utilization}%')
"
```

### Systemd Management

**User-level services (no sudo required):**

```bash
# Status
systemctl --user status gpu-monitor-scheduler gpu-monitor-web

# Restart
systemctl --user restart gpu-monitor-web

# View logs
journalctl --user -u gpu-monitor-scheduler -f
journalctl --user -u gpu-monitor-web -f

# Stop
systemctl --user stop gpu-monitor-scheduler gpu-monitor-web

# Disable auto-start
systemctl --user disable gpu-monitor-scheduler gpu-monitor-web

# Enable start on boot (optional, requires sudo once)
sudo loginctl enable-linger $(whoami)
```

**System-level services (requires sudo):**

```bash
# Status
sudo systemctl status gpu-monitor-scheduler gpu-monitor-web

# Restart
sudo systemctl restart gpu-monitor-web

# View logs
sudo journalctl -u gpu-monitor-scheduler -f
sudo journalctl -u gpu-monitor-web -f

# Stop
sudo systemctl stop gpu-monitor-scheduler gpu-monitor-web

# Disable auto-start
sudo systemctl disable gpu-monitor-scheduler gpu-monitor-web
```

## Architecture Overview

### Core Components

1. **Django Web Application** (`gpu_monitor/`)
   - Settings in `gpu_monitor/settings.py`
   - URL routing in `gpu_monitor/urls.py`
   - Uses django-simpleui for enhanced admin
   - SQLite database in `data/db.sqlite3`

2. **GPU Monitoring App** (`gpu_app/`)
   - `models.py`: GPUInfo model stores GPU state
   - `utils.py`: `get_local_gpu_info()` queries nvidia-smi, `update_gpu_database()` syncs to DB
   - `views.py`: `/api/gpu-status/` endpoint for dashboard
   - `admin.py`: Read-only admin interface

3. **Task Management App** (`task_app/`)
   - `models.py`: Task and TaskLog models
   - `utils.py`: `LocalTaskRunner` executes tasks with CUDA_VISIBLE_DEVICES
   - `views.py`: Dashboard and `/api/task-queue/` endpoint
   - `admin.py`: Full CRUD for tasks

4. **Background Scheduler** (`scheduler.py`)
   - Runs as separate process
   - Updates GPU info every 10 seconds
   - Matches pending tasks with available GPUs
   - Spawns threads to execute tasks
   - Logs to `logs/scheduler.log`

5. **Real-time Dashboard** (`templates/dashboard.html`)
   - Polls `/api/gpu-status/` and `/api/task-queue/` every 5 seconds
   - Displays GPU metrics with progress bars
   - Shows active task queue

### Data Flow

1. **GPU Monitoring**: scheduler.py → `update_gpu_database()` → nvidia-smi → GPUInfo model → API → Dashboard
2. **Task Scheduling**: User creates Task → scheduler detects pending → `find_available_gpus()` → `LocalTaskRunner.execute()` → subprocess with CUDA_VISIBLE_DEVICES → logs
3. **Task Status**: Task status ('pending' → 'running' → 'completed'/'failed') → admin + dashboard

### Key Design Decisions

- **Direct Host Execution**: No Docker, runs directly on host with virtual environment
- **Local Subprocess**: Tasks run via subprocess.Popen with CUDA_VISIBLE_DEVICES
- **Thread-based Scheduler**: Each task in daemon thread; scheduler tracks active threads
- **GPU Allocation**: Checks `is_occupied` flag and process list; supports exclusive/shared mode
- **Logging**: Task stdout/stderr to `logs/tasks/task_{id}_{name}_{timestamp}.log`
- **SQLite**: Simple database, no external DB server required

## Important Implementation Details

### GPU Detection and Allocation

Two mechanisms track GPU availability:

1. **Process-based**: Queries nvidia-smi for running processes
2. **Flag-based**: Sets `is_occupied=True` when task starts, `False` when done

Scheduling logic:
- `exclusive_gpu=True`: GPU must have no processes AND `is_occupied=False`
- `exclusive_gpu=False`: GPU must have enough free memory

### Task Execution Flow

1. Scheduler finds pending task with highest priority
2. `find_available_gpus()` returns GPU indices or None
3. If available: `LocalTaskRunner.execute()` spawns subprocess with `CUDA_VISIBLE_DEVICES=<indices>`
4. Task runs in thread; `wait_for_completion()` blocks until done
5. On completion: update status, free GPUs, log result

### Process Management

- **start.sh**: Starts scheduler with nohup, saves PID to `.scheduler.pid`, then starts Django server
- **stop.sh**: Kills processes by PID file or pkill
- **Systemd**: Manages both services with auto-restart

### Admin Interface

- **GPUInfo**: Read-only, auto-updated by scheduler
- **Task**: Full CRUD, color-coded status badges, duration calculation
- **TaskLog**: Read-only, auto-created during execution

## Common Modifications

### Change Scheduler Update Interval

Edit `scheduler.py` line 107:
```python
scheduler = TaskScheduler(update_interval=10)  # seconds
```

### Change Web Port

Edit `start.sh` and `gpu-monitor-web.service`:
```bash
python manage.py runserver 0.0.0.0:8888  # Change 8888
```

### Add Email Notifications

1. Create `notification/email_notification.py`
2. Import in `task_app/utils.py`
3. Call in `LocalTaskRunner.wait_for_completion()`

### Use Production WSGI Server

Replace Django dev server with gunicorn:
```bash
pip install gunicorn
gunicorn gpu_monitor.wsgi:application --bind 0.0.0.0:8888 --workers 4
```

Update `start.sh` and systemd service accordingly.

## File Structure

```
gpu_tasker/
├── gpu_monitor/          # Django project
│   ├── settings.py       # Configuration
│   └── urls.py           # URL routing
├── gpu_app/              # GPU monitoring
│   ├── models.py         # GPUInfo model
│   ├── utils.py          # nvidia-smi interface
│   ├── views.py          # API endpoints
│   └── admin.py          # Admin config
├── task_app/             # Task management
│   ├── models.py         # Task, TaskLog models
│   ├── utils.py          # LocalTaskRunner
│   ├── views.py          # Dashboard, API
│   └── admin.py          # Admin config
├── templates/
│   └── dashboard.html    # Real-time UI
├── scheduler.py          # Background scheduler
├── manage.py             # Django CLI
├── requirements.txt      # Dependencies
├── deploy.sh             # One-click setup
├── start.sh              # Start platform
├── stop.sh               # Stop platform
├── gpu-monitor-scheduler.service  # Systemd service
└── gpu-monitor-web.service        # Systemd service
```

## Troubleshooting

### Scheduler Not Running

```bash
# Check process
ps aux | grep scheduler.py

# Check PID file
cat .scheduler.pid

# Start manually
source venv/bin/activate
python scheduler.py &
```

### Tasks Stuck in Pending

1. Check scheduler logs: `tail -f logs/scheduler.log`
2. Verify GPUs detected: Admin panel → GPU Information
3. Check GPU availability: Ensure `is_occupied=False`
4. Verify requirements: GPU count and memory must be satisfiable

### Port Already in Use

```bash
# Find process
sudo lsof -i :8888

# Kill process
sudo kill <PID>

# Or change port in start.sh
```

### Virtual Environment Issues

```bash
# Recreate venv
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## API Endpoints

- `GET /api/gpu-status/` - Current GPU status
- `GET /api/task-queue/` - Active tasks (pending + running)
- `GET /admin/` - Django admin
- `GET /` - Dashboard (requires login)

## Security Considerations

- Tasks run with platform user's permissions
- No command validation - users can run arbitrary commands
- No resource limits - tasks can consume all GPU memory
- Admin panel accessible to all authenticated users

For production:
1. Change SECRET_KEY in settings.py
2. Set DEBUG=False
3. Add ALLOWED_HOSTS restriction
4. Use HTTPS with reverse proxy (nginx/Apache)
5. Implement per-user resource quotas
6. Add command whitelist or sandboxing
7. Use gunicorn/uwsgi instead of Django dev server
