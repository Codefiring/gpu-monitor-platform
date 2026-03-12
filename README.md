# GPU Monitor Platform

A simplified, single-server GPU monitoring and task management platform for managing GPU workloads on Ubuntu servers with multiple GPUs.

## Features

- 🖥️ **Real-time GPU Monitoring**: Live dashboard showing GPU utilization, memory, temperature, and power
- 📋 **Task Queue Management**: Create and manage GPU tasks with automatic scheduling
- 👥 **Multi-user Support**: Each user can create and manage their own tasks
- 🎯 **Smart Scheduling**: Automatically assigns tasks to available GPUs based on requirements
- 📊 **Visual Dashboard**: Beautiful web interface with real-time updates
- 🔒 **User Authentication**: Integrated with Django admin for user management
- 📝 **Task Logging**: Complete logs for each task execution
- ⚡ **Simple Deployment**: No Docker required, runs directly on host

## Requirements

- Ubuntu 20.04+ (or similar Linux distribution)
- NVIDIA GPU(s) with drivers installed
- Python 3.8+

## Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/Codefiring/gpu-monitor-platform.git
cd gpu-monitor-platform
```

### 2. Deploy

```bash
./deploy.sh
```

The script will:
- Check for NVIDIA drivers and Python
- Create virtual environment
- Install dependencies
- Initialize database
- Create admin user
- Optionally install systemd services for auto-start

### 3. Start Platform

**Option A: Manual Start**
```bash
./start.sh
```

**Option B: Systemd (if installed during deployment)**
```bash
sudo systemctl start gpu-monitor-scheduler gpu-monitor-web
```

### 4. Access

- **Dashboard**: http://localhost:8888/
- **Admin Panel**: http://localhost:8888/admin/

## Usage

### Creating Tasks

1. Log in to admin panel at http://localhost:8888/admin/
2. Navigate to "GPU Tasks" → "Add GPU Task"
3. Fill in task details:
   - **Name**: Task identifier
   - **User**: Task owner
   - **Working Directory**: Execution directory
   - **Command**: Command to run (e.g., `python train.py`)
   - **GPU Count**: Number of GPUs required
   - **Memory Required**: Minimum GPU memory (MB)
   - **Exclusive GPU**: Require GPUs with no other processes
   - **Priority**: Higher = scheduled first

### Monitoring

- **Dashboard**: Real-time GPU status and active tasks
- **Admin Panel**: Full task management and logs

## Management

### Manual Control

```bash
# Start platform
./start.sh

# Stop platform
./stop.sh

# View logs
tail -f logs/scheduler.log
tail -f logs/tasks/*.log
```

### Systemd Control

```bash
# Status
sudo systemctl status gpu-monitor-scheduler gpu-monitor-web

# Start/Stop/Restart
sudo systemctl start gpu-monitor-web
sudo systemctl stop gpu-monitor-scheduler
sudo systemctl restart gpu-monitor-web

# View logs
sudo journalctl -u gpu-monitor-scheduler -f
sudo journalctl -u gpu-monitor-web -f

# Disable auto-start
sudo systemctl disable gpu-monitor-scheduler gpu-monitor-web
```

## Architecture

- **Django Web App**: Admin interface and REST API
- **Task Scheduler**: Background process monitoring and scheduling tasks
- **GPU Monitor**: Queries nvidia-smi for real-time GPU status
- **SQLite Database**: Stores tasks, logs, and GPU information

### How It Works

1. Scheduler continuously queries nvidia-smi for GPU status
2. Pending tasks are matched with available GPUs
3. Tasks execute locally with CUDA_VISIBLE_DEVICES set
4. All output captured in log files
5. Status updates in real-time

## Configuration

### Change Port

Edit `start.sh` and systemd service files:
```bash
python manage.py runserver 0.0.0.0:8888  # Change 8888
```

### Scheduler Interval

Edit `scheduler.py`:
```python
scheduler = TaskScheduler(update_interval=10)  # seconds
```

## Troubleshooting

### GPU Not Detected

```bash
# Check NVIDIA drivers
nvidia-smi

# Check Python can access GPUs
source venv/bin/activate
python -c "from gpu_app.utils import get_local_gpu_info; print(get_local_gpu_info())"
```

### Tasks Not Running

1. Check scheduler is running: `ps aux | grep scheduler.py`
2. Check logs: `tail -f logs/scheduler.log`
3. Verify GPUs available in admin panel

### Port Already in Use

```bash
# Find process using port 8888
sudo lsof -i :8888

# Kill process
sudo kill <PID>
```

## Security Notes

- Change SECRET_KEY in `gpu_monitor/settings.py` for production
- Use strong admin passwords
- Consider using nginx/Apache as reverse proxy with HTTPS
- Tasks run with the user's permissions - review commands before execution

## License

MIT License

## Acknowledgments

Based on [GPUTasker](https://github.com/cnstark/gputasker) by cnstark
