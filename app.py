import mysql.connector as ms
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from flask import Flask, render_template, request
import numpy as np

conexion = ms.connect(host='us-cdbr-east-06.cleardb.net', 
                      database='heroku_10d26a3bc956359', 
                      user='bf96f903006815', 
                      password='a6e26608')

micursor = conexion.cursor()

col1 = ["title", "author", "`main genre`", "`second genre`","num_page", "rating", "sinopsis"]

micursor.execute(f"SELECT {', '.join(col1)} FROM libros")
filas = micursor.fetchall()

libros = pd.DataFrame(filas, columns=col1)

col2 = ["title", "author", "sinopsis", "`main genre`", "`second genre`", "rating", "num_page", "cover"]

micursor.execute(f"SELECT {', '.join(col2)} FROM recomendaciones")
filas = micursor.fetchall()

recomendaciones = pd.DataFrame(filas, columns=col2)

# Inicializa la aplicación Flask

app = Flask(__name__)

# Define la función para convertir a número
def convierte_a_numero(cadena):
    numeros = [c for c in str(cadena) if c.isdigit()]
    if numeros:
        return int("".join(numeros))
    else:
        return None 

# Aplica la función a la columna "num_page" de los DataFrames
libros["num_page"] = libros["num_page"].apply(convierte_a_numero)
recomendaciones["num_page"] = recomendaciones["num_page"].apply(convierte_a_numero)

# Función para filtrar los libros por longitud y género
def filtro_longitud(preferencia, limite, libros_recomendaciones):
    if preferencia.lower() == "corto":
        return libros_recomendaciones[libros_recomendaciones['num_page'] <= limite]
    elif preferencia.lower() == "extenso":
        return libros_recomendaciones[libros_recomendaciones['num_page'] > limite]
    else:
        return libros_recomendaciones

def filtro_genero(genero, libros):
    if genero != "Cualquiera":        
        return libros[(libros['`main genre`'] == genero)]
    else:
        return libros

# Función para comparar la sinopsis de los libros leídos con la sinopsis del libro a recomendar y asignar una puntuación a cada libro leído
def comparar_sinopsis(sinopsis, libros_libros):
    puntuaciones = []
    for libro in libros_libros['sinopsis']:
        puntuaciones.append(similitud_cos(libro, sinopsis))
    libros_libros['puntuacion'] = puntuaciones
    libros_libros_ordenados = libros_libros.sort_values(by='puntuacion', ascending=False)
    return libros_libros_ordenados

# Recomendador de libros basado en la sinopsis y el género del libro utilizando la similitud del coseno y hacer un random de los libros que tengan una puntuación mayor a 0.5
def recomendar_libro(preferencia, limite, genero, libros_libros, libros_recomendaciones):   
    if request.method == 'POST':
        datos = request.form.to_dict()

    libros_filtrados_por_genero = filtro_genero(genero, libros_recomendaciones)
    libros_filtrados_por_genero = libros_filtrados_por_genero.sample(20).reset_index(drop=True)
    print("Se han seleccionado 5 libros para leer")
    print(libros_filtrados_por_genero.head(5)) 
    libros_filtrados_por_longitud = filtro_longitud(preferencia, limite, libros_filtrados_por_genero)
    libros_ordenados_por_rating = libros_filtrados_por_longitud.sort_values(by='rating', ascending=False)
    for i, libro in libros_ordenados_por_rating.iterrows():
        libros_libros_comparados = comparar_sinopsis(libro['sinopsis'], libros_libros)
        if libros_libros_comparados.iloc[0]['title'] != libro['title']:
            if pd.isna(libro['num_page']):
                # handle NaN value
                print("Nada")
            else:
                libro['num_page'] = int(libro['num_page'])
                
            return libro['title'], libro['author'], libro['`main genre`'], libro['`second genre`'], libro['num_page'], libro['rating'], libro['sinopsis'], libro['cover']
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
        libro_recomendado = recomendar_libro(preferencia_longitud, limite_paginas, genero_elegido, libros, recomendaciones)
        print("El libro elegido es: ", libro_recomendado[0])
        return render_template('index.html', libro=libro_recomendado)

app.run(debug=True, port = 1023)

