"""Inspiration taken from:
 https://github.com/bokeh/bokeh/tree/branch-2.4/examples/app/movies"""

import sqlite3 as sql
from os.path import dirname, join

import numpy as np
import pandas as pd
import pandas.io.sql as psql

from bokeh.io import curdoc
from bokeh.layouts import column, row, gridplot
from bokeh.models import ColumnDataSource, Div, Select, Slider, TextInput, RangeSlider
from bokeh.plotting import figure
from bokeh.sampledata.movies_data import movie_path
import sys

from os.path import dirname, join, abspath
try:
    from utils.helper_functions import get_genres, map_point_size
except ImportError:
    project_root = abspath(join(dirname(__file__), r".\.."))
    if project_root not in sys.path:
        sys.path.append(project_root)
    from utils.helper_functions import get_genres, map_point_size

# load constants
MIN_POINT_SIZE = 10
MAX_POINT_SIZE = 100
HIST_BINS = 50

# Read the data from bokeh samples
conn = sql.connect(movie_path)
query = open(join(dirname(__file__), r'.\..\utils', 'query.sql')).read()
movies = psql.read_sql(query, conn)

movies["color"] = np.where(movies["Oscars"] > 0, "orange", "grey")
movies["alpha"] = np.where(movies["Oscars"] > 0, 0.9, 0.25)
movies.fillna(0, inplace=True)  # just replace missing values with zero
movies["revenue"] = movies.BoxOffice.apply(lambda x: '{:,d}'.format(int(x)))

axis_map: dict = {
    "Tomato Meter": "Meter",
    "Numeric Rating": "numericRating",
    "Number of Reviews": "Reviews",
    "Box Office (dollars)": "BoxOffice",
    "Length (minutes)": "Runtime",
    "Year": "Year",
}
genres = get_genres(movies)
genres.insert(0, 'All')
desc = Div(text=open(join(dirname(__file__), r'.\..\templates', "description.html")).read(),
           sizing_mode="stretch_width")

# Create Input controls
slider_reviews = Slider(title="Minimum number of reviews", value=80, start=10, end=300, step=10)
slider_year_range = RangeSlider(title="Year released",
                                start=movies.Year.min(),
                                end=movies.Year.max(),
                                value=(1990,
                                       movies.Year.max()),  # fixed point because before 1990 is not that interest
                                step=1)
slider_oscars = Slider(title="Minimum number of Oscar wins", start=0, end=4, value=0, step=1)
slider_boxoffice = Slider(title="Dollars at Box Office (millions)", start=0, end=800, value=0, step=1)
select_genre = Select(title="Genre", value="All",
                      options=genres)
director = TextInput(title="Director name contains")
cast = TextInput(title="Cast names contains")
select_x_axis = Select(title="X Axis", options=sorted(axis_map.keys()), value="Tomato Meter")
select_y_axis = Select(title="Y Axis", options=sorted(axis_map.keys()), value="Number of Reviews")

# Create Column Data Source that will be used by the plot
source = ColumnDataSource(data=dict(x=[], y=[], color=[], title=[], year=[], revenue=[], alpha=[], size=[]))

TOOLTIPS = [
    ("Title", "@title"),
    ("Year", "@year"),
    ("$", "@revenue")
]

p = figure(height=400, width=650, title="", toolbar_location=None, tooltips=TOOLTIPS)
p.circle(x="x", y="y", source=source, color="color", line_color=None, fill_alpha="alpha", size='size')

# create the horizontal histogram
hhist, hedges = np.histogram(movies['Meter'], bins=HIST_BINS)
p_histogram = figure(toolbar_location=None, width=p.width, height=200,
                     min_border=10, min_border_left=50, y_axis_location="right")
p_histogram.xgrid.grid_line_color = None
p_histogram.yaxis.major_label_orientation = np.pi/4
p_histogram.background_fill_color = "#fafafa"

h_hist_quad = p_histogram.quad(bottom=0, top=hhist, left=hedges[:-1],  right=hedges[1:], color="gray")
h_hist_quad_oscar = p_histogram.quad(bottom=0, top=hhist, left=hedges[:-1],  right=hedges[1:], color="orange")

# create the vertical histogram
vhist, vedges = np.histogram(movies['Reviews'], bins=HIST_BINS)
p_histogram_v = figure(toolbar_location=None, width=200, height=p.height,
                       min_border=10, min_border_left=50, y_axis_location="right")
