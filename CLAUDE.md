# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a simplified GPU monitoring and task management platform designed for single-server deployments with multiple NVIDIA GPUs. It's based on GPUTasker but streamlined for local execution without SSH complexity.

**Key Architecture**: Django web app + background scheduler + SQLite database + Docker deployment

## Development Commands

### Docker-based Development (Recommended)

```bash
# Build and start the platform
docker-compose -f docker-compose.simple.yml up -d

# View logs
docker-compose -f docker-compose.simple.yml logs -f

# Stop the platform
docker-compose -f docker-compose.simple.yml down

# Restart after code changes
docker-compose -f docker-compose.simple.yml restart

# Access container shell
docker exec -it gpu_monitor bash

# Run Django management commands
docker exec gpu_monitor python manage.py <command>

# Create superuser
docker exec -it gpu_monitor python manage.py createsuperuser

# Run migrations
docker exec gpu_monitor python manage.py migrate

# Collect static files
docker exec gpu_monitor python manage.py collectstatic --noinput
```

### Local Development (Without Docker)

```bash
# Install dependencies
pip install -r requirements.txt

# Create directories
mkdir -p data logs logs/tasks static

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Start Django dev server
python manage.py runserver 0.0.0.0:8000

# Start scheduler (in separate terminal)
python scheduler.py
```

### Testing GPU Detection

```bash
# Test nvidia-smi access
docker exec gpu_monitor nvidia-smi

# Test GPU info collection
docker exec gpu_monitor python -c "
import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gpu_monitor.settings')
django.setup()
from gpu_app.utils import get_local_gpu_info
print(get_local_gpu_info())
"

# Check GPU database
docker exec gpu_monitor python manage.py shell -c "
from gpu_app.models import GPUInfo
for gpu in GPUInfo.objects.all():
    print(f'GPU {gpu.index}: {gpu.name} - {gpu.utilization}%')
"
```

## Architecture Overview

### Core Components

1. **Django Web Application** (`gpu_monitor/`)
   - Settings in `gpu_monitor/settings.py`
   - URL routing in `gpu_monitor/urls.py`
   - Uses django-simpleui for enhanced admin interface
   - SQLite database stored in `data/db.sqlite3`

2. **GPU Monitoring App** (`gpu_app/`)
   - `models.py`: GPUInfo model stores GPU state
   - `utils.py`: `get_local_gpu_info()` queries nvidia-smi, `update_gpu_database()` syncs to DB
   - `views.py`: `/api/gpu-status/` endpoint for real-time dashboard
   - `admin.py`: Read-only admin interface for GPU info

3. **Task Management App** (`task_app/`)
   - `models.py`: Task and TaskLog models
   - `utils.py`: `LocalTaskRunner` executes tasks locally with CUDA_VISIBLE_DEVICES
   - `views.py`: Dashboard view and `/api/task-queue/` endpoint
   - `admin.py`: Full CRUD interface for task management

4. **Background Scheduler** (`scheduler.py`)
   - Runs in separate thread/process
   - Updates GPU info every 10 seconds (configurable)
   - Finds pending tasks and matches them with available GPUs
   - Spawns threads to execute tasks via `run_task()`
   - Logs to `logs/scheduler.log`

5. **Real-time Dashboard** (`templates/dashboard.html`)
   - JavaScript polls `/api/gpu-status/` and `/api/task-queue/` every 5 seconds
   - Displays GPU metrics with progress bars
   - Shows active task queue

### Data Flow

1. **GPU Monitoring**: scheduler.py → `update_gpu_database()` → nvidia-smi → GPUInfo model → API → Dashboard
2. **Task Scheduling**: User creates Task in admin → scheduler.py detects pending task → `find_available_gpus()` → `LocalTaskRunner.execute()` → subprocess with CUDA_VISIBLE_DEVICES → logs to file
3. **Task Status**: Task model status field ('pending' → 'running' → 'completed'/'failed') → displayed in admin and dashboard

### Key Design Decisions

- **Local Execution**: Tasks run via subprocess.Popen with CUDA_VISIBLE_DEVICES, not SSH
- **Thread-based Scheduler**: Each task runs in a daemon thread; scheduler tracks active threads
- **GPU Allocation**: `find_available_gpus()` checks `is_occupied` flag and process list; supports exclusive or shared mode
- **Logging**: Task stdout/stderr captured to `logs/tasks/task_{id}_{name}_{timestamp}.log`
- **Database**: SQLite for simplicity (no MariaDB setup required)

## Important Implementation Details

### GPU Detection and Allocation

The platform uses two mechanisms to track GPU availability:

1. **Process-based**: Queries nvidia-smi for running processes (via `get_local_gpu_info()`)
2. **Flag-based**: Sets `is_occupied=True` when task starts, `False` when done

