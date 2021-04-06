print('Importando librerias')
import pandas as pd
import numpy as np
import geopandas
import matplotlib.pyplot as plt
import mapclassify
import math
import os

from cartopy import crs
from mpl_toolkits.axes_grid1 import make_axes_locatable
from matplotlib.colors import LinearSegmentedColormap
from tkinter import *
import glob
from PIL import Image, ImageTk
from tkinter import ttk
import tkinter.font as TkFont

import ipywidgets as widgets
from ipywidgets import interact, interact_manual

def read_dataframe(path):
    if(path[-4:] == ".csv"):
        try:
            df = pd.read_csv(path)
        except:
            df = pd.read_csv(path, sep=';')
    else:
        df = pd.read_excel(path)
    return df

def reduce_dataframe(df, measure):

    df = df.loc[df['Measure'] == measure]
    
    df = df[['#Average Value', 'Country or Area', 'Year']]
    return df

def genera_mapa():
    world = geopandas.read_file(
        geopandas.datasets.get_path('naturalearth_lowres')
    )
    world.drop(["continent", "pop_est", "iso_a3", "gdp_md_est"], axis=1, inplace = True)

    comp = pd.read_excel("output.xlsx", header=None)

    #Actualización de nombres del dataset del mundo
    for i in range(len(comp)):
        old = comp[1][i]
        new = comp[0][i]
        if(world[world['name'] == old].index.any()):
            ind = world[world['name'] == old].index[0]
            world.at[ind, 'name'] = new
    world = world.set_index('name')
    return world

def elimina_Areas(df, world):
    res = df.copy()
    res = res[res['Country or Area'].isin(list(world.index.values.tolist()))]
    return res

def vacia_carpeta():
    files = glob.glob('plots/*')
    for f in files:
        os.remove(f)


def genera_gif(fp_out = "image.gif"):
    fp_in = "plots/*"
    if len(os.listdir('plots')) != 0:
        # https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html#gif
        img, *imgs = [Image.open(f) for f in sorted(glob.glob(fp_in))]
        img.save(fp=fp_out, format='GIF', append_images=imgs, save_all=True, duration=350, loop=0)

def getPrevYearValue(df, year, index, column, fechaInicial, distance, world):
    if(year < fechaInicial or math.isnan(year)):
        return None, None
    else:
        df2 = df.loc[df['Year'] == year]
        df2 = pd.concat([world, df2], axis=1)
    try:
        res = float(df2.loc[index, column].rstrip('%'))
    except:
        distance += 1
        res, distance = getPrevYearValue(df, year-1, index, column, fechaInicial, distance, world)   
    return res, distance

def getNextYearValue(df, year, index, column, fechaFinal, distance, world):
    if(year > fechaFinal or math.isnan(year)):
        return None, None
    else:
        df2 = df.loc[df['Year'] == year + 1]
        df2 = df2.set_index('Country or Area')
        df2 = pd.concat([world, df2], axis=1)
    try:
        res = float(df2.loc[index, column].rstrip('%'))
    except:
        distance += 1
        res, distance = getNextYearValue(df, year+1, index, column, fechaFinal, distance, world)
    return res, distance

def getNextValue(row, column, df, fechaFinal, i, iterations, world):
    currentYearValue = row['#Average Value']
    if(currentYearValue is None):
        return None
    if((not math.isnan(currentYearValue))):
        NextYearValue, distance = getNextYearValue(df, row['Year'], row.name, column, fechaFinal, 1, world)
        if(NextYearValue is not None):
            return currentYearValue + ((NextYearValue - currentYearValue)/distance)*i/iterations
        else: return currentYearValue
    else: return None

def regression(row, column, df, fechaInicial, fechaFinal, world):
    prv, d1 = getPrevYearValue(df, row['Year'], row.name, column, fechaInicial, 0, world)
    nxt, d2 = getNextYearValue(df, row['Year'], row.name, column, fechaFinal, 1, world)
    if(d1==0):
        return prv
    if(d2==0):
        return nxt
    if(prv == None):
        return None
    if(nxt == None):
        return prv
    return prv + d1*((nxt-prv)/(d1+d2))

def getFiles(path):
    files = glob.glob(path + '/*')
    res = []
    for f in files:
        res.append(os.path.basename(f))
    return res

def convertToFloat(df, column='#Average Value'):
    res = df.copy()
    res[column] = res[column].astype(str)
    res[column] = res[column].apply(lambda y : ''.join(filter(lambda x: x.isdigit() or x=='.', y)))
    res[column] = res[column].replace('', np.nan)
    res[column] = res[column].astype(float)
    return res

def getValueRange(df, column='#Average Value', fechaInicial=2000, fechaFinal=2018):
    return df[column].min(), df[column].max()

