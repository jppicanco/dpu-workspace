#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SKILL: Validação Anti-Alucinação
Versão: 3.0
Data: 2026-03-06

Valida citações em peças jurídicas para combater alucinações.
Uso obrigatório antes da formatação DOCX/PDF.

v2.0: Suporte ao Banco de Fontes Verificadas (--banco).
Quando o Banco é fornecido, a validação cruza citações com marcadores [Fxxx]
contra as entradas do Banco. Sem Banco, opera no modo legado (v1.0).

v3.0: Removida integração RAG/ChromaDB. Pesquisa de jurisprudência agora
é feita via servidores MCP (BNP + CJF) na etapa de pesquisa jurídica.
"""

import re
import os
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple, Optional
import argparse

# Forçar stdout/stderr para UTF-8 no Windows (evita erros de encoding no terminal)
if sys.stdout.encoding != 'utf-8':
    sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)
if sys.stderr.encoding != 'utf-8':
    sys.stderr = open(sys.stderr.fileno(), mode='w', encoding='utf-8', buffering=1)


class ValidadorAntiAlucinacao:
    """Valida citações em peças jurídicas e remove/transforma alucinações."""

    # Padrões regex para detectar citações
    PATTERNS = {
        'processo_stj': r'(?:REsp|AgRg|EREsp|AREsp|EDcl)\s+(?:no\s+)?(?:n[º°]?\s*)?(\d{1,3}\.?\d{3}\.?\d{3})[/-]?([A-Z]{2})',
        'processo_tnu': r'(?:PUIL|PEDILEF)\s+(?:n[º°]?\s*)?(\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4})',
        'tema_tnu': r'Tema\s+(?:n[º°]?\s*)?(\d+)(?:\s+da\s+TNU)?',
        'ministro': r'(?:Ministro?|Min\.)\s+([A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõç]+(?:\s+[A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõç]+){1,4})',
        'doutrina': r'(?:como\s+(?:leciona|ensina|afirma|destaca)|segundo)\s+([A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõç]+(?:\s+[A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõç]+){0,3})\s*\([12]\d{3}',
        'lei_federal': r'(?:Lei|art\.|artigo)\s+(?:n[º°]?\s*)?(\d{1,2}\.?\d{3})[/-](\d{2,4})',
        'sumula': r'Súmula\s+(?:n[º°]?\s*)?(\d+)(?:\s+do\s+(STJ|STF|TST))?',
        'instrucao_normativa': r'(?:IN|Instrução\s+Normativa)\s+(?:n[º°]?\s*)?(\d+)[/-](\d{4})',
        'portaria': r'Portaria\s+(?:n[º°]?\s*)?(\d+)[/-](\d{4})',
        'data_julgamento': r'(?:julgad[oa]|publicad[oa])\s+em\s+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
    }

    # Padrão para detectar marcadores de fonte [Fxxx]
    PATTERN_MARCADOR_FONTE = r'\[F(\d{3})\]'

    # Legislação federal conhecida (sempre verificável)
    LEGISLACAO_CONHECIDA = {
        # Previdência Social
        '8212/91': 'Lei 8.212/91 (Custeio da Previdência)',
        '8213/91': 'Lei 8.213/91 (Plano de Benefícios)',
        '9876/99': 'Lei 9.876/99 (Fator Previdenciário)',
        '10666/03': 'Lei 10.666/03 (Previdência Social)',
        '10741/03': 'Lei 10.741/03 (Estatuto do Idoso)',
        '142/2013': 'LC 142/2013 (Aposentadoria PcD)',
        # Assistência Social
        '8742/93': 'Lei 8.742/93 (LOAS)',
        # Trabalhista / FGTS
        '8036/90': 'Lei 8.036/90 (FGTS)',
        # Processo / Procedimento
        '9784/99': 'Lei 9.784/99 (Processo Administrativo Federal)',
        '10259/01': 'Lei 10.259/01 (JEF Federal)',
        '9099/95': 'Lei 9.099/95 (Juizados Especiais)',
        '13105/15': 'Lei 13.105/15 (CPC)',
        # DPU e acesso à justiça
        '80/94': 'LC 80/94 (Lei Orgânica da DPU)',
        '1060/50': 'Lei 1.060/50 (Assistência Judiciária)',
        # Direitos fundamentais / vulnerabilidade
        '13146/15': 'Lei 13.146/15 (Estatuto da Pessoa com Deficiência)',
        '8078/90': 'Lei 8.078/90 (CDC)',
        '8080/90': 'Lei 8.080/90 (SUS)',
        # Prescrição / Fazenda Pública
        '20910/32': 'DL 20.910/32 (Prescrição contra Fazenda)',
        '9469/97': 'Lei 9.469/97 (Fazenda Pública)',
        # Registros Públicos / outros
        '6015/73': 'Lei 6.015/73 (Registros Públicos)',
    }

    # Princípios jurídicos consolidados (baixo risco)
    PRINCIPIOS_CONSOLIDADOS = [
        'boa-fé objetiva',
        'venire contra factum proprium',
        'confiança legítima',
        'segurança jurídica',
        'isonomia',
        'legalidade',
        'dignidade da pessoa humana',
        'proteção social',
        'vedação ao retrocesso social',
    ]

    def __init__(self, arquivo_peca: str, documentos_fonte: List[str] = None,
                 rigor: str = 'ALTO', banco_path: str = None):
        self.arquivo_peca = Path(arquivo_peca)
        self.documentos_fonte = documentos_fonte or []
        self.rigor = rigor.upper()
        self.banco_path = Path(banco_path) if banco_path else None

        self.texto_original = ""
        self.texto_validado = ""
        self.citacoes_verificadas = []
        self.citacoes_transformadas = []
        self.citacoes_removidas = []
        self.relatorio = []

        # Banco de Fontes Verificadas
        self.banco: Optional[Dict] = None
        self.banco_ids: Dict[str, Dict] = {}  # Mapa id -> fonte
        self.fontes_utilizadas: List[Dict] = []  # Fontes efetivamente usadas na peça
        self.modo_banco = False

    def carregar_banco(self) -> bool:
        """Carrega o Banco de Fontes Verificadas (JSON)."""
        if not self.banco_path or not self.banco_path.exists():
            return False

        try:
            with open(self.banco_path, 'r', encoding='utf-8') as f:
                self.banco = json.load(f)

            # Indexar fontes por ID
            for fonte in self.banco.get('fontes', []):
                self.banco_ids[fonte['id']] = fonte

            self.modo_banco = True
            print(f"[OK] Banco de Fontes carregado: {self.banco_path.name}")
            print(f"     Total de fontes no Banco: {len(self.banco_ids)}")
            return True

        except Exception as e:
            print(f"[AVISO] Erro ao carregar Banco: {e}")
            return False

    def extrair_marcadores_fonte(self, texto: str) -> List[Dict]:
        """Extrai marcadores [Fxxx] do texto com suas posições."""
        marcadores = []
        for match in re.finditer(self.PATTERN_MARCADOR_FONTE, texto):
            id_fonte = f"F{match.group(1)}"
            marcadores.append({
                'id': id_fonte,
                'texto': match.group(0),
                'posicao': match.span(),
            })
        return marcadores

    def verificar_marcador_no_banco(self, id_fonte: str) -> Tuple[bool, str]:
        """Verifica se marcador [Fxxx] existe no Banco."""
        if id_fonte in self.banco_ids:
            fonte = self.banco_ids[id_fonte]
            verif = fonte.get('verificacao', {})
            metodo = verif.get('metodo', 'desconhecido')

            if metodo == 'url':
                return True, f"Banco [{id_fonte}]: {fonte['citacao'][:60]} — URL: {verif.get('url', 'N/A')}"
            elif metodo == 'documento':
                return True, f"Banco [{id_fonte}]: {fonte['citacao'][:60]} — Doc: {verif.get('documento', 'N/A')}, p. {verif.get('pagina', 'N/A')}"
            else:
                return True, f"Banco [{id_fonte}]: {fonte['citacao'][:60]}"

        return False, f"Marcador [{id_fonte}] NAO encontrado no Banco"

    def ler_peca(self) -> str:
        """Lê o arquivo da peça."""
        with open(self.arquivo_peca, 'r', encoding='utf-8') as f:
            self.texto_original = f.read()
        return self.texto_original

    def ler_documentos_fonte(self) -> Dict[str, str]:
        """Lê documentos PDF fonte e extrai texto."""
        fontes = {}

        # Expandir wildcards e diretórios
        from glob import glob
        arquivos_expandidos = []
        for pattern in self.documentos_fonte:
            p = Path(pattern)
            if p.is_dir():
                # Se for diretório, pegar todos os PDFs dentro
                arquivos_expandidos.extend(sorted(p.glob('*.pdf')))
                arquivos_expandidos.extend(sorted(p.glob('*.PDF')))
            elif '*' in pattern:
                arquivos_expandidos.extend([Path(f) for f in glob(pattern)])
            else:
                arquivos_expandidos.append(p)

        # Deduplicar preservando ordem
        vistos = set()
        arquivos_unicos = []
        for a in arquivos_expandidos:
            key = str(a.resolve())
            if key not in vistos:
                vistos.add(key)
                arquivos_unicos.append(a)

        for caminho in arquivos_unicos:
            caminho = Path(caminho)
            if not caminho.exists():
                print(f"[AVISO] Arquivo não encontrado: {caminho}")
                continue

            nome = caminho.name

            # Tentar extrair texto do PDF
            try:
                import pypdf
                texto_extraido = []
                with open(caminho, 'rb') as pdf_file:
                    pdf_reader = pypdf.PdfReader(pdf_file)
                    for page in pdf_reader.pages[:20]:  # Limitar a 20 páginas
                        texto_extraido.append(page.extract_text())

                fontes[nome] = "\n".join(texto_extraido)
                print(f"[OK] PDF lido: {nome} ({len(pdf_reader.pages)} páginas)")

            except ImportError:
                # pypdf não instalado - usar apenas nome
                fontes[nome] = f"Documento: {nome}"
                print(f"[AVISO] pypdf não instalado - verificação limitada para: {nome}")
            except Exception as e:
                fontes[nome] = f"Documento: {nome}"
                print(f"[AVISO] Erro ao ler PDF {nome}: {e}")

        return fontes

    def extrair_citacoes(self, texto: str) -> List[Dict]:
        """Extrai todas as citações do texto."""
        citacoes = []

        # Calcular posição do fim do endereçamento (primeiras linhas antes do primeiro ##)
        pos_cabecalho = texto.find('\n##')
        if pos_cabecalho == -1:
            pos_cabecalho = texto.find('\n\n\n')
        if pos_cabecalho == -1:
            pos_cabecalho = 0

        for tipo, pattern in self.PATTERNS.items():
            matches = re.finditer(pattern, texto, re.IGNORECASE)
            for match in matches:
                # Ignorar ocorrências de 'ministro' no endereçamento (cabeçalho da petição)
                if tipo == 'ministro' and match.start() < pos_cabecalho:
                    continue
                citacoes.append({
                    'tipo': tipo,
                    'texto': match.group(0),
                    'posicao': match.span(),
                    'grupos': match.groups(),
                })

        # Ordenar por posição no texto
        citacoes.sort(key=lambda x: x['posicao'][0])
        return citacoes

    def verificar_legislacao(self, numero: str) -> bool:
        """Verifica se é legislação conhecida."""
        # Remove formatação
        numero_limpo = re.sub(r'[./\-]', '', numero)
        for lei_conhecida in self.LEGISLACAO_CONHECIDA.keys():
            lei_limpa = re.sub(r'[./\-]', '', lei_conhecida)
            if lei_limpa in numero_limpo or numero_limpo in lei_limpa:
                return True
        return False

    def verificar_em_fontes(self, citacao: str, documentos: Dict) -> Tuple[bool, str]:
        """Verifica se citação existe nos documentos fonte."""
        # Busca texto literal (com tolerância a espaços)
        citacao_limpa = re.sub(r'\s+', ' ', citacao.lower()).strip()

        # Extrair números significativos para busca
        # Para processos/REsp: 5+ dígitos; para Temas/Súmulas: 2+ dígitos
        numeros_longos = re.findall(r'\d{5,}', citacao)   # processos
        numeros_curtos = re.findall(r'\d{2,}', citacao)   # temas, súmulas

        for nome_doc, conteudo in documentos.items():
            conteudo_lower = conteudo.lower()

            # Verificar se é documento paradigma (sempre aceitar)
            if 'paradigma' in nome_doc.lower():
                return True, f"Paradigma: {nome_doc}"

            # Busca literal da citação completa
            if citacao_limpa in conteudo_lower:
                return True, f"Confirmado em: {nome_doc}"

            # Busca por números longos (processos)
            for numero in numeros_longos:
                if numero in conteudo:
                    return True, f"Número {numero} encontrado em: {nome_doc}"

            # Busca por números curtos apenas quando a citação completa tem padrão
            # de Tema ou Súmula (evita falsos positivos com números genéricos)
            citacao_upper = citacao.upper()
            if any(kw in citacao_upper for kw in ('TEMA', 'SÚMULA', 'SUMULA')):
                for numero in numeros_curtos:
                    # Buscar o número com contexto de "Tema" ou "Súmula" no documento
                    if re.search(r'(?:Tema|S[uú]mula)\s+' + re.escape(numero), conteudo, re.IGNORECASE):
                        return True, f"Referência '{citacao}' encontrada em: {nome_doc}"

        return False, ""

    def citacao_tem_marcador_proximo(self, citacao: Dict, marcadores: List[Dict], texto: str) -> Optional[str]:
        """Verifica se uma citação tem um marcador [Fxxx] próximo (até 5 chars depois)."""
        fim_citacao = citacao['posicao'][1]
        for m in marcadores:
            inicio_marcador = m['posicao'][0]
            # Marcador deve estar até 5 caracteres após o fim da citação
            if 0 <= (inicio_marcador - fim_citacao) <= 5:
                return m['id']
        return None

    def classificar_risco(self, citacao: Dict, fontes: Dict, marcadores: List[Dict] = None) -> Tuple[str, str]:
        """
        Classifica risco de alucinação.
        Retorna: (nivel_risco, justificativa)

        No modo Banco: citações com marcador válido = ZERO, sem marcador = ALTO.
        No modo legado: comportamento original.
        """
        tipo = citacao['tipo']
        texto = citacao['texto']

        # ===== MODO BANCO =====
        if self.modo_banco and marcadores is not None:
            # Verificar se citação tem marcador [Fxxx] próximo
            id_fonte = self.citacao_tem_marcador_proximo(citacao, marcadores, self.texto_original)

            if id_fonte:
                # Verificar se o marcador existe no Banco
                existe, justificativa = self.verificar_marcador_no_banco(id_fonte)
                if existe:
                    # Registrar fonte utilizada
                    if id_fonte in self.banco_ids:
                        self.fontes_utilizadas.append(self.banco_ids[id_fonte])
                    return 'ZERO', justificativa
                else:
                    return 'ALTO', f'Marcador [{id_fonte}] inexistente no Banco → remover'

            # Citação sem marcador no modo Banco
            # Verificar legislação conhecida (não precisa de marcador)
            if tipo == 'lei_federal':
                numero = f"{citacao['grupos'][0]}/{citacao['grupos'][1]}"
                if self.verificar_legislacao(numero):
                    return 'ZERO', f'Legislação federal verificável: {numero}'

            # Princípios consolidados (não precisam de marcador)
            texto_lower = texto.lower()
            for principio in self.PRINCIPIOS_CONSOLIDADOS:
                if principio in texto_lower:
                    return 'ZERO', f'Princípio consolidado: {principio}'

            # No modo Banco, citações sem marcador e não legislação = ALTO risco
            if tipo in ['processo_stj', 'processo_tnu', 'tema_tnu', 'ministro', 'doutrina', 'data_julgamento']:
                return 'ALTO', f'Citação sem marcador [Fxxx] no modo Banco → remover'

            # Verificar nos documentos fonte como fallback
            confirmado, fonte = self.verificar_em_fontes(texto, fontes)
            if confirmado:
                return 'ZERO', f'Confirmado (legado): {fonte}'

            return 'ALTO', 'Citação não rastreável no modo Banco → remover'

        # ===== MODO LEGADO (sem Banco) =====

        # RISCO ZERO: Legislação federal conhecida
        if tipo == 'lei_federal':
            numero = f"{citacao['grupos'][0]}/{citacao['grupos'][1]}"
            if self.verificar_legislacao(numero):
                return 'ZERO', f'Legislação federal verificável: {numero}'

        # RISCO ZERO: Princípios consolidados
        texto_lower = texto.lower()
        for principio in self.PRINCIPIOS_CONSOLIDADOS:
            if principio in texto_lower:
                return 'ZERO', f'Princípio consolidado: {principio}'

        # RISCO ZERO: Confirmado em documentos fonte
        confirmado, fonte = self.verificar_em_fontes(texto, fontes)
        if confirmado:
            return 'ZERO', f'Confirmado: {fonte}'

        # RISCO BAIXO: Doutrina (pode virar princípio)
        if tipo == 'doutrina':
            if self.rigor == 'BAIXO':
                return 'BAIXO', 'Doutrina consolidada (rigor baixo)'
            return 'BAIXO', 'Doutrina não verificada → converter em princípio'

        # RISCO MÉDIO: Jurisprudência não confirmada
        if tipo in ['processo_stj', 'processo_tnu', 'tema_tnu']:
            if self.rigor == 'BAIXO':
                return 'MEDIO', 'Jurisprudência plausível (rigor baixo)'
            return 'MEDIO', 'Jurisprudência não confirmada → generalizar'

        # RISCO ZERO: Instrução Normativa / Portaria / Súmula (normas verificáveis)
        if tipo in ['instrucao_normativa', 'portaria', 'sumula']:
            return 'ZERO', f'Norma/ato administrativo verificável: {texto}'

        # RISCO ALTO: Dados específicos não verificáveis
        if tipo in ['ministro', 'data_julgamento']:
            if self.rigor in ['BAIXO', 'MEDIO']:
                return 'MEDIO', 'Dado específico não confirmado (rigor flexível)'
            return 'ALTO', 'Dado específico não verificável → remover'

        return 'MEDIO', 'Citação não classificada'

    def transformar_citacao_doutrina(self, texto: str) -> str:
        """Transforma citação doutrinária em princípio geral."""
        # Extrai o conceito principal
        if 'boa-fé' in texto.lower():
            return 'A boa-fé objetiva, princípio fundamental das relações jurídicas,'
        elif 'venire' in texto.lower():
            return 'A vedação ao comportamento contraditório (venire contra factum proprium), derivada da boa-fé objetiva,'
        elif 'confian' in texto.lower():
            return 'O princípio da confiança legítima, derivado da segurança jurídica,'
        else:
            return 'A doutrina reconhece que'

    def transformar_citacao_jurisprudencia(self, texto: str, tipo: str) -> str:
        """Transforma citação jurisprudencial em afirmação genérica."""
        if 'STJ' in texto.upper():
            return 'A jurisprudência do Superior Tribunal de Justiça tem reconhecido que'
        elif 'STF' in texto.upper():
            return 'O Supremo Tribunal Federal já se manifestou no sentido de que'
        elif 'TNU' in texto.upper():
            return 'A Turma Nacional de Uniformização possui entendimento de que'
        else:
            return 'A jurisprudência dos tribunais superiores é no sentido de que'

    def processar_citacoes(self):
        """Processa todas as citações encontradas."""
        fontes = self.ler_documentos_fonte()
        citacoes = self.extrair_citacoes(self.texto_original)

        # Extrair marcadores [Fxxx] se modo Banco ativo
        marcadores = None
        if self.modo_banco:
            marcadores = self.extrair_marcadores_fonte(self.texto_original)
            print(f"[INFO] Modo Banco ativo: {len(marcadores)} marcadores [Fxxx] encontrados no texto")

        texto_processado = self.texto_original
        offset = 0  # Ajuste de posição após modificações

        for citacao in citacoes:
            risco, justificativa = self.classificar_risco(citacao, fontes, marcadores)

            inicio, fim = citacao['posicao']
            inicio += offset
            fim += offset

            texto_citacao = texto_processado[inicio:fim]

            if risco == 'ZERO':
                # Manter como está
                self.citacoes_verificadas.append({
                    'texto': texto_citacao,
                    'tipo': citacao['tipo'],
                    'justificativa': justificativa
                })

            elif risco == 'BAIXO':
                # Transformar em princípio
                if citacao['tipo'] == 'doutrina':
                    novo_texto = self.transformar_citacao_doutrina(texto_citacao)
                    texto_processado = texto_processado[:inicio] + novo_texto + texto_processado[fim:]
                    offset += len(novo_texto) - len(texto_citacao)

                    self.citacoes_transformadas.append({
                        'original': texto_citacao,
                        'transformado': novo_texto,
                        'justificativa': justificativa
                    })

            elif risco == 'MEDIO':
                # Generalizar jurisprudência
                if citacao['tipo'] in ['processo_stj', 'processo_tnu', 'tema_tnu']:
                    novo_texto = self.transformar_citacao_jurisprudencia(texto_citacao, citacao['tipo'])
                    texto_processado = texto_processado[:inicio] + novo_texto + texto_processado[fim:]
                    offset += len(novo_texto) - len(texto_citacao)

                    self.citacoes_transformadas.append({
                        'original': texto_citacao,
                        'transformado': novo_texto,
                        'justificativa': justificativa
                    })
                else:
                    # Remover
                    texto_processado = texto_processado[:inicio] + texto_processado[fim:]
                    offset -= len(texto_citacao)

                    self.citacoes_removidas.append({
                        'texto': texto_citacao,
                        'justificativa': justificativa
                    })

            elif risco == 'ALTO':
                # Remover completamente
                texto_processado = texto_processado[:inicio] + texto_processado[fim:]
                offset -= len(texto_citacao)

                self.citacoes_removidas.append({
                    'texto': texto_citacao,
                    'justificativa': justificativa
                })

        self.texto_validado = texto_processado

    def gerar_relatorio(self) -> str:
        """Gera relatório de validação em Markdown."""
        linhas = [
            "# RELATÓRIO DE VALIDAÇÃO ANTI-ALUCINAÇÃO",
            f"**Peça:** {self.arquivo_peca.name}",
            f"**Data:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Nível de rigor:** {self.rigor}",
            f"**Modo:** {'BANCO DE FONTES' if self.modo_banco else 'LEGADO (sem Banco)'}",
            "",
        ]

        if self.modo_banco:
            linhas.append(f"**Banco:** {self.banco_path.name}")
            linhas.append(f"**Fontes no Banco:** {len(self.banco_ids)}")
            linhas.append(f"**Fontes utilizadas na peça:** {len(self.fontes_utilizadas)}")
            linhas.append("")

        # Status
        if len(self.citacoes_removidas) == 0 and len(self.citacoes_transformadas) == 0:
            status = "OK APROVADO"
        elif len(self.citacoes_removidas) == 0:
            status = "OK APROVADO COM RESSALVAS (transformações aplicadas)"
        elif len(self.citacoes_removidas) <= 3:
            status = "AVISO APROVADO COM RESSALVAS (remoções aplicadas)"
        else:
            status = "ATENÇÃO: Múltiplas remoções realizadas"

        linhas.append(f"**Status:** {status}")
        linhas.append("")

        # Citações verificadas
        linhas.append(f"## CITAÇÕES VERIFICADAS ({len(self.citacoes_verificadas)})")
        if self.citacoes_verificadas:
            for cit in self.citacoes_verificadas:
                linhas.append(f"OK `{cit['texto'][:80]}...` → {cit['justificativa']}")
        else:
            linhas.append("Nenhuma citação verificada diretamente.")
        linhas.append("")

        # Citações transformadas
        linhas.append(f"## CITAÇÕES TRANSFORMADAS ({len(self.citacoes_transformadas)})")
        if self.citacoes_transformadas:
            for cit in self.citacoes_transformadas:
                linhas.append(f"AVISO **Original:** `{cit['original'][:80]}...`")
                linhas.append(f"   **Transformado:** `{cit['transformado'][:80]}...`")
                linhas.append(f"   **Justificativa:** {cit['justificativa']}")
                linhas.append("")
        else:
            linhas.append("Nenhuma transformação necessária.")
        linhas.append("")

        # Citações removidas
        linhas.append(f"## CITAÇÕES REMOVIDAS ({len(self.citacoes_removidas)})")
        if self.citacoes_removidas:
            for cit in self.citacoes_removidas:
                linhas.append(f"REMOVIDA `{cit['texto'][:80]}...` → {cit['justificativa']}")
        else:
            linhas.append("Nenhuma remoção necessária.")
        linhas.append("")

        # Recomendações
        linhas.append("## RECOMENDAÇÕES")
        if len(self.citacoes_removidas) == 0:
            linhas.append("- OK Nenhuma citação não verificável foi encontrada")
            linhas.append("- OK A peça está segura para formatação")
        else:
            linhas.append(f"- AVISO {len(self.citacoes_removidas)} citação(ões) removida(s)")
            linhas.append("- Revisar se argumentos centrais foram afetados")
            linhas.append("- Se necessário, fornecer fontes adicionais")

        if len(self.citacoes_transformadas) > 0:
            linhas.append(f"- INFO {len(self.citacoes_transformadas)} citação(ões) transformada(s) em argumentação genérica")

        linhas.append("")
        linhas.append("---")
        linhas.append("**Arquivo validado:** `" + str(self.arquivo_peca.stem) + "_VALIDADO.txt`")
        linhas.append("")

        return "\n".join(linhas)

    def gerar_relatorio_fontes(self) -> str:
        """Gera relatório de fontes utilizadas (apenas no modo Banco)."""
        if not self.modo_banco:
            return ""

        # Deduplicar fontes
        ids_vistos = set()
        fontes_unicas = []
        for f in self.fontes_utilizadas:
            if f['id'] not in ids_vistos:
                ids_vistos.add(f['id'])
                fontes_unicas.append(f)

        linhas = [
            "# FONTES UTILIZADAS NA PEÇA",
            f"**Peça:** {self.arquivo_peca.name}",
            f"**Data:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Total de fontes utilizadas:** {len(fontes_unicas)}",
            "",
            "---",
            "",
            "## LISTA DE FONTES COM VERIFICAÇÃO",
            "",
        ]

        for f in fontes_unicas:
            verif = f.get('verificacao', {})
            metodo = verif.get('metodo', 'desconhecido')

            linhas.append(f"### [{f['id']}] {f.get('tipo', 'N/A').upper()}")
            linhas.append(f"**Citação:** {f.get('citacao', 'N/A')}")

            if f.get('trecho_relevante'):
                linhas.append(f"**Trecho:** {f['trecho_relevante'][:200]}")

            if metodo == 'url':
                linhas.append(f"**Verificação:** URL — {verif.get('url', 'N/A')}")
            elif metodo == 'documento':
                linhas.append(f"**Verificação:** Documento — {verif.get('documento', 'N/A')}, página {verif.get('pagina', 'N/A')}")
            else:
                linhas.append(f"**Verificação:** {metodo}")

            linhas.append(f"**Confiança:** {f.get('confianca', 'N/A')}")
            linhas.append("")

        linhas.append("---")
        linhas.append("**Cada fonte acima pode ser verificada pelo Defensor de forma independente.**")
        linhas.append("")

        return "\n".join(linhas)

    def salvar_arquivos(self):
        """Salva arquivos de saída."""
        base_path = self.arquivo_peca.parent
        stem = self.arquivo_peca.stem

        # Arquivo validado
        validado_path = base_path / f"{stem}_VALIDADO.txt"
        with open(validado_path, 'w', encoding='utf-8') as f:
            f.write(self.texto_validado)
        print(f"[OK] Arquivo validado salvo: {validado_path}")

        # Relatório
        relatorio_path = base_path / f"{stem}_RELATORIO_VALIDACAO.md"
        with open(relatorio_path, 'w', encoding='utf-8') as f:
            f.write(self.gerar_relatorio())
        print(f"[OK] Relatório salvo: {relatorio_path}")

        # Backup do original
        backup_path = base_path / f"{stem}_BACKUP_ORIGINAL.txt"
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(self.texto_original)
        print(f"[OK] Backup do original salvo: {backup_path}")

        # Relatório de fontes (apenas no modo Banco)
        if self.modo_banco and self.fontes_utilizadas:
            fontes_path = base_path / f"{stem}_FONTES.md"
            with open(fontes_path, 'w', encoding='utf-8') as f:
                f.write(self.gerar_relatorio_fontes())
            print(f"[OK] Relatório de fontes salvo: {fontes_path}")

    def validar(self):
        """Executa validação completa."""
        print("\n" + "="*60)
        print("VALIDAÇÃO ANTI-ALUCINAÇÃO")
        print("="*60)
        print(f"Peça: {self.arquivo_peca.name}")
        print(f"Rigor: {self.rigor}")

        # Carregar Banco se disponível
        if self.banco_path:
            self.carregar_banco()
            if self.modo_banco:
                print(f"Modo: BANCO DE FONTES VERIFICADAS")
            else:
                print(f"Modo: LEGADO (Banco não encontrado)")
        else:
            print(f"Modo: LEGADO (sem Banco)")

        print("-"*60)

        self.ler_peca()
        print(f"[OK] Peça lida ({len(self.texto_original)} caracteres)")

        self.processar_citacoes()
        print(f"[OK] Citações processadas")
        print(f"  - Verificadas: {len(self.citacoes_verificadas)}")
        print(f"  - Transformadas: {len(self.citacoes_transformadas)}")
        print(f"  - Removidas: {len(self.citacoes_removidas)}")

        if self.modo_banco:
            # Deduplicar para contagem
            ids_unicos = set(f['id'] for f in self.fontes_utilizadas)
            print(f"  - Fontes do Banco utilizadas: {len(ids_unicos)}")

        self.salvar_arquivos()

        print("-"*60)
        if len(self.citacoes_removidas) == 0:
            print("[OK] VALIDACAO APROVADA")
        elif len(self.citacoes_removidas) <= 3:
            print("[AVISO] VALIDACAO APROVADA COM RESSALVAS")
        else:
            print("[ATENCAO] Multiplas remocoes - revisar relatorio")
        print("="*60 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description='Valida citações em peças jurídicas (anti-alucinação)'
    )
    parser.add_argument(
        '--entrada',
        required=True,
        help='Arquivo .txt da peça a validar'
    )
    parser.add_argument(
        '--fontes',
        nargs='*',
        default=[],
        help='Documentos PDF fonte (paradigmas)'
    )
    parser.add_argument(
        '--rigor',
        choices=['BAIXO', 'MEDIO', 'ALTO'],
        default='ALTO',
        help='Nível de rigor da validação (padrão: ALTO)'
    )
    parser.add_argument(
        '--banco',
        default=None,
        help='Caminho do Banco de Fontes Verificadas (JSON). Se fornecido, ativa modo Banco.'
    )
    args = parser.parse_args()

    validador = ValidadorAntiAlucinacao(
        arquivo_peca=args.entrada,
        documentos_fonte=args.fontes,
        rigor=args.rigor,
        banco_path=args.banco,
    )

    validador.validar()


if __name__ == '__main__':
    main()
