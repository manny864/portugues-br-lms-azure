#!/usr/bin/env python3
"""
Script determinista e idempotente para inicializar Git, crear el repositorio en GitHub
(manny864/portugues-br-lms-azure) y publicar toda la arquitectura del proyecto.
Basado estrictamente en directivas/lms_ptbr_azure_SOP.md.
"""

import json
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
TMP_DIR = BASE_DIR / ".tmp"
REPO_NAME = "portugues-br-lms-azure"
REPO_DESC = "LMS de Portugués Brasileño (PT-BR) A1-C2 para Hispanohablantes + Infraestructura Serverless FinOps en Azure con Terraform y Self-Hosted Runner"


def run_cmd(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=str(BASE_DIR), capture_output=True, text=True, check=check)


def main():
    TMP_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Inicializar repositorio Git en rama main si no existe
    if not (BASE_DIR / ".git").exists():
        run_cmd(["git", "init", "-b", "main"])

    # 2. Verificar usuario autenticado en GitHub CLI
    user_proc = run_cmd(["gh", "api", "user", "--jq", ".login"])
    owner = user_proc.stdout.strip() or "manny864"
    full_repo = f"{owner}/{REPO_NAME}"

    # 3. Hacer stage y commit de todos los archivos del proyecto
    run_cmd(["git", "add", "."])
    status_proc = run_cmd(["git", "status", "--porcelain"])
    if status_proc.stdout.strip():
        run_cmd([
            "git",
            "commit",
            "-m",
            "feat: LMS Portugues Brasileno (A1-C2) SPA + Azure FinOps Terraform & Self-Hosted Runner"
        ])

    # 4. Verificar si el repositorio ya existe en GitHub; si no, crearlo y hacer push
    view_proc = run_cmd(["gh", "repo", "view", full_repo, "--json", "url,name"], check=False)
    if view_proc.returncode != 0:
        run_cmd([
            "gh",
            "repo",
            "create",
            full_repo,
            "--public",
            "--description",
            REPO_DESC,
            "--source=.",
            "--remote=origin",
            "--push"
        ])
    else:
        # Asegurar remoto y hacer push
        remotes = run_cmd(["git", "remote"], check=False).stdout.split()
        repo_url = f"https://github.com/{full_repo}.git"
        if "origin" not in remotes:
            run_cmd(["git", "remote", "add", "origin", repo_url])
        else:
            run_cmd(["git", "remote", "set-url", "origin", repo_url])
        run_cmd(["git", "pull", "--rebase", "origin", "main"], check=False)
        run_cmd(["git", "push", "-u", "origin", "main"])

    final_view = run_cmd(["gh", "repo", "view", full_repo, "--json", "url,name,owner,visibility"])
    repo_info = json.loads(final_view.stdout)

    with open(TMP_DIR / "github_repo_result.json", "w", encoding="utf-8") as f:
        json.dump(repo_info, f, indent=2)


if __name__ == "__main__":
    main()
