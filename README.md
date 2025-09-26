# 🚀 SSH/GCloud MCP Server — The DevOps Swiss Army Knife 🛠️

> _“Why click buttons when you can `ssh_execute` and fumble and bumble your way to Cloud Architectured Grace!?”_

Welcome to the **SSH/GCloud MCP Server** —  asynchronous, Python-powered bridge between your local machine and the remote cloud realms of Google Compute Engine (GCE) 
+ any SSH-accessible host. Built for developers, sysadmins, CI/CD pipelines, and anyone who’d rather type than click.

Think of it as **your personal cloud butler**, ready to fetch logs, start instances, deploy apps, or just run `uname -a` on that server in Tokyo — all via structured MCP tools.


---

## ✨ Features at a Glance

✅ **SSH Remote Control**  
→ Connect to any SSH host (key or password auth)  
→ Execute arbitrary shell commands remotely  
→ Get structured JSON responses with exit codes, stdout, stderr — no more guessing!

✅ **Google Cloud Integration**  
→ List, start, and stop GCE instances programmatically  
→ Auto-initialize GCloud client per project  
→ Retrieve instance metadata: IPs, zones, machine types, statuses

✅ **One-Click Deployments**  
→ Deploy apps to App Engine via remote SSH host (perfect for CI runners!)  
→ Traffic shifting included — because blue/green shouldn’t be manual

✅ **MCP-Ready & Async All the Way**  
→ Built for Model Context Protocol servers (think LLM agents, AI devops assistants)  
→ Fully async with `asyncio`, `paramiko`, and Google’s official `compute_v1` client  
→ Tools exposed cleanly — plug into Claude, Cursor, VS Code, or your own agent brain

---

## 🧰 Tools Exposed (aka “What Can I Do?”)

| Tool Name                  | Description                                                                 |
|---------------------------|-----------------------------------------------------------------------------|
| `ssh_connect`             | Establish SSH connection to a remote host                                   |
| `ssh_execute`             | Run a shell command on a connected SSH host → returns structured JSON       |
| `gcloud_list_instances`   | List all GCE instances in a zone                                            |
| `gcloud_start_instance`   | Power on a GCE VM                                                           |
| `gcloud_stop_instance`    | Gracefully shut down a GCE VM                                               |
| `deploy_to_gcloud`        | SSH into a host and deploy an app to App Engine + shift traffic automatically |

Each tool returns clean, parseable output — perfect for chaining in automated workflows or feeding to an LLM agent.

---

## ⚙️ Installation & Setup

### Prerequisites

- Python 3.9+
- `pip`
- Google Cloud SDK authenticated (`gcloud auth login`)
- SSH keys or passwords for target hosts
- Google Cloud Project ID & permissions for Compute Engine API

### Install Dependencies

```bash
pip install paramiko google-cloud-compute mcp-server
```

> 💡 Tip: Use a virtual environment! (`python -m venv venv && source venv/bin/activate`)

### Set Environment (Optional)

You may want to pre-set some env vars:

```bash
export GOOGLE_APPLICATION_CREDENTIALS="path/to/service-account-key.json"
```

---

## 🚦 Quick Start

Run the server:

```bash
python ssh_gcloud_mcp_server.py
```

That’s it. The server will listen on stdio — perfect for piping into/from LLM agents or automation scripts.

Example workflow from an agent:

```json
{
  "tool": "ssh_connect",
  "arguments": {
    "host": "my-dev-server.example.com",
    "username": "deployer",
    "key_path": "~/.ssh/id_rsa_deploy"
  }
}
```

Then:

```json
{
  "tool": "ssh_execute",
  "arguments": {
    "host": "my-dev-server.example.com",
    "command": "df -h /"
  }
}
```

And finally, deploy:

```json
{
  "tool": "deploy_to_gcloud",
  "arguments": {
    "host": "ci-runner.internal",
    "project_id": "my-awesome-project-123",
    "app_path": "/home/deployer/my-app",
    "service_name": "default"
  }
}
```

