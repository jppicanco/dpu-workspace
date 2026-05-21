# Regras de atuação aprendidas — DPU/TNU/STJ

Arquivo carregado dinamicamente no prompt do Claude pra planejamento de atuação.
Adicionar uma regra por seção quando JP detectar erro recorrente.

Toda regra deve:
- Descrever o erro a evitar
- Dar exemplo concreto
- Estado claro como deveria ser

---

## Agravo contra inadmissão de PUIL

**ERRO COMUM:** confundir Presidente da Turma Recursal de origem com Presidente
da TNU no fluxo do PUIL.

**FLUXO CORRETO:**
1. PUIL é interposto na origem (Turma Recursal).
2. Presidente da TR de ORIGEM faz juízo de admissibilidade prévio.
3. Se Presidente da TR INADMITE → cabe AGRAVO (contra o Presidente da TR, não da TNU).
4. Agravo sobe pra TNU.
5. Presidente da TNU faz novo juízo de admissibilidade.
6. Presidente TNU ADMITE → distribui ao Relator → julgamento colegiado.
7. Presidente TNU INADMITE → NÃO cabe agravo interno contra essa decisão (regra
   geral; verificar caso específico via RITNU).

**REGRA:** quando ver "agravo contra inadmissão de PUIL", confirmar que é
contra o Presidente da TURMA RECURSAL DE ORIGEM, não contra o Presidente da TNU.

**Origem da regra:** JP correção em 2026-05-21.

---

## Decisão de admissão de PUIL pelo Presidente TNU

**ERRO COMUM:** chamar decisão de admissão de "favorável" / "vitória".

**REALIDADE:** decisão de admissão de PUIL é NEUTRA. Significa apenas que:
- Há indícios de divergência (juízo formal positivo)
- O processo segue pra julgamento colegiado
- NÃO há decisão de mérito ainda
- NÃO é vitória nem derrota

**REGRA:** decisões de admissão / conhecimento / distribuição / conversão em
diligência = SEMPRE rotular como "neutra". Vitória só se há provimento.

**Origem:** JP correção em 2026-05-21.

---

## Decisão monocrática Presidente TNU — recursos

**REGRA:** decisão monocrática do Presidente da TNU é irrecorrível por agravo
interno na maioria absoluta dos casos. Cabe no máximo ED quando há
omissão/contradição/obscuridade clara.

**Origem:** JP múltiplas correções em 2026-05-21.

---

## Cabimento de recursos contra colegiada TNU

**ERRO COMUM:** generalizar ED como único recurso cabível contra acórdão TNU.

**FLUXO REAL:** acórdão colegiado TNU pode admitir, conforme caso:
- **ED**: se há omissão/contradição/obscuridade/erro material — critérios estritos
- **REsp ao STJ**: por contrariedade a tese do STJ ou divergência jurisprudencial
- **RE ao STF**: por violação direta à Constituição
- **Agravo interno**: NÃO cabe (decisão é colegiada, não monocrática)

**REGRA:** estudar o caso pra decidir. NÃO presumir ED como padrão.

**Origem:** JP correção em 2026-05-21.

---

## Como adicionar nova regra

JP detectou erro do Claude → editar este arquivo:
1. Adicionar nova seção `## Tema`
2. Descrever ERRO COMUM
3. Descrever REALIDADE/FLUXO CORRETO
4. Descrever REGRA explícita
5. Anotar **Origem**: JP correção em <data>

Próxima chamada de planejamento já considera a nova regra. Sem deploy.
