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

## Sobrestamento — DESPACHO vs ARQUIVAMENTO

**ERRO COMUM:** tratar todo sobrestamento como ARQUIVAMENTO (ou todo como DESPACHO).
Existem **dois tipos distintos** com atuações completamente diferentes.

**TIPO 1 — Sobrestamento COM devolução à instância anterior:**
- Ministro/Relator sobrestа E determina retorno dos autos à instância inferior
  (ex: TNU sobrestа e devolve à Turma Recursal; STJ sobrestа e devolve à TNU).
- **Atuação: ARQUIVAMENTO.**
- Despacho de arquivamento explicando o sobrestamento + devolução.
- Comunicar ao colega que atua na instância anterior para as providências que
  entender cabíveis, resguardada a sua independência funcional.

**TIPO 2 — Sobrestamento SEM devolução (processo fica parado na instância atual):**
- Ministro/Relator sobrestа aguardando julgamento de caso-piloto/leading case,
  mas os autos permanecem na instância atual (TNU, STJ etc).
- **Atuação: DESPACHO** (simples ciência + aguardar).
- Movimentação: "Aguardar o andamento processual" / "Ciente do sobrestamento —
  aguardar o julgamento do caso-piloto."
- NÃO arquivar: o processo pode retomar e exigir atuação futura.

**COMO DIFERENCIAR:** leia o dispositivo da decisão. Se disser "retornem/remetam/
devolvam os autos à origem / à instância de origem" → Tipo 1 (arquivar + comunicar
colega). Se disser apenas "sobrestа aguardando" / "suspende-se até" → Tipo 2 (despacho).

**Exemplo real Tipo 2:** PAJ 2023-039-10482 — Presidente TNU sobrestou aguardando
PUIL 6129/DF no STJ (processo-piloto do Tema 337). Autos ficam na TNU.
Opus=DESPACHO ✓, Grok=ARQUIVAMENTO ✗.

**Origem:** JP correção em 2026-06-11.

---

## Cálculo de prazo recursal — e-Proc TNU/STJ (+10 dias corridos)

**ERRO COMUM:** contar os dias úteis do prazo a partir da data de disponibilização
da intimação, esquecendo os 10 dias corridos do e-Proc.

**REALIDADE (e-Proc):** a intimação eletrônica só é considerada ABERTA após **10 dias
corridos** da disponibilização — ciência ficta no 10º dia corrido, se não for consultada
antes. Só ENTÃO começam a correr os dias úteis do prazo recursal.

**REGRA — sempre calcular assim:**
1. Data da disponibilização + **10 dias corridos** = data de abertura/ciência.
2. A partir do 1º dia útil seguinte, conte os **dias úteis** do prazo (agravo interno e
   ED na TNU/STJ = 15 dias úteis; **SEM dobra** da DPU em JEF/TNU).
3. Informe a **data-limite** resultante.

**Exemplo:** disponibilização 22/05 → +10 corridos = ~01/06 → +15 dias úteis ≈ 22/06.
NÃO é 29/05 (erro de ignorar os 10 corridos).

**Origem:** JP correção em 2026-06-16.

---

## Como adicionar nova regra

JP detectou erro do Claude → editar este arquivo:
1. Adicionar nova seção `## Tema`
2. Descrever ERRO COMUM
3. Descrever REALIDADE/FLUXO CORRETO
4. Descrever REGRA explícita
5. Anotar **Origem**: JP correção em <data>

Próxima chamada de planejamento já considera a nova regra. Sem deploy.
