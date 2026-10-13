---
tags: [MP]
tipo: sistema
status: ativo
updated: 2026-10-13
autor: agente
---

# Como funciona

- `src/mediakit/vc.py`: abre o `vectorcraft-cli mcp --headless` e manda comandos (`run_command`) um a um. A montagem para se o VectorCraft não estiver no commit de `vectorcraft/VERSAO`.
- `pagina.py` + `kit.py`: cada página é um artboard de 1920 × 1080; no fim tudo é reduzido a 75 % e exportado (PDF 1440 × 810 pt e `.vectorcraft`).
- `fotos.py`: recorte e tratamento raster antes do vetor; avisa abaixo de 96 ppi.
- `cenas.py` + `imagens/gerar_cena.sh`: cena gerada pelo Codex (GPT Image) com o logo; entra só se marcada "usar"; cada geração vai para `cota.json`. `codex_gerar.sh` é cópia da v9.
- `checagem/`: tinta (sobreposição pela tinta da letra), conteúdo (número fora da ficha, travessão), arquivo (`validar_pdf.py` da v9) e o prompt do revisor independente.
- `referencias.py`: lê o repertório do cofre (`SISTEMAS/GERAR MEDIAKIT/repertorio/capturas`) e acrescenta referência nova sem editar as existentes; o registro das novas fica em `biblioteca/referencias.json`.
- `pecas.py` + `biblioteca/pecas/`: cenas aprovadas reaproveitáveis.
- `kits/<kit>/kit.py`: um script por kit. `kits/legado/` guarda os testes Nike e Spotify e o mapa de SP (`sp.json`).
- `receitas/`: o livro de técnicas do VectorCraft, cada uma com prova. `receitas/vch.py` é a ponte para o cliente novo.
- `acervos/`: cópia espelhada das pastas de mídia kit dos clientes (a fonte é o cofre; atualiza só por `scripts/espelhar_acervos.sh`).
- `skill/`: a skill `gerar-mediakit-vc`, ligada em `~/.claude/skills` e `~/.agents/skills`.
