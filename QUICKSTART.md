# Quick Start Guide

## GPU Monitor Platform - Quick Start

### Prerequisites

```bash
# Check NVIDIA GPU
nvidia-smi

# Check Python 3
python3 --version
```

### Installation (2 minutes)

```bash
# 1. Clone repository
git clone https://github.com/Codefiring/gpu-monitor-platform.git
cd gpu-monitor-platform

# 2. Run deployment
./deploy.sh

# 3. Follow prompts to create admin user
```

### Start Platform

```bash
./start.sh
```

Platform will be available at:
- Dashboard: http://localhost:8888/
- Admin: http://localhost:8888/admin/

### Create First Task

1. Login to admin panel
2. Go to "GPU Tasks" → "Add GPU Task"
3. Example:
   ```
   Name: Test Task
   User: [your username]
   Working Directory: /tmp
   Command: nvidia-smi && sleep 30
   GPU Count: 1
   Exclusive GPU: Yes
   Status: pending
   ```
4. Save and watch it run on the dashboard

### View Logs

```bash
# Scheduler logs
tail -f logs/scheduler.log

# Task logs
ls logs/tasks/
tail -f logs/tasks/task_*.log
```

### Stop Platform

```bash
./stop.sh
```

### Common Commands

```bash
# Start
./start.sh

# Stop
./stop.sh

# Check status
ps aux | grep -E "scheduler.py|manage.py runserver"

# View GPU status
source venv/bin/activate
python manage.py shell -c "from gpu_app.models import GPUInfo; [print(f'GPU {g.index}: {g.utilization}%') for g in GPUInfo.objects.all()]"
```

### Troubleshooting

**Can't access http://localhost:8888/**
```bash
# Check if running
ps aux | grep "manage.py runserver"

# Check logs
tail logs/scheduler.log

# Restart
./stop.sh && ./start.sh
```

**Tasks not running**
```bash
# Check scheduler
ps aux | grep scheduler.py
tail -f logs/scheduler.log

# Verify GPU available
nvidia-smi
```

**GPU not detected**
```bash
# Test nvidia-smi
nvidia-smi

# Test in Python
source venv/bin/activate
python -c "from gpu_app.utils import get_local_gpu_info; print(get_local_gpu_info())"
```

### Systemd Auto-start

If you installed systemd services during deployment:

**User-level (no sudo):**
```bash
# Status
systemctl --user status gpu-monitor-scheduler gpu-monitor-web

# Restart
systemctl --user restart gpu-monitor-web

# View logs
journalctl --user -u gpu-monitor-scheduler -f
```

**System-level (requires sudo):**
```bash
# Status
sudo systemctl status gpu-monitor-scheduler gpu-monitor-web

# Restart
sudo systemctl restart gpu-monitor-web

# View logs
sudo journalctl -u gpu-monitor-scheduler -f
```

### Next Steps

- Add more users in admin panel
- Create tasks for your workloads
- Monitor GPU usage on dashboard
- Check task logs for debugging
