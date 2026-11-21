# Staging server: step by step

Goal: a real server on the internet, with HTTPS, running exactly what production will run, where you can test
with real phones. Use the same steps later for production (a second server and domain).

A small VPS (1 to 2 GB RAM, 1 to 2 vCPU, Ubuntu 24.04) is plenty for a pilot with a few families.

## 1. Choose a server
Any VPS provider works (DigitalOcean, Vultr, Linode/Akamai, Hetzner, AWS Lightsail ...). Pick a region close to
your users; for Bangladesh that usually means Singapore or Mumbai where offered. Check which payment methods
the provider accepts before you sign up.

## 2. Make an SSH key (on your Windows PC, PowerShell)
    ssh-keygen -t ed25519 -C "guardian"
    type $env:USERPROFILE\.ssh\id_ed25519.pub
Copy the printed line. Paste it into the provider's "SSH keys" page, then create the server (Ubuntu 24.04) with
that key selected. Note the server's public IP address.

## 3. Domain name
You need a domain name for HTTPS. Buy a cheap one (staging can use a subdomain such as `staging.yourdomain.com`),
or use a free dynamic-DNS name. Create a DNS **A record** pointing the name to the server's IP, and wait a few
minutes until `nslookup staging.yourdomain.com` shows that IP.

## 4. Upload the project and prepare the server
From PowerShell in the folder that contains `ParentalGuardian.zip`:

    scp ParentalGuardian.zip root@SERVER_IP:/root/
    ssh root@SERVER_IP

On the server:

    apt-get update && apt-get install -y unzip
    unzip ParentalGuardian.zip
    bash ParentalGuardian/deployment/setup-server.sh

The script updates the system, enables a firewall (ports 22, 80, 443 only), automatic security updates and
fail2ban, installs Docker, creates a `guardian` user, makes SSH key-only, and copies the project to
`/home/guardian/app`. Keep your first SSH window open and test the next step in a second window.

## 5. Configure and start
    ssh guardian@SERVER_IP
    cd ~/app/deployment
    cp .env.example .env
    nano .env

Set `DOMAIN`, `ENVIRONMENT=staging`, and put the output of `openssl rand -hex 32` in `DB_PASSWORD` and again,
separately, in `SECRET_KEY`. Then:

    docker compose up -d --build
    docker compose ps
    docker compose logs -f backend      # Ctrl+C to leave

The first start takes a few minutes (builds the backend, creates the database tables, gets the HTTPS
certificate). Verify:

    curl https://staging.yourdomain.com/api/health/ready

Expected: `{"status":"ok","database":"ok"}`. Then open `https://staging.yourdomain.com` in a browser and create an account.
If the certificate fails, the usual causes are DNS not pointing at the server yet, or ports 80/443 blocked
by the provider's own firewall (look for a "firewall" or "security group" setting in the provider panel).

## 6. Backups, cleanup and monitoring
    crontab -e
and paste the lines from `crontab.example` (adjust paths if you changed the user). Then run a first backup by hand
and check it exists:

    bash ~/app/deployment/backup.sh && ls ~/app/deployment/backups

Set up alerts as described in `MONITORING.md` (10 minutes). Test a restore once on a spare database before you
trust the backups, and copy the `backups/` folder off the server regularly (for example to your PC with `scp`).

## 7. Point the Android apps at staging
Both apps have a `staging` build type. In `app/build.gradle.kts` of `child-android` and `parent-android`, change
`https://staging.example.com/api` to `https://staging.yourdomain.com/api`, then in Android Studio choose
Build, Select Build Variant, `staging`, and run on a real phone. Debug builds keep talking to your PC.

## 8. What to test on staging
- [ ] Register, log in, add a child, pair a real phone, see location/battery/usage after a sync
- [ ] Leave the phone idle with the screen off for 3 hours: data still arrives (see the note on phone brands in `child-android/README.md`)
- [ ] Airplane mode for an hour, then back online: queued points arrive
- [ ] Switch the phone off: the dashboard warns "No update from the phone" after 2 hours
- [ ] Disconnect the phone from the dashboard: the child app returns to the pairing screen
- [ ] Reboot the phone: the notification returns and syncing resumes
- [ ] `docker compose restart backend` and a full server reboot: everything comes back by itself
- [ ] A backup restores into a fresh database

## Updating, rolling back, removing
    # update: copy the new project files to ~/app (keep deployment/.env and backups/), then
    bash ~/app/deployment/backup.sh
    cd ~/app/deployment && docker compose up -d --build
    docker compose logs --tail 100 backend      # migrations run here

    # roll back code: put the previous files back and run docker compose up -d --build again.
    # roll back the database only from a backup, so always back up before updating.

    # remove everything (DELETES THE DATABASE): docker compose down -v

## Troubleshooting
| Symptom | Check |
|---|---|
| Browser shows a certificate error | DNS A record, ports 80/443 open at the provider, `docker compose logs web` |
| `502 Bad Gateway` on /api | `docker compose ps` (is backend "healthy"?), `docker compose logs backend` |
| Backend keeps restarting | `.env` values missing (`DB_PASSWORD`, `SECRET_KEY`, `DOMAIN`), see the logs |
| Apps say "Can't reach the server" | `BASE_URL` in the build variant, must be `https://DOMAIN/api` |
| Child data stops arriving | Phone brand battery settings, parent revoked the device, see MONITORING.md |

## Updating from GitHub instead of copying files
Once the project is in a **private** GitHub repository, the server can pull updates itself.
1. On the server (as `guardian`): `ssh-keygen -t ed25519 -f ~/.ssh/github_deploy -N ""` then `cat ~/.ssh/github_deploy.pub`.
2. On GitHub: repository, Settings, Deploy keys, Add deploy key, paste it (leave "Allow write access" off).
3. Tell SSH to use it: `nano ~/.ssh/config` and add

       Host github.com
         IdentityFile ~/.ssh/github_deploy
         IdentitiesOnly yes

4. Replace the copied project with a clone, keeping your settings and backups:

       mv ~/app ~/app-old
       git clone git@github.com:YOUR_USERNAME/ParentalGuardian.git ~/app
       cp ~/app-old/deployment/.env ~/app/deployment/.env
       cp -r ~/app-old/deployment/backups ~/app/deployment/backups 2>/dev/null || true

5. From then on, to update: `cd ~/app && git pull && bash deployment/backup.sh && cd deployment && docker compose up -d --build`
