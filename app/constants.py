from typing import Dict, List

DATA_PROPERTIES_MAPPING = {

    'perpetrator_identification': ('Pessoas', 'Autores', 'Identificação'),
    'perpetrator_gender': ('Pessoas', 'Autores', 'Sexo'),
    'perpetrator_ethnicity': ('Pessoas', 'Autores', 'Raça/Cor'),
    'perpetrator_age_range': ('Pessoas', 'Autores', 'Idade'),
    'perpetrator_academic_level': ('Pessoas', 'Autores', 'Escolaridade'),
    'perpetrator_job_status': ('Pessoas', 'Autores', 'Empregado(a)'),
    'perpetrator_victim_relationship': ('Pessoas', 'Autores', 'Relação com a Vítima'),

    'victim_gender': ('Pessoas', 'Vítima', 'Sexo'),
    'victim_ethnicity': ('Pessoas', 'Vítima', 'Raça/Cor'),
    'victim_age_range': ('Pessoas', 'Vítima', 'Idade'),
    'victim_academic_level': ('Pessoas', 'Vítima', 'Escolaridade'),
    'victim_job_status': ('Pessoas', 'Vítima', 'Empregado(a)'),

    'date_day_type': ('Momentos', 'Dia', 'Tipo de Dia'),
    'date_day_of_the_week': ('Momentos', 'Dia', 'Dia da Semana'),
    'date_time_of_day': ('Momentos', 'Horário', 'N/A'),

    'concentration': ('Lugares', 'Concentração', 'N/A'),
    'place_type': ('Lugares', 'Tipo de lugar', 'N/A'),

    'weapon': ('Modalidade', 'Meio empregado', 'N/A'),
    'typology': ('Modalidade', 'Tipologia', 'N/A'),
}


def format_data_characteristics(data: Dict) -> List:
    output = list()
    for db_field, property_paths in DATA_PROPERTIES_MAPPING.items():
        if len(property_paths) != 3:
            continue

        if not isinstance(data[db_field], list):
            continue

        first_node = next((item for item in output if item["name"] == property_paths[0]), None)
        if not first_node:
            output.append(first_node := dict(name=property_paths[0], iconName=None, data=list()))

        second_node = next((item for item in first_node["data"] if item["name"] == property_paths[1]), None)
        if not second_node:
            first_node["data"].append(second_node := dict(name=property_paths[1], data=list()))

        second_node["data"].append({property_paths[2]: data[db_field]})

    return output
