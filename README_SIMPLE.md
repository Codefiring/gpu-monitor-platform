# GPU Monitor Platform

A simplified, single-server GPU monitoring and task management platform. Perfect for managing GPU workloads on a single Ubuntu server with multiple GPUs.

## Features

- 🖥️ **Real-time GPU Monitoring**: Live dashboard showing GPU utilization, memory, temperature, and power
- 📋 **Task Queue Management**: Create and manage GPU tasks with automatic scheduling
- 👥 **Multi-user Support**: Each user can create and manage their own tasks
- 🎯 **Smart Scheduling**: Automatically assigns tasks to available GPUs based on requirements
- 📊 **Visual Dashboard**: Beautiful web interface with real-time updates
- 🔒 **User Authentication**: Integrated with Django admin for user management
- 📝 **Task Logging**: Complete logs for each task execution
- ⚡ **One-Click Deployment**: Simple deployment script for quick setup

## Requirements

- Ubuntu 20.04+ (or similar Linux distribution)
- NVIDIA GPU(s) with drivers installed
- Docker and Docker Compose
- NVIDIA Container Toolkit

## Quick Start

### 1. Clone or Download

```bash
cd /path/to/gpu_tasker
```

### 2. One-Click Deploy

```bash
./deploy.sh
```

The script will:
- Check for required dependencies (Docker, NVIDIA drivers, etc.)
- Install missing components
- Build the Docker image
- Start the services
- Guide you through creating an admin user

### 3. Access the Platform

- **Dashboard**: http://localhost:8888/
- **Admin Panel**: http://localhost:8888/admin/

## Manual Deployment

If you prefer manual deployment:

```bash
# Create directories
mkdir -p data logs logs/tasks static

# Build Docker image
docker build -f Dockerfile.simple -t gpu-monitor:latest .

# Start services
docker-compose -f docker-compose.simple.yml up -d

# Create admin user
docker exec -it gpu_monitor python manage.py createsuperuser
```

## Usage

### Creating Users

1. Go to http://localhost:8888/admin/
2. Log in with your admin credentials
3. Navigate to "Users" and click "Add User"
4. Create users for each person who will use the platform

### Creating Tasks

1. Log in to the admin panel
2. Navigate to "GPU Tasks"
3. Click "Add GPU Task"
4. Fill in the task details:
   - **Name**: Task identifier
   - **User**: Select the user who owns this task
   - **Working Directory**: Where the command will be executed
   - **Command**: The command to run (e.g., `python train.py`)
   - **GPU Count**: Number of GPUs required
   - **Memory Required**: Minimum GPU memory needed (MB)
   - **Exclusive GPU**: Whether to require GPUs with no other processes
   - **Priority**: Higher numbers get scheduled first

### Monitoring

- **Dashboard**: View real-time GPU status and active tasks
- **Admin Panel**: Manage tasks, view logs, and check task history

## Architecture

### Components

- **Django Web Application**: Admin interface and API
- **Task Scheduler**: Background process that monitors and schedules tasks
- **GPU Monitor**: Collects GPU information using nvidia-smi
- **SQLite Database**: Stores tasks, logs, and GPU information

### How It Works

1. **GPU Monitoring**: The scheduler continuously queries nvidia-smi for GPU status
2. **Task Scheduling**: Pending tasks are matched with available GPUs based on requirements
3. **Task Execution**: Tasks run locally with CUDA_VISIBLE_DEVICES set appropriately
4. **Logging**: All task output is captured in log files
5. **Status Updates**: Task status is updated in real-time

## Configuration

### Environment Variables

Edit `docker-compose.simple.yml` to customize:

```yaml
environment:
  - DEBUG=False
  - SECRET_KEY=your-secret-key-here
```

### Port Configuration

Change the port mapping in `docker-compose.simple.yml`:

```yaml
ports:
  - "8888:8000"  # Change 8888 to your preferred port
```

### Scheduler Interval

Edit `scheduler.py` to change the update interval:

```python
scheduler = TaskScheduler(update_interval=10)  # seconds
```

## Differences from Original GPUTasker

This simplified version differs from the original gputasker:

| Feature | Original GPUTasker | This Version |
|---------|-------------------|--------------|
| **Deployment** | Multi-server cluster | Single server |
| **Connection** | SSH to remote nodes | Local execution |
| **Database** | MariaDB | SQLite |
| **Complexity** | Higher | Lower |
| **Setup Time** | ~30 minutes | ~5 minutes |
| **Use Case** | GPU clusters | Single server |

## Management Commands

### View Logs

```bash
# All logs
docker-compose -f docker-compose.simple.yml logs -f

# Scheduler logs only
docker exec gpu_monitor tail -f logs/scheduler.log

# Task logs
ls logs/tasks/
```

### Stop Platform

```bash
docker-compose -f docker-compose.simple.yml down
```

### Restart Platform

```bash
docker-compose -f docker-compose.simple.yml restart
```

### Backup Database

```bash
cp data/db.sqlite3 data/db.sqlite3.backup
```

### Update Platform

```bash
# Pull latest changes
git pull

# Rebuild and restart
docker-compose -f docker-compose.simple.yml down
docker build -f Dockerfile.simple -t gpu-monitor:latest .
docker-compose -f docker-compose.simple.yml up -d
```

## Troubleshooting

### GPU Not Detected

```bash
# Check NVIDIA drivers
nvidia-smi

# Check Docker GPU access
docker run --rm --gpus all nvidia/cuda:12.2.0-base-ubuntu22.04 nvidia-smi
```

### Container Won't Start

```bash
# Check logs
docker-compose -f docker-compose.simple.yml logs

# Check if port is in use
sudo lsof -i :8888
```

### Tasks Not Running

1. Check scheduler logs: `docker exec gpu_monitor tail -f logs/scheduler.log`
2. Verify GPUs are available in admin panel
3. Check task status and logs in admin panel

## Security Notes

- Change the default SECRET_KEY in production
- Use strong passwords for admin users
- Consider using HTTPS with a reverse proxy (nginx/tracd)
- Restrict access to the admin panel
- Review task commands before execution

## Contributing

This is a simplified version based on [GPUTasker](https://github.com/cnstark/gputasker).

## License

MIT License - See LICENSE file for details

## Support

For issues and questions:
- Check the troubleshooting section
- Review logs for error messages
- Open an issue on GitHub

## Acknowledgments

Based on [GPUTasker](https://github.com/cnstark/gputasker) by cnstark
