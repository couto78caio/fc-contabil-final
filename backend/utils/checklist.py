import os
import json

def atualizar_checklist(cnpj, modalidade, mes):
    path = os.path.join('uploads', cnpj, 'checklist.json')
    checklist = {}

    if os.path.exists(path):
        with open(path, 'r') as f:
            checklist = json.load(f)

    if mes not in checklist:
        checklist[mes] = []

    if modalidade not in checklist[mes]:
        checklist[mes].append(modalidade)

    with open(path, 'w') as f:
        json.dump(checklist, f)