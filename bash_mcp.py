#!/usr/bin/env python3
"""
Bash Shell Guru MCP Server - Expert command line and scripting assistant
"""

import asyncio
import subprocess
import json
import os
import shlex
from typing import Any, Dict, List, Optional
from pathlib import Path

from mcp.server import Server
from mcp.types import Tool, TextContent

# Initialize the MCP Server
server = Server("bash-guru-mcp")

# Store command history for context
command_history: List[Dict[str, Any]] = []
MAX_HISTORY = 50

class BashGuru:
    """Expert bash and command line assistant"""
    
    @staticmethod
    async def execute_command(command: str, 
                             working_dir: Optional[str] = None,
                             timeout: Optional[int] = 30) -> Dict[str, Any]:
        """Execute a shell command with proper error handling"""
        try:
            # Store in history
            if len(command_history) >= MAX_HISTORY:
                command_history.pop(0)
            
            # Use shell=True carefully - for trusted input only
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=working_dir or os.getcwd(),
                env={**os.environ, 'LC_ALL': 'C', 'LANG': 'C'}  # Performance optimization
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), 
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                return {
                    "command": command,
                    "error": f"Command timed out after {timeout} seconds",
                    "success": False
                }
            
            result = {
                "command": command,
                "stdout": stdout.decode('utf-8', errors='replace'),
                "stderr": stderr.decode('utf-8', errors='replace'),
                "exit_code": process.returncode,
                "success": process.returncode == 0,
                "working_dir": working_dir or os.getcwd()
            }
            
            command_history.append(result)
            return result
            
        except Exception as e:
            return {
                "command": command,
                "error": str(e),
                "success": False
            }
    
    @staticmethod
    def get_bash_tip(topic: str) -> str:
        """Provide expert bash tips based on the extensive knowledge base"""
        tips = {
            "performance": """
🚀 Bash Performance Tips:
• Disable Unicode for speed: export LC_ALL=C LANG=C
• Use built-ins over external commands: ${var##*/} instead of basename
• Use read with timeout as sleep alternative: read -t 0.1 <> <(:) 
• Prefer [[ ]] over [ ] for conditionals (faster)
• Use ((...)) for arithmetic instead of expr
""",
            "arrays": """
📚 Bash Array Mastery:
• Reverse array: shopt -s extdebug; f()(printf '%s\\n' "${BASH_ARGV[@]}"); f "$@"
• Random element: "${arr[RANDOM % ${#arr[@]}]}"
• Remove duplicates: declare -A tmp; for i in "${arr[@]}"; do tmp["$i"]=1; done; echo "${!tmp[@]}"
• Cycle through: arr[${i:=0}]; ((i=i>=${#arr[@]}-1?0:++i))
""",
            "strings": """
✂️ String Manipulation Excellence:
• Uppercase: ${var^^}  |  Lowercase: ${var,,}  |  Toggle case: ${var~~}
• Trim whitespace: ${var//[[:space:]]/}
• URL encode: printf '%%%02X' "'$char" for special chars
• Strip pattern: ${var##pattern} (from start), ${var%%pattern} (from end)
""",
            "loops": """
🔄 Loop Optimization:
• Compact for: for((;i++<10;)){ echo "$i";}
• Infinite loop: for((;;)){ echo hi;}
• Read file: while IFS= read -r line; do ...; done < file
• Brace expansion: {1..100}, {a..z}, {01..100} (zero-padded)
""",
            "files": """
📁 File Operations:
• Create empty: >file (shortest) or :>file
• Read to string: file_data=$(<"file")
• Read to array: mapfile -t arr < "file" (Bash 4+)
• Count files: count() { printf '%s\\n' "$#"; }; count /path/*
""",
            "best_practices": """
✨ Best Practices:
• Shebang: #!/usr/bin/env bash (not #!/bin/bash)
• Command substitution: $(cmd) not \`cmd\`
• Functions: name() { ... } not function name() { ... }
• Quote variables: "$var" not $var
• Check if command exists: type -p cmd &>/dev/null
""",
            "shortcuts": """
⚡ Powerful Shortcuts:
• Last command: !!
• Last argument: !$
• Parameter expansion: ${var:-default} (use default if unset)
• Quick backup: cp file{,.bak}
• Previous directory: cd -
• Process substitution: diff <(cmd1) <(cmd2)
"""
        }
        
        return tips.get(topic, f"Topic '{topic}' not found. Available: " + ", ".join(tips.keys()))