def show_world_map(df, world, yr=2000, cmap="Greens", estilo="", title="", smooth=False, regrs=False, fechaFinal=2020, fechaInicial=2000, showYear=True, proj='PlateCarree', min=0, max=100):
    if(smooth): 
        iterations = 10
    else:
        iterations = 2
    projection = 'crs.' + proj + '()'
    
    df2 = df.loc[df['Year'] == yr]
    df2 = df2.set_index('Country or Area')
    if df2.empty:
        return None
    aux2 = pd.concat([world, df2], axis=1)
    aux2 = aux2[aux2['geometry'].notna()]
    if(regrs):
        aux['Year']=yr
        aux['#Average Value'] = aux.apply(regression, args=('#Average Value',df,fechaInicial, fechaFinal, world), axis=1)
        
    for j in range(1, iterations):
        plt.style.use(estilo)
        if (proj != 'None'):
            crs1 = eval(projection)
            fig, ax = plt.subplots(1, 1, figsize=(20,14), subplot_kw={'projection': crs1})
            ccrs_proj4 = crs1.proj4_init
            aux = aux2.copy()
            aux = aux.to_crs(ccrs_proj4)
            ax.gridlines()
        else:
            fig, ax = plt.subplots(1, 1, figsize=(20,14))
            aux = aux2.copy()
            plt.axis('off')

        aux['#Average Value'] = aux.apply(getNextValue, args=('#Average Value',df,fechaFinal, j, iterations, world), axis=1)        
        aux.plot(
            ax=ax,
            edgecolor='black', linewidth=2,
            column='#Average Value',
            missing_kwds={
                "color": "lightgrey",
                "edgecolor": "black",
                "hatch": "///",
                "label": "Missing values",
            },
        )
        aux.plot(ax=ax, 
                legend=True, 
                vmin=min, vmax=max,
                cmap=cmap,
                column='#Average Value',
                legend_kwds={
                    'shrink': 1,     
                    'orientation': 'horizontal'
                })

        if(showYear):
            ax.set_title(yr, fontsize=128,  x=0, y=-0.15)
        fig.suptitle(title, fontsize=32, y=0.97)
        fig.savefig(f'plots/plot-{yr}-{j}.jpg')
        plt.close('all')

