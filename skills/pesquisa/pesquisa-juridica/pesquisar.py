#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SKILL: Pesquisa Juridica - Banco de Fontes Verificadas
Versao: 1.0
Data: 2026-02-15

Extrai citacoes dos documentos fornecidos e gera o Banco de Fontes
Verificadas (JSON) para uso durante a elaboracao de pecas juridicas.

O Banco e complementado pelo Claude com fontes da web (Fases 2 e 3).
Este script executa a Fase 1 (extracao de documentos) e a Fase 4 (compilacao).
"""

import re
import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple, Optional
from glob import glob

# Forçar stdout/stderr para UTF-8 no Windows (evita erros de encoding no terminal)
if sys.stdout.encoding != 'utf-8':
    sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)
if sys.stderr.encoding != 'utf-8':
    sys.stderr = open(sys.stderr.fileno(), mode='w', encoding='utf-8', buffering=1)


class PesquisadorJuridico:
    """Extrai citacoes de documentos e gera Banco de Fontes Verificadas."""

    # Padroes regex para detectar citacoes (mesmos do validar_peca.py + extras)
    PATTERNS = {
        'processo_stj': r'(?:REsp|AgRg|EREsp|AREsp|EDcl)\s+(?:no\s+)?(?:n[º°]?\s*)?(\d{1,3}\.?\d{3}\.?\d{3})[/-]?([A-Z]{2})',
        'processo_tnu': r'(?:PUIL|PEDILEF)\s+(?:n[º°]?\s*)?(\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4})',
        'tema_tnu': r'Tema\s+(?:n[º°]?\s*)?(\d+)(?:\s+da\s+TNU)?',
        'tema_stj': r'Tema\s+(?:n[º°]?\s*)?(\d+)(?:\s+do\s+STJ)?',
        'ministro': r'(?:Ministro?|Min\.)\s+([A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõç]+(?:\s+[A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõç]+){1,4})',
        'doutrina': r'(?:como\s+(?:leciona|ensina|afirma|destaca)|segundo)\s+([A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõç]+(?:\s+[A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõç]+){0,3})\s*\([12]\d{3}',
        'lei_federal': r'(?:Lei|art\.|artigo)\s+(?:n[º°]?\s*)?(\d{1,2}\.?\d{3})[/-](\d{2,4})',
        'sumula': r'Súmula\s+(?:n[º°]?\s*)?(\d+)(?:\s+do\s+(STJ|STF|TST))?',
        'instrucao_normativa': r'(?:IN|Instrução\s+Normativa)\s+(?:n[º°]?\s*)?(\d+)[/-](\d{4})',
        'data_julgamento': r'(?:julgad[oa]|publicad[oa])\s+em\s+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
        'ementa': r'EMENTA[:\s]+(.*?)(?:\n\n|\Z)',
    }

    # URLs conhecidas de legislacao federal
    URLS_LEGISLACAO = {
        '8212/91': 'https://www.planalto.gov.br/ccivil_03/leis/l8212cons.htm',
        '8213/91': 'https://www.planalto.gov.br/ccivil_03/leis/l8213cons.htm',
        '80/94': 'https://www.planalto.gov.br/ccivil_03/leis/lcp/lcp80.htm',
        '9876/99': 'https://www.planalto.gov.br/ccivil_03/leis/l9876.htm',
        '13146/15': 'https://www.planalto.gov.br/ccivil_03/leis/l13146.htm',
        '13105/15': 'https://www.planalto.gov.br/ccivil_03/leis/l13105.htm',
        '10741/03': 'https://www.planalto.gov.br/ccivil_03/leis/2003/l10.741.htm',
        '8078/90': 'https://www.planalto.gov.br/ccivil_03/leis/l8078compilado.htm',
        '8080/90': 'https://www.planalto.gov.br/ccivil_03/leis/l8080.htm',
        '1060/50': 'https://www.planalto.gov.br/ccivil_03/leis/l1060.htm',
    }

    def __init__(self, documentos_fonte: List[str], processo: str = '', saida: str = 'saida/banco_fontes_verificadas.json'):
        self.documentos_fonte = documentos_fonte
        self.processo = processo
        self.saida = Path(saida)
        self.fontes: List[Dict] = []
        self.contador_id = 0

    def proximo_id(self) -> str:
        """Gera proximo ID sequencial."""
        self.contador_id += 1
        return f"F{self.contador_id:03d}"

    def extrair_texto_txt(self, caminho_txt: Path) -> List[Dict]:
        """Extrai texto de TXT pre-convertido (gerado por converter.py)."""
        paginas = []
        try:
            with open(caminho_txt, 'r', encoding='utf-8') as f:
                conteudo = f.read()
            # Separar por marcadores de pagina: --- Pagina X/Y [...] ---
            partes = re.split(r'--- Pagina (\d+)/\d+ \[.*?\] ---\n', conteudo)
            # partes[0] e texto antes do primeiro marcador (vazio normalmente)
            # partes[1] = num pagina, partes[2] = texto, partes[3] = num pagina, ...
            for i in range(1, len(partes) - 1, 2):
                num_pagina = int(partes[i])
                texto = partes[i + 1].strip()
                if texto and texto != "[Pagina de assinatura eletronica omitida]":
                    paginas.append({
                        'numero': num_pagina,
                        'texto': texto
                    })
            print(f"[OK] TXT lido: {caminho_txt.name} ({len(paginas)} paginas com texto)")
        except Exception as e:
            print(f"[AVISO] Erro ao ler TXT {caminho_txt.name}: {e}")
        return paginas

    def extrair_texto_pdf(self, caminho: Path) -> List[Dict]:
        """Extrai texto de PDF com numero de pagina. Usa TXT pre-convertido se disponivel."""
        # Auto-deteccao: se existe .txt ao lado do PDF, usar ele (sem limite de paginas)
        caminho_txt = caminho.with_suffix('.txt')
        if caminho_txt.exists():
            return self.extrair_texto_txt(caminho_txt)

        paginas = []
        try:
            import pypdf
            with open(caminho, 'rb') as pdf_file:
                pdf_reader = pypdf.PdfReader(pdf_file)
                for i, page in enumerate(pdf_reader.pages[:30]):
                    texto = page.extract_text()
                    if texto and texto.strip():
                        paginas.append({
                            'numero': i + 1,
                            'texto': texto
                        })
            print(f"[OK] PDF lido: {caminho.name} ({len(paginas)} paginas com texto)")
        except ImportError:
            print(f"[AVISO] pypdf nao instalado - leitura limitada para: {caminho.name}")
        except Exception as e:
            print(f"[AVISO] Erro ao ler PDF {caminho.name}: {e}")
        return paginas

    def extrair_citacoes_de_pagina(self, texto: str, documento: str, pagina: int) -> List[Dict]:
        """Extrai citacoes de uma pagina de texto."""
        citacoes_encontradas = []

        for tipo, pattern in self.PATTERNS.items():
            if tipo == 'ementa':
                continue  # Tratar ementas separadamente
            matches = re.finditer(pattern, texto, re.IGNORECASE)
            for match in matches:
                # Extrair contexto ao redor (50 chars antes e depois)
                inicio = max(0, match.start() - 50)
                fim = min(len(texto), match.end() + 50)
                contexto = texto[inicio:fim].replace('\n', ' ').strip()

                citacoes_encontradas.append({
                    'tipo': tipo,
                    'texto': match.group(0),
                    'contexto': contexto,
                    'documento': documento,
                    'pagina': pagina,
                    'grupos': match.groups(),
                })

        return citacoes_encontradas

    def classificar_tipo_fonte(self, tipo_citacao: str) -> str:
        """Mapeia tipo de citacao para tipo de fonte do Banco."""
        mapa = {
            'processo_stj': 'jurisprudencia',
            'processo_tnu': 'jurisprudencia',
            'tema_tnu': 'tese_repetitiva',
            'tema_stj': 'tese_repetitiva',
            'ministro': 'jurisprudencia',
            'doutrina': 'doutrina',
            'lei_federal': 'legislacao',
            'sumula': 'sumula',
            'instrucao_normativa': 'legislacao',
            'data_julgamento': 'jurisprudencia',
        }
        return mapa.get(tipo_citacao, 'outro')

    def obter_url_legislacao(self, numero: str) -> Optional[str]:
        """Busca URL conhecida para legislacao federal."""
        numero_limpo = re.sub(r'[.\-]', '', numero)
        for lei, url in self.URLS_LEGISLACAO.items():
            lei_limpa = re.sub(r'[.\-]', '', lei)
            if lei_limpa in numero_limpo or numero_limpo in lei_limpa:
                return url
        return None

    def criar_entrada_fonte(self, citacao: Dict, is_paradigma: bool = False) -> Dict:
        """Cria uma entrada no Banco a partir de uma citacao extraida."""
        tipo_fonte = 'paradigma' if is_paradigma else self.classificar_tipo_fonte(citacao['tipo'])

        verificacao = {
            'metodo': 'documento',
            'documento': citacao['documento'],
            'pagina': citacao['pagina']
        }

        # Se for legislacao, tentar adicionar URL
        if citacao['tipo'] == 'lei_federal' and len(citacao['grupos']) >= 2:
            numero_lei = f"{citacao['grupos'][0]}/{citacao['grupos'][1]}"
            url = self.obter_url_legislacao(numero_lei)
            if url:
                verificacao = {
                    'metodo': 'url',
                    'url': url
                }

        return {
            'id': self.proximo_id(),
            'tipo': tipo_fonte,
            'citacao': citacao['texto'],
            'trecho_relevante': citacao['contexto'],
            'verificacao': verificacao,
            'confianca': 'ALTA'
        }

    def deduplicar_fontes(self):
        """Remove fontes duplicadas (mesma citacao)."""
        vistos = set()
        fontes_unicas = []
        for fonte in self.fontes:
            # Normalizar texto para comparacao
            chave = re.sub(r'\s+', ' ', fonte['citacao'].lower().strip())
            if chave not in vistos:
                vistos.add(chave)
                fontes_unicas.append(fonte)
        self.fontes = fontes_unicas

        # Renumerar IDs
        for i, fonte in enumerate(self.fontes):
            fonte['id'] = f"F{i+1:03d}"
        self.contador_id = len(self.fontes)

    def processar_documentos(self):
        """Fase 1: Processa todos os documentos fonte."""
        print("\n" + "=" * 60)
        print("PESQUISA JURIDICA — FASE 1: EXTRACAO DE DOCUMENTOS")
        print("=" * 60)

        # Expandir wildcards e diretórios
        arquivos = []
        for pattern in self.documentos_fonte:
            p = Path(pattern)
            if p.is_dir():
                # Se for diretório, expandir todos os PDFs dentro
                arquivos.extend(sorted(str(f) for f in p.glob('*.pdf')))
                arquivos.extend(sorted(str(f) for f in p.glob('*.PDF')))
            elif '*' in pattern:
                arquivos.extend(glob(pattern))
            else:
                arquivos.append(pattern)

        if not arquivos:
            print("[AVISO] Nenhum documento fonte encontrado.")
            return

        for arq in arquivos:
            caminho = Path(arq)
            if not caminho.exists():
                print(f"[AVISO] Arquivo nao encontrado: {arq}")
                continue

            is_paradigma = 'paradigma' in caminho.name.lower()
            if is_paradigma:
                print(f"[PARADIGMA] Processando paradigma: {caminho.name}")

            paginas = self.extrair_texto_pdf(caminho)
            total_citacoes = 0

            for pag in paginas:
                citacoes = self.extrair_citacoes_de_pagina(
                    pag['texto'],
                    caminho.name,
                    pag['numero']
                )
                for cit in citacoes:
                    entrada = self.criar_entrada_fonte(cit, is_paradigma)
                    self.fontes.append(entrada)
                    total_citacoes += 1

            print(f"  -> {total_citacoes} citacoes extraidas de {caminho.name}")

        # Deduplicar
        antes = len(self.fontes)
        self.deduplicar_fontes()
        depois = len(self.fontes)
        if antes != depois:
            print(f"\n[INFO] Deduplicacao: {antes} -> {depois} fontes unicas")

    def gerar_banco(self) -> Dict:
        """Fase 4: Gera o Banco de Fontes Verificadas em JSON."""
        banco = {
            'metadados': {
                'data_geracao': datetime.now().isoformat(),
                'processo': self.processo,
                'total_fontes': len(self.fontes),
                'versao': '1.0',
                'nota': 'Este banco foi gerado automaticamente a partir dos documentos fornecidos. '
                        'Claude deve complementar com fontes das Fases 2 (legislacao) e 3 (jurisprudencia web) '
                        'e apresentar ao Defensor antes de iniciar a redacao.'
            },
            'fontes': self.fontes
        }
        return banco

    def salvar_banco(self, banco: Dict):
        """Salva o Banco em arquivo JSON."""
        # Garantir que diretorio existe
        self.saida.parent.mkdir(parents=True, exist_ok=True)

        with open(self.saida, 'w', encoding='utf-8') as f:
            json.dump(banco, f, ensure_ascii=False, indent=2)

        print(f"\n[OK] Banco de Fontes salvo: {self.saida}")
        print(f"     Total de fontes: {len(self.fontes)}")

    def gerar_resumo(self, banco: Dict) -> str:
        """Gera resumo textual do Banco para apresentar ao Defensor."""
        fontes = banco['fontes']

        # Agrupar por tipo
        por_tipo = {}
        for f in fontes:
            tipo = f['tipo']
            if tipo not in por_tipo:
                por_tipo[tipo] = []
            por_tipo[tipo].append(f)

        linhas = [
            f"BANCO DE FONTES VERIFICADAS — Processo {self.processo}",
            f"Data: {banco['metadados']['data_geracao'][:10]}",
            f"Total de fontes: {banco['metadados']['total_fontes']}",
            "",
        ]

        nomes_tipos = {
            'jurisprudencia': 'JURISPRUDENCIA',
            'jurisprudencia_web': 'JURISPRUDENCIA (WEB)',
            'legislacao': 'LEGISLACAO',
            'sumula': 'SUMULAS',
            'tese_repetitiva': 'TESES REPETITIVAS',
            'doutrina': 'DOUTRINA',
            'paradigma': 'PARADIGMAS (verificados pelo Defensor)',
        }

        for tipo, nome in nomes_tipos.items():
            if tipo in por_tipo:
                linhas.append(f"{nome} ({len(por_tipo[tipo])}):")
                for f in por_tipo[tipo]:
                    verif = f['verificacao']
                    if verif['metodo'] == 'url':
                        fonte_str = f"URL: {verif['url']}"
                    else:
                        fonte_str = f"{verif['documento']}, p. {verif['pagina']}"
                    linhas.append(f"  [{f['id']}] {f['citacao'][:80]} — Fonte: {fonte_str}")
                linhas.append("")

        return "\n".join(linhas)

    def executar(self):
        """Executa pipeline completo de pesquisa (Fases 1 e 4)."""
        print("\n" + "=" * 60)
        print("PESQUISA JURIDICA — BANCO DE FONTES VERIFICADAS")
        print("=" * 60)
        if self.processo:
            print(f"Processo: {self.processo}")
        print("-" * 60)

        # Fase 1: Extracao
        self.processar_documentos()

        # Fase 4: Compilacao
        banco = self.gerar_banco()
        self.salvar_banco(banco)

        # Resumo
        resumo = self.gerar_resumo(banco)
        print("\n" + "-" * 60)
        print(resumo)
        print("-" * 60)

        # Salvar resumo
        resumo_path = self.saida.parent / f"{self.saida.stem}_RESUMO.txt"
        with open(resumo_path, 'w', encoding='utf-8') as f:
            f.write(resumo)
        print(f"[OK] Resumo salvo: {resumo_path}")

        print("\n" + "=" * 60)
        print("[INFO] Fases 2 e 3 (legislacao e jurisprudencia web) devem ser")
        print("       complementadas pelo Claude e adicionadas ao Banco JSON.")
        print("       Apresente o Banco ao Defensor antes de iniciar a redacao.")
        print("=" * 60 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description='Pesquisa Juridica — Gera Banco de Fontes Verificadas'
    )
    parser.add_argument(
        '--fontes',
        nargs='*',
        default=[],
        help='Documentos PDF fonte (aceita wildcards)'
    )
    parser.add_argument(
        '--processo',
        default='',
        help='Numero do processo'
    )
    parser.add_argument(
        '--saida',
        default='saida/banco_fontes_verificadas.json',
        help='Caminho do arquivo JSON de saida (padrao: saida/banco_fontes_verificadas.json)'
    )

    args = parser.parse_args()

    pesquisador = PesquisadorJuridico(
        documentos_fonte=args.fontes,
        processo=args.processo,
        saida=args.saida
    )

    pesquisador.executar()


if __name__ == '__main__':
    main()