# Tool definitions

@server.tool()
async def shell_execute(
    command: str,
    working_dir: Optional[str] = None,
    timeout: Optional[int] = 30
) -> str:
    """
    Execute a shell command in bash
    
    Args:
        command: The bash command to execute
        working_dir: Optional working directory
        timeout: Command timeout in seconds (default: 30)
    
    Returns:
        JSON with command output, error, and exit code
    """
    result = await BashGuru.execute_command(command, working_dir, timeout)
    return json.dumps(result, indent=2)


@server.tool()
async def shell_script(
    script: str,
    working_dir: Optional[str] = None,
    timeout: Optional[int] = 60
) -> str:
    """
    Execute a multi-line bash script
    
    Args:
        script: Multi-line bash script
        working_dir: Optional working directory  
        timeout: Script timeout in seconds (default: 60)
    
    Returns:
        JSON with script output
    """
    # Save script to temp file for better error reporting
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
        f.write("#!/usr/bin/env bash\nset -euo pipefail\n")  # Safe defaults
        f.write(script)
        script_path = f.name
    
    try:
        os.chmod(script_path, 0o755)
        result = await BashGuru.execute_command(f"bash {script_path}", working_dir, timeout)
        return json.dumps(result, indent=2)
    finally:
        os.unlink(script_path)


@server.tool()
async def bash_tip(topic: str = "best_practices") -> str:
    """
    Get expert bash tips and tricks
    
    Args:
        topic: Topic for tips (performance, arrays, strings, loops, files, best_practices, shortcuts)
    
    Returns:
        Expert tips on the requested topic
    """
    return BashGuru.get_bash_tip(topic)


@server.tool()
async def explain_command(command: str) -> str:
    """
    Explain what a bash command does
    
    Args:
        command: The command to explain
    
    Returns:
        Detailed explanation of the command
    """
    # Use man pages and help
    explanations = []
    
    # Try to get the base command
    parts = shlex.split(command)
    if not parts:
        return "Invalid command"
    
    base_cmd = parts[0]
    
    # Check if it's a builtin
    builtin_check = await BashGuru.execute_command(f"type -t {base_cmd}")
    
    if builtin_check['success']:
        cmd_type = builtin_check['stdout'].strip()
        explanations.append(f"Command type: {cmd_type}")
        
        if cmd_type == "builtin":
            help_result = await BashGuru.execute_command(f"help {base_cmd} 2>/dev/null | head -20")
            if help_result['success']:
                explanations.append(f"Builtin help:\n{help_result['stdout']}")
        else:
            # Try man page
            man_result = await BashGuru.execute_command(f"man {base_cmd} 2>/dev/null | head -30")
            if man_result['success']:
                explanations.append(f"Man page excerpt:\n{man_result['stdout']}")
    
    # Analyze the full command
    explanations.append(f"\nCommand breakdown:")
    explanations.append(f"• Base command: {base_cmd}")
    if len(parts) > 1:
        explanations.append(f"• Arguments: {' '.join(parts[1:])}")
    
    return "\n".join(explanations)


@server.tool()
async def shell_history(last_n: int = 10) -> str:
    """
    Get recent command history from this session
    
    Args:
        last_n: Number of recent commands to show
    
    Returns:
        Recent command history with results
    """
    recent = command_history[-last_n:] if len(command_history) > last_n else command_history
    
    history_output = []
    for i, cmd in enumerate(recent, 1):
        status = "✓" if cmd.get('success') else "✗"
        history_output.append(f"{i}. [{status}] {cmd.get('command', 'Unknown')}")
        if not cmd.get('success') and cmd.get('stderr'):
            history_output.append(f"   Error: {cmd['stderr'][:100]}...")
    
    return "\n".join(history_output) if history_output else "No command history yet"


