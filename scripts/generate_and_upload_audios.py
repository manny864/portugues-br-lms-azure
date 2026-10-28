#!/usr/bin/env python3
"""
Script determinista para:
1. Obtener las credenciales de Azure AI Speech (cog-speech-*) y Storage Account desplegados con Terraform.
2. Sintetizar los 8 audios reales del curso en formato .opus (ogg-24khz-16bit-mono-opus)
   usando las voces neuronales brasileñas de Azure AI Speech (pt-BR-FranciscaNeural, pt-BR-AntonioNeural, pt-BR-ThalitaNeural).
3. Subir los 8 archivos .opus al contenedor 'media' en Azure Blob Storage (a1/, a2/, b2/, c2/).
4. Actualizar la URL base del CDN en scripts/generate_curriculum.py y regenerar data/curriculum.json + js/curriculum-fallback.js.
"""

import json
import subprocess
import urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
TF_DIR = BASE_DIR / "infra" / "terraform"
TMP_AUDIO_DIR = BASE_DIR / ".tmp" / "audios"


def run_cmd(cmd: list[str], cwd: Path = BASE_DIR) -> str:
    proc = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, check=True)
    return proc.stdout.strip()


def synthesize_ssml_to_opus(speech_key: str, region: str, ssml: str, out_path: Path):
    url = f"https://{region}.tts.speech.microsoft.com/cognitiveservices/v1"
    headers = {
        "Ocp-Apim-Subscription-Key": speech_key,
        "Content-Type": "application/ssml+xml",
        "X-Microsoft-OutputFormat": "ogg-24khz-16bit-mono-opus",
        "User-Agent": "SotaqueBrasileiroLMS/2.0"
    }
    req = urllib.request.Request(url, data=ssml.encode("utf-8"), headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:
        audio_bytes = resp.read()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(audio_bytes)
    return len(audio_bytes)


def build_audio_specs() -> list[dict]:
    return [
        {
            "blob_path": "a1/bossa-padaria-ipanema.opus",
            "ssml": """<speak version='1.0' xml:lang='pt-BR'>
              <voice name='pt-BR-ThalitaNeural'>
                <prosody rate='-5%'>Bom dia, Rio! O sol já nasceu lá na praia de Ipanema.</prosody>
              </voice>
              <voice name='pt-BR-FranciscaNeural'>
                <break time='400ms'/>Oi, bom dia! Tudo joia? O que você vai querer hoje?
              </voice>
              <voice name='pt-BR-AntonioNeural'>
                <break time='400ms'/>Tudo ótimo! Me vê um pão de queijo quentinho e um copo de suco de laranja, por gentileza.
              </voice>
              <voice name='pt-BR-FranciscaNeural'>
                <break time='400ms'/>Pra já! Tem café fresquinho também. Vai pagar no cartão ou no Pix?
              </voice>
              <voice name='pt-BR-AntonioNeural'>
                <break time='400ms'/>Vou pagar no Pix mesmo. Muito obrigado, viu? Valeu!
              </voice>
            </speak>"""
        },
        {
            "blob_path": "a1/pedido-padaria.opus",
            "ssml": """<speak version='1.0' xml:lang='pt-BR'>
              <voice name='pt-BR-AntonioNeural'>
                Tudo ótimo! Me vê um pão de queijo quentinho e um copo de suco de laranja, por gentileza. Vou pagar no Pix.
              </voice>
            </speak>"""
        },
        {
            "blob_path": "a2/fim-de-semana-sp.opus",
            "ssml": """<speak version='1.0' xml:lang='pt-BR'>
              <voice name='pt-BR-FranciscaNeural'>
                E aí, Lucas! Como foi o seu fim de semana? Descansou bastante?
              </voice>
              <voice name='pt-BR-AntonioNeural'>
                <break time='450ms'/>Cara, foi corrido! No sábado eu acordei cedo, fiz feira e à noite a gente tirou várias fotos no show.
              </voice>
            </speak>"""
        },
        {
            "blob_path": "a2/rotina-sabado.opus",
            "ssml": """<speak version='1.0' xml:lang='pt-BR'>
              <voice name='pt-BR-AntonioNeural'>
                No sábado eu acordei cedo, fiz feira e à noite a gente tirou várias fotos no show.
              </voice>
            </speak>"""
        },
        {
            "blob_path": "b2/podcast-cafe-carreira.opus",
            "ssml": """<speak version='1.0' xml:lang='pt-BR'>
              <voice name='pt-BR-FranciscaNeural'>
                Fala, pessoal! Se você estiver ouvindo a gente no trânsito ou no home office, seja muito bem-vindo.
              </voice>
              <voice name='pt-BR-AntonioNeural'>
                <break time='400ms'/>Pois é, Mari! Hoje meu carro deu problema, tive que deixar na oficina, mas assim que eu chegar no escritório vou te mandar o relatório.
              </voice>
              <voice name='pt-BR-FranciscaNeural'>
                <break time='400ms'/>Relaxa, sem estresse! Quando você puder revisar os números, a gente marca uma call rápida. Só cuidado para não apagar a planilha!
              </voice>
              <voice name='pt-BR-AntonioNeural'>
                <break time='400ms'/>Haha, pode deixar! Se o cliente quiser mudar o escopo, a gente negocia um novo prazo na hora.
              </voice>
            </speak>"""
        },
        {
            "blob_path": "b2/podcast-trecho-oficina.opus",
            "ssml": """<speak version='1.0' xml:lang='pt-BR'>
              <voice name='pt-BR-AntonioNeural'>
                Hoje meu carro deu problema, tive que deixar na oficina, mas assim que eu chegar no escritório vou te mandar o relatório.
              </voice>
            </speak>"""
        },
        {
            "blob_path": "c2/painel-economia-governanca.opus",
            "ssml": """<speak version='1.0' xml:lang='pt-BR'>
              <voice name='pt-BR-ThalitaNeural'>
                Boa noite a todos. À medida que avançamos na transição energética, torna-se imprescindível alinharmos a regulação às demandas reais da sociedade.
              </voice>
              <voice name='pt-BR-AntonioNeural'>
                <break time='450ms'/>Concordo plenamente, Helena. Não obstante os desafios fiscais a curto prazo, o fato de os investidores apostarem em matrizes limpas evita prejuízos futuros.
              </voice>
              <voice name='pt-BR-ThalitaNeural'>
                <break time='450ms'/>Sem dúvida. Antes de as empresas tomarem decisões precipitadas, cabe às lideranças combaterem qualquer preconceito contra novas tecnologias.
              </voice>
            </speak>"""
        },
        {
            "blob_path": "c2/debate-trecho-investidores.opus",
            "ssml": """<speak version='1.0' xml:lang='pt-BR'>
              <voice name='pt-BR-AntonioNeural'>
                Não obstante os desafios fiscais a curto prazo, o fato de os investidores apostarem em matrizes limpas evita prejuízos futuros.
              </voice>
            </speak>"""
        }
    ]


def main():
    TMP_AUDIO_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Leer outputs de Terraform
    tf_out_raw = run_cmd(["terraform", "output", "-json"], cwd=TF_DIR)
    tf_out = json.loads(tf_out_raw)

    rg_name = tf_out["resource_group_name"]["value"]
    cdn_media_url = tf_out["frontdoor_cdn_media_url"]["value"].rstrip("/")
    blob_endpoint = tf_out["blob_storage_primary_endpoint"]["value"].rstrip("/")
    storage_account_name = blob_endpoint.split("//")[1].split(".")[0]

    # 2. Obtener nombre y clave de Azure AI Speech y Storage Account
    speech_name = run_cmd([
        "az", "cognitiveservices", "account", "list",
        "--resource-group", rg_name,
        "--query", "[0].name",
        "-o", "tsv"
    ])
    speech_region = run_cmd([
        "az", "cognitiveservices", "account", "show",
        "--name", speech_name,
        "--resource-group", rg_name,
        "--query", "location",
        "-o", "tsv"
    ])
    speech_key = run_cmd([
        "az", "cognitiveservices", "account", "keys", "list",
        "--name", speech_name,
        "--resource-group", rg_name,
        "--query", "key1",
        "-o", "tsv"
    ])
    storage_key = run_cmd([
        "az", "storage", "account", "keys", "list",
        "--account-name", storage_account_name,
        "--resource-group", rg_name,
        "--query", "[0].value",
        "-o", "tsv"
    ])

    # 3. Sintetizar cada audio .opus con Azure AI Speech y subirlo al contenedor 'media'
    uploaded = []
    for spec in build_audio_specs():
        local_file = TMP_AUDIO_DIR / spec["blob_path"]
        size_bytes = synthesize_ssml_to_opus(speech_key, speech_region, spec["ssml"], local_file)

        run_cmd([
            "az", "storage", "blob", "upload",
            "--account-name", storage_account_name,
            "--account-key", storage_key,
            "--container-name", "media",
            "--name", spec["blob_path"],
            "--file", str(local_file),
            "--content-type", "audio/ogg",
            "--overwrite", "true",
            "--output", "none"
        ])

        uploaded.append({
            "blobPath": spec["blob_path"],
            "sizeBytes": size_bytes,
            "cdnUrl": f"{cdn_media_url}/{spec['blob_path']}",
            "directBlobUrl": f"{blob_endpoint}/media/{spec['blob_path']}"
        })

    # 4. Actualizar scripts/generate_curriculum.py con la URL real del CDN de Azure Front Door
    gen_curr_path = BASE_DIR / "scripts" / "generate_curriculum.py"
    curr_code = gen_curr_path.read_text(encoding="utf-8")
    old_placeholder = "https://cdn-ptbr-lms.azurefd.net/media"
    if old_placeholder in curr_code:
        curr_code = curr_code.replace(old_placeholder, cdn_media_url)
        gen_curr_path.write_text(curr_code, encoding="utf-8")

    # Regenerar data/curriculum.json y js/curriculum-fallback.js
    run_cmd(["python3", "scripts/generate_curriculum.py"])

    result = {
        "status": "ok",
        "speechService": speech_name,
        "storageAccount": storage_account_name,
        "cdnMediaBaseUrl": cdn_media_url,
        "blobMediaBaseUrl": f"{blob_endpoint}/media",
        "filesUploaded": uploaded
    }
    (BASE_DIR / ".tmp" / "audio_upload_result.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )


if __name__ == "__main__":
    main()
