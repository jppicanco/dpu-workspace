# Modelos padronizados de arquivamento

## Objetivo

Pasta com modelões pré-validados de despachos de arquivamento por tese fixada
conhecida. Permitem que o Grok 4.3 (no M4) gere despachos rápidos sem precisar
elaboração intelectual original.

## Quando usar

- Tese fixada conhecida e estável (TNU/STJ pacificou)
- Caso concreto se encaixa no modelão sem nuance
- Citações jurisprudenciais já validadas no modelão

## Quando NÃO usar (escalar pra Claude no PC)

- Caso atípico que exige distinguishing
- Tese ainda em formação (sem precedente firmado)
- Cliente em situação de vulnerabilidade que demande argumentação própria

## Estrutura proposta

```
modelos/
  tipo1-irrecorribilidade/
    ed-protelatorio-presidente-tnu.md
    decisao-monocratica-final-stj.md
    ...
  tipo2-inviabilidade-merito/
    tema-359-tnu-complementacao.md
    tese-X-stj-recursos-repetitivos.md
    ...
  tipo3-vitoria-obtida/
    transito-em-julgado-favoravel.md
    ...
```

## Como funciona

Cada `.md` na pasta é um modelão com:
- Título
- Frente da tese fixada
- Texto do despacho com placeholders `{{paj}}`, `{{assistido}}`, `{{decisao}}`, etc.
- Citações jurisprudenciais (já verificadas — fonte rastreável)
- Anti-alucinação dispensada SE o Grok só preencher placeholders sem editar
  citações

## Status

PASTA VAZIA — modelões a serem populados pelo JP conforme casos recorrentes
forem aparecendo. Cada modelão é UMA validação Claude por tema; depois Grok
reusa N vezes.

## Workflow proposto

1. JP encontra caso que se encaixa em padrão recorrente
2. JP pede Claude (no PC) pra fazer o despacho COM anti-alucinação completa
3. Claude entrega despacho + valida
4. JP aprova
5. Claude transforma o despacho em modelão (com placeholders) e salva nesta pasta
6. Grok no M4 passa a usar o modelão pra casos futuros idênticos
