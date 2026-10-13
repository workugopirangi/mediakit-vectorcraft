---
tags: [MP]
tipo: nota
status: ativo
updated: 2026-10-13
autor: agente
---

# Foto de cliente esticada na página inteira

**Quando:** 13/10/2026, kit Sprint × World Tennis, página 2.
**O que aconteceu:** a foto f4 (739 × 980 px, mandada pelo cliente) foi posta em página cheia: 37 ppi, borrada em tela cheia. O validador da v9 só avisou "13 imagens abaixo de 96 ppi", sem dizer qual.
**Correção:** a foto foi para um painel em pé de 700 × 930 (101 ppi). `fotos.preparar_foto` agora avisa na hora, com o nome do arquivo e a caixa.
**Regra:** foto pequena vai em painel; página cheia só com foto de 1920 px ou mais.
