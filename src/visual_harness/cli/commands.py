"""Comandos do `vh` (TechSpecs Seção 36-37): fino cliente HTTP da API
já construída nos Steps 7-9, não uma segunda implementação do backend.
"""
import json
import os
import signal
from pathlib import Path

import httpx
import typer
import uvicorn

from visual_harness.events.types import EventType
from visual_harness.main import DEFAULT_HOST, DEFAULT_PORT, build_app

app = typer.Typer(help="Visual Harness: observabilidade humanizada pra agentes de IA.")

PID_FILE = Path.home() / ".visual-harness" / "server.pid"

HostOption = typer.Option(DEFAULT_HOST, "--host")
PortOption = typer.Option(DEFAULT_PORT, "--port")


def _base_url(host: str, port: int) -> str:
    return f"http://{host}:{port}"


@app.command()
def start(host: str = HostOption, port: int = PortOption) -> None:
    """Sobe o backend em primeiro plano (Ctrl+C pra parar)."""
    PID_FILE.parent.mkdir(parents=True, exist_ok=True)
    PID_FILE.write_text(str(os.getpid()), encoding="utf-8")
    try:
        uvicorn.run(build_app(), host=host, port=port)
    finally:
        PID_FILE.unlink(missing_ok=True)


@app.command()
def stop() -> None:
    """Encerra o backend iniciado por `vh start` (lido do PID salvo)."""
    if not PID_FILE.exists():
        typer.echo("vh: nenhum servidor registrado (sem PID salvo)")
        raise typer.Exit(code=1)

    pid = int(PID_FILE.read_text(encoding="utf-8").strip())
    try:
        os.kill(pid, signal.SIGTERM)
        typer.echo(f"vh: sinal de encerramento enviado (PID {pid})")
    except ProcessLookupError:
        typer.echo(f"vh: processo {pid} não existe mais, limpando PID salvo")
    finally:
        PID_FILE.unlink(missing_ok=True)


@app.command()
def status(host: str = HostOption, port: int = PortOption) -> None:
    """Consulta /api/health do backend."""
    try:
        response = httpx.get(f"{_base_url(host, port)}/api/health", timeout=2.0)
        response.raise_for_status()
        body = response.json()
        typer.echo(
            f"vh: rodando (versão {body['version']}, "
            f"uptime {body['uptime']:.1f}s, "
            f"{body['connected_adapters']} adapter(s) conectado(s))"
        )
    except httpx.HTTPError:
        typer.echo("vh: não está rodando (ou não alcançável nesse host/porta)")
        raise typer.Exit(code=1)


@app.command()
def demo(
    stop_: bool = typer.Option(False, "--stop", help="para o demo em vez de iniciar"),
    host: str = HostOption,
    port: int = PortOption,
) -> None:
    """Inicia (ou para, com --stop) o modo demo do backend."""
    action = "stop" if stop_ else "start"
    response = httpx.post(f"{_base_url(host, port)}/api/demo/{action}", timeout=2.0)
    response.raise_for_status()
    typer.echo(f"vh: demo {response.json()['state']}")


@app.command()
def event(
    type_: EventType = typer.Option(
        None, "--type", help="tipo do evento (Seção 9); obrigatório sem --json"
    ),
    session: str = typer.Option("cli", "--session"),
    source: str = typer.Option("cli", "--source"),
    path: str = typer.Option(None, "--path", help="atalho pra payload.path"),
    command: str = typer.Option(None, "--command", help="atalho pra payload.command"),
    payload: str = typer.Option(None, "--payload", help="JSON extra mesclado no payload"),
    json_event: str = typer.Option(
        None, "--json", help="evento inteiro em JSON, ignora as outras flags"
    ),
    host: str = HostOption,
    port: int = PortOption,
) -> None:
    """Emite um evento pro backend (Seção 16, 20, 36-37).

    No PowerShell, aspas simples por fora com \\" literal por dentro
    (ver docs/events.md para o porque disso):
    vh event --json '{\\"type\\": \\"test_failed\\", \\"session_id\\": \\"s1\\"}'
    """
    if json_event is not None:
        body = json.loads(json_event)
    else:
        if type_ is None:
            typer.echo("vh: --type é obrigatório quando --json não é usado")
            raise typer.Exit(code=2)
        merged_payload: dict = json.loads(payload) if payload else {}
        if path is not None:
            merged_payload["path"] = path
        if command is not None:
            merged_payload["command"] = command
        body = {
            "session_id": session,
            "source": source,
            "type": type_.value,
            "payload": merged_payload,
        }

    response = httpx.post(f"{_base_url(host, port)}/api/events", json=body, timeout=2.0)
    if response.status_code != 200:
        typer.echo(f"vh: evento rejeitado ({response.status_code}): {response.text}")
        raise typer.Exit(code=1)
    typer.echo(f"vh: evento {body.get('type', '?')} enviado")


if __name__ == "__main__":
    app()
