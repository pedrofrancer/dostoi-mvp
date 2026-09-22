"""Stub do entry point `vh` (TechSpecs Seção 36). Comandos de verdade
(`vh start`, `vh event`, `vh demo`...) chegam no Step 10; por ora só
prova que o empacotamento resolve o entry point ponta a ponta.
"""
import typer

app = typer.Typer(help="Visual Harness: ainda não implementado (Step 10).")


@app.callback(invoke_without_command=True)
def main():
    typer.echo("vh: comandos ainda não implementados (ver Step 10 no roadmap)")


if __name__ == "__main__":
    app()
