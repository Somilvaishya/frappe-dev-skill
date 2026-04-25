# Deployment & Bench Reference

## Essential Bench Commands

### Site Management
```bash
# Create a new site
bench new-site mysite.localhost \
  --admin-password admin \
  --mariadb-root-password root \
  --install-app erpnext \
  --install-app my_app

# Install app on existing site
bench --site mysite.localhost install-app my_app

# Uninstall app
bench --site mysite.localhost uninstall-app my_app

# Drop a site (DESTRUCTIVE)
bench drop-site mysite.localhost --force --no-backup

# Backup site
bench --site mysite.localhost backup --with-files
bench --site mysite.localhost backup --backup-path /path/to/backup/

# Restore
bench --site mysite.localhost restore /path/to/database.sql.gz \
  --with-private-files /path/to/private.tar.gz \
  --with-public-files /path/to/public.tar.gz

# List apps installed on site
bench --site mysite.localhost list-apps

# Run a command on the site
bench --site mysite.localhost console  # Python REPL
bench --site mysite.localhost execute my_app.utils.some_function
```

### Migrations
```bash
# Migrate all sites (run after any code/schema change)
bench migrate

# Migrate specific site
bench --site mysite.localhost migrate

# Run specific patch
bench --site mysite.localhost run-patch my_app.patches.v1_1.my_patch

# Check pending patches
bench --site mysite.localhost list-patches

# Migrate DocType schema changes to production
# 1. Export in dev: bench --site devsite export-fixtures
# 2. Commit fixtures to git
# 3. In prod: git pull && bench migrate
```

### Development
```bash
# Enable developer mode (writes DocType JSON to disk)
bench set-config -g developer_mode 1

# Clear cache (always after code changes)
bench clear-cache
bench --site mysite.localhost clear-cache

# Rebuild assets
bench build --app my_app
bench build --force  # Force rebuild all

# Watch for JS/CSS changes in dev
bench watch

# Start dev server
bench start

# Execute Python in site context
bench --site mysite.localhost execute "frappe.db.get_all('Sales Order', limit=5)"
```

### App Management
```bash
# Create new app
bench new-app my_app

# Get app from GitHub
bench get-app https://github.com/org/my_app --branch main
bench get-app my_app  # from PyPI if published

# Update apps
bench update --pull                    # Pull all apps from git
bench update --patch                   # Run patches
bench update --build                   # Rebuild assets
bench update                           # All of the above

# Publish app version
# Update version in my_app/__init__.py then:
bench --site mysite.localhost set-config app_version "1.2.0"
```

---

## Production Setup

### Initial Setup
```bash
# Set up production (Nginx + supervisor)
sudo bench setup production frappe_user

# Or with Let's Encrypt SSL
sudo bench setup lets-encrypt mysite.com

# Reload after config changes
sudo supervisorctl reload
sudo nginx -t && sudo nginx -s reload
```

### Multi-Tenancy
```bash
# Add a second site to existing bench
bench new-site site2.example.com --install-app erpnext

# Set up DNS multitenancy (wildcard subdomain)
bench config dns_multitenant on

# Add custom domain to a site
bench setup add-domain mysite.com --site site2.example.com
```

### Scaling
```bash
# Add more worker processes in Procfile or supervisor
# config/supervisor.conf — increase numprocs for workers

# High-memory worker for large jobs
bench set-config -g background_workers 4  # default is 1
bench set-config -g long_job_timeout 3600

# Redis configuration
# config/redis_cache.conf — maxmemory
# config/redis_queue.conf — separate queue instance
```

---

## site_config.json Reference

```json
{
    "db_name": "site_db_name",
    "db_password": "secret",
    "db_host": "localhost",
    "db_port": 3306,
    
    "developer_mode": 0,          // 1 in dev
    "maintenance_mode": 0,        // 1 to show maintenance page
    "pause_scheduler": 0,         // 1 to stop cron jobs
    
    "redis_cache": "redis://localhost:13000",
    "redis_queue": "redis://localhost:11000",
    "redis_socketio": "redis://localhost:12000",
    
    "background_workers": 2,
    "gunicorn_workers": 4,        // Usually 2*cores + 1
    
    "mail_server": "smtp.gmail.com",
    "mail_port": 587,
    "use_tls": 1,
    "mail_login": "user@gmail.com",
    "mail_password": "app_password",
    "auto_email_id": "no-reply@mycompany.com",
    
    "max_file_size": 25000000,    // bytes (25MB)
    
    "limits": {
        "space_usage": {
            "database_size": 1073741824,  // 1GB
            "backup_size": 536870912,     // 512MB
            "files_size": 536870912
        }
    }
}
```

---

## Zero-Downtime Deployment Pattern

```bash
# 1. Pull latest code
cd frappe-bench
git -C apps/my_app pull origin main

# 2. Run migrations (Frappe handles backward-compatible migrations first)
bench --site mysite.localhost migrate

# 3. Rebuild assets
bench build --app my_app

# 4. Reload supervisor gracefully (no downtime)
sudo supervisorctl restart frappe-bench-web:
# Note: workers restart one-by-one automatically

# 5. Verify
bench --site mysite.localhost doctor
```

---

## Scheduler & Background Services Diagnostics

```bash
# Check scheduler status
bench --site mysite.localhost doctor

# Enable/disable scheduler
bench --site mysite.localhost enable-scheduler
bench --site mysite.localhost disable-scheduler

# Check if scheduler is running
bench --site mysite.localhost execute "frappe.utils.scheduler.is_scheduler_disabled()"

# View queued jobs
bench --site mysite.localhost execute \
  "from rq import Queue; from redis import Redis; \
   q = Queue(connection=Redis()); print(q.jobs)"

# View failed jobs
bench --site mysite.localhost execute \
  "from rq import Queue; from redis import Redis; \
   from rq.job import Job; \
   print(frappe.get_all('RQ Job', {'status': 'failed'}, limit=10))"
```

---

## Bench Procfile Services

```
# Typical Procfile
web: bench serve --port 8000
socketio: node apps/frappe/socketio.js
watch: bench watch
schedule: bench schedule
worker_short: bench worker --queue short
worker_default: bench worker --queue default
worker_long: bench worker --queue long
redis_cache: redis-server config/redis_cache.conf
redis_queues: redis-server config/redis_queue.conf
redis_socketio: redis-server config/redis_socketio.conf
```

---

## Common Production Issues

| Issue | Diagnosis | Fix |
|-------|-----------|-----|
| Site down 500 | `cat logs/frappe.log` | Check traceback, usually migration needed |
| Scheduler not running | `bench doctor` | Restart: `supervisorctl restart frappe-bench-schedule:` |
| Assets not loading | Browser 404 on .js | `bench build && supervisorctl restart frappe-bench-web:` |
| DB connection fail | Check error log | Check `db_host`, `db_port` in site_config |
| Slow queries | `frappe.db.sql("SHOW PROCESSLIST")` | Add index via `frappe.db.add_index()` |
| High memory | `ps aux --sort=-%mem` | Reduce `gunicorn_workers`, check for memory leaks |
| Queue full | Check RQ dashboard | Scale workers or fix slow background jobs |
