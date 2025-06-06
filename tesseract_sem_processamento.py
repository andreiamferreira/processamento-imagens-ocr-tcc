# -*- coding: utf-8 -*-
"""Tesseract Sem Processamento.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1mDRCNVaWx7VRrOlyI0D6OJ776vR0XA7M
"""

from google.colab import drive
drive.mount('/content/gdrive')

!apt-get install -y tesseract-ocr
!pip install pytesseract opencv-python-headless
!pip install python-Levenshtein

from PIL import Image, ImageOps
import numpy as np
import cv2
import pytesseract
from collections import Counter
import string
from sklearn.metrics import mean_squared_error
from skimage import data, img_as_float
from skimage.metrics import structural_similarity as ssim
import os
import matplotlib.pyplot as plt
import pandas as pd
import Levenshtein

pasta_imagens = '/content/gdrive/MyDrive/tcc/imagens_dataset/imagens/listas_isoladas'
csv_transcricoes = '/content/gdrive/MyDrive/tcc/imagens_dataset/imagens/rotulos.csv'

"""Função para redimensionar a imagem para otimizar o processamento do OCR"""

def redimensionar_imagem(imagem):
    maxima_dimensao_pixels = 1600
    altura, largura = imagem.shape[:2]
    if max(altura, largura) > maxima_dimensao_pixels:
        if altura > largura:
            nova_altura = maxima_dimensao_pixels
            nova_largura = int(largura * (nova_altura / altura))
        else:
            nova_largura = maxima_dimensao_pixels
            nova_altura = int(altura * (nova_largura / largura))

        imagem_redimensionada = cv2.resize(imagem, (nova_largura, nova_altura), interpolation=cv2.INTER_LANCZOS4)
        return imagem_redimensionada
    return imagem

def calcular_similiaridade(texto, resultado_ocr):
    texto_original_normalizado = "".join(filter(str.isalnum, texto.lower()))
    resultado_ocr_normalizado = "".join(filter(str.isalnum, resultado_ocr.lower()))

    if not texto_original_normalizado and not resultado_ocr_normalizado:
        return 1.0
    if not texto_original_normalizado or not resultado_ocr_normalizado:
        return 0.0

    distancia_levenshtein = Levenshtein.distance(texto_original_normalizado, resultado_ocr_normalizado)
    acuracia = 1 - (distancia_levenshtein / max(len(texto_original_normalizado), len(resultado_ocr_normalizado)))

    return acuracia

def exibir_tabela_resultados(resultados):
    df = pd.DataFrame(resultados)
    df_ordem_crescente = df.sort_values(by='acuracia_ocr', ascending=False)

    print("\n" + "="*120)
    print(" " * 45 + "RELATÓRIO DE ACURÁCIA E QUALIDADE DE IMAGEM OCR")
    print("="*120)

    print(df_ordem_crescente[[
        'nome_arquivo',
        'acuracia_ocr'
    ]].to_string(index=False))
    print("="*120)

    if not df.empty:
        media_acuracia_geral = df['acuracia_ocr'].mean()
        print(f"Média geral: {media_acuracia_geral:.2f}%")
    else:
        print("Não há resultados para cálculo.")
    print("="*120)

try:
    df_transcricoes = pd.read_csv(csv_transcricoes, sep=";")
    df_transcricoes['nome_arquivo_lista_separada'] = df_transcricoes['nome_arquivo_lista_separada'].str.lower()
    print(f"CSV de transcrições carregado com sucesso de: {csv_transcricoes}")
except FileNotFoundError:
    print(f"Arquivo CSV não encontrado")
except KeyError:
    print("Colunas 'nome_arquivo_lista_separada' e 'lista_ingredientes_sem_avisos' não encontradas.")


imagens = [f for f in os.listdir(pasta_imagens) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

resultados = []

if not imagens:
    print(f"Nenhuma imagem encontrada na pasta: {pasta_imagens}")
else:
    for imagem in imagens:
        caminho_imagem = os.path.join(pasta_imagens, imagem)
        print(f"\n Imagem: {imagem}")

        descricao_original = "Não encontrado no CSV"
        coluna = df_transcricoes[df_transcricoes['nome_arquivo_lista_separada'] == imagem.lower()]
        if not coluna.empty:
            descricao_original = coluna['lista_ingredientes_com_avisos'].iloc[0]
            print(f"Descrição de referência (CSV): '{descricao_original}'")

        try:
            imagem_array_cv = cv2.imread(caminho_imagem)
            image_pil = Image.fromarray(imagem_array_cv)

            custom_config = r'--oem 1 --psm 6 -c tessedit_char_whitelist="1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyzáÁéÉíÍóÓúÚãÃõÕâÂêÊôÔç.:,!()-\' "'
            texto = pytesseract.image_to_string(image_pil, config=custom_config)

            print("Texto extraído:")
            print(texto)

            plt.imshow(image_pil)
            plt.axis('off')
            plt.title("Imagem Processada")
            plt.show()

            acuracia = 0.0
            if descricao_original != "Não encontrado no CSV":
                acuracia = calcular_similiaridade(descricao_original, texto)
                print(f"Acurácia do OCR - Levenshtein: {acuracia:.4f}")
            else:
                print("descrição de referência não encontrada.")

            resultados.append({
                'nome_arquivo': imagem,
                'texto_ocr': texto,
                'descricao_csv': descricao_original,
                'acuracia_ocr': acuracia
            })

            plt.figure(figsize=(15, 7))

        except Exception as e:
            print(f"Erro ao processar a imagem {imagem}: {e}")
            resultados.append({
                'nome_arquivo': imagem,
                'texto_ocr': "ERRO DE PROCESSAMENTO",
                'descricao_csv': descricao_original,
                'acuracia_ocr': 0.0
            })

if resultados:
  exibir_tabela_resultados(resultados)
else:
    print("\nNenhum resultado.")