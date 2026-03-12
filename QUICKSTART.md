# Quick Start Guide

## GPU Monitor Platform - Quick Start

### Prerequisites Check

```bash
# Check NVIDIA GPU
nvidia-smi

# Check Docker
docker --version

# Check Docker Compose
docker-compose --version
```

### Installation (5 minutes)

```bash
# 1. Navigate to the project directory
cd /home/cyberic/Projects/gpu-monitor-platform/gpu_tasker

# 2. Run the deployment script
./deploy.sh

# 3. Follow the prompts to create an admin user
```

### First Login

1. Open browser: http://localhost:8888/admin/
2. Login with your admin credentials
3. Create additional users if needed

### Create Your First Task

1. In admin panel, go to "GPU Tasks"
2. Click "Add GPU Task"
3. Example configuration:
   ```
   Name: Test Task
   User: [your username]
   Working Directory: /tmp
   Command: nvidia-smi && sleep 30
   GPU Count: 1
   Exclusive GPU: Yes
   Status: pending
   ```
4. Click "Save"

### Monitor Execution

1. Dashboard: http://localhost:8888/
2. Watch GPU status update in real-time
3. See your task in the queue
4. Task will automatically start when GPU is available

### View Task Logs

1. In admin panel, go to "GPU Tasks"
2. Click on your task
3. Check the "Log File" field for the path
4. Or check in: `logs/tasks/`

### Common Commands

```bash
# View all logs
docker-compose -f docker-compose.simple.yml logs -f

# Stop platform
docker-compose -f docker-compose.simple.yml down

# Restart platform
docker-compose -f docker-compose.simple.yml restart

# Check GPU status
docker exec gpu_monitor python -c "
import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gpu_monitor.settings')
django.setup()
from gpu_app.utils import get_local_gpu_info
print(get_local_gpu_info())
"
```

### Troubleshooting

**Problem**: Can't access http://localhost:8888/

**Solution**:
```bash
# Check if container is running
docker ps | grep gpu_monitor

# Check logs
docker logs gpu_monitor

# Restart
docker-compose -f docker-compose.simple.yml restart
```

**Problem**: Tasks not running

**Solution**:
1. Check scheduler logs: `docker exec gpu_monitor tail -f logs/scheduler.log`
2. Verify GPU is available in admin panel
3. Check task status is "pending"

**Problem**: GPU not detected

**Solution**:
```bash
# Test GPU access in container
docker exec gpu_monitor nvidia-smi

# If fails, check NVIDIA Container Toolkit
sudo systemctl restart docker
```

### Next Steps

- Add more users in admin panel
- Create tasks for your workloads
- Monitor GPU usage on dashboard
- Check task logs for debugging

### Support

- Check README_SIMPLE.md for detailed documentation
- Review logs for error messages
- Ensure all prerequisites are installed
