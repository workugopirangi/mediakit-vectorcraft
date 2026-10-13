---
tags: [MP]
tipo: nota
status: ativo
updated: 2026-10-13
autor: agente
---

# A caixa da fonte acusa sobreposição que não existe

**Quando:** 13/10/2026, kit Sprint × World Tennis.
**O que aconteceu:** a checagem por caixa de linha (`pdftotext -bbox-layout`) acusou 24 "sobreposições", todas falsas: manchetes de entrelinha apertada, que é o estilo da referência Nike. O único encosto real (preço da página 11) se perdia no meio.
**Correção:** `checagem/tinta.py` mede pela tinta de cada letra. Kit final: 0 acusações; cópia com o defeito: 1, a certa.
