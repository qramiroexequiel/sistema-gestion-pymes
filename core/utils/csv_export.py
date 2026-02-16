"""
Utilidades para exportación CSV.
"""

import csv
from django.http import HttpResponse


def export_csv_response(filename, headers, rows):
    """
    Genera una respuesta HTTP con CSV.
    
    Args:
        filename: Nombre del archivo (sin extensión)
        headers: Lista de encabezados
        rows: Lista de listas con datos
    
    Returns:
        HttpResponse con CSV
    """
    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = f'attachment; filename="{filename}.csv"'
    
    # UTF-8 BOM para compatibilidad con Excel
    response.write('\ufeff')
    
    writer = csv.writer(response)
    writer.writerow(headers)
    
    for row in rows:
        writer.writerow(row)
    
    return response

