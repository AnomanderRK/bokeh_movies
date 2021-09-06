import pandas as pd


def get_genres(df: pd.DataFrame, genres_col: str = 'Genre') -> list:
    """get genres from df"""
    genres = list()

    for _, row in df.iterrows():
        try:
            current_genres: list = row[genres_col].split() if row[genres_col] else []
            for genre in current_genres:
                genre = genre.strip().strip(',').capitalize()
                if genre not in genres:
                    genres.append(genre)
        except AttributeError:
            pass
    return genres


def map_point_size(revenue: float, min_revenue: float, max_revenue: float,
                   map_min: float = 0.1, map_max: float = 0.9) -> float:
    """
    map revenue from min_revenue-max_revenue range to map_min-map_max

    Parameters
    ----------
    revenue:
        revenue for current row
    min_revenue:
        min revenue in selection
    max_revenue:
        max revenue in selection
    map_min:
        min size value in mapping
    map_max:
        max size value in mapping

    Returns
    -------
    mapping value to map_min-map_max range

    """
    if not (min_revenue < revenue < max_revenue):
        # values outside range
        return map_min if revenue <= map_min else map_max
    current_value = revenue - min_revenue
    map_range = map_max - map_min
    revenue_range = max_revenue - min_revenue
    return map_min + (map_range / revenue_range) * current_value
