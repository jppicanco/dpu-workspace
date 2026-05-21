# Skill: Busca Rápida Jurisprudencial

## Status

PLACEHOLDER — Skill light a ser implementada. Roda no Grok 4.3 no M4.

## Objetivo

Versão minimalista da `pesquisa-juridica/`. Apenas chama MCPs (BNP, CJF) e
retorna lista de precedentes encontrados em formato bruto. Sem síntese, sem
Banco de Fontes Verificadas completo, sem validação anti-alucinação.

## Quando usar

- Triagem inicial: precisa saber rapidamente se há precedente sobre um tema
- Verificar se vale escalar pra `pesquisa-juridica/` (full no PC)
- Pre-triagem de PAJ no fluxo `verificar-pajs` do jarbas-dpu

## Quando NÃO usar (usar `pesquisa-juridica/` full)

- Pesquisa pra elaboração de peça
- Quando precisa Banco de Fontes Verificadas com `[Fxxx]`
- Quando vai citar diretamente o precedente

## Pipeline previsto

```
Input: tema/palavra-chave + tribunal (opcional)
   ↓
MCP `bnp-api` → buscar_precedentes(termo)
MCP `cjf-jurisprudencia` → buscar_jurisprudencia_cjf(termo)
   ↓
Output: lista bruta de precedentes encontrados
   - número
   - relator
   - data
   - ementa curta (sem síntese)
   - link
```

## Diferenças vs `pesquisa-juridica/` full

| | `busca-rapida/` (M4 Grok) | `pesquisa-juridica/` (PC Claude) |
|---|---|---|
| MCPs chamados | BNP + CJF | BNP + CJF + Planalto + docs |
| Output | Lista bruta | Banco de Fontes Verificadas + análise |
| Anti-alucinação | Não | Sim (skill validacao/anti-alucinacao) |
| Custo cognitivo | Baixo | Alto |
| Tempo | ~5-10s | ~minutos |
| Uso | Triagem | Elaboração |

## A implementar

- [ ] Definir formato de input (palavras-chave estruturadas)
- [ ] Script Python que chama os MCPs e formata output
- [ ] Integração com skill `triagem/` (chamada automática quando relevante)
- [ ] Documentar limites: número máximo de hits, timeout
