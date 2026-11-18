"""Regras de tradução: junção de linhas da mesma frase e rótulos da cena."""
from chalicelib.traducao import juntar_continuacoes, traduzir_rotulos


def test_junta_frase_quebrada_em_duas_linhas():
    # Caso real: o Translate traduzia "Государственный" sozinho como "De propriedade do Estado"
    assert juntar_continuacoes(['Государственный', 'исторический музей']) == \
        ['Государственный исторический музей']


def test_mantem_frases_independentes():
    assert juntar_continuacoes(['Rauchen verboten', 'Bitte nicht rauchen']) == \
        ['Rauchen verboten', 'Bitte nicht rauchen']
    assert juntar_continuacoes(['Выход в город', 'Красная площадь']) == \
        ['Выход в город', 'Красная площадь']


def test_pontuacao_encerra_a_frase():
    assert juntar_continuacoes(['Achtung!', 'nicht betreten']) == ['Achtung!', 'nicht betreten']


def test_arabe_fica_separado_e_linhas_vazias_somem():
    assert juntar_continuacoes(['شارع التحرير', '', 'Tahrir Street']) == ['شارع التحرير', 'Tahrir Street']


def test_rotulos_comuns_usam_traducao_fixa_sem_chamar_o_translate(aws):
    # Caso real: "Sign" virava "assine"
    assert traduzir_rotulos(['Sign', 'Text', 'Monument']) == ['placa', 'texto', 'monumento']
    assert aws['translate'].chamadas == []


def test_rotulos_desconhecidos_vao_para_o_translate(aws):
    aws['translate'].dicionario = {'Gazebo': 'Coreto'}
    assert traduzir_rotulos(['Sign', 'Gazebo', 'Tower']) == ['placa', 'coreto', 'torre']
    assert aws['translate'].chamadas == [('Gazebo', 'en')]