def interfaz():
    ### VENTANA 1
    ventana= Tk()
    
    default_font = TkFont.nametofont("TkDefaultFont")
    default_font.configure(size=16)
    ventana.option_add("*Font", default_font)
    
    C = Canvas(ventana, bg="skyblue", height=250, width=300)
    
    styles = plt.style.available
    colores = ['Greens', 'viridis', 'plasma', 'inferno', 'magma', 'cividis', 'Greys', 'Purples', 'Blues', 'Oranges', 'Reds', 'YlOrBr', 'YlOrRd', 'OrRd', 'PuRd', 'RdPu', 'BuPu', 'GnBu', 'PuBu', 'YlGnBu', 'PuBuGn', 'BuGn', 'YlGn', 'binary', 'gist_yarg', 'gist_gray', 'gray', 'bone', 'pink', 'spring', 'summer', 'autumn', 'winter', 'cool', 'Wistia', 'hot', 'afmhot', 'gist_heat', 'copper', 'PiYG', 'PRGn', 'BrBG', 'PuOr', 'RdGy', 'RdBu', 'RdYlBu', 'RdYlGn', 'Spectral', 'coolwarm', 'bwr', 'seismic','Pastel1', 'Pastel2', 'Paired', 'Accent', 'Dark2', 'Set1', 'Set2', 'Set3', 'tab10', 'tab20', 'tab20b', 'tab20c']
    goals = getFiles('datos')
    projections = ['AlbersEqualArea', 'AzimuthalEquidistant', 'EquidistantConic', 'LambertConformal', 'LambertCylindrical', 'Mercator', 'Mollweide', 'Orthographic', 'Robinson', 'Sinusoidal', 'Stereographic', 'TransverseMercator', 'InterruptedGoodeHomolosine', 'RotatedPole', 'Geostationary', 'NearsidePerspective', 'EckertI', 'EckertII', 'LambertAzimuthalEqualArea', 'EqualEarth']
        
    
    ventana.title("Selección de parámetros")
    ventana.geometry("1280x720")
    goal = StringVar()
    goal.set(goals[0])
    
    fechaInicial = IntVar()
    fechaInicial.set("2000")
    fechaFinal = IntVar()
    fechaFinal.set("2018")
    estilo = StringVar()
    cmap = StringVar()
    cmap.set(colores[0])
    smooth= BooleanVar()
    regr= BooleanVar()
    title = StringVar()
    showYear= BooleanVar()
    showYear.set(True)
    proj = StringVar()
    proj.set(projections[0])

    etiqueta1 = Label(ventana, text="GOAL",  width=12).place(relx=.022, rely=.3)
    caja1 =  OptionMenu(ventana, goal, *goals).place(relx=.33, rely=.3)
    etiqueta3 = Label(ventana, text=" Fechas:",  width=12).place(relx=.022, rely=.454)
    caja3a = Entry(ventana, textvariable=fechaInicial, justify="center", width=6).place(relx=.33 , rely=.454)
    caja3b = Entry(ventana, textvariable=fechaFinal, justify="center",  width=6).place(relx=.40 , rely=.454)
    etiqueta4 = Label(ventana, text=" Estilo:",  width=12).place(relx=.022, rely=.53)
    spinbox4 = Spinbox(ventana, textvariable=estilo, values=styles,  justify="center",  wrap = True, width = 12).place(relx=.33 , rely=.53)
    etiqueta5 = Label(ventana, text=" Coloreado:",  width=12).place(relx=.55, rely=0.3)
    spinbox5 = OptionMenu(ventana, cmap, *colores).place(relx=.77 , rely=.3)
    etiqueta6 = Label(ventana, text=" Título ",  width=12).place(relx=.022, rely=0.15)
    caja6 = Entry(ventana, textvariable=title, justify="center", width=90).place(relx=.15 , rely=.15)
    etiqueta7 = Label(ventana, text=" Proyección ",  width=12).place(relx=.55, rely=0.454)
    caja7 = OptionMenu(ventana, proj, *projections).place(relx=.77 , rely=.454)
    
    seleccion1 = Radiobutton(ventana, text="Sin suavizado", value=False, variable=smooth, bg = "skyblue", width=12).place(relx = .065, rely = .7)
    seleccion2 = Radiobutton(ventana, text="Con suavizado", value=True, variable=smooth, bg = "skyblue", width=12).place(relx = .22, rely = .7)
    seleccion3 = Radiobutton(ventana, text="Sin regresión ", value=False, variable=regr, bg = "skyblue", width=12).place(relx = .065, rely = .78)
    seleccion4 = Radiobutton(ventana, text="Con regresión ", value=True, variable=regr, bg = "skyblue", width=12).place(relx = .22, rely = .78)                          
    seleccion5 = Radiobutton(ventana, text="Mostrar año", value=True, variable=showYear, bg = "skyblue", width=12).place(relx = .065, rely = .86)
    seleccion6 = Radiobutton(ventana, text="No mostrar Año", value=False, variable=showYear, bg = "skyblue", width=12).place(relx = .22, rely = .86)
    boton = Button(ventana, text="Aceptar", command=ventana.destroy, bg = "dodgerblue", activebackground = "skyblue",width = 20, font=('Comic Sans MS', 15, 'bold')).place(relx=.712, rely=.808)
    
    C.pack(fill=BOTH, expand=YES)
    image = Image.open("image.png")
    bg = ImageTk.PhotoImage(image)
    C.create_image( 0, 0, image = bg, anchor = "nw")
    ventana.mainloop()
    
    goal = goal.get()
    fechaInicial = fechaInicial.get()
    fechaFinal = fechaFinal.get()
    estilo = estilo.get()
    cmap = cmap.get()
    smooth = smooth.get()
    regr = regr.get()
    title = title.get()
    showYear = showYear.get()
    proj = proj.get()
    
    df = read_dataframe('datos/' + goal)
    
    ### VENTANA 2
    ventana= Tk()
    C = Canvas(ventana, bg="skyblue", height=250, width=300)
    ventana.title("Selección Measure")
    ventana.geometry("1200x300")
    
    measures=df['Measure'].unique()
    measure = StringVar()
    measure.set(measures[0])
    
    etiqueta2 = Label(ventana, text=" Measure").place(relx=.022, rely=.374)
    options2 = OptionMenu(ventana, measure, *measures).place(relx=.33 , rely=.374)

    boton = Button(ventana, text="Aceptar", command=ventana.destroy, bg = "dodgerblue", activebackground = "skyblue",width = 15, font=('Comic Sans MS', 15, 'bold')).place(relx=.45, rely=.808)
    C.pack(fill=BOTH, expand=YES)
    image = Image.open("image2.png")
    bg = ImageTk.PhotoImage(image)
    C.create_image( 0, 0, image = bg, anchor = "nw")
    ventana.mainloop()
    
    measure = measure.get()

    return goal, fechaInicial, fechaFinal, estilo, title, cmap, smooth, regr, showYear, df, measure, proj

def buclePrincipal():
    print('Obteniendo parametros')
    goal, fechaInicial, fechaFinal, estilo, title, cmap, smooth, regrs, showYear, df, measure, proj = interfaz()
    
    print('Reduciendo parámetros del dataframe')
    df = reduce_dataframe(df, measure)
    
    print('Convirtiendo la columna #Average Value a Float')
    df = convertToFloat(df, column='#Average Value')
        
    print('Cargando mapa del mundo')
    world = genera_mapa()
    
    print('Eliminando Areas (Conjuntos de paises)')
    df = elimina_Areas(df, world)
    
    print('Calculando Valores máximo y mínimo')
    min, max = getValueRange(df, column='#Average Value', fechaInicial=fechaInicial , fechaFinal=fechaFinal)

    print('Vaciando carpeta de ejecuciones anteriores')
    vacia_carpeta()
    
    print('Generando Imagenes')
    for i in range(fechaInicial, fechaFinal):
        print('Creando imagenes del año', i)
        try:
            show_world_map(df, world, yr=i, cmap=cmap, estilo=estilo, title=title, smooth=smooth, regrs=regrs, fechaFinal=fechaFinal, fechaInicial=fechaInicial, showYear=showYear, proj=proj, max=max, min=min)
        except:
            None
    print('Generando el gif')
    genera_gif()
    print('Ejecución exitosa')


buclePrincipal()