p_histogram_v.xgrid.grid_line_color = None
p_histogram_v.yaxis.major_label_orientation = np.pi/4
p_histogram_v.background_fill_color = "#fafafa"

v_hist_quad = p_histogram_v.quad(bottom=vedges[:-1], top=vedges[1:], left=0,  right=vhist, color="gray")
v_hist_quad_oscar = p_histogram_v.quad(bottom=vedges[:-1], top=vedges[1:], left=0,  right=vhist, color="orange")


def select_movies():
    genre_val = select_genre.value
    director_val = director.value.strip()
    cast_val = cast.value.strip()
    selected = movies[
        (movies.Reviews >= slider_reviews.value) &
        (movies.BoxOffice >= (slider_boxoffice.value * 1e6)) &
        (movies.Year >= slider_year_range.value[0]) &       # min range
        (movies.Year <= slider_year_range.value[1]) &       # max range
        (movies.Oscars >= slider_oscars.value)
        ]

    if genre_val != "All":
        selected = selected[selected.Genre.str.contains(genre_val) == True]
    if director_val != "":
        selected = selected[selected.Director.str.contains(director_val) == True]
    if cast_val != "":
        selected = selected[selected.Cast.str.contains(cast_val) == True]
    return selected


def update():
    df = select_movies()
    x_name = axis_map[select_x_axis.value]
    y_name = axis_map[select_y_axis.value]

    p.xaxis.axis_label = select_x_axis.value
    p.yaxis.axis_label = select_y_axis.value
    p.title.text = "%d movies selected" % len(df)
    # map revenue to point size
    df.loc[:, 'revenue'] = df.loc[:, 'revenue'].str.replace(",", "").astype(float)
    min_revenue = min(df["revenue"])
    max_revenue = max(df["revenue"])
    size = df["revenue"].apply(lambda r: map_point_size(revenue=r,
                                                        min_revenue=min_revenue,
                                                        max_revenue=max_revenue,
                                                        map_min=MIN_POINT_SIZE,
                                                        map_max=MAX_POINT_SIZE))
    source.data = dict(
        x=df[x_name],
        y=df[y_name],
        color=df["color"],
        title=df["Title"],
        year=df["Year"],
        revenue=df["revenue"],
        alpha=df["alpha"],
        size=size,
    )
    # update histograms
    # horizontal
    h_hist1, h_edges = np.histogram(df[x_name], bins=HIST_BINS)
    h_hist_quad.data_source.data["top"] = h_hist1
    h_hist_quad.data_source.data["left"] = h_edges[:-1]
    h_hist_quad.data_source.data["right"] = h_edges[1:]
    # vertical
    v_hist1, v_edges = np.histogram(df[y_name], bins=HIST_BINS)
    v_hist_quad.data_source.data["right"] = v_hist1
    v_hist_quad.data_source.data["bottom"] = v_edges[:-1]
    v_hist_quad.data_source.data["top"] = v_edges[1:]
    # update separate histogram for movies that won at least one oscar
    # horizontal
    h_hist2, h_edges_o = np.histogram(df.loc[df.Oscars > 1, x_name], bins=HIST_BINS)
    h_hist_quad_oscar.data_source.data["top"] = h_hist2
    h_hist_quad_oscar.data_source.data["left"] = h_edges_o[:-1]
    h_hist_quad_oscar.data_source.data["right"] = h_edges_o[1:]
    # vertical
    v_hist2, v_edges_o = np.histogram(df.loc[df.Oscars > 1, y_name], bins=HIST_BINS)
    v_hist_quad_oscar.data_source.data["right"] = v_hist2
    v_hist_quad_oscar.data_source.data["bottom"] = v_edges_o[:-1]
    v_hist_quad_oscar.data_source.data["top"] = v_edges_o[1:]


controls = [slider_reviews, slider_boxoffice, select_genre,
            slider_year_range, slider_oscars, director,
            cast, select_x_axis, select_y_axis]
for control in controls:
    control.on_change('value', lambda attr, old, new: update())

# create layout
inputs = column(*controls, width=320)
plot_grid = gridplot([[p, p_histogram_v], [p_histogram, None]], merge_tools=False)
l = column(desc, row(inputs, plot_grid), sizing_mode="scale_both")

update()  # initial load of the data

curdoc().add_root(l)
curdoc().title = "Movies"
