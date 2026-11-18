"""Tradução fixa dos rótulos mais comuns do Rekognition (DetectLabels).

O Translate recebe cada rótulo como uma palavra solta, sem contexto, e erra casos
frequentes: "Sign" (placa) virou "assine" em todos os testes reais. Os rótulos deste
dicionário não passam pelo Translate (mais correto e mais barato); os demais continuam
sendo traduzidos por ele.
"""

ROTULOS_PT = {
    # Texto e sinalização (aparecem em quase toda placa)
    'Sign': 'placa', 'Symbol': 'símbolo', 'Text': 'texto', 'Road Sign': 'sinal de trânsito',
    'Logo': 'logotipo', 'Plaque': 'placa comemorativa', 'Scoreboard': 'painel',
    'Label': 'etiqueta', 'Banner': 'faixa', 'Poster': 'cartaz', 'Billboard': 'outdoor',
    'Advertisement': 'anúncio', 'Arrow': 'seta', 'Number': 'número', 'Alphabet': 'alfabeto',
    'Word': 'palavra', 'Handwriting': 'escrita à mão', 'Emblem': 'emblema', 'Badge': 'distintivo',
    'First Aid': 'primeiros socorros', 'Stopsign': 'placa de pare', 'Stop Sign': 'placa de pare',
    'Traffic Light': 'semáforo', 'Light': 'luz', 'Graphics': 'gráfico', 'Art': 'arte',
    'Pattern': 'padrão', 'Flag': 'bandeira', 'Clock': 'relógio',
    # Construções e pontos turísticos
    'Building': 'edifício', 'Architecture': 'arquitetura', 'Monument': 'monumento',
    'Landmark': 'ponto turístico', 'Temple': 'templo', 'Shrine': 'santuário',
    'Pillar': 'pilar', 'Column': 'coluna', 'Parthenon': 'Partenon', 'Gate': 'portão',
    'Arch': 'arco', 'Church': 'igreja', 'Cathedral': 'catedral', 'Mosque': 'mesquita',
    'Dome': 'cúpula', 'Tower': 'torre', 'Castle': 'castelo', 'Palace': 'palácio',
    'Statue': 'estátua', 'Sculpture': 'escultura', 'Museum': 'museu', 'Bridge': 'ponte',
    'Wall': 'parede', 'Brick': 'tijolo', 'Door': 'porta', 'Window': 'janela',
    'Fence': 'cerca', 'Pole': 'poste', 'Shop': 'loja', 'Restaurant': 'restaurante',
    'Prayer': 'local de oração', 'Worship': 'local de culto',
    # Cidade, transporte e ambiente
    'City': 'cidade', 'Street': 'rua', 'Road': 'via', 'Urban': 'área urbana',
    'Downtown': 'centro da cidade', 'Neighborhood': 'bairro', 'Outdoors': 'ao ar livre',
    'Indoors': 'ambiente interno', 'Sky': 'céu', 'Tree': 'árvore', 'Plant': 'planta',
    'Nature': 'natureza', 'Water': 'água', 'River': 'rio', 'Mountain': 'montanha',
    'Night': 'noite', 'Car': 'carro', 'Vehicle': 'veículo', 'Transportation': 'transporte',
    'Train': 'trem', 'Subway': 'metrô', 'Railway': 'ferrovia', 'Train Station': 'estação de trem',
    'Bus': 'ônibus', 'Bicycle': 'bicicleta', 'Parking': 'estacionamento',
    # Pessoas
    'Person': 'pessoa', 'Human': 'pessoa', 'People': 'pessoas', 'Crowd': 'multidão',
    'Tourist': 'turista', 'Pedestrian': 'pedestre',
}


def traducao_fixa(rotulo):
    return ROTULOS_PT.get(rotulo)