@server.tool()
async def create_script(
    purpose: str,
    filename: Optional[str] = None,
    make_executable: bool = True
) -> str:
    """
    Generate a bash script for a specific purpose
    
    Args:
        purpose: Description of what the script should do
        filename: Optional filename to save the script
        make_executable: Whether to make the script executable
    
    Returns:
        Generated bash script with best practices
    """
    # Generate a template based on purpose
    templates = {
        "backup": """#!/usr/bin/env bash
set -euo pipefail  # Exit on error, undefined variables, pipe failures
IFS=$'\\n\\t'      # Set Internal Field Separator

# Backup script with rotation
SOURCE_DIR="${1:-$HOME}"
BACKUP_DIR="${2:-/backup}"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="backup_${DATE}.tar.gz"

# Create backup
tar -czf "${BACKUP_DIR}/${BACKUP_NAME}" "${SOURCE_DIR}" 2>/dev/null || {
    echo "Backup failed" >&2
    exit 1
}

# Rotate old backups (keep last 5)
ls -t "${BACKUP_DIR}"/backup_*.tar.gz 2>/dev/null | tail -n +6 | xargs -r rm

echo "Backup completed: ${BACKUP_NAME}"
""",
        "monitor": """#!/usr/bin/env bash
set -euo pipefail

# System monitoring script
while true; do
    clear
    echo "=== System Monitor - $(date) ==="
    echo
    echo "CPU & Memory:"
    top -bn1 | head -5
    echo
    echo "Disk Usage:"
    df -h | grep -E '^/dev/'
    echo
    echo "Network:"
    ss -tunap 2>/dev/null | head -10
    
    read -t 5 -n 1 -p "Press any key to exit..." && break
done
""",
        "default": """#!/usr/bin/env bash
set -euo pipefail  # Exit on error, undefined variables, pipe failures
IFS=$'\\n\\t'      # Set Internal Field Separator

# Script: {purpose}
# Generated by Bash Guru MCP

# === Configuration ===
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly SCRIPT_NAME="$(basename "${BASH_SOURCE[0]}")"

# === Functions ===
log() {{ echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*" >&2; }}
die() {{ log "ERROR: $*"; exit 1; }}

# === Main ===
main() {{
    log "Starting ${SCRIPT_NAME}"
    
    # TODO: Implement {purpose}
    
    log "Completed successfully"
}}

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
"""
    }
    
    # Choose template
    template_key = "default"
    for key in templates:
        if key in purpose.lower():
            template_key = key
            break
    
    script = templates[template_key].format(purpose=purpose)
    
    # Save if filename provided
    if filename:
        filepath = Path(filename)
        filepath.write_text(script)
        if make_executable:
            os.chmod(filepath, 0o755)
        return f"Script saved to {filepath.absolute()}\n\n{script}"
    
    return script


@server.tool()
async def optimize_command(command: str) -> str:
    """
    Optimize a bash command for better performance or elegance
    
    Args:
        command: The command to optimize
    
    Returns:
        Optimized version with explanation
    """
    optimizations = []
    
    # Check for common optimizations
    if "cat" in command and "|" in command and "grep" in command:
        optimizations.append("• Instead of 'cat file | grep pattern', use 'grep pattern file'")
    
    if "$(basename" in command:
        optimizations.append("• Instead of '$(basename $path)', use '${path##*/}' (pure bash)")
    
    if "$(dirname" in command:
        optimizations.append("• Instead of '$(dirname $path)', use '${path%/*}' (pure bash)")
    
    if "sleep" in command:
        optimizations.append("• Instead of 'sleep 0.1', use 'read -t 0.1 <> <(:)' (built-in)")
    
    if "`" in command:
        optimizations.append("• Replace backticks ` with $() for command substitution")
    
    if "for i in $(ls" in command or "for i in `ls" in command:
        optimizations.append("• Instead of 'for i in $(ls)', use 'for i in *' (glob expansion)")
    
    if not optimizations:
        optimizations.append("Command looks good! Consider these general tips:")
        optimizations.append("• Use [[ ]] instead of [ ] for conditionals")
        optimizations.append("• Quote variables: \"$var\" instead of $var")
        optimizations.append("• Use built-ins when possible")
    
    return "\n".join([f"Optimizations for: {command}", ""] + optimizations)


async def main():
    """Main entry point for the MCP server"""
    from mcp.server.stdio import stdio_server
    async with stdio_server() as streams:
        await server.run(*streams)


if __name__ == "__main__":
    asyncio.run(main())