---

## 🌐 Architecture Overview

```
[ MCP Client (LLM Agent / CLI / IDE) ]
           ↓ stdio
[ SSH/GCloud MCP Server (this script) ]
           ↓
   [ SSHManager ] ↔ Paramiko → Remote Hosts
           ↓
 [ GCloudManager ] ↔ Google Cloud API → GCE Instances
```

Stateful SSH connections are cached per-host. GCloud clients are lazily initialized per-project.

---

## 🔐 Security Notes
🔒 **SSH Keys > Passwords** — Always prefer key-based auth. Passwords are supported but discouraged.
🔐 **Least Privilege** — Ensure service accounts and SSH users have minimal required permissions.
🚫 **Don’t expose this server publicly** — It’s designed for localhost/stdio use within trusted environments (e.g., inside an agent runtime).
🧼 **Connections aren’t auto-closed** — Consider adding a `ssh_disconnect` tool if long-running sessions become an issue.

---

## 🤖 Example: AI DevOps Agent Workflow
Imagine prompting your AI assistant:

> “Check disk space on prod-web-01, then restart the ‘api-cache’ GCE instance in us-central1-a under project ‘acme-prod’.”

Your agent might call:
1. `ssh_connect(host="prod-web-01.acme.internal", username="admin", key_path="~/.ssh/acme")`
2. `ssh_execute(host="prod-web-01.acme.internal", command="df -h /var/lib/cache")`
3. `gcloud_stop_instance(project_id="acme-prod", instance_name="api-cache", zone="us-central1-a")`
4. `gcloud_start_instance(project_id="acme-prod", instance_name="api-cache", zone="us-central1-a")`

All without you touching a terminal. Magic? No. **Automation.**

---

## 🐞 Troubleshooting

❌ **“No connection to host”** → Did you call `ssh_connect` first?  
❌ **Auth failures** → Double-check paths to private keys or GCloud credentials  
❌ **Zone errors** → Default is `us-central1-a` — override with `zone` parameter  
❌ **JSON parsing errors** → Tools return strings — parse with `json.loads()` on client side

---

## 🧪 Testing Locally?

Spin up a local SSH server with Docker for testing:

```bash
docker run -d -p 2222:22 --name test-ssh \
  -e ROOT_PASSWORD=secret \
  linuxserver/openssh-server
```

Then connect via:

```json
{
  "tool": "ssh_connect",
  "arguments": {
    "host": "localhost",
    "port": 2222,
    "username": "root",
    "password": "secret"
  }
}
```

---

## 📈 Future Ideas / Contributions Welcome!

- Add `ssh_upload_file` / `ssh_download_file`
- Support SSH tunnels or port forwarding
- Add `gcloud_create_instance` / `delete_instance`
- Health check tool: `ping_instance` or `check_ssh_health`
- Config file support for pre-defined hosts/projects
- Auto-reconnect logic for dropped SSH sessions

PRs happily accepted! 🎉

---

## 📜 License
MIT — Go forth and automate responsibly.

---

## 💬 Final Words

This isn’t just another script. It’s a **bridge between human intent and machine action** — whether you’re an AI model reasoning over infrastructure, a tired engineer at 2 AM, or a CI pipeline deploying the next unicorn startup.
So go ahead. Connect. Execute. Deploy. Conquer.

> _“The cloud is yours. Command it.”_

—

💻 Made with ❤️ and `asyncio.sleep(0)`  
🔗 Part of the **Model Context Protocol** ecosystem  
🌐 Works with Claude, Cursor, Continue.dev, and any MCP-compatible client

---

> ⚡ **Pro Tip**: Pipe this into an LLM agent and say:  
> *“If disk usage > 90% on any web server, restart the cache instance and notify me.”*  
> ...and watch the future unfold.

---

**Author**: (the brilliant automator)  
**Repo**: Your private infra repo   
**Version**: 1.0 “First Flight” ✈️
