import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from flask import Flask, render_template, request
import numpy as np
import os, sys, stat

# Cambia los permisos de los archivos para que se puedan ejecutar en Heroku

# Definir los directorios a los que se les cambiarán los permisos.
directories = ['.', './static', './templates', './static/src', './static/components']

# Recorrer los directorios y cambiar los permisos de cada archivo.
for directory in directories:
    for root, dirs, files in os.walk(directory):
        for name in files:
            path = os.path.join(root, name)
            permisos_actuales = os.stat(path).st_mode
            print(f"Los permisos actuales del archivo {path} son: {oct(permisos_actuales & 0o777)}")
            os.chmod(path, 0o755)
            # Obtener información sobre el archivo.
            file_stat = os.stat(path)
            # Imprimir el modo (permisos) del archivo en octal.
            print(f"Los permisos del archivo {path} son: {oct(file_stat.st_mode & 0o777)}")

# Inicializa la aplicación Flask

app = Flask(__name__)

# Lee los archivos de Excel
leidos = pd.read_excel("Libros.xlsx")
para_leer = pd.read_excel("listofbooks.xlsx")

# Define la función para convertir a número
def convierte_a_numero(cadena):
    numeros = [c for c in str(cadena) if c.isdigit()]
    if numeros:
        return int("".join(numeros))
    else:
        return None 

# Aplica la función a la columna "num_page" de los DataFrames
leidos["num_page"] = leidos["num_page"].apply(convierte_a_numero)
para_leer["num_page"] = para_leer["num_page"].apply(convierte_a_numero)

# Función para filtrar los libros por longitud y género
def filtro_longitud(preferencia, limite, libros_para_leer):
    if preferencia.lower() == "corto":
        return libros_para_leer[libros_para_leer['num_page'] <= limite]
    elif preferencia.lower() == "extenso":
        return libros_para_leer[libros_para_leer['num_page'] > limite]
    else:
        return libros_para_leer

def filtro_genero(genero, libros):
    if genero != "Cualquiera":        
        return libros[(libros['main genre'] == genero)]
    else:
        return libros

# Función para comparar la sinopsis de los libros leídos con la sinopsis del libro a recomendar y asignar una puntuación a cada libro leído
def comparar_sinopsis(sinopsis, libros_leidos):
    puntuaciones = []
    for libro in libros_leidos['sinopsis']:
        puntuaciones.append(similitud_cos(libro, sinopsis))
    libros_leidos['puntuacion'] = puntuaciones
    libros_leidos_ordenados = libros_leidos.sort_values(by='puntuacion', ascending=False)
    return libros_leidos_ordenados

# Recomendador de libros basado en la sinopsis y el género del libro utilizando la similitud del coseno y hacer un random de los libros que tengan una puntuación mayor a 0.5
def recomendar_libro(preferencia, limite, genero, libros_leidos, libros_para_leer):   
    if request.method == 'POST':
        datos = request.form.to_dict()
        print(datos)  # Agregar esta línea

    libros_filtrados_por_genero = filtro_genero(genero, libros_para_leer)
    libros_filtrados_por_genero = libros_filtrados_por_genero.sample(20).reset_index(drop=True)
    print("Se han seleccionado 5 libros para leer")
    print(libros_filtrados_por_genero.head(5)) 
    libros_filtrados_por_longitud = filtro_longitud(preferencia, limite, libros_filtrados_por_genero)
    libros_ordenados_por_rating = libros_filtrados_por_longitud.sort_values(by='rating', ascending=False)
    for i, libro in libros_ordenados_por_rating.iterrows():
        libros_leidos_comparados = comparar_sinopsis(libro['sinopsis'], libros_leidos)
        if libros_leidos_comparados.iloc[0]['title'] != libro['title']:
            if pd.isna(libro['num_page']):
                # handle NaN value
                print("Nada")
            else:
                libro['num_page'] = int(libro['num_page'])
                
            return libro['title'], libro['author'], libro['main genre'], libro['second genre'], libro['num_page'], libro['rating'], libro['sinopsis'], libro['cover']
    return "No se encontró un libro para recomendar"

# Función para calcular la similitud del coseno
def similitud_cos(s1, s2):
    tfidf = TfidfVectorizer().fit_transform([s1, s2])
    return ((tfidf * tfidf.T).A)[0,1]

# Ruta inicial
@app.route('/', methods=['GET', 'POST'])
def recomendar():
    if request.method == 'GET':
        # Lógica para la solicitud GET
        return render_template('index.html')
    elif request.method == 'POST':
        # Lógica para la solicitud POST
        preferencia_longitud = request.form['longitud']
        if preferencia_longitud.lower() == "corto":
            limite_paginas = 500
        elif preferencia_longitud.lower() == "extenso":
            limite_paginas = 500
        else:
            limite_paginas = 0
        genero_elegido = request.form['genero']
        libro_recomendado = recomendar_libro(preferencia_longitud, limite_paginas, genero_elegido, leidos, para_leer)
        print("El libro elegido es: ", libro_recomendado[0])
        return render_template('index.html', libro=libro_recomendado)

app.run(debug=True, port = 1023)
