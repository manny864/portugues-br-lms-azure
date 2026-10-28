#!/usr/bin/env python3
"""
Script determinista e idempotente para configurar OIDC entre Azure Entra ID y GitHub Actions
para el workflow de FinOps Shift-Left (.github/workflows/finops-shift-left.yml).
Basado estrictamente en directivas/lms_ptbr_azure_SOP.md:
1. Obtiene SUBSCRIPTION_ID y TENANT_ID de la sesión activa de Azure CLI.
2. Crea o recupera la App Registration 'sp-github-oidc-ptbr-lms' y su Service Principal.
3. Asigna el rol 'Reader' en la suscripción al Service Principal.
4. Crea las credenciales federadas OIDC para:
   - Pull Requests: repo:manny864/portugues-br-lms-azure:pull_request
   - Rama main:     repo:manny864/portugues-br-lms-azure:ref:refs/heads/main
5. Registra AZURE_CLIENT_ID, AZURE_TENANT_ID y AZURE_SUBSCRIPTION_ID en los secretos del repo de GitHub.
"""

import json
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
TMP_DIR = BASE_DIR / ".tmp"
TF_DIR = BASE_DIR / "infra" / "terraform"

REPO_FULL_NAME = "manny864/portugues-br-lms-azure"
APP_DISPLAY_NAME = "sp-github-oidc-ptbr-lms"


def run_cmd(cmd: list[str], check: bool = True, cwd: Path = BASE_DIR) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, check=check)


def main():
    TMP_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Obtener datos de la suscripción y tenant activos en Azure CLI
    acc_proc = run_cmd(["az", "account", "show", "--output", "json"])
    acc_info = json.loads(acc_proc.stdout)
    subscription_id = acc_info["id"]
    tenant_id = acc_info["tenantId"]

    # 2. Verificar si la App Registration ya existe o crearla
    list_app_proc = run_cmd([
        "az", "ad", "app", "list",
        "--display-name", APP_DISPLAY_NAME,
        "--output", "json"
    ])
    existing_apps = json.loads(list_app_proc.stdout)

    if existing_apps:
        app_info = existing_apps[0]
    else:
        create_app_proc = run_cmd([
            "az", "ad", "app", "create",
            "--display-name", APP_DISPLAY_NAME,
            "--output", "json"
        ])
        app_info = json.loads(create_app_proc.stdout)

    app_id = app_info["appId"]        # AZURE_CLIENT_ID
    app_object_id = app_info["id"]    # Object ID de la aplicación para federated-credential

    # 3. Asegurar que exista el Service Principal asociado a la App Registration
    sp_list_proc = run_cmd([
        "az", "ad", "sp", "list",
        "--filter", f"appId eq '{app_id}'",
        "--output", "json"
    ])
    existing_sps = json.loads(sp_list_proc.stdout)
    if existing_sps:
        sp_info = existing_sps[0]
    else:
        sp_create_proc = run_cmd([
            "az", "ad", "sp", "create",
            "--id", app_id,
            "--output", "json"
        ])
        sp_info = json.loads(sp_create_proc.stdout)

    sp_object_id = sp_info["id"]

    # 4. Asignar rol 'Reader' en la suscripción de forma idempotente
    scope = f"/subscriptions/{subscription_id}"
    role_proc = run_cmd([
        "az", "role", "assignment", "create",
        "--assignee-object-id", sp_object_id,
        "--assignee-principal-type", "ServicePrincipal",
        "--role", "Reader",
        "--scope", scope,
        "--output", "json"
    ], check=False)

    # 5. Configurar las Federated Credentials (Pull Request y rama main)
    fed_list_proc = run_cmd([
        "az", "ad", "app", "federated-credential", "list",
        "--id", app_object_id,
        "--output", "json"
    ])
    existing_feds = {f["name"]: f for f in json.loads(fed_list_proc.stdout)}

    desired_feds = [
        {
            "name": "github-actions-pr-finops",
            "issuer": "https://token.actions.githubusercontent.com",
            "subject": f"repo:{REPO_FULL_NAME}:pull_request",
            "description": "Federated credential OIDC para FinOps Shift-Left en Pull Requests",
            "audiences": ["api://AzureADTokenExchange"]
        },
        {
            "name": "github-actions-main-branch",
            "issuer": "https://token.actions.githubusercontent.com",
            "subject": f"repo:{REPO_FULL_NAME}:ref:refs/heads/main",
            "description": "Federated credential OIDC para ejecuciones en la rama main",
            "audiences": ["api://AzureADTokenExchange"]
        }
    ]

    for fed in desired_feds:
        if fed["name"] not in existing_feds:
            param_file = TMP_DIR / f"fed_{fed['name']}.json"
            param_file.write_text(json.dumps(fed, indent=2), encoding="utf-8")
            run_cmd([
                "az", "ad", "app", "federated-credential", "create",
                "--id", app_object_id,
                "--parameters", str(param_file),
                "--output", "json"
            ])

    # 6. Guardar AZURE_CLIENT_ID, AZURE_TENANT_ID y AZURE_SUBSCRIPTION_ID en GitHub Secrets
    secrets_to_set = {
        "AZURE_CLIENT_ID": app_id,
        "AZURE_TENANT_ID": tenant_id,
        "AZURE_SUBSCRIPTION_ID": subscription_id
    }

    # También verificamos si hay un static_web_app_api_key en terraform output para configurarlo si aún no está
    swa_key_proc = run_cmd(["terraform", "output", "-raw", "static_web_app_api_key"], check=False, cwd=TF_DIR)
    if swa_key_proc.returncode == 0 and swa_key_proc.stdout.strip() and "Warning" not in swa_key_proc.stdout:
        secrets_to_set["AZURE_STATIC_WEB_APPS_API_TOKEN"] = swa_key_proc.stdout.strip()

    for secret_name, secret_val in secrets_to_set.items():
        run_cmd([
            "gh", "secret", "set", secret_name,
            "--body", secret_val,
            "--repo", REPO_FULL_NAME
        ])

    # Verificar lista de secretos en el repositorio
    gh_secrets_proc = run_cmd(["gh", "secret", "list", "--repo", REPO_FULL_NAME])

    summary = {
        "status": "ok",
        "appDisplayName": APP_DISPLAY_NAME,
        "azureClientId": app_id,
        "azureTenantId": tenant_id,
        "azureSubscriptionId": subscription_id,
        "roleAssigned": "Reader",
        "federatedSubjects": [f["subject"] for f in desired_feds],
        "githubSecretsConfigured": list(secrets_to_set.keys()),
        "githubSecretListOutput": gh_secrets_proc.stdout.strip().splitlines()
    }

    with open(TMP_DIR / "oidc_setup_result.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)


if __name__ == "__main__":
    main()
