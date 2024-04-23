from typing import Dict, List

DATA_PROPERTIES_MAPPING = {

    'perpetrator_identification': ('Personas', 'Autores', 'Identificación'),
    'perpetrator_gender': ('Personas', 'Autores', 'Sexo'),
    'perpetrator_ethnicity': ('Personas', 'Autores', 'Raça/Cor'),
    'perpetrator_age_range': ('Personas', 'Autores', 'Idade'),
    'perpetrator_academic_level': ('Personas', 'Autores', 'Educación'),
    'perpetrator_job_status': ('Personas', 'Autores', 'Empleado'),
    'perpetrator_victim_relationship': ('Personas', 'Autores', 'Relación con la víctima'),

    'victim_gender': ('Personas', 'Víctima', 'Sexo'),
    'victim_ethnicity': ('Personas', 'Víctima', 'Raça/Cor'),
    'victim_age_range': ('Personas', 'Víctima', 'Idade'),
    'victim_academic_level': ('Personas', 'Víctima', 'Educación'),
    'victim_job_status': ('Personas', 'Víctima', 'Empleado'),

    'date_day_type': ('Momentos', 'Día', 'Tipo de Día'),
    'date_day_of_the_week': ('Momentos', 'Día', 'Día de la semana'),
    'date_time_of_day': ('Momentos', 'Horario', 'N/A'),

    'concentration': ('Lugares', 'Concentración', 'N/A'),
    'place_type': ('Lugares', 'Tipo de lugar', 'N/A'),

    'weapon': ('Modalidad', 'Empleado significa', 'N/A'),
    'typology': ('Modalidad', 'Tipo', 'N/A'),
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