When scheduling tasks:
- `exclusive_gpu=True`: GPU must have no processes AND `is_occupied=False`
- `exclusive_gpu=False`: GPU must have enough free memory

### Task Execution Flow

1. Scheduler finds pending task with highest priority
2. `find_available_gpus()` returns list of GPU indices or None
3. If GPUs available: `LocalTaskRunner.execute()` spawns subprocess with `CUDA_VISIBLE_DEVICES=<indices>`
4. Task runs in thread; `wait_for_completion()` blocks until done
5. On completion: update task status, free GPUs, log result

### Docker Deployment

The `docker-compose.simple.yml` runs a single container that:
- Runs migrations on startup
- Starts scheduler.py in background (`&`)
- Starts Django dev server in foreground
- Mounts `data/` and `logs/` for persistence
- Exposes all GPUs via `deploy.resources.reservations.devices`

### Admin Interface Customization

- **GPUInfo**: Read-only (no add/delete), auto-updated by scheduler
- **Task**: Full CRUD, color-coded status badges, duration calculation
- **TaskLog**: Read-only, auto-created by task execution

## Common Modifications

### Change Scheduler Update Interval

Edit `scheduler.py` line 107:
```python
scheduler = TaskScheduler(update_interval=10)  # Change to desired seconds
```

### Change Web Port

Edit `docker-compose.simple.yml` line 8:
```yaml
ports:
  - "8888:8000"  # Change 8888 to desired port
```

### Add Email Notifications

The original GPUTasker had email notifications. To re-add:
1. Create `notification/email_notification.py` with send functions
2. Import in `task_app/utils.py`
3. Call `send_task_start_email()`, `send_task_finish_email()`, etc. in `LocalTaskRunner`

### Support Multi-Server (Revert to GPUTasker Architecture)

This would require:
1. Add GPUServer model
2. Replace subprocess calls with SSH (paramiko or fabric)
3. Add UserConfig model for SSH credentials
4. Modify `get_local_gpu_info()` to accept host parameter
5. Update scheduler to iterate over servers

## File Structure

```
gpu_tasker/
├── gpu_monitor/          # Django project settings
│   ├── settings.py       # Main configuration
│   └── urls.py           # URL routing
├── gpu_app/              # GPU monitoring
│   ├── models.py         # GPUInfo model
│   ├── utils.py          # nvidia-smi interface
│   ├── views.py          # API endpoints
│   └── admin.py          # Admin config
├── task_app/             # Task management
│   ├── models.py         # Task, TaskLog models
│   ├── utils.py          # LocalTaskRunner, run_task()
│   ├── views.py          # Dashboard, API
│   └── admin.py          # Admin config
├── templates/
│   └── dashboard.html    # Real-time monitoring UI
├── scheduler.py          # Background task scheduler
├── manage.py             # Django CLI
├── requirements.txt      # Python dependencies
├── Dockerfile.simple     # Container image
├── docker-compose.simple.yml  # Deployment config
└── deploy.sh             # One-click setup script
```

## Troubleshooting

### Scheduler Not Running

Check if scheduler process is active:
```bash
docker exec gpu_monitor ps aux | grep scheduler
```

If not running, restart container or run manually:
```bash
docker exec -d gpu_monitor python scheduler.py
```

### Tasks Stuck in Pending

1. Check scheduler logs: `docker exec gpu_monitor tail -f logs/scheduler.log`
2. Verify GPUs detected: Check admin panel → GPU Information
3. Check GPU availability: Ensure `is_occupied=False` and no blocking processes
4. Verify task requirements: GPU count and memory requirements must be satisfiable

### GPU Not Detected in Container

Ensure NVIDIA Container Toolkit is installed and Docker has GPU access:
```bash
docker run --rm --gpus all nvidia/cuda:12.2.0-base-ubuntu22.04 nvidia-smi
```

If fails, reinstall NVIDIA Container Toolkit and restart Docker daemon.

### Database Locked Errors

SQLite doesn't handle high concurrency well. If seeing "database is locked":
1. Reduce scheduler update interval
2. Add retry logic with exponential backoff
3. Consider migrating to PostgreSQL for production

## API Endpoints

- `GET /api/gpu-status/` - Current GPU status (used by dashboard)
- `GET /api/task-queue/` - Active tasks (pending + running)
- `GET /admin/` - Django admin interface
- `GET /` - Dashboard (requires login)

## Security Considerations

- Tasks run with container's user permissions (root by default in Docker)
- No command validation - users can run arbitrary commands
- No resource limits - tasks can consume all GPU memory
- Admin panel accessible to all authenticated users

For production:
1. Change SECRET_KEY in settings.py
2. Set DEBUG=False
3. Add ALLOWED_HOSTS restriction
4. Use HTTPS with reverse proxy
5. Implement per-user resource quotas
6. Add command whitelist or sandboxing
7. Run container as non-root user
