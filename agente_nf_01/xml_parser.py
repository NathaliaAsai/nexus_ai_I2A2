# xml_parser.py

import xml.etree.ElementTree as ET
import pandas as pd
from typing import Tuple

def parse_nfe_xml(file_path: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Lê um arquivo XML de Nota Fiscal Eletrônica (NFe) e extrai dados do cabeçalho e dos itens.

    Retorna:
    - DataFrame com o cabeçalho da nota
    - DataFrame com os itens da nota
    """
    tree = ET.parse(file_path)
    root = tree.getroot()

    # Namespace para evitar problemas com XMLs diferentes
    ns = {'ns': root.tag.split('}')[0].strip('{')}

    # Cabeçalho
    emitente = root.find('.//ns:emit', ns)
    ide = root.find('.//ns:ide', ns)
    total = root.find('.//ns:total/ns:ICMSTot', ns)
    infNFe = root.find('.//ns:infNFe', ns)

    header_data = {
        "CHAVE DE ACESSO": infNFe.attrib.get('Id', '').replace('NFe', ''),
        "RAZÃO SOCIAL EMITENTE": emitente.find('ns:xNome', ns).text if emitente is not None else '',
        "CNPJ EMITENTE": emitente.find('ns:CNPJ', ns).text if emitente is not None else '',
        "DATA DE EMISSÃO": ide.find('ns:dhEmi', ns).text if ide is not None else '',
        "VALOR NOTA FISCAL": float(total.find('ns:vNF', ns).text) if total is not None else 0.0,
        "UF EMITENTE": emitente.find('ns:enderEmit/ns:UF', ns).text if emitente is not None else ''
    }

    header_df = pd.DataFrame([header_data])

    # Itens da nota
    items = []
    for det in root.findall('.//ns:det', ns):
        prod = det.find('ns:prod', ns)
        if prod is not None:
            item_data = {
                "CHAVE DE ACESSO": header_data["CHAVE DE ACESSO"],
                "DESCRIÇÃO DO PRODUTO/SERVIÇO": prod.find('ns:xProd', ns).text,
                "QUANTIDADE": float(prod.find('ns:qCom', ns).text),
                "VALOR UNITÁRIO": float(prod.find('ns:vUnCom', ns).text),
                "VALOR TOTAL": float(prod.find('ns:vProd', ns).text)
            }
            items.append(item_data)

    items_df = pd.DataFrame(items)

    return header_df, items_df
